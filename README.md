Standalone Ansible project managing the gateway layer for the home infrastructure. Runs independently of the application layer and can be deployed or updated without touching application services.

## Architecture

```
                         Internet
                             │
               ┌─────────────▼────────────┐
               │      Cloudflare Edge      │
               │    (tunnel inbound)       │
               └─────────────┬────────────┘
                             │
               ┌─────────────▼────────────┐
               │          Traefik          │
               │  reverse proxy · TLS      │
               │  dynamic routing          │
               └──────┬──────────┬────────┘
                      │          │ forwardAuth
               routes to    ┌────▼─────────────┐
               app services │    Authelia        │
               (the-shed)   │  SSO / 2FA portal  │
                            └────────┬───────────┘
                                     │ LDAP
                            ┌────────▼───────────┐
                            │       LLDAP         │
                            │  user directory     │
                            └────────────────────┘

Cloudflare Companion — watches Traefik API, auto-creates DNS CNAMEs for each service
Cloudflare DDNS      — keeps zone @ record updated with current public IP
```

## Roles

| Role | Tag | Purpose |
|------|-----|---------|
| cloudflare | cloudflare | Outbound tunnel + DDNS companion containers |
| traefik | traefik | Reverse proxy, TLS via Cloudflare DNS challenge, dynamic routing, blue-green traffic switching |
| lldap | lldap | Lightweight LDAP user directory backing Authelia |
| authelia | authelia | SSO/2FA portal with OIDC provider; two replicas sharing Redis + MariaDB state |

## Routing

All externally-accessible services are declared in the `gateway_services` list in `group_vars/gateway.yml`. Each entry:

```yaml
- domain: haus.clan.ng
  service: homeassistant-active   # Docker service name, or blue-green weighted service
  auth: bypass                    # bypass | one_factor | two_factor | management
  bluegreen: true                 # optional — routes via file provider weighted service
  local: true                     # optional — internal subnet only, no TLS
  middleware: nextcloud-chain     # optional — custom Traefik middleware
```

`roles/traefik/templates/dynamic.yml` generates Traefik routers from this list at deploy time. Adding or changing a route means updating `gateway_services` and re-running `-t gateway` (which updates both Traefik routes and Authelia access policies) — no changes to the application layer are needed.

### Auth tiers

| Value | Policy |
|-------|--------|
| bypass | No auth check |
| one_factor | Username + password |
| two_factor | Username + password + TOTP |
| management | two_factor + membership in `management` LDAP group |

Local routes (`local: true`) skip Authelia entirely and are restricted to the internal subnet via IP allowlist. A complete Authelia outage has no impact on local access to any service.

## Authelia resilience

Two replicas (`authelia` + `authelia_local`) share the same Redis session store and MariaDB. Both register under the `authelia-cluster` Docker DNS alias; Traefik's `forwardAuth` round-robins between them. If one dies, the other continues serving auth checks transparently.

Accepted single points of failure: Redis and MariaDB.

## Blue-green deployments

Currently used for Home Assistant. Coordinated with the application layer:

1. The application layer deploys blue and green containers, notifies the `deploy: bluegreen` handler
2. Handler starts the inactive colour, waits for Traefik to register it as healthy
3. `bluegreen.yml` (Traefik file provider) switches weights 100/0 → 0/100
4. Old container stops; active colour state persisted to disk

Logic lives in `roles/traefik/handlers/bluegreen.yml` + `bluegreen_switch.yml`. Rollback fires automatically if the health check or switch fails.

## Connecting a new application

Integrating a new project or service requires two steps: label the container and register the route.

### 1. Label the container (application side)

The container must be on the `traefik_webgateway` Docker network and expose exactly one label so Traefik knows which port to forward to:

```yaml
# docker-compose.yml (in the application project)
services:
  myapp:
    networks:
      - traefik_webgateway
    labels:
      - "traefik.enable=true"
      - "traefik.http.services.myapp.loadbalancer.server.port=8080"

networks:
  traefik_webgateway:
    external: true
```

No router or middleware labels are needed — all routing policy lives in shed-gateway.

### 2. Register the route (shed-gateway side)

Add an entry to `gateway_services` in `group_vars/gateway.yml`:

```yaml
- domain: myapp.clan.ng
  service: myapp          # must match the Traefik service name (container name by default)
  auth: two_factor        # bypass | one_factor | two_factor | management
```

Then re-deploy the gateway:

```bash
ansible-playbook -i hosts/inventory.ini main.yml --vault-id shed@.vault-pass-shed-gateway.txt -t gateway
```

This updates both Traefik routes and Authelia access control rules. Using `-t traefik` alone will create the route but **not** update Authelia's access policy — any service with `auth` other than `bypass` will return 403 without a login redirect.

Cloudflare Companion picks up the new service automatically and creates the DNS CNAME record.

### Optional: local-only variant

Add a second entry with `local: true` for subnet-only access (no TLS, no auth check):

```yaml
- domain: haus.myapp
  service: myapp
  auth: bypass
  local: true
```

### Optional: OIDC (if the app supports it)

Add a client block to `roles/authelia/templates/configuration.yaml.jinja` under `identity_providers.oidc.clients`:

```yaml
- id: myapp
  secret: "{{ vault_oidc_myapp_secret }}"
  redirect_uris:
    - "https://myapp.clan.ng/auth/callback"
  scopes: [openid, profile, email, groups]
```

Add `vault_oidc_myapp_secret` to `host_vars/shed/vault.yml`, then re-run `-t authelia`.

### Optional: custom middleware

If the service needs non-standard headers or redirects, define a middleware in `roles/traefik/templates/dynamic.yml` and reference it in the `gateway_services` entry as `middleware: my-middleware-name`.

## Commands

Full run:
```bash
ansible-playbook -i hosts/inventory.ini main.yml --vault-id shed@.vault-pass-shed-gateway.txt
```

Scoped (`-t`):
```
cloudflare | traefik | lldap | authelia | gateway
```

Dry-run: append `--check`

## Secrets

All secrets in `host_vars/shed/vault.yml` (ansible-vault encrypted). See placeholder keys in that file.
