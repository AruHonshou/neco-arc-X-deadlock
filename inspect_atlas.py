from PIL import Image

im = Image.open('_pack/portrait_reference/png/hideout_portraits_color_psd_52e10adb.png').convert('RGB')
for y in [0,64,127,128,192,255,256,320,384,448,512,576,640,704,768,832,896,960,1023]:
    row = [im.getpixel((x, y)) for x in range(1024)]
    runs = []
    s = 0
    c = row[0]
    for x, v in enumerate(row[1:], 1):
        if v != c:
            if x - s > 20:
                runs.append((s, x - 1, c))
            s = x
            c = v
    if 1024 - s > 20:
        runs.append((s, 1023, c))
    print('y', y, runs[:12])
