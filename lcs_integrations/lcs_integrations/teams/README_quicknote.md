# Teams Quick-Note Webhook

Vertrieb schreibt in Teams eine kurze Projektnotiz — der Bot ordnet sie
automatisch dem passenden LCS Project zu und loggt sie als Kommentar.

## Einrichtung (einmalig, Team-Owner)

1. Teams-Kanal → ⋯ → Connectors → **Outgoing Webhook** → erstellen.
   - Name: `QuickNote`
   - Callback-URL: `https://<crm-host>/api/method/lcs_integrations.teams.quicknote_webhook.handle`
2. Teams zeigt einmalig ein **HMAC-Secret** an → kopieren.
3. In der Site hinterlegen (nicht committen):

   ```
   bench --site <site> set-config teams_quicknote_hmac_secret "<secret>"
   bench --site <site> set-config teams_quicknote_user "<frappe-user>"
   ```

   Der `teams_quicknote_user` ist der Service-User, unter dem Notizen
   geloggt werden — seine LCS-Project-Rechte bestimmen, welche Projekte
   der Matcher sieht.

## Benutzung

```
@QuickNote Kranbahn Vinci: Statik freigegeben, Montage kann Montag starten
```

- **Eindeutiger Treffer** → Notiz wird sofort geloggt, Bot antwortet mit dem Ziel.
- **Mehrdeutig** → Bot listet die Top-Kandidaten; Notiz mit Projektname/-nummer wiederholen.
- **Kein Treffer** → Bot bittet um Projektname/-nummer.

Der Absender-Name aus Teams wird der Notiz vorangestellt: `[Teams - <Name>] …`.

## Sicherheit

- Jede Anfrage ist HMAC-SHA256-signiert (Teams-Secret); ungültige Signaturen → 401.
- Der `auth_hook` `authenticate` validiert die Signatur, bevor Frappes
  `validate_auth` den 2-teiligen `Authorization: HMAC …`-Header ablehnt.
- Der Bot antwortet als rohe Bot-Framework-Activity (`{"type":"message","text":…}`),
  damit Teams die Antwort inline rendert.
