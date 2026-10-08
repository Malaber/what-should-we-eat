# Onionary

Native SwiftUI cooking companion. Bundle ID and App Store Connect SKU:
**`de.malaber.onionary`**. Supports iPhone and iPad on iOS 17+.

## Cooking

Search recipes from your active household, or resume a recently visited recipe.
The current adventure opens after suspension or termination, including offline.
Ingredients and steps are checklists. **Go back** reverses the latest check or
uncheck; History records timestamps for every action and undo.

The **− / +** controls change portions by one while preserving any fractional
part. Tap the portion count to type an exact amount. **Adjust portions** accepts
decimal values such as `1.53` and `4.32`, with either a
comma or point. Use a multiplier, original/desired portions, or an available
ingredient amount in its original unit. 170 g instead of 200 g produces a 0.85
multiplier. Adjustments always start from original quantities; cooking times do
not scale and unquantified ingredients remain unquantified. Existing recipes have
no serving-count field, so original servings are set locally for portion mode.

Progress is saved atomically on this device, separately per backend and account.
An adventure snapshots its recipe so backend edits cannot invalidate its checklist.
Signing out retains progress for the next sign-in. Progress does not synchronize
between devices. Tokens are stored in Keychain.

## Backend setup and existing accounts

1. Install root `requirements.txt`. It pins `fastpasskey` 0.2.6 with the same wheel
   hash used by Planini and Tracy.
2. Set `APP_BASE_URL` to the exact public HTTPS origin, such as
   `https://onionary.malaber.de`, without an API path or query. Local browser
   development can use `http://localhost:8000`; IP addresses cannot be RP IDs.
3. Configure the database and a random `SECRET_KEY` of at least 32 characters.
4. Run `python -m execution.db.init_db` before deploying the updated application.
5. Existing accounts: run `python -m execution.enroll_passkey chef@example.com`
   on the server. Privately share the resulting 15-minute link with the verified
   account owner. Starting enrollment consumes it; if cancelled, issue a new
   link. This also adds another passkey without removing existing keys or data.
6. New accounts can register with a passkey at `/auth/login`.

The web UI also uses passkeys. Legacy password endpoints return 410 by default.
`ALLOW_LEGACY_PASSWORD_AUTH=true` is available only for a temporary migration
window and the API compatibility tests. The native app has no password flow.

WebAuthn uses the configured RP domain, not a caller-supplied Host header.
Challenges and enrollment links are consumed once in SQL across all workers.
The mobile handoff uses a fixed `de.malaber.onionary://auth` callback, random state,
and S256 PKCE. Codes expire in two minutes; tokens never enter callback URLs.
Authentication occurs in the selected server's browser origin, following Tracy's
approach, so custom domains need no associated-domain entitlement. Custom servers
must run this backend version and have valid HTTPS certificates.

## Build and test

Requires Xcode 26+ (Icon Composer assets), an installed iOS simulator, XcodeGen
2.38+, and Python 3.12+ for the backend.

```sh
python -m pytest
python -m playwright install chromium
python -m pytest execution/tests/e2e -o addopts='' --browser chromium
bash ios/Onionary/Scripts/test.sh
```

The script runs Swift core tests, generates the Xcode project, chooses an installed
iPhone simulator, and runs UI tests. Set `SIMULATOR_ID` to select a specific device.
Test fixtures are Debug-only and excluded from Release builds.

```sh
cd ios/Onionary
xcodegen generate
open Onionary.xcodeproj
```

GitHub Actions tests backend migrations, builds the container, exercises real
WebAuthn in desktop/mobile Chromium, and builds/tests iOS. No Apple signing secrets
are needed in CI. Workflows activate when this repository moves to GitHub.

## Background TestFlight upload

Uses the sibling apps' team (`VWKG94374J`) and the Apple account configured in
Xcode. App Store Connect must contain an iOS app with bundle ID and SKU
**`de.malaber.onionary`**. A record using `onionary.malaber.de` is a different
bundle ID and cannot receive this build.

```sh
python3 execution/start_onionary_testflight.py 1.0.0 1
python3 execution/start_onionary_testflight.py --status
tail -f .tmp/onionary-testflight/build.log
```

The detached worker tests, archives, and exports directly to App Store Connect.
It survives terminal/chat disconnects, records the exit status, and prevents
concurrent uploads using a file lock. Logs remain in `.tmp/`; archives and test
results live in the system temporary directory. Increase the build number for
later uploads. Successful export confirms upload acceptance, not completion of
Apple's processing or TestFlight review.

Foreground equivalent:

```sh
bash ios/Onionary/Scripts/upload_testflight.sh 1.0.0 1
```

To retry just an export after correcting App Store Connect settings:

```sh
python3 execution/start_onionary_testflight.py 1.0.0 1 --archive /absolute/path/Onionary.xcarchive
```

The worker validates the archive's bundle ID and version. Archive/export commands
use the system PATH because Homebrew rsync can break Xcode's IPA packaging.
