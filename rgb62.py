"""
BASE-RGB62: positional system with base 16_777_216 * 62.

Each digit is one RGB color plus one symbol from:
    0-9 A-Z a-z   (62 glyphs)

Digit layout (d in 0 .. BASE-1):
    color  = d % 16_777_216     -> #RRGGBB
    symbol = d // 16_777_216    -> alphabet[symbol]

0                          -> #000000 0
16_777_215                 -> #FFFFFF 0
16_777_216                 -> #000000 1
1_041_873_791              -> #FFFFFF z
1_041_873_792              -> #000000 0   #000000 1
"""

COLOR_BASE = 256 ** 3          # 16_777_216
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
SYMBOL_BASE = len(ALPHABET)    # 62
BASE = COLOR_BASE * SYMBOL_BASE  # 1_041_873_792


def to_rgb62(n: int) -> list[int]:
    """Digits of n in base COLOR_BASE*62, most-significant first. n >= 0."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(n % BASE)
        n //= BASE
    return digits[::-1]


def split_digit(d: int) -> tuple[int, str]:
    if not 0 <= d < BASE:
        raise ValueError(f"digit out of range: {d}")
    color = d % COLOR_BASE
    symbol = ALPHABET[d // COLOR_BASE]
    return color, symbol


def color_to_rgb(c: int) -> tuple[int, int, int]:
    return (c >> 16) & 255, (c >> 8) & 255, c & 255


def color_to_hex(c: int) -> str:
    r, g, b = color_to_rgb(c)
    return f"#{r:02X}{g:02X}{b:02X}"


def ansi_glyph(d: int) -> str:
    """Colored glyph block. Needs a truecolor terminal."""
    color, symbol = split_digit(d)
    r, g, b = color_to_rgb(color)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    fg = "0;0;0" if lum > 140 else "255;255;255"
    return f"\033[48;2;{r};{g};{b}m\033[38;2;{fg}m {symbol} \033[0m {color_to_hex(color)} {symbol}"


def explain(n: int) -> None:
    digits = to_rgb62(n)
    width = len(digits)
    print(f"n = {n}")
    print(f"base = {BASE}  (= {COLOR_BASE} * {SYMBOL_BASE})")
    print(f"digits = {width}   (covers 0 .. {BASE**width - 1})")
    print(f"alphabet = {ALPHABET}")
    print()

    recon = 0
    for d in digits:
        recon = recon * BASE + d
    print(f"reconstructed = {recon}   match={recon == n}")
    print()
    header = (
        f"{'pos':>4}  {'place value':>28}  {'digit':>12}  "
        f"{'HEX':>8}  {'sym':>3}  {'sym#':>4}  RGB"
    )
    print(header)
    print("-" * len(header))
    for i, d in enumerate(digits):
        place = BASE ** (width - 1 - i)
        color, symbol = split_digit(d)
        r, g, b = color_to_rgb(color)
        sym_i = d // COLOR_BASE
        print(
            f"{i:>4}  {place:>28}  {d:>12}  {color_to_hex(color):>8}  "
            f"{symbol:>3}  {sym_i:>4}  ({r:3},{g:3},{b:3})"
        )
    print()
    print("sequence (MSB -> LSB), each cell is color+symbol:")
    for d in digits:
        print("  " + ansi_glyph(d))
    print()
    print("  " + "  ".join(
        f"{color_to_hex(split_digit(d)[0])}{split_digit(d)[1]}" for d in digits
    ))


def swatch_image(n: int, out_path: str = "rgb62.png", cell: int = 96) -> None:
    """PNG strip: one colored glyph per digit. Requires Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    digits = to_rgb62(n)
    w, h = cell * len(digits), cell + 40
    img = Image.new("RGB", (w, h), (32, 32, 32))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", cell // 2)
        small = ImageFont.truetype("DejaVuSans.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
        small = font
    for i, d in enumerate(digits):
        color, symbol = split_digit(d)
        rgb = color_to_rgb(color)
        x0 = i * cell
        draw.rectangle([x0, 0, x0 + cell - 1, cell - 1], fill=rgb)
        lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        fill = (0, 0, 0) if lum > 140 else (255, 255, 255)
        bbox = draw.textbbox((0, 0), symbol, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x0 + (cell - tw) / 2, (cell - th) / 2 - 4), symbol, fill=fill, font=font)
        draw.text((x0 + 4, cell + 6), f"{color_to_hex(color)}{symbol}", fill=(230, 230, 230), font=small)
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
        samples = (
            0,
            255,
            COLOR_BASE - 1,
            COLOR_BASE,
            BASE - 1,
            BASE,
            BASE**2 + 42,
        )
        for sample in samples:
            explain(sample)
            print("=" * 78)
