from pathlib import Path
import vpk

packs = [
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game\citadel\pak01_dir.vpk"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game\citadel\maps\dl_hideout.vpk"),
]
needle = b"Stinger.KillStreak"
for pack_path in packs:
    try:
        pack = vpk.open(str(pack_path))
    except Exception as exc:
        print(pack_path, exc)
        continue
    for name in pack:
        try:
            data = pack[name].read()
        except Exception:
            continue
        if needle in data and not str(name).endswith("music.vsndevts_c"):
            print(pack_path.name, name, len(data))
