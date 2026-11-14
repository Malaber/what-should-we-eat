# Onionary App Store artwork

The CI workflow uses the iPhone and iPad captures from the passing native test
suite. Each device artifact contains four unmodified screenshots and three
framed portraits in `en-US/portraits/`. The three portraits feature the cooking
checklist, recipe book, and portion controls. Each portrait retains the
corresponding device's App Store upload dimensions.

The `en-US/creative/` directory contains editable SVGs and opaque
5244 × 2950 PNGs for the product-page header and search results. The versions
ending in `-safe-area-preview.png` are review crops. Upload the full-size
`header.png` and `search-results.png` through App Store Connect.

The renderer measures the actual SVG artwork against Apple's universal safe
rectangle at x=1921, y=660, width=1402, height=962. The crops let you inspect
the part that stays visible. Confirm the final artwork in App Store Connect's
placement previews before publishing.

- [Apple creative asset specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications)
- [Editable artwork and shared CI renderer](creative/README.md)

Generate both kinds of artwork locally from the four original XCTest PNGs:

```sh
python -m pip install -r marketing/requirements.txt
python execution/render_marketing_assets.py .tmp/marketing/iphone/en-US --family iphone
```

Use Inkscape for SVG output. The renderer uses bundled Lora and Manrope fonts
with their SIL Open Font Licenses. CI checks every output's dimensions and
decodes it, verifies the source capture hashes, and makes the screenshot
bundles available as artifacts. Main releases attach the same validated
bundles as ZIPs.
