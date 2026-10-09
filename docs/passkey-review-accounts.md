# App Review accounts and passkey administration

Onionary uses real non-admin review accounts and passkeys. SQLAdmin at `/admin/`
is the operator frontend, matching Planini and Tracy. User-facing passkey changes
live at `/auth/security` and in iOS Settings → Manage passkeys.

## Prepare an administrator

Register your own account normally, then grant the exact existing account access
on the backend server:

```sh
cd /srv/docker-ansible/onionary
sudo docker compose exec api python -m execution.admin_access you@example.com
```

Append `--revoke` to remove administrator access. Each admin request checks the
current database session and administrator flag. Forms require a session-bound
CSRF token and same-origin submission. No password-based admin login exists.

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
> https://onionary-test.malaber.de, and sign in with that passkey. The link works
> once and expires [UTC DATE/TIME]. Opening or cancelling does not consume it;
> successful enrollment does. Contact onionary@schaedler.rocks for a fresh link.

Issue one link per reviewer. Links preserve existing passkeys and recipes.
The **Passkey links** table supports search by public identifier, sorting and
pagination; details show issuer, creation, expiry, use, and revocation timestamps.
Use **Revoke link** to invalidate unused links. No raw token or token hash is shown
in admin lists/details. Raw tokens only appear in the URL fragment and are not
sent in HTTP paths or referrers. Enrollment and admin responses disable caching.

For manual recovery, verify identity outside Onionary before issuing a link.
Treat the full link like a credential. Account/passkey deletion and recovery are
not interchangeable: deleting all passkeys keeps recipes but revokes all sessions;
a new administrator enrollment link is then required. Removing keys here cannot
delete their saved copies from a password manager; those copies no longer work.

## User-facing management

Users can add, rename, remove, or replace keys. A fresh assertion from their own
key confirms each operation. Removing the last key uses the separate **Delete all
passkeys** action with an explicit warning and typed confirmation. Replacement
removes old keys only after the new key is verified and stored successfully.

## Implementation and release

FastPasskey 0.2.6 already supplies enrollment-link protocol support, WebAuthn
verification, name validation, and browser serialization. Onionary reuses that
core with its synchronous integer-ID database and SQL single-use flow storage;
SQLAdmin supplies administrative tables/forms. No bespoke recovery-admin SPA.
Run migrations before serving the updated image. Existing saved passkeys remain
valid; old records show unknown creation time rather than an invented timestamp.
