import pathlib
import vpk

pack = vpk.open(r"C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game\citadel\maps\dl_hideout.vpk")
name = "maps/dl_hideout/worldnodes/n0_lr0_c2_s_cb_mesh.vmdl_c"
out = pathlib.Path("_pack/portrait_reference/n0_lr0_c2_s_cb_mesh.vmdl_c")
out.write_bytes(pack[name].read())
print(out, out.stat().st_size)
