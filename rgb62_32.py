"""
BASE-RGB62-32: positional system.

Each digit is:
    one RGB color
    one glyph from 0-9 A-Z a-z
    one inverse-color pixel somewhere in a 32x32 grid

BASE = 16_777_216 * 62 * 1024 = 1_065_151_889_408

Digit layout (d in 0 .. BASE-1), least-significant field first:
    pixel  = d % 1024                 -> (x, y) = (pixel % 32, pixel // 32)
    color  = (d // 1024) % 16_777_216 -> #RRGGBB
    symbol = d // (1024 * 16_777_216) -> alphabet[symbol]

Inverse color is bitwise NOT of the 24-bit color (always different).
"""

COLOR_BASE = 256 ** 3
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
SYMBOL_BASE = len(ALPHABET)
GRID = 32
PIXEL_BASE = GRID * GRID  # 1024
BASE = COLOR_BASE * SYMBOL_BASE * PIXEL_BASE  # 1_065_151_889_408


def to_digits(n: int) -> list[int]:
    """Digits of n, most-significant first. n >= 0."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(n % BASE)
        n //= BASE
    return digits[::-1]


def split_digit(d: int) -> tuple[int, str, int, int]:
    """Return color, symbol, pixel_x, pixel_y."""
    if not 0 <= d < BASE:
        raise ValueError(f"digit out of range: {d}")
    pixel = d % PIXEL_BASE
    rest = d // PIXEL_BASE
    color = rest % COLOR_BASE
    symbol = ALPHABET[rest // COLOR_BASE]
    return color, symbol, pixel % GRID, pixel // GRID


def color_to_rgb(c: int) -> tuple[int, int, int]:
    return (c >> 16) & 255, (c >> 8) & 255, c & 255


def inverse_color(c: int) -> int:
    return c ^ 0xFFFFFF


def color_to_hex(c: int) -> str:
    r, g, b = color_to_rgb(c)
    return f"#{r:02X}{g:02X}{b:02X}"


def explain(n: int) -> None:
    digits = to_digits(n)
    width = len(digits)
    print(f"n = {n}")
    print(f"base = {BASE}")
    print(f"      = {COLOR_BASE} colors * {SYMBOL_BASE} symbols * {PIXEL_BASE} pixel slots")
    print(f"digits = {width}   (covers 0 .. {BASE**width - 1})")
    print(f"alphabet = {ALPHABET}")
    print()

    recon = 0
    for d in digits:
        recon = recon * BASE + d
    print(f"reconstructed = {recon}   match={recon == n}")
    print()
    print(
        f"{'pos':>4}  {'place value':>34}  {'digit':>16}  "
        f"{'HEX':>8}  {'sym':>3}  {'pix':>7}  {'inv':>8}"
    )
    print("-" * 96)
    for i, d in enumerate(digits):
        place = BASE ** (width - 1 - i)
        color, symbol, x, y = split_digit(d)
        print(
            f"{i:>4}  {place:>34}  {d:>16}  {color_to_hex(color):>8}  "
            f"{symbol:>3}  ({x:2},{y:2})  {color_to_hex(inverse_color(color)):>8}"
        )
    print()
    print("sequence (MSB -> LSB): HEX + symbol + inverse pixel (x,y)")
    for d in digits:
        color, symbol, x, y = split_digit(d)
        print(f"  {color_to_hex(color)}{symbol}  inv@{x},{y}  {color_to_hex(inverse_color(color))}")


def swatch_image(n: int, out_path: str = "rgb62_32.png", scale: int = 8) -> None:
    """One scaled 32x32 cell per digit. Inverse pixel is the only different pixel.
    Glyph is drawn over the cell. Requires Pillow.
    """
    from PIL import Image, ImageDraw, ImageFont

    digits = to_digits(n)
    cell = GRID * scale
    pad = 28
    w = cell * len(digits)
    h = cell + pad
    img = Image.new("RGB", (w, h), (24, 24, 24))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", cell // 2)
        small = ImageFont.truetype("DejaVuSans.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
        small = font

    for i, d in enumerate(digits):
        color, symbol, x, y = split_digit(d)
        rgb = color_to_rgb(color)
        inv = color_to_rgb(inverse_color(color))
        x0 = i * cell
        block = Image.new("RGB", (GRID, GRID), rgb)
        block.putpixel((x, y), inv)
        block = block.resize((cell, cell), Image.Resampling.NEAREST)
        img.paste(block, (x0, 0))
        lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        fill = (0, 0, 0) if lum > 140 else (255, 255, 255)
        bbox = draw.textbbox((0, 0), symbol, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x0 + (cell - tw) / 2, (cell - th) / 2 - 6), symbol, fill=fill, font=font)
        # mark the inverse pixel with a 1px hairline so it stays findable under the glyph
        px, py = x0 + x * scale, y * scale
        draw.rectangle([px, py, px + scale - 1, py + scale - 1], outline=inv)
        draw.text(
            (x0 + 2, cell + 4),
            f"{color_to_hex(color)}{symbol} @{x},{y}",
            fill=(230, 230, 230),
            font=small,
        )
    img.save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        raw = sys.argv[1].replace("_", "")
        value = int(raw)
        explain(value)
        if "--png" in sys.argv:
            swatch_image(value)
    else:
        samples = (0, 1023, 1024, COLOR_BASE * PIXEL_BASE, BASE - 1, BASE, BASE + 7)
        for sample in samples:
            explain(sample)
            print("=" * 96)
