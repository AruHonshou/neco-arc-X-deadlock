"""Exercise compiled soundevents in the running local game; not gameplay proof."""
from game_console import command
from build_pack import *

mapping=json.loads((WORK/'mapping.json').read_text(encoding='utf-8'))
report=[]
command('sv_cheats 1; snd_showstart 1',.2)
for i,m in enumerate(mapping):
    command('snd_sos_stop_all_soundevents',.2)
    log=command('snd_sos_start_soundevent '+m['event'],.5)
    log+=command('soundinfo',.2)
    found=sorted(set(re.findall(r'sounds[\\/]aru[\\/]\w+\.vsnd',log)))
    expected={s.replace('/','\\') for s in m['fields']['vsnd_files']}
    selected=[f for f in found if f.replace('/','\\') in expected]
    write(WORK/'logs'/f'runtime_event_{i:02}.txt',log)
    item=dict(event=m['event'],selected=selected,passed=bool(selected))
    report.append(item)
    print(json.dumps(item),flush=True)
command('snd_sos_stop_all_soundevents',.3)
write(WORK/'runtime_events.json',json.dumps(report,indent=2))
