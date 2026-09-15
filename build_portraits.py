"""Build the Neco Arc portrait atlases from the 30 downloaded source images."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps, ImageDraw


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "_pack" / "portraits_neco_arc" / "source"
OUT = ROOT / "_pack" / "portraits_neco_arc" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

# These rectangles follow the image cells already present in the Yuri reference
# atlas. They preserve the UV layout used by the game's hideout map.
MAIN_RECTS = [
    (0, 0, 140, 136), (140, 0, 280, 136), (280, 0, 419, 136),
    (419, 0, 558, 136), (558, 0, 695, 136), (695, 0, 844, 136),
    (844, 0, 1024, 280),
    (0, 136, 140, 280), (140, 136, 280, 280), (280, 136, 419, 280),
    (419, 136, 558, 280), (558, 136, 695, 280), (695, 136, 844, 280),
    (0, 280, 140, 700), (140, 280, 280, 700), (280, 280, 419, 700),
    (419, 280, 731, 500), (419, 500, 731, 700),
    (731, 280, 844, 548), (844, 280, 934, 448), (934, 280, 1024, 550),
    (731, 548, 844, 621), (731, 621, 844, 700),
    (0, 700, 100, 840), (100, 700, 190, 770), (100, 770, 190, 840),
    (190, 700, 280, 840), (280, 700, 370, 840), (370, 700, 470, 840),
    (470, 700, 570, 840), (570, 700, 660, 840), (660, 700, 752, 840),
    (844, 700, 1024, 840),
    (0, 840, 318, 960), (318, 840, 484, 960), (484, 840, 670, 960),
    (670, 840, 836, 960), (836, 840, 1024, 1024), (710, 960, 836, 1024),
]
SECOND_RECTS = [
    (0, 0, 680, 282), (680, 0, 1024, 565),
    (0, 282, 680, 565), (0, 565, 673, 1024),
]
LARGE_RECTS = [(0, 0, 512, 1024)]


def source_images() -> list[Image.Image]:
    paths = sorted(
        [p for p in SOURCE.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}],
        key=lambda p: int(p.name[:2]),
    )
    if len(paths) != 30:
        raise RuntimeError(f"Expected 30 portrait images, found {len(paths)}")
    images = []
    for path in paths:
        with Image.open(path) as image:
            images.append(image.convert("RGB"))
    return images


def fill_rect(canvas: Image.Image, image: Image.Image, rect: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = rect
    width, height = x1 - x0, y1 - y0
    # Fit fills every frame so no original Yuri pixels remain visible. The
    # center crop is intentional: portraits are more legible at the frame size.
    fitted = ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.48))
    canvas.paste(fitted, (x0, y0))


def build(name: str, size: tuple[int, int], rects: list[tuple[int, int, int, int]], images: list[Image.Image]) -> Path:
    canvas = Image.new("RGB", size, (26, 19, 22))
    for index, rect in enumerate(rects):
        fill_rect(canvas, images[index % len(images)], rect)
    path = OUT / name
    canvas.save(path, format="PNG", optimize=True)
    return path


def make_preview(paths: list[Path]) -> None:
    thumbs = []
    for path in paths:
        with Image.open(path) as image:
            thumb = image.copy()
            thumb.thumbnail((512, 512), Image.Resampling.LANCZOS)
            thumbs.append((path.stem, thumb))
    out = Image.new("RGB", (1024, 1100), (18, 18, 18))
    draw = ImageDraw.Draw(out)
    x, y = 0, 0
    for name, thumb in thumbs:
        if x + thumb.width > 1024:
            x = 0
            y += 540
        out.paste(thumb, (x, y + 24))
        draw.text((x + 4, y + 4), name, fill=(255, 255, 255))
        x += 512
    out.save(OUT / "preview.png", format="PNG", optimize=True)


def make_source_contact(images: list[Image.Image]) -> None:
    cell_w = cell_h = 256
    cols, rows = 5, 6
    out = Image.new("RGB", (cols * cell_w, rows * cell_h), (18, 18, 18))
    draw = ImageDraw.Draw(out)
    for index, image in enumerate(images):
        x = (index % cols) * cell_w
        y = (index // cols) * cell_h
        tile = ImageOps.fit(image, (cell_w, cell_h), method=Image.Resampling.LANCZOS)
        out.paste(tile, (x, y))
        draw.rectangle((x, y, x + 34, y + 22), fill=(0, 0, 0))
        draw.text((x + 5, y + 5), f"{index + 1:02d}", fill=(255, 255, 255))
    path = ROOT / "_pack" / "portraits_neco_arc" / "GameBanana" / "neco_arc_30_contact.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path, format="PNG", optimize=True)


def main() -> None:
    images = source_images()
    outputs = [
        build("hideout_portraits_color_psd_52e10adb.png", (1024, 1024), MAIN_RECTS, images),
        build("hideout_portraits_02_color_psd_e147c504.png", (1024, 1024), SECOND_RECTS, images),
        build("hideout_portrait_large_color_psd_bc05d6c1.png", (512, 1024), LARGE_RECTS, images),
    ]
    make_preview(outputs)
    make_source_contact(images)
    print("Built:")
    for path in outputs:
        print(path, path.stat().st_size)
    print("Preview:", OUT / "preview.png")


if __name__ == "__main__":
    main()
