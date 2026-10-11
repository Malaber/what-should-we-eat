# App Review accounts and passkey administration

Onionary uses real non-admin review accounts and passkeys. SQLAdmin at `/admin/`
is the operator frontend, matching Planini and Tracy. User-facing passkey changes
live at `/auth/security` and in iOS Settings → Manage passkeys.

## Prepare an administrator

Register your own account with a passkey on the target instance first. Production
and test have separate databases: grant access separately on each instance.
On the production backend server, from its Compose deployment directory:

```sh
cd /srv/docker-ansible/onionary
sudo docker compose exec api python -m execution.admin_access you@example.com
```

Then open **https://onionary.malaber.de/admin/** and sign in with that account's
passkey. Test administration is **https://onionary-test.malaber.de/admin/**; run
the same command from the test instance's Compose directory to grant access there.
The static app website at app.onionary.malaber.de has no admin interface or accounts.
If access returns 403, verify the exact email and instance used in the command.

Append `--revoke` to remove administrator access. Each admin request checks the
current database session and administrator flag. Forms require a session-bound
CSRF token and same-origin submission. No password-based admin login exists.

## Populate a dedicated review kitchen

Create a non-admin account in **Accounts → New Account**, then run on the same
instance (the account does not need to have redeemed a passkey link yet):

```sh
cd /srv/docker-ansible/onionary
sudo docker compose exec api python -m execution.seed_review_account review@example.com
```

This copies the bundled sample recipes with ingredients, steps, tags and two-person
base portions into that account's personal kitchen. It plans four meals, one marked
cooked, so the meal plan and shopping list have content. These are demo quantities
and nutrition, not dietary guidance. No real user data is copied.

The command refuses admins, shared kitchens and existing non-demo recipes. Running
it again on the unchanged sample kitchen does nothing. It does not overwrite edits,
reset passkeys, delete anything or generate credentials. Cooking checkmarks/history
are local to each iOS installation, so reviewers create their own while cooking.
After seeding, issue a fresh one-use passkey link as described below.

## Prepare Apple's review account

1. Sign in at `/admin/`. In **Accounts → New Account**, create a dedicated account
   using an email you control. It gets its own empty kitchen and is never admin.
2. Open account details (eye icon) and issue an additional-passkey link.
3. Open this preparation link in a separate browser profile, add a passkey, and
   populate the kitchen with recipes for review.
4. Issue a **fresh** link for Apple. Choose an expiry from 1–720 hours (30 days).
   Copy the full URL; it is displayed only once. Do not redeem Apple's link.
5. Add the link and these instructions to App Store Connect review notes:

> Onionary uses passkeys. Open [LINK] in Safari on your review device and create
> a passkey for the prepared account. Then open Onionary, choose backend
> https://onionary.malaber.de (or the exact instance used to create this link), and sign in with that passkey. The link works
> once and expires [UTC DATE/TIME]. Opening or cancelling does not consume it;
> successful enrollment does. Contact onionary@schaedler.rocks for a fresh link.

Issue one link per reviewer. Links preserve existing passkeys and recipes.
The **Passkey links** table supports search by public identifier, sorting and
pagination; details show issuer, creation, expiry, use, and revocation timestamps.
Use **Revoke link** to invalidate unused links. No raw token or token hash is shown
in admin lists/details. Raw tokens only appear in the URL fragment and are not
sent in HTTP paths or referrers. Enrollment and admin responses disable caching.

For manual recovery, verify identity outside Onionary before issuing a link.
Treat the full link like a credential. Recovery links add a working passkey;
they do not delete existing keys, recipes, or the account. Revoke an unused link
from SQLAdmin if it is no longer needed.

## User-facing management

Users manage keys on the account settings page. They can add and rename passkeys
or remove a key when another remains. Deleting the last passkey is blocked so
an account cannot be left without a login method. Management requires a fresh
passkey assertion. Administrators issue enrollment links through SQLAdmin, not a
custom recovery frontend.

## Implementation and release

FastPasskey 0.2.6 already supplies enrollment-link protocol support, WebAuthn
verification, name validation, and browser serialization. Onionary reuses that
core with its synchronous integer-ID database and SQL single-use flow storage;
SQLAdmin supplies administrative tables/forms. No bespoke recovery-admin SPA.
Run migrations before serving the updated image. Existing saved passkeys remain
valid; old records show unknown creation time rather than an invented timestamp.

## iOS session lifetime and recovery

Native access tokens last 14 days. A separate, opaque refresh credential permits
silent renewal for a further 28 days, up to an absolute 42 days after passkey
sign-in. Renewal rotates both credentials and never extends that absolute
boundary. Revoked or inactive accounts cannot renew. Refresh credentials are
stored only in the device Keychain; the backend stores their hashes. Existing
older app sessions need one passkey sign-in to receive renewable credentials.

Settings shows the access expiry, final passkey deadline and a manual passkey
refresh action. When access expires, the app renews silently before sync. At the
final deadline it offers passkey sign-in over the current interface; cancelling
keeps cached recipes, meal plan, cooking checkmarks and editor drafts intact.
Reauthentication must use the same account. It resynchronizes automatically and
does not restart the cooking adventure. Network failures do not sign users out
or repeat uncertain writes. A save rejected with 401 can be sent once after
successful silent renewal; other failed saves remain in the editor for review.

The widget refresh icon opens Kitchen and syncs through that same session flow.
It does not give the widget extension access to account credentials. iOS controls
background execution; silent renewal runs when the app is active or makes a sync
request, without presenting passkey UI until interaction is necessary.
