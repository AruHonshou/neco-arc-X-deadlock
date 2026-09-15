from pathlib import Path
import vpk

addons = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game\citadel\addons")
targets = {
    "models/hideout/materials/hideout_portraits_color_psd_52e10adb.vtex_c",
    "models/hideout/materials/hideout_portraits_02_color_psd_e147c504.vtex_c",
    "models/hideout/materials/hideout_portrait_large_color_psd_bc05d6c1.vtex_c",
}
for path in sorted(addons.glob("*.vpk")):
    try:
        pack = vpk.open(str(path))
        found = sorted(targets.intersection({str(name) for name in pack}))
        if found:
            print(path.name, found)
    except Exception as exc:
        print(path.name, "ERROR", exc)
