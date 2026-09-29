#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pillow"]
# ///
"""Arrange images into a labeled grid (A, B, C, ...) and save as one image.

Usage: griddify [-o OUT] [--grid WxH] [--cell-width PX]
                 [--image-height PX] [--label-height PX] [--margin PX]
                 [--font-size PX] [--font PATH] [--labels A,B,C,...] [--no-labels]
                 IMAGE [IMAGE ...]

Grid size defaults to the most-square W x H (W >= H) whose product equals the
number of images, if one exists (W and H both != 1). Otherwise falls back to
a near-square grid with some empty cells. --grid WxH overrides this and must
exactly account for every image.
"""
import argparse
import math
import os
import re
import string

from PIL import Image, ImageDraw, ImageFont, ImageOps

# Candidate bold fonts to try, in order, across macOS/Linux.
BOLD_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def resolve_font(path, size):
    candidates = [path] if path else BOLD_FONT_CANDIDATES
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    if path:
        raise SystemExit(f"griddify: font not found: {path}")
    return ImageFont.load_default(size=size)


def parse_grid(s):
    m = re.fullmatch(r"(\d+)[xX](\d+)", s)
    if not m:
        raise SystemExit(f"griddify: --grid must look like WxH (e.g. 5x2), got {s!r}")
    return int(m.group(1)), int(m.group(2))


def auto_grid(n):
    """Most-square (cols, rows) with cols >= rows and cols*rows == n, both != 1.

    Falls back to a near-square grid with empty cells (n prime, or n == 1).
    """
    best = None
    for w in range(2, n):
        if n % w == 0:
            h = n // w
            if h != 1:
                pair = (max(w, h), min(w, h))
                if best is None or abs(pair[0] - pair[1]) < abs(best[0] - best[1]):
                    best = pair
    if best is not None:
        return best
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return cols, rows


def default_labels(n):
    letters = list(string.ascii_uppercase)
    if n <= len(letters):
        return letters[:n]
    # Fall back to AA, AB, ... once the alphabet runs out.
    labels = list(letters)
    while len(labels) < n:
        labels.append(labels[len(labels) - len(letters)] + letters[len(labels) % len(letters)])
    return labels[:n]


def main():
    parser = argparse.ArgumentParser(
        description="Arrange images into a labeled grid (A, B, C, ...) and save as one image."
    )
    parser.add_argument("images", nargs="+", help="Image files to place in the grid, in order.")
    parser.add_argument("-o", "--out", default="griddify-out.png", help="Output image path (default: %(default)s).")
    parser.add_argument("--grid", help="Grid size as WxH (e.g. 5x2); overrides automatic sizing. W*H must be >= the number of images.")
    parser.add_argument("--cell-width", type=int, default=520, help="Cell width in px (default: %(default)s).")
    parser.add_argument("--image-height", type=int, default=390, help="Image area height per cell in px (default: %(default)s).")
    parser.add_argument("--label-height", type=int, default=155, help="Label area height per cell in px (default: %(default)s).")
    parser.add_argument("--margin", type=int, default=25, help="Outer margin in px (default: %(default)s).")
    parser.add_argument("--font-size", type=int, default=125, help="Label font size in px (default: %(default)s).")
    parser.add_argument("--font", help="Path to a .ttf/.otf font for labels (default: auto-detected bold font).")
    parser.add_argument("--labels", help="Comma-separated custom labels (default: A, B, C, ...).")
    parser.add_argument("--no-labels", action="store_true", help="Skip drawing labels.")
    args = parser.parse_args()

    n = len(args.images)
    if args.grid:
        cols, rows = parse_grid(args.grid)
        if cols * rows < n:
            raise SystemExit(f"griddify: --grid {args.grid} holds {cols * rows} cells but {n} images were given")
    else:
        cols, rows = auto_grid(n)

    if args.no_labels:
        labels = [""] * n
    elif args.labels:
        labels = [s.strip() for s in args.labels.split(",")]
        if len(labels) != n:
            raise SystemExit(f"griddify: --labels has {len(labels)} entries but {n} images were given")
    else:
        labels = default_labels(n)

    cell_w = args.cell_width
    image_h = args.image_height
    label_h = 0 if args.no_labels else args.label_height
    margin = args.margin

    W = margin * 2 + cols * cell_w
    H = margin * 2 + rows * (image_h + label_h)

    canvas = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas)
    font = None if args.no_labels else resolve_font(args.font, args.font_size)

    for i, path in enumerate(args.images):
        im = Image.open(path).convert("RGB")

        # Scale the original image to fit its cell, preserving aspect ratio.
        fitted = ImageOps.contain(im, (cell_w - 30, image_h - 25))

        col = i % cols
        row = i // cols

        x0 = margin + col * cell_w
        y0 = margin + row * (image_h + label_h)

        # Center image within the image portion of the cell.
        x = x0 + (cell_w - fitted.width) // 2
        y = y0 + (image_h - fitted.height) // 2

        canvas.paste(fitted, (x, y))

        if args.no_labels:
            continue

        letter = labels[i]
        box = draw.textbbox((0, 0), letter, font=font)
        tw = box[2] - box[0]
        th = box[3] - box[1]

        tx = x0 + (cell_w - tw) // 2
        ty = y0 + image_h + (label_h - th) // 2 - 8

        draw.text((tx, ty), letter, font=font, fill="black")

    save_kwargs = {"quality": 96} if args.out.lower().endswith((".jpg", ".jpeg")) else {}
    canvas.save(args.out, **save_kwargs)

    empty = cols * rows - n
    note = f" ({empty} empty cell{'s' if empty != 1 else ''})" if empty else ""
    print(f"Grid: {cols}x{rows}{note}")
    print(args.out)


if __name__ == "__main__":
    main()
