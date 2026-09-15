from PIL import Image

im = Image.open("_pack/portrait_reference/png/hideout_portraits_color_psd_52e10adb.png").convert("RGB")
bg = (29, 21, 17)
for y in [0, 50, 100, 135, 136, 200, 278, 280, 400, 550, 700, 840, 950, 1023]:
    runs = []
    on = False
    for x in range(im.width):
        is_bg = im.getpixel((x, y)) == bg
        if is_bg and not on:
            start = x
            on = True
        if on and (not is_bg or x == im.width - 1):
            end = x - 1 if not is_bg else x
            if end - start > 20:
                runs.append((start, end))
            on = False
    print(y, runs)
