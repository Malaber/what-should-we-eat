Editable universal artwork and reusable CI instructions: [creative/README.md](creative/README.md).

# Onionary App Store marketing

The screenshot workflow renders current simulator captures into three extra PNGs
inside each existing device ZIP:

- `en-US/creative/header.png`: Kopfzeile, 5244×2950, opaque RGB.
- `en-US/creative/search-results.png`: Suchergebnisse, 5244×2950, opaque RGB.
- `en-US/05-cooking-with-onionary.png`: framed device with marketing copy, same
  accepted screenshot dimensions as that device's raw captures.

The four original screenshots remain unchanged. Upload creative files through
App Store Connect's Header and Search Results tab; upload the portrait alongside
screenshots. Preview Apple's responsive cropping before submission. Outputs are
English, matching the existing en-US capture bundle. No production account data
or generated UI is used. The frame is a neutral device silhouette, not an Apple
hardware artwork asset. CI does not call an image-generation service.

Sources checked 2026-10-11:
- https://developer.apple.com/app-store/asset-best-practices/
- https://developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications

`assets/onionary-kitchen.png` was created with the built-in imagegen tool using
the existing Onionary icon as a style reference. Prompt:

> Create a premium Onionary cooking-companion marketing background, landscape
> 3:2, high resolution. Reference image is the existing Onionary icon, style
> reference only. Warm ivory paper background, tactile softly sculpted 3D
> illustration in plum-purple, pale onion pink and sage green. A small open plum
> recipe book whose pages form onion layers, with a tiny smiling onion mascot,
> placed in the lower LEFT quarter, occupying no more than 30% of canvas width
> and 35% height. A few tasteful basil leaves and a lemon wedge near bottom left
> perimeter. Vast quiet cream negative space across upper half and entire right
> half for later deterministic typography and real phone screenshot insertion.
> Elegant editorial food-app campaign, soft studio shadows, restrained
> composition. No text, no lettering, no phone, no interface, no badge, no
> watermark. Full bleed background, no rounded icon tile or borders.

Fonts are Lora and Manrope from google/fonts (`ofl/lora`, `ofl/manrope`), bundled
with their SIL Open Font Licenses. Pillow is pinned in `requirements.txt` here.

Local render (after installing this directory's requirements):

```sh
python execution/render_marketing_assets.py .tmp/marketing/iphone/en-US --family iphone
```

The renderer requires exactly one fresh `02-cooking-companion*.png` and validates
its device dimensions. It records the screenshot SHA-256 in a manifest. Missing
or ambiguous input fails rather than falling back to a stale checked-in screen.

### Shared CI renderer

`screenshots.yml` calls the merged `Malaber/github-workflows` reusable creative
workflow pinned to commit `2e162b82a123229371804e967273fce54b36b19f`.
Capture jobs produce real UI captures and the portrait composition; Linux rendering
jobs generate the universal SVG/PNG pair; bundle jobs reunite them before release
packaging. No artwork is uploaded to App Store Connect automatically.

Other apps supply their own renderer, requirements file, screenshot artifact/glob
and output artifact. The contract is `--screenshot PATH --output DIRECTORY`, with
`header.svg`, `search-results.svg` and matching opaque RGB 5244 × 2950 PNGs.
Branding, copy, typography and layouts remain caller-owned; the shared workflow
handles rendering dependencies and strict output validation.
