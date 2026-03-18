# shed-gateway

Standalone Ansible project managing the gateway layer for the home infrastructure. Runs independently of `the-shed` and can be deployed or updated without touching application services.

## Purpose

Manages:
- **Traefik** — reverse proxy, TLS termination, routing, blue-green traffic switching
- **Cloudflare** — tunnel (inbound) and DDNS companion (outbound DNS)
- **Authelia** — SSO/2FA auth portal with OIDC provider
- **LLDAP** — lightweight LDAP directory backing Authelia

## Prerequisites

- Ansible + `ansible-galaxy collection install -r requirements.yml`
- Vault password (for `host_vars/shed/vault.yml`)
- SSH access to the shed host on port 86

## Quick start

```bash
ansible-galaxy collection install -r requirements.yml
ansible-playbook main.yml
```

Tag-scoped runs:
```bash
ansible-playbook main.yml --tags cloudflare
ansible-playbook main.yml --tags traefik
ansible-playbook main.yml --tags authelia
ansible-playbook main.yml --tags lldap
```

## Roles

| Role | Description |
|------|-------------|
| `cloudflare` | Cloudflare tunnel + DDNS companion containers |
| `traefik` | Traefik v3 reverse proxy, TLS via Cloudflare DNS challenge, dynamic file-based blue-green routing |
| `authelia` | Authelia v4.38 SSO portal, backed by LLDAP, with OIDC for Nextcloud |
| `lldap` | Lightweight LDAP (lldap) user directory |

## Vault variables

All secrets live in `host_vars/shed/vault.yml` (ansible-vault encrypted). See the placeholder keys in that file.

## Deployment workflow

Templates are not applied automatically — they are rendered and deployed by running the playbook. **Always run the playbook after changing any template, task, or variable file.**

Recommended workflow:
```bash
# Dry-run first to preview changes
ansible-playbook main.yml --check

# Apply changes
ansible-playbook main.yml
```

If you change a template and don't run the playbook, the running containers will continue using the old rendered config until the next playbook run.

## Migration note

**Do not remove gateway roles from `the-shed/main.yml`** until this project is deployed, all routes verified, and Phase 4 Docker label migration confirmed working on every service.
