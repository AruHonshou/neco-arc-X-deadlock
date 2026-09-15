from PIL import Image, ImageDraw, ImageFont

src = Image.open("_pack/portrait_reference/png/hideout_portraits_color_psd_52e10adb.png").convert("RGB")
out = src.copy()
d = ImageDraw.Draw(out)
font = ImageFont.load_default()
for x in range(0, 1025, 64):
    d.line((x, 0, x, 1024), fill=(255, 0, 0), width=1)
    if x < 1024:
        d.text((x + 2, 2), str(x), fill=(255, 0, 0), font=font)
for y in range(0, 1025, 64):
    d.line((0, y, 1024, y), fill=(255, 0, 0), width=1)
    if y < 1024:
        d.text((2, y + 2), str(y), fill=(255, 0, 0), font=font)
out.save("_pack/portrait_reference/png/atlas_grid64.png")
