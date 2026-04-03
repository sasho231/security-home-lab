# DevSecOps Pipeline — Security Findings Report

## Environment
- Platform: GitLab CE (self-hosted, Docker)
- Scanner: Gitleaks, Semgrep, Checkov
- Project: security-lab-app
- Date: April 2026
- Pipeline: .gitlab-ci.yml — automated on every commit

---

## Finding 1 — Hardcoded API Key (CRITICAL)
**Tool:** Gitleaks  
**Rule:** generic-api-key  
**File:** app.py, Line 10  
**Commit:** 44210304d5c7d6e226219d6e0b539a6197e0e96f  

**Evidence:**
Finding: API_KEY = "sk-1234567890abcdef"
Secret:  sk-1234567890abcdef
Entropy: 4.247928

**Risk:** Hardcoded API keys committed to source control are exposed to anyone with repo access. 
If the repo is ever made public or leaked, the key is permanently compromised — 
even after deletion, it remains in git history.

**Remediation:** Replace with environment variable.
```python
# Before (vulnerable)
API_KEY = "sk-1234567890abcdef"

# After (fixed)
API_KEY = os.environ.get('API_KEY')
```
**Status:** FIXED in commit — removed hardcoded value, using os.environ.get()

---

## Finding 2 — SAST Issues in Python Code (MEDIUM)
**Tool:** Semgrep  
**Rules run:** 328  
**Findings:** 2 blocking  
**Files scanned:** 5  

**Risk:** Static analysis identified security anti-patterns in the Python code 
including debug mode enabled (exposes stack traces to users) and insecure defaults.

**Remediation:** 
```python
# Before (vulnerable)
app.run(debug=True)

# After (fixed)
app.run(debug=False)
```
**Status:** FIXED — debug mode disabled

---

## Finding 3 — Kubernetes Manifest Misconfigurations (HIGH)
**Tool:** Checkov  
**Framework:** Kubernetes  
**File:** k8s/apps/sample-app-deployment.yaml  

**Checks Failed:**
- CKV_K8S_11: CPU limits not set — container can consume unlimited CPU
- CKV_K8S_12: Memory limits not set — container can cause OOM on node
- CKV_K8S_13: runAsNonRoot not set — container runs as root by default
- CKV_K8S_28: readOnlyRootFilesystem not set — filesystem is writable
- CKV_K8S_20: allowPrivilegeEscalation not set — process can gain more privileges

**Risk:** Containers running as root with no resource limits and writable filesystems 
are significantly easier to exploit and escape from.

**Remediation:**
```yaml
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
resources:
  limits:
    memory: "128Mi"
    cpu: "500m"
```
**Status:** FIXED — security context and resource limits added

---

## Pipeline Summary

| Scan | Tool | Findings | Status |
|------|------|----------|--------|
| Secret Detection | Gitleaks | 1 critical (API key) | Fixed |
| SAST | Semgrep | 2 medium | Fixed |
| IaC Security | Checkov | 5 misconfigs | Fixed |

## Key Lessons
1. Secrets must never be hardcoded — environment variables or secrets managers only
2. Kubernetes manifests need explicit security contexts — defaults are insecure
3. Automated scanning catches issues before they reach production
4. Fix → commit → pipeline re-runs automatically — this is the DevSecOps feedback loop

## Tools Used
- **Gitleaks** — secret scanning, detects credentials in source code
- **Semgrep** — SAST, finds security bugs by pattern matching code
- **Checkov** — IaC scanner, validates Kubernetes/Terraform against security benchmarks
- **GitLab CI/CD** — pipeline orchestration, runs scans automatically on every push
