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
