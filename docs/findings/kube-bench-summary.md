# kube-bench Security Audit Summary

**Date:** 2026-04-02
**Tool:** kube-bench (CIS Kubernetes Benchmark)
**Scope:** Worker Node (Section 4) + Kubernetes Policies (Section 5)

---

## Overall Results

| Status | Count |
|--------|-------|
| PASS   | 17    |
| FAIL   | 2     |
| WARN   | 42    |
| INFO   | 0     |

---

## Section 4 — Worker Node Security Configuration

**Results: 17 PASS | 2 FAIL | 7 WARN**

### 4.1 Worker Node Configuration Files

| ID     | Status | Check |
|--------|--------|-------|
| 4.1.1  | FAIL   | kubelet service file permissions are not 600 or more restrictive |
| 4.1.2  | PASS   | kubelet service file ownership is root:root |
| 4.1.3  | WARN   | proxy kubeconfig file permissions (manual check) |
| 4.1.4  | WARN   | proxy kubeconfig file ownership (manual check) |
| 4.1.5  | PASS   | kubelet.conf permissions set to 600 or more restrictive |
| 4.1.6  | PASS   | kubelet.conf ownership is root:root |
| 4.1.7  | PASS   | Certificate authorities file permissions are 644 or more restrictive |
| 4.1.8  | PASS   | Client certificate authorities file ownership is root:root |
| 4.1.9  | FAIL   | kubelet config.yaml permissions are not 600 or more restrictive |
| 4.1.10 | PASS   | kubelet config.yaml ownership is root:root |

### 4.2 Kubelet

| ID     | Status | Check |
|--------|--------|-------|
| 4.2.1  | PASS   | --anonymous-auth is set to false |
| 4.2.2  | PASS   | --authorization-mode is not AlwaysAllow |
| 4.2.3  | PASS   | --client-ca-file is set |
| 4.2.4  | PASS   | --read-only-port is set to 0 |
| 4.2.5  | PASS   | --streaming-connection-idle-timeout is not 0 |
| 4.2.6  | PASS   | --make-iptables-util-chains is true |
| 4.2.7  | PASS   | --hostname-override is not set |
| 4.2.8  | PASS   | eventRecordQPS is set appropriately |
| 4.2.9  | WARN   | --tls-cert-file and --tls-private-key-file not configured |
| 4.2.10 | PASS   | --rotate-certificates is not false |
| 4.2.11 | PASS   | RotateKubeletServerCertificate is true |
| 4.2.12 | WARN   | Strong cryptographic ciphers not enforced |
| 4.2.13 | WARN   | No limit set on pod PIDs |
| 4.2.14 | WARN   | --seccomp-default not set to true |
| 4.2.15 | WARN   | --IPAddressDeny not set |

### 4.3 kube-proxy

| ID    | Status | Check |
|-------|--------|-------|
| 4.3.1 | PASS   | kube-proxy metrics service is bound to localhost |

---

## Section 5 — Kubernetes Policies

**Results: 0 PASS | 0 FAIL | 35 WARN**

All checks in this section are Manual and resulted in WARN — they require human review.

### 5.1 RBAC and Service Accounts (13 WARNs)

| ID     | Check |
|--------|-------|
| 5.1.1  | cluster-admin role may be over-assigned |
| 5.1.2  | Access to Secrets not minimized |
| 5.1.3  | Wildcard use in Roles/ClusterRoles not eliminated |
| 5.1.4  | Create access to pods not minimized |
| 5.1.5  | Default service accounts may be actively used |
| 5.1.6  | Service Account Tokens may be auto-mounted unnecessarily |
| 5.1.7  | system:masters group membership not verified |
| 5.1.8  | Bind, Impersonate, Escalate permissions not minimized |
| 5.1.9  | Create access to PersistentVolumes not minimized |
| 5.1.10 | Access to node proxy sub-resource not minimized |
| 5.1.11 | Access to CSR approval sub-resource not minimized |
| 5.1.12 | Access to webhook configuration objects not minimized |
| 5.1.13 | Service account token creation access not minimized |

### 5.2 Pod Security Standards (13 WARNs)

| ID     | Check |
|--------|-------|
| 5.2.1  | No active policy control mechanism (PSA/OPA) confirmed |
| 5.2.2  | Privileged containers not restricted |
| 5.2.3  | hostPID containers not restricted |
| 5.2.4  | hostIPC containers not restricted |
| 5.2.5  | hostNetwork containers not restricted |
| 5.2.6  | allowPrivilegeEscalation not restricted |
| 5.2.7  | Root containers not restricted |
| 5.2.8  | NET_RAW capability not restricted |
| 5.2.9  | Added capabilities not restricted |
| 5.2.10 | Capabilities not dropped across the board |
| 5.2.11 | Windows HostProcess containers not restricted |
| 5.2.12 | HostPath volumes not restricted |
| 5.2.13 | HostPorts not restricted |

### 5.3 Network Policies and CNI (2 WARNs)

| ID    | Check |
|-------|-------|
| 5.3.1 | CNI support for NetworkPolicies not confirmed |
| 5.3.2 | Not all namespaces have NetworkPolicies defined |

### 5.4 Secrets Management (2 WARNs)

| ID    | Check |
|-------|-------|
| 5.4.1 | Secrets may be exposed as environment variables instead of files |
| 5.4.2 | No external secret storage solution in use |

### 5.5 Extensible Admission Control (1 WARN)

| ID    | Check |
|-------|-------|
| 5.5.1 | ImagePolicyWebhook not configured for image provenance |

### 5.6 General Policies (4 WARNs)

| ID    | Check |
|-------|-------|
| 5.6.1 | Administrative namespace boundaries may not be defined |
| 5.6.2 | seccomp profile (RuntimeDefault) not set in Pod definitions |
| 5.6.3 | SecurityContext not applied to Pods and Containers |
| 5.6.4 | default namespace may be in use |

---

## Critical Findings (FAIL)

### 4.1.1 — kubelet service file permissions too permissive

**Risk:** The kubelet service file is readable by non-root users, potentially exposing startup arguments including sensitive flags.

**Remediation:**
```bash
chmod 600 /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
```

---

### 4.1.9 — kubelet config.yaml permissions too permissive

**Risk:** The kubelet configuration file may be readable by non-root users, exposing security-relevant settings.

**Remediation:**
```bash
chmod 600 /var/lib/kubelet/config.yaml
```

---

## High-Priority Warnings

These WARNs carry the most security impact and should be addressed first:

| Priority | ID     | Reason |
|----------|--------|--------|
| High     | 4.2.9  | Kubelet not using explicit TLS cert/key — relies on auto-generated certs only |
| High     | 4.2.12 | Weak ciphers may be in use for kubelet TLS |
| High     | 4.2.14 | seccomp not defaulted — containers run without syscall filtering |
| High     | 5.2.1  | No Pod Security Admission or policy controller active |
| High     | 5.2.2  | Privileged containers can be scheduled without restriction |
| High     | 5.2.6  | allowPrivilegeEscalation not blocked — containers can escalate to root |
| High     | 5.1.1  | cluster-admin role bindings not audited |
| High     | 5.1.3  | Wildcard RBAC rules grant overly broad permissions |
| Medium   | 5.3.2  | Namespaces without NetworkPolicies allow unrestricted pod-to-pod traffic |
| Medium   | 5.4.1  | Secrets as env vars are visible in `kubectl describe` and process listings |
| Medium   | 5.6.4  | Resources in default namespace lack isolation |

---

## Recommended Remediation Order

1. **Fix the two FAILs** — file permission changes are low-risk and immediate.
2. **Enable seccomp defaults** (4.2.14) — set `seccompDefault: true` in kubelet config or via `--seccomp-default`.
3. **Configure TLS explicitly** (4.2.9, 4.2.12) — set `tlsCertFile`, `tlsPrivateKeyFile`, and `tlsCipherSuites` in kubelet config.
4. **Enforce Pod Security Admission** (5.2.1+) — apply `restricted` or `baseline` PSA labels to namespaces.
5. **Audit and tighten RBAC** (5.1.1, 5.1.3, 5.1.5, 5.1.6) — review cluster-admin bindings, remove wildcards, disable automounting where not needed.
6. **Apply SecurityContext to workloads** (5.2.6, 5.2.7, 5.6.2, 5.6.3) — set `runAsNonRoot`, `allowPrivilegeEscalation: false`, `seccompProfile`.
7. **Enforce NetworkPolicies on all namespaces** (5.3.2) — default-deny ingress/egress with explicit allow rules.
8. **Migrate secrets to files or external store** (5.4.1, 5.4.2).
9. **Move workloads out of default namespace** (5.6.4).
