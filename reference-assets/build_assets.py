#!/usr/bin/env python3
"""
Reference-asset downloader for edit overlays.

Reads manifest.csv, searches Wikimedia Commons for each query, downloads files
whose long side is >= MIN_SIDE px and whose license is free to reuse, and
(for rows flagged `cutout`) builds overlay-ready variants:
  *_alpha_black.png  dark subject on transparent  (use Normal / Multiply)
  *_alpha_white.png  white subject on transparent (use Normal / Screen over dark footage)

Output:  assets/<folder>/originals/*  +  assets/<folder>/overlays/*
         assets/CREDITS.csv  (title, author, license, source URL for every file)

Usage:
  pip install pillow
  python3 build_assets.py                  # everything
  python3 build_assets.py --only math      # one folder
  python3 build_assets.py --licenses pd    # public domain / CC0 only (safest for client work)
Re-running skips files already downloaded.
"""
import argparse, csv, html, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

API = "https://commons.wikimedia.org/w/api.php"
UA = "OverlayAssetKit/1.0 (personal edit-asset collector; thegaugeashtonn@gmail.com)"
MIN_SIDE = 3840
PD_RE = re.compile(r"public domain|pd-|cc0|cc zero", re.I)
FREE_RE = re.compile(r"public domain|pd-|cc0|cc zero|cc[- ]by(-sa)?[- ]", re.I)
DELAY = 1.5


def get(url, binary=False, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            time.sleep(DELAY)
            return data if binary else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                wait = int(e.headers.get("retry-after", 20)) + 5 * i
                print(f"   rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(5 * (i + 1))
    raise RuntimeError("giving up on " + url)


def search(query, limit=30):
    q = {
        "action": "query", "format": "json", "generator": "search",
        "gsrnamespace": 6, "gsrsearch": f"{query} filew:>={MIN_SIDE // 2}",
        "gsrlimit": limit, "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
    }
    data = get(API + "?" + urllib.parse.urlencode(q))
    pages = (data.get("query") or {}).get("pages") or {}
    return sorted(pages.values(), key=lambda p: p.get("index", 0))


def strip(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def candidates(pages, pd_only):
    ok = FREE_RE if not pd_only else PD_RE
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        if ii.get("mime") not in ("image/jpeg", "image/png", "image/tiff"):
            continue
        if max(ii.get("width", 0), ii.get("height", 0)) < MIN_SIDE:
            continue
        meta = ii.get("extmetadata", {})
        lic = strip(meta.get("LicenseShortName", {}).get("value"))
        if not ok.search(lic):
            continue
        yield {
            "title": p["title"], "url": ii["url"], "w": ii["width"], "h": ii["height"],
            "license": lic, "author": strip(meta.get("Artist", {}).get("value"))[:120],
            "page": ii.get("descriptionurl", ""),
        }


def safe(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name.replace("File:", ""))[:90]


def make_overlays(path, outdir):
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = None
    stem = os.path.splitext(os.path.basename(path))[0]
    im = Image.open(path).convert("L")
    # dark-on-light source -> alpha from darkness; threshold to clean paper/white bg
    alpha = ImageOps.invert(im).point(lambda v: 0 if v < 40 else min(255, int((v - 40) * 255 / 215)))
    black = Image.new("L", im.size, 0)
    white = Image.new("L", im.size, 255)
    Image.merge("LA", (black, alpha)).save(os.path.join(outdir, stem + "_alpha_black.png"))
    Image.merge("LA", (white, alpha)).save(os.path.join(outdir, stem + "_alpha_white.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(os.path.dirname(__file__), "manifest.csv"))
    ap.add_argument("--out", default="assets")
    ap.add_argument("--only", help="only folders whose name contains this text")
    ap.add_argument("--licenses", choices=["pd", "free"], default="free")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    credits_path = os.path.join(args.out, "CREDITS.csv")
    seen = set()
    if os.path.exists(credits_path):
        with open(credits_path, newline="", encoding="utf-8") as f:
            seen = {r["file"] for r in csv.DictReader(f)}
    cf = open(credits_path, "a", newline="", encoding="utf-8")
    cw = csv.writer(cf)
    if not seen:
        cw.writerow(["file", "title", "author", "license", "size", "source"])

    with open(args.manifest, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if not r["folder"].startswith("#")]

    for r in rows:
        if args.only and args.only not in r["folder"]:
            continue
        want = int(r.get("count") or 1)
        orig = os.path.join(args.out, r["folder"], "originals")
        over = os.path.join(args.out, r["folder"], "overlays")
        os.makedirs(orig, exist_ok=True)
        print(f"[{r['folder']}] {r['query']}  (want {want})")
        got = 0
        try:
            pages = search(r["query"])
        except Exception as e:
            print("   search failed:", e)
            continue
        for c in candidates(pages, args.licenses == "pd"):
            if got >= want:
                break
            ext = os.path.splitext(urllib.parse.urlparse(c["url"]).path)[1].lower() or ".jpg"
            rel = os.path.join(r["folder"], "originals", safe(c["title"]))
            rel = os.path.splitext(rel)[0] + ext
            dest = os.path.join(args.out, rel)
            if not os.path.exists(dest):
                try:
                    with open(dest, "wb") as out:
                        out.write(get(c["url"], binary=True))
                except Exception as e:
                    print("   download failed:", c["title"], e)
                    if os.path.exists(dest):
                        os.remove(dest)
                    continue
                print(f"   + {os.path.basename(dest)}  {c['w']}x{c['h']}  {c['license']}")
            got += 1
            if rel not in seen:
                cw.writerow([rel, c["title"], c["author"], c["license"], f"{c['w']}x{c['h']}", c["page"]])
                cf.flush()
                seen.add(rel)
            if (r.get("cutout") or "").strip().lower() in ("y", "yes", "1") and dest.lower().endswith((".jpg", ".png", ".tif", ".tiff")):
                os.makedirs(over, exist_ok=True)
                try:
                    make_overlays(dest, over)
                except Exception as e:
                    print("   overlay build failed:", e)
        if got < want:
            print(f"   only found {got}/{want} qualifying 4K+ free files for this query")
    cf.close()
    print("\nDone. Check assets/CREDITS.csv for license + author of every file.")


if __name__ == "__main__":
    sys.exit(main())
