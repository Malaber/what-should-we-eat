# Kitchen, sharing, and legal identity rollout

## Before updating the backend

Set these **public** operator values in the Ansible-generated `/srv/docker-ansible/onionary/app.env` (and its source template/variables so subsequent deployments retain them):

```dotenv
IMPRESSUM_NAME=Your full operator name or company
IMPRESSUM_ADDRESS=Your complete postal address
IMPRESSUM_EMAIL=your-instance-contact@example.com
```

These examples are placeholders; replace all three with the actual instance operator. The API refuses startup if any value is blank/missing, or if the email has an invalid shape. No bypass is provided for production. The Compose example also requires these values during interpolation. The separate `onionary.malaber.de` app website is unaffected.

Run the existing migration service before starting the new API image. Migration `20261009_02` adds `recipe_shares`; it does not rewrite recipes. Older app versions remain compatible with existing endpoints. Use the immutable `sha-<commit>` image for this PR, since feature branches do not overwrite the established `development` tag. After merge, `main` is also available. Follow the existing Traefik/Compose deployment guide.

## Recipe copies

In web recipe management or iOS cooking options, choose **Share recipe copy**. Web links last 24 hours; iOS lets you choose 1–168 hours. Anyone possessing the link can read its frozen recipe until expiry/revocation. Links contain no session credentials or household IDs; source edits do not propagate. The token is in the URL fragment and stored hashed server-side.

On the destination instance, choose **Import recipe**, select Onionary on web, and paste the full link. Review the draft before saving. Saving creates new ingredients, steps, and recipe IDs in your own kitchen. There is no following, remote update, or synchronization. Link lists in web recipe management and iOS Settings support revocation; already-imported copies are unaffected.

Remote imports require a publicly reachable HTTPS origin on port 443. Private IP addresses, redirects, arbitrary paths, oversized responses, and invalid formats are rejected. DNS results are validated and the connection is pinned to a validated IP with normal TLS hostname verification. No login token, cookie, or environment proxy is sent to a remote instance. Private-only deployments can export/import manually; this feature deliberately cannot probe LAN services.

## iOS share extension and settings

The extension bundle is `de.malaber.onionary.share`. Both app and extension require App Group `group.de.malaber.onionary` in Apple Developer signing/provisioning before a device/TestFlight archive. The simulator build verifies the extension is embedded. Enable the group for both identifiers when configuring signing.

Share a Chefkoch or Onionary URL from Safari to Onionary. The extension saves only the URL in the App Group inbox, then asks you to open Onionary for authenticated draft review. No credentials are exposed to the extension, and no recipe is silently saved. Only one pending URL is kept; sharing a later URL replaces it.

Settings has a single active backend, appearance (System/Light/Dark), and language (System/English/German). Preferences persist. Switching backend retains per-account cooking files. Recipe edits leave existing cooking snapshots untouched; **Restart with latest recipe** explicitly resets checks/history using the edited recipe.

## Validation and CI

Run backend pytest, desktop/mobile Playwright, the packaged PostgreSQL smoke test, Swift tests and simulator UI tests. The follow-up TestFlight release uses `v0.2.0-rc.3` / `0.2.0 (3)`. The upload script preserves each target’s bundle ID and disables automatic version/build rewriting. GitHub CI results will be reviewed when the user returns; do not poll idle jobs.
