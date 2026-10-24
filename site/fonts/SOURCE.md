# LXGW WenKai source

Titles, the brand, and quotations use [LXGW WenKai](https://github.com/lxgw/LxgwWenKai) (霞鹜文楷).

| | |
|---|---|
| Version | **1.522** (name table ID 5: `Version 1.522; March 17, 2026`) |
| Release | https://github.com/lxgw/LxgwWenKai/releases/tag/v1.522 |
| License | SIL Open Font License 1.1, in `OFL.txt` next to these files |
| Weights | Regular (`wenkai-regular.woff2`, CSS weight 400) and Medium (`wenkai-medium.woff2`, CSS weight 700) |

The two woff2 files in this directory are the pinned build inputs. They are the v1.522 faces previously cut to 1,048 glyphs. `site/build.py` does not ship them as-is. It subsets them again, at build time, with [fontTools](https://github.com/fonttools/fonttools) (`fontTools.subset`, the `pyftsubset` tool; MIT license) to the characters that page actually draws in this face:

- weight 400: quotation paragraphs (`.quote p`, `.epigraph p`)
- weight 700: `h1`, `h2`, and `.brand`

`brotli` (MIT) compresses the subset to woff2. `@font-face` uses `font-display: swap`. The built site copies `OFL.txt` to `public/assets/fonts/` beside the subset files. The upstream additional permission allows a web-only woff2 subset that keeps the reserved font name.

Pinned sha256:

- `wenkai-regular.woff2` `fb87ae45b0543bf877f01409dfee757339d83ea9420eabf0323e6cdab5aa7352`
- `wenkai-medium.woff2` `29ef82ff317fa12c0b80f94fbbecdd1cd48a952ed2ed4efdeae9f1d2ca16f758`

The tool versions used to cut the subset are pinned in `requirements.txt`.
