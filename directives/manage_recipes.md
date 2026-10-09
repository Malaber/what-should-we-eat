# Manage Recipes — Directive

## Goal
Create, read, update, delete, filter, and randomly select recipes via the API. All recipe operations are scoped to the user's active household and require authentication.

## Prerequisites
- Stack running (see `directives/local_development.md`)
- Authenticated user with a valid JWT token

## Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/recipes` | Create recipe (with ingredients, steps, tags) |
| `GET` | `/recipes` | List recipes, optional filters: `?tag=…&max_kcal=…&max_total_time=…` |
| `GET` | `/recipes/{id}` | Get single recipe |
| `PUT` | `/recipes/{id}` | Update recipe (partial — only sent fields are changed) |
| `DELETE` | `/recipes/{id}` | Delete recipe |
| `POST` | `/recipes/random` | Randomly pick *n* recipes from filtered set |
| `POST` | `/recipes/import/{invite_code}` | Copy all recipes from another household into the active one |
| `POST` | `/recipes/import/parse/html` | Parse a Chefkoch URL/HTML into a recipe draft for review |

## Tools / Scripts
- `execution/api/routers/recipes.py` — CRUD and random-selection router
- `execution/api/recipe_import.py` — HTML parsing and fetching for external imports (Chefkoch)
- `execution/api/schemas.py` — Pydantic models (`RecipeCreate`, `RecipeUpdate`, `RecipeOut`, etc.)
- `execution/db/models.py` — SQLAlchemy models (`Recipe`, `Ingredient`, `InstructionStep`, `Tag`)
- `execution/db/seed_recipes.py` — Bulk seed recipes from generated insert chunks

## Edge Cases & Learnings
- **Household scoping**: All recipe queries filter by `active_household_id`. Users see only their active household's recipes.
- **Demo household**: The household matching `DEMO_HOUSEHOLD_ID` is read-only; create/update/delete returns 403.
- **Tags**: Matched case-insensitively and created on-the-fly if they don't exist. Orphaned tags are cleaned up after recipe update/delete.
- **Shopping list**: Merges ingredients by `(name, unit)`. Ingredients without a quantity are listed but not summed.
- **Random selection**: Returns all candidates if fewer than `count` are available. Supports `exclude_ids` for re-rolling without duplicates.
- **Recipe import (Chefkoch)**: Parses JSON-LD `@type: Recipe` from HTML. Supports Unicode fractions and German units in ingredient parsing. Only `chefkoch.de` domains are allowed; redirect targets are validated.
- **Household import**: Copies recipes including ingredients, steps, and tags. Tags are shared by reference (not duplicated).
- **Onionary passkeys**: Uses `fastpasskey` 0.2.6, matching Planini and Tracy.
  Set `APP_BASE_URL` to the exact HTTPS origin; local WebAuthn requires `localhost`,
  since IP addresses are not valid RP domains. Run database migrations before
  deployment. Existing users enroll via `python -m execution.enroll_passkey EMAIL`;
  links are private, default to 24 hours (up to 30 days), and are consumed only
  after successful enrollment. SQLAdmin at `/admin/` is the operator UI. Password auth is disabled by default; legacy compatibility is migration-only.
- **iOS builds**: `python3 execution/start_onionary_testflight.py VERSION BUILD`
  starts a background test/archive/upload. Use `--status` and the log in
  `.tmp/onionary-testflight/`. See `ios/Onionary/README.md` for signing setup.
- **Cooking state**: Decimal scaling uses original quantities. Serving counts are
  set locally because the API has no original-serving field. Cooking snapshots,
  timestamped checklist history, and undo state persist separately per account.
- **Xcode packaging**: Run archive/export with `PATH=/usr/bin:/bin:/usr/sbin:/sbin`.
  Homebrew rsync 3.5 can cause `exportArchive Copy failed` during IPA packaging.
  The background upload tool accepts `--archive PATH` to retry an existing archive
  after an App Store Connect metadata correction without rebuilding.
- **Fork deployment**: GitHub `Malaber/what-should-we-eat` owns CI and GHCR images.
  Development remains `codex/onionary-ios-companion`; see
  `docs/development-deployment.md` and `deploy/compose.test.yml`. App website
  lives only in `website/` on GitHub Pages at `onionary.malaber.de`; use a separate
  backend origin such as `onionary-test.malaber.de` for passkeys/API traffic.
- **Release versions**: Upstream API was 0.1.0 without Git tags; fork baseline is
  0.2.0. Use stable `vX.Y.Z` and development `vX.Y.Z-rc.N` tags. Container builds
  use `execution/version.py`; version and commit are embedded as OCI labels.

- **Cross-instance copies**: `POST /recipe-shares` creates an expiring snapshot.
  `POST /recipe-shares/preview` fetches a public HTTPS copy for review before the
  normal recipe create endpoint saves it. Tokens are hashed; remote fetches pin
  validated public DNS addresses and never forward authentication. See
  `docs/kitchen-sharing-deployment.md` for legal identity and extension signing.
