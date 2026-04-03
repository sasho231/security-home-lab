# 🔐 Security Home Lab

> A hands-on cybersecurity architecture lab built from scratch on a local machine using exclusively open-source tooling. Implements real-world security patterns: Zero Trust Architecture, Kubernetes Security Posture Management, runtime threat detection, SIEM, and DevSecOps — zero cloud cost.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Windows 10 Host                              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    WSL2 — Ubuntu 22.04                       │   │
│  │                                                              │   │
│  │  ┌─────────────────────────────┐  ┌──────────────────────┐  │   │
│  │  │     Docker Engine           │  │   Tools (native)     │  │   │
│  │  │                             │  │                      │  │   │
│  │  │  ┌──────────────────────┐   │  │  kubectl             │  │   │
│  │  │  │   kind K8s Cluster   │   │  │  helm                │  │   │
│  │  │  │  ┌────────────────┐  │   │  │  trivy               │  │   │
│  │  │  │  │ control-plane  │  │   │  │  k9s                 │  │   │
│  │  │  │  ├────────────────┤  │   │  │  git                 │  │   │
│  │  │  │  │    worker 1    │  │   │  └──────────────────────┘  │   │
│  │  │  │  │  ┌──────────┐  │  │   │                            │   │
│  │  │  │  │  │  Falco   │  │  │   │                            │   │
│  │  │  │  │  │  (eBPF)  │  │  │   │                            │   │
│  │  │  │  │  └──────────┘  │  │   │                            │   │
│  │  │  │  ├────────────────┤  │   │                            │   │
│  │  │  │  │    worker 2    │  │   │                            │   │
│  │  │  │  │  ┌──────────┐  │  │   │                            │   │
│  │  │  │  │  │Falcosick │  │  │   │                            │   │
│  │  │  │  │  │    UI    │  │  │   │                            │   │
│  │  │  │  │  └──────────┘  │  │   │                            │   │
│  │  │  │  └────────────────┘  │   │                            │   │
│  │  │  └──────────────────────┘   │                            │   │
│  │  │                             │                            │   │
│  │  │  ┌──────────────────────┐   │                            │   │
│  │  │  │   Docker Compose     │   │                            │   │
│  │  │  │                      │   │                            │   │
│  │  │  │  Wazuh Manager       │   │                            │   │
│  │  │  │  Wazuh Indexer       │   │                            │   │
│  │  │  │  Wazuh Dashboard     │   │                            │   │
│  │  │  │  ─────────────────   │   │                            │   │
│  │  │  │  GitLab CE           │   │                            │   │
│  │  │  │  GitLab Runner       │   │                            │   │
│  │  │  │  ─────────────────   │   │                            │   │
│  │  │  │  Keycloak (next)     │   │                            │   │
│  │  │  └──────────────────────┘   │                            │   │
│  │  └─────────────────────────────┘                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detection Pipeline

```
K8s workload activity
        │
        ▼
┌───────────────┐     syscall events      ┌─────────────────┐
│  Falco (eBPF) │ ──────────────────────► │  Falcosidekick  │
│  DaemonSet    │                         │  Alert Router   │
└───────────────┘                         └────────┬────────┘
                                                   │
                          ┌────────────────────────┼────────────────────┐
                          ▼                        ▼                    ▼
                 ┌────────────────┐      ┌──────────────┐     ┌────────────────┐
                 │ Falcosidekick  │      │   Wazuh      │     │    Slack /     │
                 │      UI        │      │   SIEM       │     │    Webhook     │
                 │ localhost:2802 │      │ localhost:443 │     │   (optional)   │
                 └────────────────┘      └──────────────┘     └────────────────┘
```

---

## DevSecOps Pipeline

```
Developer pushes code
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│                    GitLab CE Pipeline                      │
│                                                           │
│  Stage: scan                                              │
│  ┌─────────────────┐ ┌──────────────┐ ┌───────────────┐  │
│  │    Gitleaks     │ │   Semgrep    │ │    Checkov    │  │
│  │                 │ │              │ │               │  │
│  │ Secret scanning │ │    SAST      │ │  IaC scanning │  │
│  │ API keys        │ │ Code bugs    │ │ K8s misconfig │  │
│  │ Passwords       │ │ Injections   │ │ Missing secctx│  │
│  └────────┬────────┘ └──────┬───────┘ └───────┬───────┘  │
│           └────────────────┼──────────────────┘          │
│                            ▼                              │
│                   All findings saved                      │
│                   as pipeline artifacts                   │
└───────────────────────────────────────────────────────────┘
        │
        ▼
   Fix findings → push again → pipeline re-runs
```

---

## Lab Components

### Kubernetes Security (KSPM)

| Tool | Purpose | Status |
|------|---------|--------|
| kind | Local 3-node K8s cluster (1 control-plane, 2 workers) | ✅ Running |
| kube-bench | CIS Kubernetes benchmark — checks cluster hardening | ✅ Done |
| Trivy | Scans images, IaC manifests, cluster for CVEs and misconfigs | ✅ Done |
| Falco | eBPF-based runtime threat detection — detects shells, sensitive file reads, privilege escalation | ✅ Running |
| Falcosidekick | Routes Falco alerts to SIEM, UI, webhooks | ✅ Running |

### SIEM & Detection

| Tool | Purpose | Status |
|------|---------|--------|
| Wazuh Manager | Receives agent events, runs detection rules, generates alerts | ✅ Running |
| Wazuh Indexer | OpenSearch-based event storage and search backend | ✅ Running |
| Wazuh Dashboard | Web UI — MITRE ATT&CK map, FIM, SCA, vulnerability detection | ✅ Running |
| Wazuh Agent | Installed on WSL2 host — monitors file integrity, auth, processes | ✅ Connected |

### DevSecOps Pipeline

| Tool | Purpose | Status |
|------|---------|--------|
| GitLab CE | Self-hosted Git server + CI/CD platform | ✅ Running |
| GitLab Runner | Pipeline executor — Docker-based job isolation | ✅ Registered |
| Gitleaks | Secret detection — finds hardcoded credentials in source code | ✅ Pipeline |
| Semgrep | SAST — static analysis, finds security bugs by pattern matching | ✅ Pipeline |
| Checkov | IaC scanner — validates K8s/Terraform against security benchmarks | ✅ Pipeline |

### Identity & Zero Trust (In Progress)

| Tool | Purpose | Status |
|------|---------|--------|
| Keycloak | Identity Provider — SSO, OIDC, SAML, MFA | 🔄 Next |
| HashiCorp Vault | Secrets management — no passwords in config files | 📋 Planned |

---

## Security Findings

Real security issues found and remediated during lab exercises.
Full reports with evidence in [docs/findings/](docs/findings/).

### DevSecOps Pipeline Findings

| Finding | Severity | Tool | File | Status |
|---------|----------|------|------|--------|
| Hardcoded API key in source code | CRITICAL | Gitleaks | app.py:10 | ✅ Fixed |
| Debug mode enabled in Flask app | MEDIUM | Semgrep | app.py | ✅ Fixed |
| Container running as root | HIGH | Checkov | k8s/deployment.yaml | ✅ Fixed |
| No resource limits set | MEDIUM | Checkov | k8s/deployment.yaml | ✅ Fixed |
| Writable root filesystem | HIGH | Checkov | k8s/deployment.yaml | ✅ Fixed |
| Privilege escalation not blocked | HIGH | Checkov | k8s/deployment.yaml | ✅ Fixed |

### Kubernetes CIS Benchmark (kube-bench)

CIS Kubernetes benchmark executed against local kind cluster.
Results documented in [docs/findings/kube-bench-results.txt](docs/findings/kube-bench-results.txt).

### Falco Runtime Detections

Custom Falco rules written and tested — alerts confirmed firing:

| Rule | MITRE Technique | Trigger |
|------|----------------|---------|
| Terminal shell in container | T1059 | kubectl exec into pod |
| Read sensitive file | T1552 | cat /etc/shadow in container |
| Suspicious download tool | T1105 | curl/wget inside container |

---

## Repository Structure

```
security-home-lab/
├── README.md
├── .gitignore
├── k8s/                          # Kubernetes manifests
│   ├── base/
│   │   ├── namespace.yaml
│   │   └── networkpolicy-default-deny.yaml
│   ├── falco/
│   │   └── values.yaml           # Helm values for Falco
│   └── apps/
│       ├── nginx-deployment.yaml
│       └── sample-app-deployment.yaml
├── docker/
│   ├── wazuh/                    # Wazuh SIEM Docker Compose
│   └── gitlab/                   # GitLab CE + Runner
├── falco-rules/                  # Custom Falco detection rules
│   └── suspicious-download.yaml
├── sample-app/                   # Deliberately insecure app for pipeline scanning
│   ├── app.py
│   ├── Dockerfile
│   └── .gitlab-ci.yml
└── docs/
    └── findings/                 # Security scan results and remediation
        ├── kube-bench-results.txt
        ├── trivy-config-scan.txt
        ├── trivy-nginx-image.txt
        └── devsecops-pipeline-findings.md
```

---

## Key Technical Decisions

### Why kind over minikube?
kind (Kubernetes IN Docker) creates disposable clusters in under 60 seconds. Entire cluster state is defined in a single YAML file — reproducible, version controlled, zero cost. Minikube is heavier and harder to script.

### Why Wazuh over raw Elastic Stack?
Wazuh ships pre-wired with SIEM, EDR agents, FIM, CIS benchmark scanning, MITRE ATT&CK mapping, and vulnerability detection out of the box. Raw ELK requires days of configuration before delivering security value. Wazuh uses Elastic under the hood — same stack, less setup.

### Why Falco with modern_ebpf driver?
The modern eBPF driver works without a kernel module — runs natively on WSL2 kernel 5.15+ with no configuration. Kernel module approach requires recompilation per kernel version. eBPF is also the production-standard approach for runtime security.

### Why GitLab CE over GitHub Actions?
Self-hosted gives full control over pipeline execution, runner configuration, and data. Demonstrates ability to operate a complete DevSecOps platform, not just consume a SaaS. GitLab CE includes secret detection, SAST, dependency scanning and container scanning in the free tier.

---

## Lessons Learned

- **Certificate management is the #1 deployment blocker** for enterprise security tools. Spent significant time debugging Wazuh TLS cert structure — directly applicable to real SIEM deployments.
- **Runner networking in containerised environments** requires explicit clone_url and extra_hosts configuration — localhost means different things inside and outside Docker.
- **eBPF driver compatibility** — modern_ebpf works on WSL2, legacy kernel module does not. Understanding driver compatibility is essential for production Falco deployments.
- **IaC is not optional** — every K8s manifest and Docker Compose file is version controlled. Cluster recreation after deletion takes under 5 minutes because all state is in Git.

---

## Environment

| Component | Specification |
|-----------|--------------|
| Host OS | Windows 10 |
| CPU | Intel i5-9300H (4c/8t, 2.4GHz) |
| RAM | 16GB (WSL2 capped at 10GB) |
| Linux | Ubuntu 22.04 via WSL2 |
| Container runtime | Docker Engine 26.x |
| Kubernetes | kind v0.23 |

---

## What's Next

- [ ] Keycloak — Identity Provider, OIDC/SAML, MFA, Zero Trust identity layer
- [ ] HashiCorp Vault — secrets management, dynamic credentials, K8s CSI integration
- [ ] Falco → Wazuh integration — K8s runtime alerts in SIEM
- [ ] kubernetes-goat — purple team exercises, attack simulation
- [ ] Terraform + AKS — cloud deployment, Azure CSPM with Prowler
