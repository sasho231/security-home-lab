# Falco Alert Testing Results


## Alerts Triggered
1. Terminal shell in container - exec into nginx pod
2. Read sensitive files - cat /etc/shadow inside container


## Custom Rules Written
- suspicious-download.yaml - detects curl/wget in containters mapped to MITRE T1105 (Ingress Tool Transfer)
