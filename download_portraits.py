from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_pack" / "portraits_neco_arc" / "source"
OUT.mkdir(parents=True, exist_ok=True)


PAGES = [
    ("horizontal", "2942199"),
    ("horizontal", "3200498"),
    ("horizontal", "2870870"),
    ("horizontal", "2942198"),
    ("horizontal", "2870744"),
    ("horizontal", "2863887"),
    ("horizontal", "2812971"),
    ("horizontal", "2774695"),
    ("horizontal", "2812512"),
    ("horizontal", "2831258"),
    ("square", "2975712"),
    ("square", "2942854"),
    ("square", "2968664"),
    ("square", "3194286"),
    ("square", "2850096"),
    ("square", "2915737"),
    ("square", "2849685"),
    ("square", "2838431"),
    ("square", "2788419"),
    ("square", "2773062"),
    ("vertical", "2959125"),
    ("vertical", "3216968"),
    ("vertical", "3248740"),
    ("vertical", "2959124"),
    ("vertical", "2953326"),
    ("vertical", "3246718"),
    ("vertical", "2916435"),
    ("vertical", "2880707"),
    ("vertical", "2801526"),
    ("vertical", "2807167"),
]


def get(url: str) -> tuple[bytes, str]:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Deadlock portrait mod preparation)"})
    with urlopen(req, timeout=45) as response:
        return response.read(), response.headers.get("Content-Type", "")


def main() -> None:
    rows = []
    for index, (group, photo_id) in enumerate(PAGES, 1):
        page_url = f"https://knowyourmeme.com/photos/{photo_id}-neco-arc"
        page, _ = get(page_url)
        text = page.decode("utf-8", errors="replace")
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            text,
            re.IGNORECASE,
        )
        if not match:
            match = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                text,
                re.IGNORECASE,
            )
        if not match:
            raise RuntimeError(f"No og:image found for {page_url}")
        image_url = html.unescape(match.group(1)).replace("&amp;", "&")
        data, content_type = get(image_url)
        if "png" in content_type.lower() or image_url.lower().split("?")[0].endswith(".png"):
            ext = ".png"
        elif "webp" in content_type.lower() or image_url.lower().split("?")[0].endswith(".webp"):
            ext = ".webp"
        else:
            ext = ".jpg"
        filename = f"{index:02d}_{group}_{photo_id}{ext}"
        path = OUT / filename
        path.write_bytes(data)
        rows.append(f"{index:02d}\t{group}\t{photo_id}\t{filename}\t{image_url}")
        print(f"{index:02d}: {filename} ({len(data):,} bytes)")

    (OUT / "sources.tsv").write_text("index\tgroup\tid\tfilename\turl\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"Downloaded {len(rows)} Neco Arc images to {OUT}")


if __name__ == "__main__":
    main()
