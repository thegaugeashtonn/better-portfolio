#!/bin/sh
# Derive the Artifact fragment from the canonical standalone resume.
# The Artifact host supplies <!doctype>/<head>/<body>, so strip our wrapper.
SRC=/home/user/better-portfolio/resume/gauge-stricklin-resume.html
OUT="$1"
sed -e '/^<!doctype html>$/d' \
    -e '/^<html lang="en">$/d' \
    -e '/^<head>$/d' \
    -e '/^<meta charset="utf-8">$/d' \
    -e '/^<meta name="viewport"/d' \
    -e '/^<\/head>$/d' \
    -e '/^<body>$/d' \
    -e '/^<\/body>$/d' \
    -e '/^<\/html>$/d' "$SRC" > "$OUT"
