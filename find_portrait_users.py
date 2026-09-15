import pathlib
import vpk

pack = vpk.open(r"C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game\citadel\maps\dl_hideout.vpk")
for entry in pack:
    name = str(entry)
    if not name.endswith((".vmdl_c", ".vmap_c")):
        continue
    data = pack[name].read()
    if b"hideout_portraits" in data.lower():
        print(name, len(data), "portrait refs")
