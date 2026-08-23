# Gauge Stricklin — Resume

## Files

- **`gauge-stricklin-resume.html`** — the resume. Source of truth. Open in a browser and
  print (Cmd/Ctrl+P → *Save as PDF*, Letter, default margins) for the PDF you send out.
  Real selectable text, so ATS parsers read it correctly. Fits 2 pages.
- **`build-artifact-fragment.sh`** — regenerates the published web version from the file
  above by stripping the `<!doctype>/<head>/<body>` wrapper. Run it after any edit, then
  republish the output.

## Editing

Everything is one self-contained file — no build step, no dependencies.

Placeholders are wrapped in `<span class="todo">` and render highlighted in blue so they
are impossible to miss. Search the file for `todo` to find every one.

The palette lives in the `:root` token block at the top of the `<style>` element, with
dark-theme and print overrides below it. Change a color once there and it updates
everywhere.

### Print length

`@media print` sets `html{font-size:8.7pt}`. Every size in the sheet is in `rem`, so that
one value scales the whole document. Raise it for larger type, lower it to fit more
content — but check the page count after, since 9.0pt pushes it to 3 pages.
