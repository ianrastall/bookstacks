# Bookstacks Coral Author Portrait Wells

This patch changes author portrait rendering for transparent black-line PNG portraits.

## What changed

- `src/styles/global.css`
  - Removes the dark-mode `filter: invert(1)` behavior from `.author-portrait`.
  - Gives author-card portrait wells a fixed light coral background in both light and dark mode.
  - Gives the author landing-page portrait frame the same light coral background.
  - Sets portraits to `object-fit: contain` so 500x500 transparent line art is not cropped.

## Why

The new author portraits are normal black-line PNGs on transparent backgrounds. Inverting them in dark mode turns the entire raster into a photo-negative-looking image. A fixed light coral portrait well keeps the same source image in both themes and preserves the intended black engraved linework.

## Apply

From the repository root:

```powershell
Expand-Archive .\bookstacks-coral-author-portraits.zip -DestinationPath . -Force
npm run build
```

The portrait files should remain at:

```text
public/img/authors/austen-jane.png
public/img/authors/kafka-franz.png
public/img/authors/tolstoy-leo.png
```
