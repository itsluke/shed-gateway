# shed-gateway

## Known issues

### authelia_mariadb: "Bad magic header in tc log"
MariaDB crashes with a corrupted `tc.log` when Docker kills the container before it can flush (SIGKILL timeout). The permanent fix is `stop_grace_period: 60s` in `compose.authelia.yaml.jinja` — already applied. If it recurs (e.g. after power loss), delete `tc.log` and restart:
```bash
docker stop authelia_mariadb authelia authelia_local
sudo rm -f /mnt/ssd_1tb2_1/docker/data/authelia/db/mariadb/tc.log
# then redeploy with ansible -t authelia
```

### authelia + authelia_local — two instances is intentional
`authelia_local` is a replica sharing the same Redis + MariaDB state. Both join the `authelia-cluster` Docker DNS alias so Traefik's `forwardAuth` round-robins between them for resilience.

## Running the playbook

```bash
ansible-playbook -i hosts/inventory.ini main.yml --vault-id shed@.vault-pass-shed-gateway.txt
```

Scope to specific roles with `-t`:
```bash
ansible-playbook -i hosts/inventory.ini main.yml --vault-id shed@.vault-pass-shed-gateway.txt -t cloudflare
ansible-playbook -i hosts/inventory.ini main.yml --vault-id shed@.vault-pass-shed-gateway.txt -t traefik
ansible-playbook -i hosts/inventory.ini main.yml --vault-id shed@.vault-pass-shed-gateway.txt -t authelia
ansible-playbook -i hosts/inventory.ini main.yml --vault-id shed@.vault-pass-shed-gateway.txt -t lldap
```

Dry-run:
```bash
ansible-playbook -i hosts/inventory.ini main.yml --vault-id shed@.vault-pass-shed-gateway.txt --check
```
