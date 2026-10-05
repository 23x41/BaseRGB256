"""
BASE-RGB256: positional numeral system with base 16_777_216.
Each digit is a 24-bit value rendered as an RGB color.

0            -> #000000
16_777_215   -> #FFFFFF
16_777_216   -> #000001 #000000
"""

BASE = 256 ** 3  # 16_777_216


def to_rgb256(n: int) -> list[int]:
    """Digits of n in base 16_777_216, most-significant first. n >= 0."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return [0]
    digits = []
    while n:
        digits.append(n % BASE)
        n //= BASE
    return digits[::-1]


def digit_to_rgb(d: int) -> tuple[int, int, int]:
    return (d >> 16) & 255, (d >> 8) & 255, d & 255


def digit_to_hex(d: int) -> str:
    r, g, b = digit_to_rgb(d)
    return f"#{r:02X}{g:02X}{b:02X}"


def ansi_block(d: int) -> str:
    """Truecolor swatch. Works in most modern terminals."""
    r, g, b = digit_to_rgb(d)
    return f"\033[48;2;{r};{g};{b}m    \033[0m {digit_to_hex(d)}"


def explain(n: int) -> None:
    digits = to_rgb256(n)
    width = len(digits)
    print(f"n = {n}")
    print(f"base = {BASE}  (= 256**3)")
    print(f"digits = {width}   (covers 0 .. {BASE**width - 1})")
    print()

    recon = 0
    for d in digits:
        recon = recon * BASE + d
    print(f"reconstructed = {recon}   match={recon == n}")
    print()
    print(f"{'pos':>4}  {'place value':>28}  {'digit (dec)':>12}  {'HEX':>8}  RGB")
    print("-" * 78)
    for i, d in enumerate(digits):
        place = BASE ** (width - 1 - i)
        r, g, b = digit_to_rgb(d)
        print(
            f"{i:>4}  {place:>28}  {d:>12}  {digit_to_hex(d):>8}  ({r:3},{g:3},{b:3})"
        )
    print()
    print("color sequence (MSB -> LSB):")
    for d in digits:
        print("  " + ansi_block(d))
    print()
    print("  " + "  ".join(digit_to_hex(d) for d in digits))


def swatch_image(n: int, out_path: str = "rgb256.png", cell: int = 80) -> None:
    """Write a PNG strip of one block per digit. Requires Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    digits = to_rgb256(n)
    w, h = cell * len(digits), cell + 36
    img = Image.new("RGB", (w, h), (32, 32, 32))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
    for i, d in enumerate(digits):
        rgb = digit_to_rgb(d)
        x0 = i * cell
        draw.rectangle([x0, 0, x0 + cell - 1, cell - 1], fill=rgb)
        lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        fill = (0, 0, 0) if lum > 140 else (255, 255, 255)
        draw.text((x0 + 4, cell + 4), digit_to_hex(d), fill=fill, font=font)
    img.save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        raw = sys.argv[1].replace("_", "")
        explain(int(raw))
        if "--png" in sys.argv:
            swatch_image(int(raw))
    else:
        for sample in (0, 255, 16_777_215, 16_777_216, 16_777_216**2 + 42):
            explain(sample)
            print("=" * 78)
