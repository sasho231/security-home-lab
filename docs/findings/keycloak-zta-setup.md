# Keycloak Identity Provider — ZTA Implementation

## What was deployed
- Keycloak 24.0 via Docker Compose
- Realm: security-lab
- Users: labuser (viewer), labadmin (admin + MFA)
- OIDC client: security-lab-app

## ZTA Identity Controls Implemented
1. Centralised identity — all auth delegated to Keycloak
2. Role-based access — lab-admin vs lab-viewer roles
3. MFA enforced — TOTP required for admin users
4. Short-lived tokens — JWT expiry enforced
5. Standard protocols — OIDC/OAuth2 same as Azure AD

## Token validation tested
- Retrieved JWT via curl password grant
- Decoded at jwt.io — confirmed roles, expiry, issuer present
- JWKS endpoint verified — public key available for validation

## Enterprise equivalents
| Keycloak | Azure AD / Entra ID |
|----------|---------------------|
| Realm | Tenant |
| Client | App Registration |
| Realm Role | App Role / Group |
| OIDC flow | OAuth2 Authorization Code flow |
| TOTP MFA | Microsoft Authenticator |
| JWT token | Azure AD access token |
