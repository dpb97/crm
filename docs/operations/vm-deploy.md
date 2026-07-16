# LCS CRM · Cloud-VM Deployment Runbook

Ziel: Nur das CRM (frappe + erpnext + crm-Fork + lcs_integrations +
pilanda_theme + pilanda_sales) produktiv auf einer Cloud-VM, mit
Entra-SSO und Outlook-Mail-Sync. Kein Dev-Server, keine Demo-Bench.

## 0 · Voraussetzungen

| Was | Empfehlung |
|---|---|
| VM | 2 vCPU / 4 GB RAM / 40 GB Disk (Ubuntu 22.04/24.04 LTS) |
| Docker | Engine ≥ 24 + compose plugin |
| DNS | `crm.<domain>` → VM-IP |
| TLS | nginx/caddy auf der VM ODER Cloud-LB davor |
| Azure | App-Registrierungen laut `docs/operations/entra-app-registration.md` |

## 1 · Image bauen (einmalig / je Release)

Auf der VM oder in CI (Token = read-only PAT für die privaten Repos):

```bash
git clone https://github.com/dpb97/crm.git && cd crm
docker build -f docker/Dockerfile.prod \
  --build-arg GITHUB_TOKEN=<PAT> \
  -t lcs-crm:$(git rev-parse --short HEAD) -t lcs-crm:latest .
```

## 2 · Konfigurieren

```bash
cp .env.prod.example .env && chmod 600 .env
# Ausfuellen: SITE_NAME, ADMIN_PASSWORD, DB_ROOT_PASSWORD,
# ENTRA_TENANT_ID / ENTRA_CLIENT_ID / ENTRA_CLIENT_SECRET
```

## 3 · Erststart

```bash
docker compose -f docker/docker-compose.prod.yml up -d
docker compose -f docker/docker-compose.prod.yml run --rm configurator
docker compose -f docker/docker-compose.prod.yml --profile setup run --rm create-site
```

Danach lauscht der Stack auf `127.0.0.1:8080`. TLS-Proxy davor (Beispiel
nginx, Zertifikat von Let's Encrypt oder LCS-CA):

```nginx
server {
    listen 443 ssl;
    server_name crm.lcs-group.com;
    ssl_certificate     /etc/ssl/crm.pem;
    ssl_certificate_key /etc/ssl/crm.key;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 4 · SSO aktivieren

App-Registrierung `LCS CRM · SSO` laut Entra-Runbook §1 (Redirect-URI auf
`https://crm.<domain>/api/method/frappe.integrations.oauth2_logins.custom`).
`create-site` ruft `msal_sso.provider.install_or_update` bereits auf; nach
`.env`-Aenderungen manuell nachziehen:

```bash
docker compose -f docker/docker-compose.prod.yml exec backend \
  bench --site $SITE_NAME execute lcs_integrations.msal_sso.provider.install_or_update
```

Login-Screen zeigt danach "Login with Microsoft".

## 5 · Outlook-Mail-Sync aktivieren

1. Die **gleiche** App-Registrierung wie SSO (der Code liest fuer beides
   `ENTRA_*`) um die **Application**-Permission `Mail.Read` erweitern +
   Admin-Consent. Ohne Postfach-Scoping liest die App JEDES Postfach im
   Tenant — daher **Application Access Policy** setzen (Exchange Online
   PowerShell):

   ```powershell
   New-ApplicationAccessPolicy -AppId <client-id> `
     -PolicyScopeGroupId mailsync-allowed@lcs-group.com `
     -AccessRight RestrictAccess
   ```

2. Je Postfach eine `Outlook Mailbox Binding` anlegen
   (Desk → Outlook Mailbox Binding → New, z. B. `vertrieb@lcs-group.com`).
3. Der Scheduler zieht das Delta stuendlich; jede neue Mail wird als
   `Communication` angelegt und via `email_domain_autolink` automatisch an
   Customer/Deal geknuepft.
4. Erstes Delta manuell anstossen + pruefen:

   ```bash
   docker compose -f docker/docker-compose.prod.yml exec backend \
     bench --site $SITE_NAME execute lcs_integrations.outlook_sync.delta_service.sync_all_bindings
   ```

## 6 · Betrieb

| Aufgabe | Befehl |
|---|---|
| Logs | `docker compose -f docker/docker-compose.prod.yml logs -f backend` |
| Backup (taeglich cronen) | `docker compose ... exec backend bench --site $SITE_NAME backup --with-files` |
| Update auf neuen Stand | Image neu bauen → `docker compose ... up -d` → `exec backend bench --site $SITE_NAME migrate` |
| Admin-PW rotieren | `exec backend bench --site $SITE_NAME set-admin-password <neu>` |

## 7 · Bewusst NICHT auf der VM

Kein pilanda/pilanda_pm/pilanda_pls, kein Helpdesk/LMS/Writer/Drive, kein
erpnext_enhancements (dessen Customer-Override-Fixture waere hier eh vom
compat-Guard in lcs_integrations neutralisiert worden — aber gar nicht erst
installieren). Die Dev-Bench auf der Workstation bleibt unveraendert.
