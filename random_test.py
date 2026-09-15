from game_console import command
from build_pack import *
results={}
for event,count in [('Music.Idol.Pickup.Lp',14),('Music.Koth.Capture.Lp',14),('Gameplay.Pause.Lp',6)]:
    seen=[]; logs=[]
    for i in range(count*4):
        command('snd_sos_stop_all_soundevents',.8)
        log=command('snd_sos_start_soundevent '+event,.35)
        snapshot=command('soundinfo',.15)
        log+=snapshot
        selections=sorted(set(re.findall(r'^\s*\d+: sounds[\\/]aru[\\/](mix_\d+|pause_\d+)\.vsnd',snapshot,re.M)))
        assert len(selections)==1,(event,selections)
        seen+=selections; logs.append(log)
        if len(set(seen))==count: break
    command('snd_sos_stop_all_soundevents',1)
    stopped=not re.search(r'sounds[\\/]aru[\\/](mix_|pause_)',command('soundinfo',.2))
    results[event]=dict(sequence=seen,distinct=len(set(seen)),all_variants_seen=len(set(seen))==count,explicit_stop_passed=stopped)
    write(WORK/'logs'/('random_'+event+'.txt'),'\n'.join(logs))
    print(event,results[event],flush=True)
    write(WORK/'runtime_random.json',json.dumps(results,indent=2))
write(WORK/'runtime_random.json',json.dumps(results,indent=2))
