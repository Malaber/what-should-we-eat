# Reusable creative-asset pipeline

Header and search-results sources are editable 5244×2950 SVGs. Both exports are
opaque RGB PNGs, suitable for Apple's universal creative-asset upload fields.
Reference checked 2026-11-03:
https://developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications

## Render and review

Install Inkscape (macOS: `brew install --cask inkscape`; Ubuntu: `apt install
inkscape`) and `python -m pip install -r marketing/requirements.txt`.

```
python marketing/creative/render.py \
  --screenshot .tmp/marketing/iphone/en-US/02-cooking-companion.png \
  --output .tmp/onionary-creative
```

Use the actual exported filename. The renderer embeds that exact screenshot and
the existing app icon; never replaces UI with an AI mockup. It outlines text using
bundled Lora/Manrope fonts before invoking Inkscape. Source SVG text stays editable;
the exported SVGs are portable and require neither external images nor fonts.
Pillow fully decodes every export and enforces 5244×2950 RGB, with an sRGB profile.
Do not upscale the PNG. Change the SVG, then render again.

Main text/icon elements are inset from canvas edges; background curves may crop.
Apple's different placements still need human review in App Store Connect's
Preview tool. No workflow uploads/replaces App Store Connect assets automatically.
Inspect full-size artwork, a thumbnail, and both placement previews before approval.

## CI and other apps

Onionary's screenshot workflow captures fictional demo content on both device
families. Capture jobs defer universal artwork to the pinned shared workflow;
bundle jobs reunite its SVG/PNG outputs with the captures. Local
`execution/render_marketing_assets.py` runs both stages together.
The existing release job validates the image sizes, full PNG decoding and source
hash, then attaches the bundle to its matching main release.

To adopt this in another app:
1. Copy the SVG + renderer contract into `marketing/creative/`.
2. Replace branding and short benefit copy with real supported features.
3. Bundle licensed fonts; keep all text outlined in exported SVGs.
4. Capture demo UI in a deterministic screenshot test; publish that artifact.
5. Call `reusable-appstore-creative.yml` in Malaber/github-workflows,
   pinned to the reviewed commit SHA. Supply the screenshot artifact,
   one exact screenshot glob, renderer path and requirements path.
6. Download its output artifact in the app's existing release packaging job.
7. Review artwork before manually updating App Store Connect.

The reusable workflow runs the caller's renderer on Linux with Inkscape and
Pillow. Brand-specific SVGs, text shaping, screenshots, and licenses stay with the
app. No credentials or paid generation are needed. Pin the runner/container and
Inkscape version for byte-identical output across environments; current jobs
validate pixel dimensions/content but do not promise identical compression bytes
between different Inkscape/platform versions.
