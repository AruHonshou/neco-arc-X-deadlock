import pathlib
import vpk

root = pathlib.Path("_pack/portrait_reference")
root.mkdir(parents=True, exist_ok=True)
pack = vpk.open(r"C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game\citadel\pak01_dir.vpk")
names = [
    "models/hideout/hideout_wallframe_portrait.vmdl_c",
    "models/hideout/materials/hideout_portraits.vmat_c",
    "models/hideout/materials/hideout_portraits02.vmat_c",
    "models/hideout/materials/hideout_portrait_large.vmat_c",
]
for name in names:
    out = root / pathlib.Path(name).name
    out.write_bytes(pack[name].read())
    print(name, out, out.stat().st_size)
