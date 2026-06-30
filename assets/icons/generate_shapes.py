"""Generate status icon shape variants — readable at 16px."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
BG = (67, 56, 202)  # #4338CA indigo
WHITE = (255, 255, 255, 255)

FONT_CANDIDATES = [
    "/System/Library/Fonts/SFMono-Bold.otf",
    "/System/Library/Fonts/Menlo.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]


def load_font(size: int):
    for path in FONT_CANDIDATES:
        p = Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                pass
    return ImageFont.load_default()


def canvas(size: int = 64) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = int(size * 0.22)
    draw.rounded_rectangle([1, 1, size - 2, size - 2], radius=r, fill=BG + (255,))
    return img, draw


def save(name: str, img: Image.Image) -> None:
    img.save(OUT / f"shape-{name}-64.png")
    img.resize((16, 16), Image.Resampling.LANCZOS).save(OUT / f"shape-{name}-16.png")


def shape_bolt(d: ImageDraw.ImageDraw, s: int) -> None:
    cx, cy = s // 2, s // 2
    pts = [
        (cx + int(s * 0.04), cy - int(s * 0.28)),
        (cx - int(s * 0.14), cy - int(s * 0.02)),
        (cx + int(s * 0.02), cy - int(s * 0.02)),
        (cx - int(s * 0.06), cy + int(s * 0.30)),
        (cx + int(s * 0.18), cy + int(s * 0.02)),
        (cx + int(s * 0.02), cy + int(s * 0.02)),
    ]
    d.polygon(pts, fill=WHITE)


def shape_bot(d: ImageDraw.ImageDraw, s: int) -> None:
    cx = s // 2
    body = [cx - int(s * 0.22), cy := s // 2 - int(s * 0.04), cx + int(s * 0.22), cy + int(s * 0.28)]
    d.rounded_rectangle(body, radius=int(s * 0.08), fill=WHITE)
    eye = max(3, s // 14)
    gap = int(s * 0.10)
    d.ellipse([cx - gap - eye, cy + int(s * 0.06), cx - gap + eye, cy + int(s * 0.06) + eye * 2], fill=BG)
    d.ellipse([cx + gap - eye, cy + int(s * 0.06), cx + gap + eye, cy + int(s * 0.06) + eye * 2], fill=BG)
    d.rectangle([cx - int(s * 0.08), cy + int(s * 0.18), cx + int(s * 0.08), cy + int(s * 0.22)], fill=BG)
    d.rectangle([cx - 2, cy - int(s * 0.12), cx + 2, cy - int(s * 0.04)], fill=WHITE)


def shape_refresh(d: ImageDraw.ImageDraw, s: int) -> None:
    cx, cy = s // 2, s // 2
    r = int(s * 0.22)
    bbox = [cx - r, cy - r, cx + r, cy + r]
    d.arc(bbox, start=45, end=300, fill=WHITE, width=max(3, s // 12))
    # arrow head top-right
    ax, ay = cx + int(r * 0.55), cy - int(r * 0.75)
    d.polygon([(ax, ay), (ax - int(s * 0.12), ay - int(s * 0.04)), (ax - int(s * 0.04), ay + int(s * 0.08))], fill=WHITE)


def shape_terminal(d: ImageDraw.ImageDraw, s: int) -> None:
    font = load_font(int(s * 0.46))
    text = ">_"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (s - tw) // 2 - bbox[0]
    y = (s - th) // 2 - bbox[1] - 1
    d.text((x, y), text, fill=WHITE, font=font)


def shape_layers(d: ImageDraw.ImageDraw, s: int) -> None:
    w, h = int(s * 0.44), int(s * 0.10)
    cx = s // 2
    for i, yoff in enumerate([0.22, 0.38, 0.54]):
        y = int(s * yoff)
        alpha = 255 - i * 35
        d.rounded_rectangle([cx - w // 2, y, cx + w // 2, y + h], radius=3, fill=(255, 255, 255, alpha))


def shape_letter_a(d: ImageDraw.ImageDraw, s: int) -> None:
    font = load_font(int(s * 0.52))
    text = "A"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (s - tw) // 2 - bbox[0]
    y = (s - th) // 2 - bbox[1] - 1
    d.text((x, y), text, fill=WHITE, font=font)


def shape_chevron(d: ImageDraw.ImageDraw, s: int) -> None:
    cx, cy = s // 2, s // 2
    w, h = int(s * 0.12), int(s * 0.22)
    for dx in (-int(s * 0.10), int(s * 0.10)):
        x = cx + dx
        d.polygon([(x - w, cy - h), (x + w, cy), (x - w, cy + h)], fill=WHITE)


def shape_chip(d: ImageDraw.ImageDraw, s: int) -> None:
    cx, cy = s // 2, s // 2
    side = int(s * 0.30)
    d.rectangle([cx - side, cy - side, cx + side, cy + side], fill=WHITE)
    inner = int(s * 0.14)
    d.rectangle([cx - inner, cy - inner, cx + inner, cy + inner], fill=BG)
    pin = max(2, s // 16)
    for px in range(cx - side, cx + side + 1, int(s * 0.12)):
        d.rectangle([px - pin, cy - side - pin * 2, px + pin, cy - side], fill=WHITE)
        d.rectangle([px - pin, cy + side, px + pin, cy + side + pin * 2], fill=WHITE)


def shape_flask(d: ImageDraw.ImageDraw, s: int) -> None:
    cx = s // 2
    neck_w = int(s * 0.08)
    d.rectangle([cx - neck_w, int(s * 0.16), cx + neck_w, int(s * 0.30)], fill=WHITE)
    d.polygon(
        [
            (cx - int(s * 0.20), int(s * 0.30)),
            (cx + int(s * 0.20), int(s * 0.30)),
            (cx + int(s * 0.16), int(s * 0.58)),
            (cx - int(s * 0.16), int(s * 0.58)),
        ],
        fill=WHITE,
    )
    d.ellipse([cx - int(s * 0.10), int(s * 0.44), cx + int(s * 0.10), int(s * 0.52)], fill=BG)


def shape_pen(d: ImageDraw.ImageDraw, s: int) -> None:
    d.line([(int(s * 0.18), int(s * 0.52)), (int(s * 0.52), int(s * 0.18))], fill=WHITE, width=max(3, s // 10))
    d.polygon(
        [
            (int(s * 0.52), int(s * 0.18)),
            (int(s * 0.58), int(s * 0.24)),
            (int(s * 0.46), int(s * 0.30)),
        ],
        fill=WHITE,
    )
    d.line([(int(s * 0.16), int(s * 0.58)), (int(s * 0.58), int(s * 0.58))], fill=WHITE, width=max(2, s // 14))


def shape_branch(d: ImageDraw.ImageDraw, s: int) -> None:
    lw = max(3, s // 12)
    d.line([(int(s * 0.28), int(s * 0.58)), (int(s * 0.28), int(s * 0.22))], fill=WHITE, width=lw)
    d.line([(int(s * 0.28), int(s * 0.36)), (int(s * 0.58), int(s * 0.22))], fill=WHITE, width=lw)
    d.line([(int(s * 0.28), int(s * 0.46)), (int(s * 0.58), int(s * 0.58))], fill=WHITE, width=lw)
    for x, y in [(int(s * 0.58), int(s * 0.22)), (int(s * 0.58), int(s * 0.58))]:
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=WHITE)


def shape_hammer(d: ImageDraw.ImageDraw, s: int) -> None:
    lw = max(3, s // 10)
    d.line([(int(s * 0.22), int(s * 0.58)), (int(s * 0.58), int(s * 0.22))], fill=WHITE, width=lw)
    d.rectangle([int(s * 0.48), int(s * 0.14), int(s * 0.66), int(s * 0.30)], fill=WHITE)


def shape_checklist(d: ImageDraw.ImageDraw, s: int) -> None:
    x0 = int(s * 0.20)
    for i, y in enumerate([int(s * 0.24), int(s * 0.40), int(s * 0.56)]):
        d.rectangle([x0, y, x0 + int(s * 0.10), y + int(s * 0.10)], outline=WHITE, width=2)
        if i < 2:
            d.line([(x0 + 2, y + 5), (x0 + 4, y + 8), (x0 + 9, y + 2)], fill=WHITE, width=2)
        d.line([(x0 + int(s * 0.16), y + 5), (x0 + int(s * 0.44), y + 5)], fill=WHITE, width=max(2, s // 16))


def shape_inbox(d: ImageDraw.ImageDraw, s: int) -> None:
    """Arrow into tray — import / generate."""
    cx = s // 2
    d.rectangle([int(s * 0.18), int(s * 0.38), int(s * 0.62), int(s * 0.58)], fill=WHITE)
    d.polygon([(cx, int(s * 0.14)), (cx - int(s * 0.14), int(s * 0.32)), (cx + int(s * 0.14), int(s * 0.32))], fill=WHITE)
    d.rectangle([cx - int(s * 0.04), int(s * 0.22), cx + int(s * 0.04), int(s * 0.36)], fill=WHITE)


SHAPES: dict[str, tuple[str, str, callable]] = {
    "bolt": ("Молния", "Запуск / действие", shape_bolt),
    "bot": ("Робот", "ИИ без «звёздочек»", shape_bot),
    "refresh": ("Цикл", "Автоматизация / повтор", shape_refresh),
    "terminal": (">_", "Dev-tool, терминал", shape_terminal),
    "layers": ("Слои", "Стек тестов / pipeline", shape_layers),
    "letter-a": ("A", "Automate — буква", shape_letter_a),
    "chevron": (">>", "Вперёд / запустить", shape_chevron),
    "chip": ("Чип", "Вычисление / engine", shape_chip),
    "flask": ("Колба", "QA / тестирование", shape_flask),
    "pen": ("Перо", "Написать тест", shape_pen),
    "branch": ("Ветка", "Git / CI pipeline", shape_branch),
    "hammer": ("Молоток", "Сборка / build", shape_hammer),
    "checklist": ("Чеклист", "Ручной → автотест", shape_checklist),
    "inbox": ("Импорт", "Сгенерировать в репо", shape_inbox),
}


def main() -> None:
    meta = []
    for key, (title, desc, drawer) in SHAPES.items():
        img, draw = canvas(64)
        drawer(draw, 64)
        save(key, img)
        meta.append((key, title, desc))
        print(key, title)

    # strip preview
    cols = len(SHAPES)
    strip = Image.new("RGBA", (cols * 36 + 8, 88), (26, 32, 40, 255))
    x = 8
    for key in SHAPES:
        strip.paste(Image.open(OUT / f"shape-{key}-16.png"), (x, 8))
        big = Image.open(OUT / f"shape-{key}-64.png").resize((32, 32), Image.Resampling.LANCZOS)
        strip.paste(big, (x, 32))
        x += 36
    strip.save(OUT / "_shapes-preview.png")
    print("preview saved")


if __name__ == "__main__":
    main()
