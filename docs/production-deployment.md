# Production domains

- Production backend: https://onionary.malaber.de — latest successful `:main` image.
- Development backend: https://onionary-test.malaber.de — existing `:development` image.
- App website: https://app.onionary.malaber.de — GitHub Pages `website/` from main.

Backend deployments remain separate in infra/selfhosted. Production uses
`apps.onionary_production`, `deploy-onionary-production.yml`, its own Vault
secrets and PostgreSQL volume. Configure required Impressum operator values
before deployment. Existing development data and passkeys are not moved.
The `:latest` image remains reserved for stable release tags.

Pages settings must use GitHub Actions with custom domain `app.onionary.malaber.de`.
The github-pages environment must allow main deployments. DNS was changed by
the operator. Update App Store Connect marketing/support/privacy URLs to:

- https://app.onionary.malaber.de/
- https://app.onionary.malaber.de/support/
- https://app.onionary.malaber.de/privacy/

Existing installed builds keep their old support URLs until updated. This PR
updates native links for the next build. No TestFlight upload is part of this
configuration change.

Deployment changes: [selfhosted !29](https://gitlab.com/malaber-ansible/selfhosted/-/merge_requests/29), then [infra !37](https://gitlab.com/Malaber/infra/-/merge_requests/37).

## Unicode operator details

Render Compose environment strings with Ansible `to_json(ensure_ascii=False)`.
The default JSON encoder emits literal `\u00e4` sequences which Compose does
not decode. Use actual UTF-8 names such as `Schädler` in inventory, update the
collection with the encoding fix, then re-run deployment to regenerate app.env.
Do not enter pre-escaped JSON text in operator variables.

## Stable main releases

Successful main CI runs create a stable release, bumping the highest version's
minor component by default (`v0.2.0-rc.3` becomes `v0.3.0`). Merged PR title and
body supply release title and notes. Labels `release:patch` / `release:major`
opt into other increments. Re-runs reuse an existing stable tag on that commit.
The release publishes matching versioned, main and latest Docker images. An
explicit screenshot workflow dispatch on the tag attaches marketing assets;
this avoids relying on tag events suppressed for GITHUB_TOKEN-created tags.

Unicode deployment fixes: [selfhosted !30](https://gitlab.com/malaber-ansible/selfhosted/-/merge_requests/30)
and [infra !38](https://gitlab.com/Malaber/infra/-/merge_requests/38).
