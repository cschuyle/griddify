# Griddify

Make a grid of labeled thumbnails from a set of input images.

Handy when you want to send someone one image and say "look at these examples."

## Usage

```
griddify img1.png img2.png ...             # output file defaults to griddify-out.png

griddify -o out.png img1.png img2.png ...
```

Grid size defaults to the most-square `W x H` that evenly fits the image
count; falls back to a near-square grid with empty cells otherwise. Override
with `--grid WxH` (must have at least as many cells as images). Run
`griddify --help` for all options.

## Optional: Packaged with bash and `uv` (Python package manager)

For convenience, `griddify` is supplied. It's a thin wrapper around the actual Python code which auto-installs and caches Python dependencies and runs the script.

How does it work? `griddify.py` declares its own deps (Pillow) inline via PEP 723. `uv run --script` reads that, builds/caches a venv for it automatically, and runs it
— no manual `pip install` or venv setup.

However, this DOES require you to install `uv`, so there's that downside. On Mac with Homebrew you could do this by `brew install uv`.

If you DON'T want to mess with `uv`, you can run the Python script directly after setting up package dependencies however you want.

