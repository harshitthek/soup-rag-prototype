# Vendored upstream documentation sources

These files are the raw Markdown inputs that produced `data/corpus.jsonl`.

- **Upstream repository:** https://github.com/MakazhanAlpamys/Soup
- **License:** Apache License 2.0 — full text in `LICENSE-soup-upstream.txt`.
  Attribution: original copyright belongs to the Soup project authors.
- **Pinned upstream commit:** `8ab26641ed34e724018e696a93a06460f26c153e`
  (recorded in `data/source_manifest.json`).
- **Download procedure:** fetched from
  `https://raw.githubusercontent.com/MakazhanAlpamys/Soup/<commit>/docs/<file>`.

## Integrity verification against `data/source_manifest.json`

11 of 12 files are byte-identical to the corpus-era sources: sha256 and byte
size match `source_manifest.json` exactly. The vendored copies are stored
with CRLF line endings because the corpus-era files were CRLF; upstream serves
LF blobs. Converting LF→CRLF reproduces the manifest hashes exactly (verified
at vendoring time). `.gitattributes` marks these files `-text` so Git never
normalizes the line endings.

**Known exception — `backends-and-ops.md`:** the corpus-era copy does not
match any upstream version found in a bounded history search around the pinned
commit (neighboring commits range 104–110 KB; the pinned blob is 34.1 KB;
the corpus-era file was 35.8 KB with identical section headings). The vendored
copy is the pinned-commit version. The exact provenance of the corpus-era copy
is recorded as an open item in `docs/EVALUATION_V2_PROGRESS.md`. This does not
affect the v2 evaluation: the file is a training document, and
`data/corpus.jsonl` (tracked, unchanged) remains the ground truth for all
retrieval experiments.

## Per-file checksums (corpus-era, from `data/source_manifest.json`)

| File | sha256 (corpus-era) | Vendored matches? |
|---|---|---|
| adapters-and-governance.md | 9d3946e4… | yes |
| backends-and-ops.md | ad8b8445… | **no** (see above) |
| commands.md | adb4def7… | yes |
| compliance.md | 9f68667a… | yes |
| data.md | 6fc0ca77… | yes |
| evaluation.md | 5908cf7a… | yes |
| models.md | c75bae4c… | yes |
| peft-and-efficiency.md | 0d22ea56… | yes |
| performance-and-quantization.md | 1530f871… | yes |
| README.md | 4cb577c5… | yes |
| serving-and-export.md | 1482c766… | yes |
| training.md | f5652edf… | yes |

Full hashes are in `data/source_manifest.json`.
