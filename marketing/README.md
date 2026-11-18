# Onionary App Store artwork

The CI workflow uses real captures from the passing iPhone, iPad and iPhone Duo
native suites. Each device gets a ZIP with raw screenshots and framed portraits
in `en-US/portraits/`. The portraits feature the cooking checklist, recipe
book and portion controls at the device's App Store upload dimensions.
The iPhone ZIP also includes a raw Lock Screen Live Activity and a framed
portrait made from it. The native test opens the iOS Lock Screen cover sheet
and verifies the actual WidgetKit activity before capture.
The Duo ZIP also includes an unfolded cooking screenshot in `en-US/inner/`.

The separate creative ZIP is shared across devices. Its `en-US/creative/`
directory contains editable SVGs and opaque
5244 × 2950 PNGs for the product-page header and search results. The versions
ending in `-safe-area-preview.png` are review crops. Upload the full-size
`header.png` and `search-results.png` through App Store Connect.

The renderer measures the actual SVG artwork against Apple's universal safe
rectangle at x=1921, y=660, width=1402, height=962. The crops let you inspect
the part that stays visible. Confirm the final artwork in App Store Connect's
placement previews before publishing.

- [Apple creative asset specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications)
- [Editable artwork and shared CI renderer](creative/README.md)
- [Apple product bezel guidelines](https://developer.apple.com/app-store/marketing/guidelines/)

Generate framed portraits locally from the original XCTest PNGs:

```sh
python -m pip install -r marketing/requirements.txt
python execution/render_marketing_assets.py .tmp/marketing/iphone/en-US --family iphone
```

Add `--include-creative` to render the shared artwork using that iPhone capture.
The renderer downloads matching model-specific Apple bezels from pinned commits
and verifies their SHA-256 digests. Set `ONIONARY_BEZELS_DIRECTORY` to a verified
local cache to render offline. Only the finished composites are packaged.

Use Inkscape for SVG output. The renderer uses bundled Lora and Manrope fonts
with their SIL Open Font Licenses. CI checks every output's dimensions and
decodes it, verifies the source capture hashes, and makes the screenshot
bundles available as artifacts. Main releases attach the same validated
bundles as ZIPs.
