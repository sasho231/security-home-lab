# STRIDE Threat Model — Security Home Lab

**Author:** Aleksandar Tishev  
**Date:** April 2026  
**Version:** 1.0  
**Methodology:** STRIDE (Microsoft)  
**Scope:** Local security lab — WSL2 + Docker + Kubernetes  

---

## 1. System Overview

This threat model covers the security home lab architecture running on Windows 10 / WSL2.
The system implements Zero Trust Architecture principles using open-source tooling across
four security domains: identity, runtime detection, SIEM, and DevSecOps.

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│  TRUST BOUNDARY: WSL2 / Ubuntu 22.04                            │
│                                                                 │
│  ┌───────────────────────────────┐  ┌──────────────────────┐   │
│  │  TRUST BOUNDARY: K8s Cluster  │  │  TRUST BOUNDARY:     │   │
│  │                               │  │  Docker Network      │   │
│  │  [K8s API Server]             │  │                      │   │
│  │       ↓                       │  │  [Wazuh Manager]     │   │
│  │  [Falco DaemonSet]            │  │       ↓              │   │
│  │       ↓ alerts                │  │  [Wazuh Indexer]     │   │
│  │  [Falcosidekick]──────────────┼─►│       ↓              │   │
│  │       ↓                       │  │  [Wazuh Dashboard]   │   │
│  │  [nginx pod / sample-app]     │  │                      │   │
│  │                               │  │  [Keycloak]          │   │
│  └───────────────────────────────┘  │                      │   │
│                                     │  [GitLab CE]         │   │
│  [Developer] ──git push──►          │  [GitLab Runner]     │   │
│  [Browser]   ──auth──────►          │                      │   │
│  [Attacker]  ──attacks───►          └──────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Assets and Data Flows

### Critical Assets

| Asset | Classification | Location | Impact if Compromised |
|-------|---------------|----------|----------------------|
| Keycloak JWT signing keys | SECRET | Keycloak container | All tokens forgeable |
| Wazuh admin credentials | SECRET | Docker volume | SIEM blinded |
| GitLab root credentials | SECRET | Docker volume | Pipeline hijacked |
| K8s kubeconfig | SECRET | WSL2 filesystem | Full cluster control |
| Wazuh security events | SENSITIVE | Wazuh Indexer | Attack history exposed |
| GitLab source code | SENSITIVE | GitLab database | IP theft |
| Falco detection rules | INTERNAL | K8s ConfigMap | Detection blind spots |
| Pipeline secrets (env vars) | SECRET | GitLab CI variables | Credential theft |

### Data Flows

| ID | Flow | Protocol | Trust Boundary Crossed |
|----|------|----------|----------------------|
| DF1 | Developer → GitLab | SSH/HTTPS | External → Docker network |
| DF2 | GitLab → GitLab Runner | HTTP | Internal Docker network |
| DF3 | GitLab Runner → Registry | HTTPS | Docker network → internet |
| DF4 | Browser → Keycloak | HTTP | External → Docker network |
| DF5 | Keycloak → Browser | HTTP (JWT) | Docker network → external |
| DF6 | App → Keycloak | HTTP (OIDC) | K8s → Docker network |
| DF7 | Falco → Falcosidekick | gRPC | K8s internal |
| DF8 | Falcosidekick → Wazuh | HTTP webhook | K8s → Docker network |
| DF9 | Wazuh Agent → Manager | TCP 1514 | WSL2 → Docker network |
| DF10 | Wazuh Manager → Indexer | HTTPS 9200 | Docker internal |
| DF11 | kubectl → K8s API | HTTPS 6443 | External → K8s |

---

## 3. STRIDE Threat Analysis

### 3.1 Kubernetes API Server

**Component:** K8s API Server (kind cluster control plane)  
**Trust Level:** High — controls entire cluster  

| ID | STRIDE | Threat | Likelihood | Impact | Control | Detection |
|----|--------|--------|-----------|--------|---------|-----------|
| T01 | Spoofing | Attacker uses stolen kubeconfig to impersonate admin | Medium | CRITICAL | kubeconfig file permissions (600), stored outside repo | Wazuh FIM on kubeconfig file |
| T02 | Tampering | Malicious admission of privileged pod bypassing security controls | Low | HIGH | Pod Security Standards (restricted), OPA/Kyverno (planned) | kube-bench CIS checks |
| T03 | Repudiation | Admin actions not logged — cannot prove who did what | Medium | MEDIUM | K8s audit logging | Wazuh agent collecting K8s audit logs |
| T04 | Info Disclosure | API server responds to unauthenticated requests | Low | HIGH | RBAC enabled, anonymous auth disabled (kube-bench) | kube-bench CIS 1.2.1 check |
| T05 | DoS | Flood of API requests exhausts server resources | Low | MEDIUM | Resource quotas per namespace | Wazuh alert on API error spikes |
| T06 | Elevation | Pod escapes container and gains node-level access | Low | CRITICAL | Non-root pods, read-only filesystem, no privileged | Falco rule: container escape |

**Residual Risk:** MEDIUM — audit logging not fully configured in lab environment.

---

### 3.2 Falco Runtime Detection

**Component:** Falco DaemonSet + Falcosidekick  
**Trust Level:** High — security control plane  

| ID | STRIDE | Threat | Likelihood | Impact | Control | Detection |
|----|--------|--------|-----------|--------|---------|-----------|
| T07 | Spoofing | Attacker spoofs Falcosidekick webhook to inject false alerts | Low | MEDIUM | Webhook runs on internal network only | N/A — meta-detection needed |
| T08 | Tampering | Attacker modifies Falco rules ConfigMap to disable detections | Low | CRITICAL | RBAC limits ConfigMap write access | Wazuh FIM on Falco config |
| T09 | Repudiation | Falco alert fired but no persistent record — could be denied | Medium | MEDIUM | Falcosidekick forwards to Wazuh (persistent storage) | Wazuh event retention |
| T10 | Info Disclosure | Falco logs contain sensitive process arguments (passwords in cmdline) | Medium | HIGH | Scrub sensitive fields in Falco output | Review Falco alert content |
| T11 | DoS | Alert flood from noisy rule overwhelms Falcosidekick | Medium | MEDIUM | Rate limiting in Falcosidekick config | Monitor Falcosidekick queue depth |
| T12 | Elevation | Falco DaemonSet has privileged access — if compromised = node takeover | Low | CRITICAL | Falco runs as DaemonSet with minimal required privileges | Wazuh monitors Falco process |

**Residual Risk:** MEDIUM — Falco → Wazuh integration pending, alerts not fully persistent.

---

### 3.3 Wazuh SIEM

**Component:** Wazuh Manager + Indexer + Dashboard  
**Trust Level:** High — security monitoring system  

| ID | STRIDE | Threat | Likelihood | Impact | Control | Detection |
|----|--------|--------|-----------|--------|---------|-----------|
| T13 | Spoofing | Attacker registers rogue Wazuh agent to inject false events | Low | HIGH | Agent authentication token required | Wazuh agent registration log |
| T14 | Tampering | Attacker modifies Wazuh rules to suppress real alerts | Low | CRITICAL | Wazuh Manager access restricted to Docker network | Wazuh FIM on ruleset |
| T15 | Repudiation | Security events deleted from Indexer — no evidence of attack | Low | HIGH | Indexer access requires authentication | Indexer access audit log |
| T16 | Info Disclosure | Wazuh dashboard exposed without auth — events visible to anyone | Low | HIGH | Dashboard requires login (admin/SecretPassword) | N/A |
| T17 | DoS | Log flood from agent overwhelms Wazuh Manager | Medium | MEDIUM | Agent buffer limits, Manager queue management | Monitor Manager CPU/memory |
| T18 | Elevation | Wazuh Manager container escape — runs with elevated Docker privileges | Low | HIGH | Container runs as non-root where possible | Falco monitors Wazuh containers |

**Residual Risk:** MEDIUM — default password not changed in lab (SecretPassword). Would be CRITICAL in production.

---

### 3.4 Keycloak Identity Provider

**Component:** Keycloak 24.0 — realm: security-lab  
**Trust Level:** CRITICAL — identity authority for all services  

| ID | STRIDE | Threat | Likelihood | Impact | Control | Detection |
|----|--------|--------|-----------|--------|---------|-----------|
| T19 | Spoofing | Attacker steals JWT token and impersonates user | Medium | HIGH | Token expiry enforced (short TTL), HTTPS in production | Wazuh alert on auth anomalies |
| T20 | Spoofing | Brute force attack on user credentials | Medium | HIGH | Account lockout policy, MFA for admin users | Keycloak login failure events → Wazuh |
| T21 | Tampering | Attacker modifies JWT claims to elevate privileges | Low | CRITICAL | Tokens signed with RS256 — requires private key to forge | jwt.io signature validation |
| T22 | Tampering | Admin modifies realm config to disable MFA | Low | HIGH | Admin access requires authentication + MFA | Keycloak admin event log |
| T23 | Repudiation | User denies performing action — no audit trail | Medium | MEDIUM | Keycloak admin events enabled | Wazuh collects Keycloak logs |
| T24 | Info Disclosure | Token contains sensitive claims visible to client | Low | MEDIUM | Minimise claims in token — only include necessary roles | Review token payload at jwt.io |
| T25 | Info Disclosure | Keycloak running on HTTP (not HTTPS) in lab | HIGH | HIGH | Acceptable in lab — HTTPS mandatory in production | N/A — known lab limitation |
| T26 | DoS | Token endpoint flooded — auth service unavailable | Low | HIGH | Rate limiting (not configured in lab) | Monitor Keycloak response times |
| T27 | Elevation | Attacker gains Keycloak admin → creates admin user | Low | CRITICAL | Admin console restricted, strong password, MFA | Keycloak admin event: user creation |

**Residual Risk:** HIGH — HTTP only in lab is a known limitation. All other controls in place.

---

### 3.5 GitLab CE + DevSecOps Pipeline

**Component:** GitLab CE + GitLab Runner  
**Trust Level:** High — controls code and deployment pipeline  

| ID | STRIDE | Threat | Likelihood | Impact | Control | Detection |
|----|--------|--------|-----------|--------|---------|-----------|
| T28 | Spoofing | Attacker pushes code as legitimate developer | Low | HIGH | SSH key authentication for git push | GitLab push event log |
| T29 | Tampering | Developer modifies .gitlab-ci.yml to disable security scans | Medium | HIGH | Pipeline file changes visible in git history | Code review process (manual) |
| T30 | Tampering | Supply chain attack — malicious scanner image pulled | Low | CRITICAL | Pin scanner image versions (not :latest) | Trivy scans scanner images |
| T31 | Repudiation | Developer claims they didn't push malicious code | Low | MEDIUM | Git commit history with author + email | GitLab commit log |
| T32 | Info Disclosure | Pipeline logs contain secrets (env vars printed) | Medium | HIGH | Mask CI variables in GitLab settings | Review pipeline job output |
| T33 | Info Disclosure | Pipeline artifacts contain sensitive scan reports | Low | MEDIUM | Artifacts expire after 1 week, access controlled | N/A |
| T34 | DoS | Pipeline flooded with commits — runner exhausted | Low | LOW | Single runner — only 1 concurrent job | Monitor runner queue |
| T35 | Elevation | GitLab Runner has Docker socket access — container escape = host access | Medium | CRITICAL | Runner uses Docker executor, socket mount is required | Falco monitors Docker socket access |

**Residual Risk:** HIGH — T35 is inherent to Docker executor design. Mitigate with Kubernetes executor in production.

---

### 3.6 Developer Workstation (WSL2)

**Component:** WSL2 Ubuntu — kubectl, git, docker, helm  
**Trust Level:** Trusted — but single point of failure  

| ID | STRIDE | Threat | Likelihood | Impact | Control | Detection |
|----|--------|--------|-----------|--------|---------|-----------|
| T36 | Spoofing | Attacker gains WSL2 access → has all tool credentials | Low | CRITICAL | Windows login protection, disk encryption (BitLocker) | N/A — outside lab scope |
| T37 | Tampering | Malicious package installed via apt/pip poisons toolchain | Low | HIGH | Only install from official repos, verify GPG keys | Wazuh FIM on /usr/local/bin |
| T38 | Info Disclosure | kubeconfig, SSH keys, .env files on WSL2 filesystem | Medium | CRITICAL | .gitignore protects secrets from GitHub, file permissions | Wazuh FIM on home directory |
| T39 | Repudiation | Local git commits not signed — cannot verify author | Medium | LOW | Git commit signing (GPG) — not configured | N/A |

**Residual Risk:** MEDIUM — local machine security outside lab control boundary.

---

## 4. Threat Summary

### By Severity

| Severity | Count | Threats |
|----------|-------|---------|
| CRITICAL | 7 | T01, T06, T08, T12, T21, T27, T35 |
| HIGH | 14 | T02, T04, T10, T13, T14, T15, T16, T18, T19, T20, T25, T28, T32, T38 |
| MEDIUM | 12 | T03, T05, T07, T09, T11, T17, T22, T23, T26, T29, T34, T37 |
| LOW | 6 | T24, T30, T31, T33, T36, T39 |

### Top 5 Risks Requiring Action

| Priority | Threat | Risk | Recommended Action |
|----------|--------|------|--------------------|
| 1 | T35 — GitLab Runner Docker socket | CRITICAL | Switch to Kubernetes executor in production |
| 2 | T25 — Keycloak HTTP only | HIGH | Enable HTTPS with TLS certificate |
| 3 | T08 — Falco rules tampering | CRITICAL | Enable Wazuh FIM on Falco ConfigMap |
| 4 | T18 — Wazuh default password | HIGH | Change SecretPassword immediately |
| 5 | T38 — Secrets on WSL2 filesystem | CRITICAL | Enable BitLocker, review file permissions |

---

## 5. Controls Coverage Map

### STRIDE vs Controls

| STRIDE Category | Primary Control | Detection | Lab Status |
|----------------|----------------|-----------|------------|
| Spoofing | Keycloak MFA + JWT tokens | Wazuh auth events | Implemented |
| Tampering | Wazuh FIM, Git history, RBAC | Falco + Wazuh | Partial |
| Repudiation | Wazuh SIEM event storage | Indexed + searchable | Implemented |
| Info Disclosure | .gitignore, Gitleaks pipeline | GitLab pipeline | Implemented |
| Denial of Service | Resource limits on K8s pods | Wazuh monitoring | Partial |
| Elevation of Privilege | Non-root pods, RBAC, Falco rules | Falco real-time | Implemented |

---

## 6. MITRE ATT&CK Mapping

Threats mapped to MITRE ATT&CK for Containers framework:

| Threat ID | ATT&CK Technique | Tactic | Falco Rule |
|-----------|-----------------|--------|-----------|
| T06 | T1611 — Escape to Host | Privilege Escalation | container_escape |
| T08 | T1562.001 — Disable Security Tools | Defense Evasion | modify_falco_config |
| T19 | T1528 — Steal Application Token | Credential Access | N/A — network level |
| T20 | T1110 — Brute Force | Credential Access | Keycloak login events |
| T28 | T1195 — Supply Chain Compromise | Initial Access | N/A |
| T29 | T1553 — Subvert Trust Controls | Defense Evasion | monitor_ci_changes |
| T35 | T1552.007 — Container API | Credential Access | docker_socket_access |
| T37 | T1554 — Compromise Host Software Binary | Persistence | Wazuh FIM |

---

## 7. Assumptions and Limitations

1. **Lab environment** — this threat model covers a local lab, not a production system. Some controls (HTTPS, network isolation, HSM) are not implemented by design.
2. **Single-tenant** — all components run on one machine. In production each component would be isolated.
3. **Trusted developer** — insider threat from the lab operator is out of scope.
4. **No network perimeter** — lab runs entirely on localhost. Production deployments require network-level controls.
5. **Container runtime trust** — Docker Engine on WSL2 is assumed trustworthy. Compromised Docker daemon is out of scope.

---

## 8. Residual Risk Acceptance

| Risk | Accepted | Justification |
|------|----------|---------------|
| Keycloak HTTP only | YES — lab only | HTTPS requires certificate infrastructure not needed for learning |
| Default Wazuh password | YES — lab only | SecretPassword acceptable in isolated lab — mandatory change before production |
| Docker socket in Runner | YES — lab only | Required for Docker executor — use K8s executor in production |
| No K8s audit logging | YES — lab only | Complex to configure in kind — implement on AKS (cloud phase) |

---

## 9. Next Steps

- [ ] Implement Wazuh FIM rules for Falco ConfigMap (T08)
- [ ] Add pre-commit hooks to prevent secret commits (T38)
- [ ] Configure Keycloak HTTPS with self-signed cert (T25)
- [ ] Change Wazuh default password (T18)
- [ ] Add OPA/Kyverno admission controller (T02)
- [ ] Enable K8s audit logging on AKS (cloud phase)
- [ ] Pin scanner image versions in .gitlab-ci.yml (T30)
- [ ] Sign git commits with GPG key (T39)

---

*Threat model generated using STRIDE methodology. Review and update when architecture changes.*
