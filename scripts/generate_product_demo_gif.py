"""Generate the beta-safe Scout product demo GIF used by the launch website."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "website" / "assets" / "scout-product-demo.gif"

BG = "#ebebe8"
INK = "#18181b"
MUTED = "#5f6068"
BLUE = "#3b82f6"
GREEN = "#16a34a"
AMBER = "#b45309"
PANEL = "#f8f7f2"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    fill: str = INK,
    bold: bool = False,
) -> None:
    draw.text(xy, text, fill=fill, font=_font(size, bold=bold))


def _round(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str = INK,
    width: int = 2,
    radius: int = 16,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _chrome(draw: ImageDraw.ImageDraw, title: str, url: str) -> None:
    _round(draw, (70, 55, 1210, 665), PANEL, outline=INK, width=3, radius=18)
    draw.rectangle((70, 55, 1210, 118), fill=INK)
    for x, color in ((96, "#ef4444"), (124, "#f59e0b"), (152, "#22c55e")):
        draw.ellipse((x, 78, x + 16, 94), fill=color)
    _text(draw, (190, 76), title, 21, fill=BG, bold=True)
    _round(draw, (475, 72, 1135, 101), "#27272a", outline="#3f3f46", width=1, radius=10)
    _text(draw, (494, 78), url, 15, fill="#d4d4d8")


def _pill(
    draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fill: str, fg: str = "#ffffff"
) -> None:
    width = 22 + len(text) * 8
    draw.rounded_rectangle((x, y, x + width, y + 32), radius=16, fill=fill)
    _text(draw, (x + 12, y + 8), text, 14, fill=fg, bold=True)


def _frame_one() -> Image.Image:
    img = Image.new("RGB", (1280, 720), BG)
    draw = ImageDraw.Draw(img)
    _chrome(draw, "Scout beta demo", "https://demo.brand/category/skincare")
    _text(draw, (110, 155), "1. Give Scout a public category URL", 42, bold=True)
    _text(
        draw,
        (112, 215),
        "Scout starts with crawl4ai, preserves source evidence, and records blocked pages instead of hiding them.",
        22,
        fill=MUTED,
    )
    _round(draw, (125, 295, 1145, 390), "#101014", outline="#101014", width=2, radius=8)
    _text(
        draw,
        (155, 326),
        "scout products skincare --site demo.brand --start-url https://demo.brand/category/skincare",
        23,
        fill=BG,
    )
    _pill(draw, 150, 450, "crawler", BLUE)
    _pill(draw, 270, 450, "source_pages.json", INK)
    _pill(draw, 475, 450, "blocked_pages.json", AMBER)
    _text(
        draw,
        (150, 510),
        "Beta-safe demo flow. No hard-site bypass guarantee.",
        24,
        fill=AMBER,
        bold=True,
    )
    return img


def _frame_two() -> Image.Image:
    img = Image.new("RGB", (1280, 720), BG)
    draw = ImageDraw.Draw(img)
    _chrome(draw, "Scout beta demo", "run: products / evidence")
    _text(draw, (110, 155), "2. Evidence becomes reusable run artifacts", 42, bold=True)
    cards = [
        ("records.json", "Typed product records", GREEN),
        ("source_pages.json", "URL, provider, hash, fetched_at", BLUE),
        ("blocked_pages.json", "Reason + provider attempts", AMBER),
        ("extraction_report.md", "Human review summary", INK),
    ]
    x = 115
    for title, body, color in cards:
        _round(draw, (x, 250, x + 245, 475), "#ffffff", outline=color, width=4, radius=14)
        _pill(draw, x + 22, 278, title, color)
        _text(draw, (x + 24, 335), body, 23, fill=INK, bold=True)
        _text(draw, (x + 24, 395), "Citable, inspectable,\nportable.", 20, fill=MUTED)
        x += 275
    _text(
        draw,
        (125, 545),
        "Scout's value is not just content retrieval. It is the evidence trail around the content.",
        26,
        fill=INK,
        bold=True,
    )
    return img


def _frame_three() -> Image.Image:
    img = Image.new("RGB", (1280, 720), BG)
    draw = ImageDraw.Draw(img)
    _chrome(draw, "Scout beta demo", "exports / downstream")
    _text(draw, (110, 155), "3. Export records to the destination that needs them", 42, bold=True)
    _round(draw, (110, 245, 1170, 505), "#ffffff", outline=INK, width=3, radius=14)
    headers = ["objectID", "name", "price", "source", "citations"]
    xs = [145, 305, 610, 760, 940]
    for x, header in zip(xs, headers, strict=True):
        _text(draw, (x, 280), header, 18, fill=MUTED, bold=True)
    rows = [
        ("demo-001", "Advanced Repair Serum", "$130.00", "Listing", "2"),
        ("demo-002", "Daily Moisture Cream", "$58.00", "Listing", "2"),
        ("demo-003", "Night Care Set", "$92.00", "Blocked detail", "1"),
    ]
    y = 330
    for row in rows:
        draw.line((135, y - 12, 1145, y - 12), fill="#d4d4d8", width=1)
        for x, value in zip(xs, row, strict=True):
            _text(draw, (x, y), value, 20, fill=INK)
        y += 54
    for x, label, color in (
        (150, "JSONL", INK),
        (270, "CSV", INK),
        (370, "SQLite", INK),
        (500, "Google Sheets", GREEN),
        (700, "Algolia", BLUE),
    ):
        _pill(draw, x, 555, label, color)
    _text(
        draw,
        (150, 612),
        "Product records to JSONL, CSV, SQLite, Google Sheets, and Algolia.",
        24,
        fill=INK,
        bold=True,
    )
    return img


def main() -> None:
    """Write the generated animated GIF."""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames = [_frame_one(), _frame_two(), _frame_three()]
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=[1300, 1500, 1700],
        loop=0,
        optimize=False,
    )
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
