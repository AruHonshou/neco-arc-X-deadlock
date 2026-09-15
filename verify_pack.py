from build_pack import *
import vpk, zlib

pak=WORK/'aru_audio_beta_dir.vpk'
stage_dir=WORK/'stage_rebuild_v2'
archive=vpk.open(str(pak))
checks=[]
for name in archive:
    entry=archive[name]
    payload=entry.read()
    assert (zlib.crc32(payload)&0xffffffff)==entry.crc32, name
    assert payload==(stage_dir/name).read_bytes(),name
    checks.append(name)
rows=json.loads((WORK/'converted.json').read_text(encoding='utf-8'))
audio_checks=[]
for row in rows:
    meta=run([VRF,'-i',stage_dir/(row['resource']+'_c'),'-b','DATA'],row['name']+'_verify.log')
    assert 'SoundType: MP3' in meta,row['name']
    assert 'Sample Rate: 44100' in meta,row['name']
    assert 'Channels: 2' in meta,row['name']
    count=int(re.search(r'SampleCount: (\d+)',meta).group(1))
    assert count==row['samples'],row['name']
    start=int(re.search(r'LoopStart: (-?\d+)',meta).group(1))
    end=int(re.search(r'LoopEnd: (-?\d+)',meta).group(1))
    assert (start==0 and end==count) if row['loop'] else start<0, (row['name'],start,end)
    audio_checks.append(dict(name=row['name'],samples=count,loop_start=start,loop_end=end))
run([VRF,'-i',pak,'-o',WORK/'roundtrip','-d','-f','soundevents/'],'roundtrip.log')
mapping=json.loads((WORK/'mapping.json').read_text(encoding='utf-8'))
for change in mapping:
    # misc.vdata is a script override and has no soundevent text to inspect
    # in the round-trip dump; its compiled resource is checked by the VPK
    # equality loop above.
    if not change['file'].startswith('soundevents'):
        continue
    text=(WORK/'roundtrip/soundevents'/change['file']).read_text(encoding='utf-8')
    a,b=event_spans(text)[change['event']]
    body=text[a:b]
    for sound in change['fields']['vsnd_files']:
        assert sound in body,(change['event'],sound)
        assert sound+'_c' in archive,sound
runtime_events=json.loads((WORK/'runtime_events.json').read_text(encoding='utf-8')) if (WORK/'runtime_events.json').exists() else []
runtime_random=json.loads((WORK/'runtime_random.json').read_text(encoding='utf-8')) if (WORK/'runtime_random.json').exists() else {}
# Older runtime snapshots can remain in _pack after a rebuild. Only count
# them as runtime evidence when every selected asset still exists in this VPK;
# otherwise report static verification and leave live-game testing pending.
def runtime_asset_exists(path):
    normalized=path.replace('\\','/').replace('.vsnd','.vsnd_c')
    return normalized in archive
runtime_events_current=bool(runtime_events) and all(
    x.get('passed') and all(runtime_asset_exists(s) for s in x.get('selected',[]))
    for x in runtime_events)
runtime_random_current=bool(runtime_random) and all(
    x.get('all_variants_seen') and x.get('explicit_stop_passed')
    and all(runtime_asset_exists('sounds/aru/'+name+'.vsnd') for name in x.get('sequence',[]))
    for x in runtime_random.values())
runtime_verified=runtime_events_current and runtime_random_current
report=dict(status='verified' if runtime_verified else 'static_checks_passed_runtime_pending',resources=len(checks),audio=audio_checks,
    changed_events=len(mapping),vpk_sha256=hashlib.sha256(pak.read_bytes()).hexdigest(),
    runtime_verified=runtime_verified,random_tests=runtime_random,
    veil='ambient_loop_event_verified' if any(x.get('event')=='Mods.Armor.VeilWalker.Ambient' and x.get('passed') for x in runtime_events) else 'pending')
write(WORK/'verification.json',json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='audio'},indent=2))
