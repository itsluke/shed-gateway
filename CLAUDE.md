# shed-gateway

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

## Key files

`group_vars/gateway.yml` — master service registry. The `gateway_services` list defines every route: domain, auth tier, local vs external, and any custom middleware. Read this first when investigating any routing or auth issue.

`roles/traefik/templates/dynamic.yml` — generates all Traefik routers and middlewares from `gateway_services` at deploy time. Routing logic lives here.

`roles/traefik/handlers/bluegreen.yml` + `bluegreen_switch.yml` — blue-green orchestration. Start here when investigating a stuck or failed Home Assistant deploy.

Live network state:
```bash
docker network ls
docker network inspect <network>
```

## Troubleshooting

Before suggesting deletion of any data directory or database: exhaust all other options first. Data loss is irreversible.

- Permissions errors → fix ownership, don't delete
- Corruption → remove only the specific broken file (lock, pid, log), not the directory
- Only suggest wiping a data directory if files are confirmed unreadable/corrupt AND a backup exists

### authelia_mariadb — "Bad magic header in tc log"

Cause: Docker SIGKILL before MariaDB flushes. Permanent fix (`stop_grace_period: 60s`) is already applied to the compose template. If it recurs after power loss:

```bash
docker stop authelia_mariadb authelia authelia_local
sudo rm -f /mnt/ssd_1tb2_1/docker/data/authelia/db/mariadb/tc.log
# then redeploy:
ansible-playbook -i hosts/inventory.ini main.yml --vault-id shed@.vault-pass-shed-gateway.txt -t authelia
```

<!-- Add further failure modes here as they are encountered -->
