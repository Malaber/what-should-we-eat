# Development backend and releases

Development branch: `codex/onionary-ios-companion`.
GitHub `main` initially mirrors upstream GitLab main; do not deploy it as Onionary
until the companion changes are merged. All new CI runs and images live in
`Malaber/what-should-we-eat`. GitLab CI has been replaced by GitHub Actions.

## Ship this branch to a test server

Use a separate hostname, for example `onionary-test.malaber.de`. The hostname
`onionary.malaber.de` is reserved for the static app website on GitHub Pages.

1. Push the development branch and wait for **Build and test** to finish. Its
   final job publishes `ghcr.io/malaber/what-should-we-eat:development` plus an
   immutable `sha-<full commit>` image for AMD64 and ARM64. PRs never publish.
2. On a test server with Docker Compose and your existing Traefik, clone this repository/branch:

   ```sh
   git clone --branch codex/onionary-ios-companion https://github.com/Malaber/what-should-we-eat.git
   cd what-should-we-eat
   cp deploy/test.env.example deploy/test.env
   openssl rand -hex 32
   openssl rand -hex 32
   ```

3. Put the two generated values into `POSTGRES_PASSWORD` and `SECRET_KEY` in
   `deploy/test.env`. Set `BACKEND_HOST`. Use hex for the database password to
   avoid URL-encoding problems. Point that hostname's DNS A/AAAA to your Traefik
   server. The defaults match Planini: Docker network `traefik_external`,
   entrypoint `websecure`, and certificate resolver `lets-encr`. Adjust the
   `TRAEFIK_*` values if your existing Traefik uses different names. Traefik must
   already be attached to that external network with its Docker provider enabled.
   This stack publishes no host ports and runs no TLS proxy.
4. If GHCR package visibility is private, either make the package public in
   GitHub package settings or authenticate the server with a read:packages token:

   ```sh
   docker login ghcr.io -u YOUR_GITHUB_USERNAME
   ```

5. Start the isolated test stack:

   ```sh
   docker compose --env-file deploy/test.env -f deploy/compose.test.yml pull
   docker compose --env-file deploy/test.env -f deploy/compose.test.yml up -d
   docker compose --env-file deploy/test.env -f deploy/compose.test.yml logs migrate api
   curl --fail https://onionary-test.malaber.de/health
   ```

   Postgres becomes healthy before the migration job runs; the API starts only
   after migrations succeed. Traefik terminates TLS and forwards HTTP to the
   Python app on port 8000. Only the API joins the Traefik network; Postgres
   and the migration job stay on the stack's default network. This stack uses
   its own named database volume, separate from production. No database port
   is public. No separate migration command is needed for initial startup.
6. Open `/auth/login` on the test backend to create a passkey account. Existing
   imported accounts need enrollment:

   ```sh
   docker compose --env-file deploy/test.env -f deploy/compose.test.yml exec api \
     python -m execution.enroll_passkey chef@example.com
   ```

   Share the resulting link privately with the verified owner. Open Onionary →
   Settings → enter the test backend origin → Continue with passkey. The already
   uploaded 1.0.0 app initially suggests the website hostname; change it manually.
   New builds suggest the separate test backend.

## Update and rollback

After a green development pipeline, pull images and recreate the stack:

```sh
docker compose --env-file deploy/test.env -f deploy/compose.test.yml pull
docker compose --env-file deploy/test.env -f deploy/compose.test.yml up -d
```

Compose reruns the exited migration job before starting the updated API. If
migration fails, inspect `logs migrate`; the new API will not start. The app
image itself runs only Uvicorn; deployments outside this Compose setup must
run `python -m execution.db.init_db` before starting the app. Keep a single
migration job per database, even if running multiple API replicas.

For reproducible deployments set `ONIONARY_IMAGE` to `ghcr.io/malaber/what-should-we-eat:sha-<full commit>`.
Back up the database before upgrades:

```sh
docker compose --env-file deploy/test.env -f deploy/compose.test.yml exec -T db \
  pg_dump -U onionary onionary > onionary-test-backup.sql
```

Keep backups outside Git and restrict their permissions. Rolling back an image
does not undo database migrations; restore a matching backup if schema changes
are incompatible. Never use `down -v` unless you intend to delete test data.

## Versions

Upstream had no Git tags and API version 0.1.0. This fork starts at **0.2.0**.
Like Planini, Git tags are the version authority: stable `v0.2.0`, development
release candidates `v0.2.0-rc.1`, `v0.2.0-rc.2`, etc. We explicitly tag releases;
ordinary commits use `<base>-dev.<sha>`. Stable tags publish `latest`; RC tags do
not. The moving `development` image only tracks successful branch pipelines.

```sh
git tag -a v0.2.0-rc.2 -m 'Onionary 0.2.0 release candidate 2'
git push github v0.2.0-rc.2
python3 execution/version.py
python3 execution/version.py --ios
```

Tag the tested commit. Do not move published tags. Xcode uses the numeric part
for marketing version; increment TestFlight build numbers independently.
**App Store Connect already accepted 1.0.0 (1)** before the fork version policy
was set. Repository/backend starts at 0.2.0; confirm Apple's version-train rules
before uploading a lower marketing version, or pass 1.0.0 explicitly with build 2.

## App website and screenshots

`website/` is deployed independently by **GitHub Pages**, from development for now.
The backend Dockerfile does not copy it. Configure Pages source **GitHub Actions**,
custom domain `onionary.malaber.de`, and DNS CNAME `onionary → Malaber.github.io`.
Enable HTTPS after GitHub issues the certificate. Change the workflow branch when
moving website ownership to main.

App Store URLs:

- Marketing: https://onionary.malaber.de/
- Support: https://onionary.malaber.de/support/
- Privacy: https://onionary.malaber.de/privacy/
- Contact: onionary@schaedler.rocks

**App Store screenshots** captures four real app screens in English on iPhone
and 13-inch iPad, with a fixed clock and synthetic recipe fixture. Download each
workflow artifact's `en-US/` PNGs; dimensions are validated. Version tags whose
commits are on `main` also publish `onionary-appstore-iphone-en-US.zip` and
`onionary-appstore-ipad-en-US.zip` on the matching GitHub Release. The workflow
creates the release if missing (prerelease for RC tags) and replaces these assets
on a rerun. Publishing an existing release also triggers capture for that tag.
Both devices must succeed before release upload; archives contain only PNGs.
Main branch pushes capture artifacts when app/screenshot code changes; create a
`v*` tag on the tested main commit to publish the corresponding release assets. No customer data or
backend credentials are used. Screenshots are raw app captures, not fabricated UI.
Local equivalent:

```sh
python3 execution/marketing_screenshots.py --device 'iPhone 17 Pro Max' --output .tmp/marketing-iphone
python3 execution/marketing_screenshots.py --device 'iPad Pro 13-inch (M5)' --output .tmp/marketing-ipad
```
