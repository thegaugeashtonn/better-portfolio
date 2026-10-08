# Overlay Reference Asset Kit

Builds a folder of 4K+ reference images (golden ratio, Vitruvian Man, Muybridge figures, Creation of Adam, landmarks, historic faces, space, textures...) for multimedia-style edits.

## Run it (on your own computer, not the cloud session)

```bash
pip install pillow
python3 build_assets.py --licenses pd    # public domain / CC0 only: safest for client work
python3 build_assets.py                  # also allows CC-BY / CC-BY-SA (see CREDITS.csv)
python3 build_assets.py --only 03        # just one folder
```

- Pulls from Wikimedia Commons, long side >= 3840px only. Anything smaller is skipped.
- Resumable: re-run any time, finished files are skipped.
- `assets/CREDITS.csv` lists author, license, and source page for every file.
- Folders flagged `cutout` in `manifest.csv` also get `overlays/*_alpha_black.png` and `*_alpha_white.png`
  (transparent background). Use white on dark footage, black on light, or just drop the original with Multiply/Screen.
- Add your own rows to `manifest.csv` (`folder,query,count,cutout`).

## Licensing, read this before client work

| License | Client/commercial use |
|---|---|
| Public domain / CC0 | Yes, no attribution |
| CC-BY / CC-BY-SA | Yes, but you must credit (CREDITS.csv has the text); SA can have share-alike implications |
| Recent photos of celebrities, cars, buildings | Often CC, but **personality/trademark rights** can still apply in ads. Fine for editorial/social, check with a lawyer for paid brand ads |

Not included, because there is no free source for them: movie stills, album art, current celebrity press photos,
Steve Jobs interview footage, branded logos. Those are copyrighted. For these, use licensed sources
(Getty/Shutterstock editorial, Artgrid/Storyblocks archive footage, or the studio's press kit) or lean on
fair use for commentary/parody only. That call is yours, and the risk is higher on paid client work.
