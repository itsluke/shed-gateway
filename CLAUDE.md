# shed-gateway

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
