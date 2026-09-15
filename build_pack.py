"""Build reproducible Deadlock audio addon. Originals are never modified."""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, math, re, shutil, subprocess, sys, wave
import imageio_ffmpeg
from mutagen.mp3 import MP3
import mutagen

ROOT = Path(__file__).resolve().parent
WORK = ROOT / '_pack'
SDK = Path(r'C:\Modding\CSDK12\Reduced_CSDK_12')
CONTENT = SDK / 'content/citadel_addons/aru_audio_pack'
GAME = SDK / 'game/citadel_addons/aru_audio_pack'
AUDIT = Path(r'C:\Modding\aru_audit_current')
VAULT_AUDIT = Path(r'C:\Modding\neut_vault_extract3\soundevents\npc\neut_vaults.vsndevts')
RC = SDK / 'game/bin_cs2/win64/resourcecompiler.exe'
VRF = Path(r'C:\Users\arumi\AppData\Local\Temp\deadlock_audio_audit_vrf20\cli\Source2Viewer-CLI.exe')
HEADER = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n'
# Custom one-shots are intentionally pushed above the stock event level.  The
# source files supplied for the new alerts are mastered with a 0 dB peak, so
# the extra event gain is what makes them clearly audible in-game.
EVENT_BOOST_DB = 6.0
LOUD_EVENT_BOOST_DB = 9.0
FOLDERS = {
    # Lobby music and the one-shot title/start cue are intentionally separate.
    'Inicio':'intro','buscandoPartida':'lobby',
    'derrota':'lose','victoria':'win',
    'sonido encontro partida':'match_found',
    'SELECCIONAR PERSONAJE':'hero_select',
    'INICIA PARTIDA':'match_start',
    'Aparece midboss':'midboss_spawn','midboss herido':'midboss_hurt',
    'aparece la urna':'urn_announce','avisoAparecelaGrieta':'rift_announce',
    'musicaTienda':'shop','musicatiendasecreta':'secret_store',
    'alfombraMagica':'carpet','velo':'veil',
    'musicaMix':'search_mix','pause':'pause',
    # The folder holds the pre-match 10..1 voices plus the pause 3/2/1 voices
    # and the final Continue cue.  The two countdowns live in two different
    # HUD panels, so two dedicated addon events serve them (see
    # prepare_events); every file is packaged and selected by stem.
    'contador':'pause_count',
    'cargar o estar dentro de la grieta':'rift_capture',
    'llevar urna':'urn_carry',
    'caida torre aliada':'tower_ally',
    'caida torre enemiga':'tower_enemy',
    'musica del sinners':'sinners_idle',
    'MUSICA DE CUANDO FINALIZA PARTIDA, EN LOS RESULTADOS DE LA PARTIDA':'postgame',
    'sonido cuando entregamos la urna':'urn_delivered',
    'sonido cuando el equipo aliado completo la carga de la grieta':'rift_win',
    'sonido cuando la carga de la grieta la completo el enemigo':'rift_lose',
    'muerte midboss':'midboss_death',
    'voz urna cuando esta esperando que alguien tome la urna':'urn_wait',
    'voces aleatorias de la urna':'urn_carry_vo',
}
LOOPS = {
    # The world shop, lobby, and objective/ambient tracks are persistent while
    # their game state is active. UI/start/result cues remain one-shots.
    'lobby','shop','secret_store','carpet','veil','pause','search_mix',
    'rift_capture','urn_carry','sinners_idle',
}

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def run(args, log):
    p = subprocess.run([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = p.stdout.decode('utf-8', errors='replace')
    write(WORK/'logs'/log, text)
    if p.returncode: raise RuntimeError(f'{log}: exit {p.returncode}; see log')
    return text

def inventory():
    rows=[]
    for folder, key in FOLDERS.items():
        # User-provided replacements can be MP3 or WAV.  Keep non-audio helper
        # files (for example the old verification .pyc files) out of the pack.
        files=sorted(p for p in (ROOT/folder).iterdir()
                     if p.is_file() and p.suffix.lower() in {'.mp3','.wav','.ogg','.oga','.flac'})
        if key=='pause_count':
            wanted={'one.wav','two.wav','tree.wav','four.wav','five.wav','six.wav',
                    'seven.wav','eight.wav','nine.wav','ten.wav','continue.wav',
                    'silence.wav'}
            files=[p for p in files if p.name.lower() in wanted]
        assert files, f'No audio in {folder}'
        # These folders intentionally contain a randomized playlist. All
        # other targets are single replacement tracks.
        assert key in {'search_mix','pause','pause_count','urn_carry_vo'} or len(files)==1, f'Ambiguous folder {folder}'
        for i,p in enumerate(files,1):
            if p.suffix.lower()=='.wav':
                with wave.open(str(p),'rb') as w:
                    duration=w.getnframes()/w.getframerate()
                    rate=w.getframerate(); channels=w.getnchannels()
            elif p.suffix.lower()=='.mp3':
                a=MP3(p).info
                duration=a.length; rate=a.sample_rate; channels=a.channels
            else:
                a=mutagen.File(str(p))
                assert a is not None and a.info is not None, f'Unsupported audio {p}'
                duration=float(a.info.length); rate=int(getattr(a.info,'sample_rate',44100)); channels=int(getattr(a.info,'channels',2))
            rows.append(dict(folder=folder,key=key,source=str(p.relative_to(ROOT)),
                name=f'{key}_{i:02}',duration=duration,rate=rate,channels=channels,
                bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                loop=key in LOOPS, resource=f'sounds/aru/{key}_{i:02}.vsnd'))
    write(WORK/'inventory.json',json.dumps(rows,indent=2,ensure_ascii=False))
    return rows

def convert(row):
    target=CONTENT/f"sounds/aru/{row['name']}.wav"
    target.parent.mkdir(parents=True,exist_ok=True)
    # Fixed gain is measured from the full recording. Never boost a clipped source.
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    src=ROOT/row['source']
    measurement=run([ff,'-hide_banner','-nostdin','-i',src,'-vn','-af','volumedetect','-f','null','-'],row['name']+'_measure.log')
    peak=float(re.search(r'max_volume: ([-\d.]+|-?inf) dB',measurement).group(1))
    mean=float(re.search(r'mean_volume: ([-\d.]+|-?inf) dB',measurement).group(1))
    # Raise the custom pack by roughly another 6 dB while retaining a small
    # true-peak margin. The guard prevents clipping when a source is already
    # mastered hot; quiet source files get the full boost.  A silent source
    # has no measurable level and stays unamplified.
    gain=0.0 if mean==-math.inf else min((-8 if row['loop'] else -5)-mean,-0.5-peak,16)
    run([ff,'-hide_banner','-nostdin','-y','-i',src,'-vn','-map_metadata','-1',
        '-af',f'volume={gain:.3f}dB','-ar','44100','-ac','2','-c:a','pcm_s16le',target],row['name']+'_convert.log')
    with wave.open(str(target),'rb') as wav:
        row['samples']=wav.getnframes()
        row['duration']=row['samples']/wav.getframerate()
    row['gain_db']=gain
    print(f"Converted {row['name']}: {row['duration']:.2f}s",flush=True)
    return row

def event_spans(text):
    # Only top-level entries (exactly one leading tab in VRF output).
    starts=list(re.finditer(r'^\t([^\s=]+)\s*=\s*\n\t\{',text,re.M))
    out={}
    for m in starts:
        pos=text.index('{',m.start()); depth=0; quoted=False; escaped=False
        for end in range(pos,len(text)):
            c=text[end]
            if quoted:
                if escaped: escaped=False
                elif c=='\\': escaped=True
                elif c=='"': quoted=False
            elif c=='"': quoted=True
            elif c=='{': depth+=1
            elif c=='}':
                depth-=1
                if not depth: break
        out[m.group(1)]=(m.start(),end+1)
    return out

def kv(v):
    if isinstance(v, tuple) and len(v) == 2 and v[0] == 'soundevent':
        return 'soundevent:'+json.dumps(v[1])
    if isinstance(v,bool): return 'true' if v else 'false'
    if isinstance(v,list): return '[ '+', '.join(kv(x) for x in v)+' ]'
    if isinstance(v,str): return json.dumps(v)
    return str(v)

def patch_event(text,name,fields):
    spans=event_spans(text)
    assert name in spans,name
    a,b=spans[name]; body=text[a:b]
    # Remove only the named direct properties, preserving nested blocks.
    for key,val in fields.items():
        m=re.search(r'^\t\t'+re.escape(key)+r'\s*=\s*',body,re.M)
        if m:
            end=m.end()
            if body[end]=='[':
                depth=0
                for j in range(end,len(body)):
                    if body[j]=='[': depth+=1
                    elif body[j]==']':
                        depth-=1
                        if depth==0: end=j+1; break
            else:
                end=body.find('\n',end)
            body=body[:m.start()]+body[end:].lstrip('\r\n')
        if val is not None:
            body=body[:-1]+'\t'+key+' = '+kv(val)+'\n\t}'
    return text[:a]+body+text[b:]

def add_event(text,name,fields,base='Base.Mod'):
    """Append a small addon-only event before the KV3 root close."""
    assert name not in event_spans(text), name
    lines=['\t'+name+' = ','\t{', '\t\tbase = '+json.dumps(base)]
    for key,val in fields.items():
        if val is not None:
            lines.append('\t\t'+key+' = '+kv(val))
    lines += ['\t}', '}','']
    root=text.rstrip()
    assert root.endswith('}'), name
    return root[:-1]+'\n'+'\n'.join(lines)

def prepare_events(rows):
    groups={key:[x for x in rows if x['key']==key] for key in FOLDERS.values()}
    VO_AUDIT = Path(r'C:\Modding\all_soundevents_20260914\soundevents\vo\generated_vo_misc.vsndevts')
    texts={p:(AUDIT/'soundevents'/p).read_text(encoding='utf-8') for p in ['music.vsndevts','ui.vsndevts','gameplay.vsndevts','mods/tech.vsndevts','mods/armor.vsndevts']}
    texts['vo/generated_vo_misc.vsndevts']=VO_AUDIT.read_text(encoding='utf-8')
    # The Sinner's Sacrifice vault has its own NPC soundevent file; replacing
    # the generic neutral-camp slot does not affect this object.
    vault_event='npc/neut_vaults.vsndevts'
    texts[vault_event]=VAULT_AUDIT.read_text(encoding='utf-8')
    mapping=[]
    def change_rows(file,event,rs,extra=None,boost=EVENT_BOOST_DB):
        fields={'vsnd_files':[x['resource'] for x in rs], 'vsnd_duration':round(max(x['duration'] for x in rs),6), 'pitch':1.0}
        # The stock event gains are conservative and several are attenuated
        # world/UI buses. Raise only the events that receive custom files,
        # leaving all untouched game audio at its original level.
        body=texts[file][event_spans(texts[file])[event][0]:event_spans(texts[file])[event][1]]
        vm=re.search(r'^\t\tvolume\s*=\s*([\-\d.]+)',body,re.M)
        fields['volume']=round((float(vm.group(1)) if vm else 0.0)+boost,3)
        if extra: fields.update(extra)
        texts[file]=patch_event(texts[file],event,fields)
        mapping.append(dict(file=file,event=event,folder=rs[0]['folder'],random=len(rs)>1,fields=fields))
    def change(file,event,key,extra=None,boost=EVENT_BOOST_DB):
        change_rows(file,event,groups[key],extra=extra,boost=boost)
    music='music.vsndevts'
    # Keep the title/main-menu music event stock.  The actual room soundtrack
    # is Music.Hideout below; overriding Music.MainMenu makes the room track
    # restart when the player opens or changes a hero.
    # The actual hideout room uses the layered citadel_music_hideout schema,
    # so replace all three layers rather than adding an unused generic field.
    lobby_files=[x['resource'] for x in groups['lobby']]
    hideout_fields={
        'vsnd_files_play_base':lobby_files,
        'vsnd_files_play_high':lobby_files,
        'vsnd_files_play_low':lobby_files,
        'vsnd_files_play_base_fx':[],
        'endpoint':None,
        'startpoint':None,
        'sync_bpm':None,
        'vsnd_duration':round(max(x['duration'] for x in groups['lobby']),6),
        'pitch':1.0,
        'volume':9.0,
    }
    texts[music]=patch_event(texts[music],'Music.Hideout',hideout_fields)
    mapping.append(dict(file=music,event='Music.Hideout',folder='buscandoPartida',random=False,fields=hideout_fields))
    # The Inicio folder is a one-shot title/start cue, never a loop.
    change(music,'Music.Title','intro',{'vsnd_files_fx':[]})
    # The old Urn/Rift mix is now the randomized matchmaking music.
    change(music,'Music.Hideout.Search','search_mix',{'type':'citadel_default_2d','base':'Base.Music.2d','endpoint':None,'startpoint':None,'sync_bpm':None})
    change(music,'Music.Hideout.Wait','search_mix')
    # Match found is a UI one-shot.  The old 30-second waiting replacement is
    # deliberately not used anymore.
    change('ui.vsndevts','UI.Matchmake.Made','match_found',boost=LOUD_EVENT_BOOST_DB)
    # The generic PlayMenu.Page.Open event belongs to the game-mode page (the
    # first screen shown after pressing Play), so it must remain stock.  The
    # hero grid/picker has its own entry event; replacing that event makes the
    # custom cue fire when the hero-selection panel opens, before a hero card
    # is clicked.  UI.HeroCard.Activate remains stock because it fires after a
    # hero is selected, which is too late for this cue.
    change('ui.vsndevts','Menu.HeroSelection.Enter','hero_select',{
        'volume_fade_out':0.1,
    },boost=LOUD_EVENT_BOOST_DB)
    # This is the actual game-start broadcast, after the pre-match countdown;
    # keep the stock match-intro music and replace only this one-shot cue.
    change(music,'Map.Broadcast.GameStart','match_start',boost=LOUD_EVENT_BOOST_DB)
    change(music,'Music.Match.Win','win',boost=LOUD_EVENT_BOOST_DB)
    change(music,'Music.Match.Lose','lose',boost=LOUD_EVENT_BOOST_DB)
    # Match the secret-shop persistence settings.  The normal shop otherwise
    # gets culled as soon as the player leaves its short radius, so returning
    # starts the track from zero instead of resuming the same loop instance.
    change(music,'Music.Shop','shop',{
        'delay_rand_min':0.0,'delay_rand_max':0.0,
        'cull_at_distance':6000.0,
        'volume_falloff_max':1400.0,
        'occlusion_min':0.4,
        'occlusion_max_velocity':0.9,
    })
    change(music,'Music.Shop.Secret','secret_store')
    change(music,'Stinger.Idol.AnnounceDrop','urn_announce')
    change(music,'Stinger.Koth.Announce','rift_announce')
    # A carried Urn and a charged Rift each get their own looping track.
    change(music,'Music.Idol.Pickup.Lp','urn_carry',{'vsnd_files_distance_xfade':[], 'volume_fade_out':0.3})
    rift_files=[x['resource'] for x in groups['rift_capture']]
    change(music,'Music.Koth.Capture.Lp','rift_capture',{
        'vsnd_files_blocked':rift_files,
        'vsnd_files_contest':rift_files,
        'vsnd_files_approach':rift_files,
    })
    # Once the Urn is on the map, its proximity/drop music uses the normal
    # shop track (never the secret-shop track), for both team-control states.
    shop_files=[x['resource'] for x in groups['shop']]
    change(music,'Music.Idol.Timer.Lp','shop',{
        'vsnd_files_opponent_control':shop_files,
        'volume_fade_out':0.3,
    })
    change(music,'Music.PostGame','postgame')

    # Killing-streak events are intentionally untouched: the game's original
    # sounds remain active and the retired custom folder is not packaged.

    # Use separate replacements for friendly and enemy tower destruction.
    tower_ally_events=[
        'Stinger.Tier1.Killed.Friendly','Stinger.Tier2.Killed.Friendly',
        'Stinger.Titan.Killed.Friendly','Stinger.TitanShield1.Killed.Friendly',
        'Stinger.TitanShield2.Killed.Friendly',
    ]
    tower_enemy_events=[
        'Stinger.Tier1.Killed.Enemy','Stinger.Tier2.Killed.Enemy',
        'Stinger.Titan.Killed.Enemy','Stinger.TitanShield1.Killed.Enemy',
        'Stinger.TitanShield2.Killed.Enemy',
    ]
    for event in tower_ally_events:
        change(music,event,'tower_ally',boost=LOUD_EVENT_BOOST_DB)
    for event in tower_enemy_events:
        change(music,event,'tower_enemy',boost=LOUD_EVENT_BOOST_DB)

    sinners_fields={'vsnd_files':[x['resource'] for x in groups['sinners_idle']],
                    'vsnd_duration':round(max(x['duration'] for x in groups['sinners_idle']),6),
                    'volume_fade_out':0.5,'pitch':1.0,'volume':EVENT_BOOST_DB}
    texts[music]=add_event(texts[music],'Music.Sinners.Nearby',sinners_fields,base='Base.Music.3d')
    mapping.append(dict(file=music,event='Music.Sinners.Nearby',folder='musica del sinners',random=False,fields=sinners_fields))
    # Sinner's Sacrifice (the vault shown in-game) uses Vault.Idle_Lp rather
    # than the generic neutral-camp ambient slot. Override that exact event.
    vault_fields={'vsnd_files':[x['resource'] for x in groups['sinners_idle']],
                  'vsnd_duration':round(max(x['duration'] for x in groups['sinners_idle']),6),
                  'volume_fade_out':0.5,'volume':4.0}
    texts[vault_event]=patch_event(texts[vault_event],'Vault.Idle_Lp',vault_fields)
    mapping.append(dict(file=vault_event,event='Vault.Idle_Lp',folder='musica del sinners',random=False,fields=vault_fields))
    change('ui.vsndevts','Gameplay.Pause.Lp','pause',{'vsnd_pause_with_game':False,'volume_fade_out':0.2})
    # The two countdown labels live in different HUD panels with their own
    # scoped stylesheets:
    #   - the pregame panel (citadel_hud_pregame_countdown.vcss) animates once
    #     per second for the whole pre-match timer: numbers 30..11, the voiced
    #     10..1 countdown, and two extra pulses at match start (32 calls);
    #   - the pause panel (hud_paused.vcss) animates three times per resume.
    # The stock tick event (fired by the game's own code for both countdowns)
    # is silenced, and each panel drives its own dedicated forward-selection
    # event, so the two sequences never share state.  The pre-match list uses
    # 32 slots (21 silent + ten..one + silent) and always completes a full
    # cycle per match; the pause list uses 3 slots and stays aligned forever.
    count_rows={Path(x['source']).stem.lower():x for x in groups['pause_count']}
    # Source 2's forward selector advances before its first playback (the
    # default starting index is 0).  Rotate each backing list so the observed
    # calls map to the displayed countdown.
    prematch_rows=[count_rows['silence']]*18 \
        +[count_rows['ten'],count_rows['nine'],count_rows['eight'],
          count_rows['seven'],count_rows['six'],count_rows['five'],
          count_rows['four'],count_rows['tree'],count_rows['two'],
          count_rows['one']] \
        +[count_rows['silence']]*4
    pause_rows=[count_rows['one'],count_rows['tree'],count_rows['two']]
    def add_countdown(name,rows):
        fields={'vsnd_files':[x['resource'] for x in rows],
                'vsnd_duration':round(max(x['duration'] for x in rows),6),
                'pitch':1.0,'volume':8.0,
                'track_1.vsnd_selection_type':'forward'}
        texts['ui.vsndevts']=add_event(texts['ui.vsndevts'],name,fields,base='Base.UI')
        mapping.append(dict(file='ui.vsndevts',event=name,folder='contador',random=False,fields=fields))
    add_countdown('Aru.PreMatch.Countdown.Tick',prematch_rows)
    add_countdown('Aru.Pause.Countdown.Tick',pause_rows)
    # Keep the stock tick defined (the game still fires it) but inaudible so
    # the CSS-driven events are the only countdown sounds.
    texts['ui.vsndevts']=patch_event(texts['ui.vsndevts'],
        'Gameplay.Pause.Resume.Countdown.Tick',{'volume':-60.0})
    change_rows('ui.vsndevts','Gameplay.Pause.End',[count_rows['continue']],
                {'volume':8.0},boost=LOUD_EVENT_BOOST_DB)
    # Midboss appearance pushed to the maximum safe UI level as requested.
    change('gameplay.vsndevts','MidBoss.Arrive','midboss_spawn',{'volume':9.0})
    change('gameplay.vsndevts','MidBoss.LowHealth','midboss_hurt')
    change('gameplay.vsndevts','MidBoss.Death','midboss_death',{'volume':9.0})
    # Urn waiting VO: single file replaces all 32 waiting/idle idol lines.
    if 'urn_wait' in groups and groups['urn_wait']:
        urn_wait_res=groups['urn_wait'][0]['resource']
        urn_wait_dur=round(groups['urn_wait'][0]['duration'],6)
        for ev in list(event_spans(texts['vo/generated_vo_misc.vsndevts']).keys()):
            if 'spirit_jar_idol_waiting_' in ev:
                texts['vo/generated_vo_misc.vsndevts']=patch_event(texts['vo/generated_vo_misc.vsndevts'],ev,{'vsnd_files':[urn_wait_res],'vsnd_duration':urn_wait_dur,'volume':8.0})
                mapping.append(dict(file='vo/generated_vo_misc.vsndevts',event=ev,folder='voz urna cuando esta esperando que alguien tome la urna',random=False,fields={'vsnd_files':[urn_wait_res],'volume':8.0}))
    # Urn carrying VO: 7 random files replace ALL 257 portador lines.
    if 'urn_carry_vo' in groups and groups['urn_carry_vo']:
        carry_files=[x['resource'] for x in groups['urn_carry_vo']]
        carry_dur=round(max(x['duration'] for x in groups['urn_carry_vo']),6)
        c_events=[ev for ev in event_spans(texts['vo/generated_vo_misc.vsndevts']).keys()
                  if any(k in ev for k in ['holder_','picked_up','dropping','dropped','delivered'])
                  and 'waiting' not in ev]
        for i,ev in enumerate(sorted(c_events)):
            res=carry_files[i % len(carry_files)]
            texts['vo/generated_vo_misc.vsndevts']=patch_event(texts['vo/generated_vo_misc.vsndevts'],ev,{'vsnd_files':[res],'vsnd_duration':carry_dur,'volume':8.0})
            mapping.append(dict(file='vo/generated_vo_misc.vsndevts',event=ev,folder='voces aleatorias de la urna',random=False,fields={'vsnd_files':[res],'volume':8.0}))
    change('mods/tech.vsndevts','Item.MagicCarpet.Lp','carpet')

    # One-shot objective result cues.  These are deliberately not added to
    # LOOPS, so the encoding contains no loop metadata for them.
    change(music,'Stinger.Idol.Returned.Team','urn_delivered',boost=LOUD_EVENT_BOOST_DB)
    change(music,'Stinger.Koth.Win','rift_win',boost=LOUD_EVENT_BOOST_DB)
    change(music,'Stinger.Koth.Lose','rift_lose',boost=LOUD_EVENT_BOOST_DB)
    # Veil Walker's stock Proc event is a one-shot activation cue. Add a
    # dedicated loop event and wire it into the invisibility modifier below;
    # Source 2 then stops it automatically when the modifier expires.
    veil=groups['veil'][0]
    ambient_fields={'vsnd_files':[veil['resource']], 'vsnd_duration':round(veil['duration'],6),
                    'volume_fade_in':0.2, 'volume_fade_out':0.2, 'pitch':1.0,
                    'volume':EVENT_BOOST_DB}
    texts['mods/armor.vsndevts']=add_event(texts['mods/armor.vsndevts'],
        'Mods.Armor.VeilWalker.Ambient',ambient_fields)
    mapping.append(dict(file='mods/armor.vsndevts',event='Mods.Armor.VeilWalker.Ambient',
        folder=veil['folder'],random=False,fields=ambient_fields))
    for p,text in texts.items():
        if p==vault_event:
            source_path=VAULT_AUDIT
        elif p=='vo/generated_vo_misc.vsndevts':
            source_path=VO_AUDIT
        else:
            source_path=AUDIT/'soundevents'/p
        original_count=len(event_spans(source_path.read_text(encoding='utf-8')))
        added={'music.vsndevts':1,'mods/armor.vsndevts':1,'ui.vsndevts':2}
        expected_count=original_count + added.get(p,0)
        assert len(event_spans(text))==expected_count
        write(CONTENT/'soundevents'/p,text)

    # Neutral/Sinner camps expose idle ambient sound slots. Pointing those
    # slots at the new 3D event makes the music audible near the camp and
    # attenuated with distance, instead of making it a global soundtrack.
    misc=(AUDIT/'scripts/misc.vdata').read_text(encoding='utf-8')
    include=re.search(r'\n\t_include\s*=\s*\n\t\[\n.*?\n\t\]\n',misc,re.S)
    if include:
        misc=misc[:include.start()]+'\n'+misc[include.end():]
    misc_events=event_spans(misc)
    camp_names=[name for name in misc_events if name=='info_neutral_trooper_camp' or name.startswith('neutral_camp_')]
    for camp in camp_names:
        misc=patch_event(misc,camp,{'m_sIdleAmbient':('soundevent','Music.Sinners.Nearby')})
        mapping.append(dict(file='scripts/misc.vdata',event=camp,folder='musica del sinners',random=False,fields={'m_sIdleAmbient':'Music.Sinners.Nearby'}))
    write(CONTENT/'scripts/misc.vdata',misc)
    # Override only the current Veil Walker modifier data. The stock modifier
    # already has recipient scoping; adding m_sAmbientLoopingSound makes the
    # custom track follow the invisibility lifetime exactly.
    abilities=(AUDIT/'scripts/abilities.vdata').read_text(encoding='utf-8')
    # Source2Viewer emits a flattened abilities.vdata but preserves the
    # original source _include list. The included definitions are already
    # present in this dump; remove the source-only include block so CSDK12 can
    # compile the standalone override without needing private source files.
    include=re.search(r'\n\t_include\s*=\s*\n\t\[\n.*?\n\t\]\n',abilities,re.S)
    assert include, 'abilities include block not found'
    abilities=abilities[:include.start()]+'\n'+abilities[include.end():]
    needle='\t\t\t\t\tm_sStartSound = soundevent:"Mods.Armor.VeilWalker.Proc"\n\t\t\t\t\tm_nAmbientLoopingSoundRecipients = "MODIFIER_SOUND_RECIPIENT_PARENT_IS_LOCAL_PLAYER"'
    replacement='\t\t\t\t\tm_sStartSound = soundevent:"Mods.Armor.VeilWalker.Proc"\n\t\t\t\t\tm_sAmbientLoopingSound = soundevent:"Mods.Armor.VeilWalker.Ambient"\n\t\t\t\t\tm_nAmbientLoopingSoundRecipients = "MODIFIER_SOUND_RECIPIENT_PARENT_IS_LOCAL_PLAYER"'
    assert abilities.count(needle)==1, 'Veil Walker modifier pattern not found'
    write(CONTENT/'scripts/abilities.vdata',abilities.replace(needle,replacement))
    write(WORK/'mapping.json',json.dumps(mapping,indent=2,ensure_ascii=False))
    return mapping

def prepare():
    rows=inventory()
    # Remove generated source assets from an earlier build. This keeps the
    # replacement addon deterministic and prevents the retired Inicio track
    # from being compiled or accidentally staged into a later VPK.
    sound_dir=CONTENT/'sounds/aru'
    if sound_dir.exists():
        for old in sound_dir.glob('*.wav'):
            old.unlink()
    enc=sound_dir/'encoding.txt'
    if enc.exists():
        enc.unlink()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        rows=list(pool.map(convert,rows))
    write(WORK/'converted.json',json.dumps(rows,indent=2,ensure_ascii=False))
    loops='\n'.join('{ fileName = "'+r['name']+'.wav" loop = { loop_start_sample = 0 loop_end_sample = '+str(r['samples'])+' } },' for r in rows if r['loop'])
    write(CONTENT/'sounds/aru/encoding.txt', HEADER+'{ compress = { format = "mp3" minbitrate = 128 maxbitrate = 192 vbr = 1 } files = [\n'+loops+'\n] }\n')
    # The roster picker is a hidden Panorama popup.  Its stock sound event is
    # not emitted on this route, so keep a tiny CSS override that fires the
    # custom event exactly when the picker loses its Hidden class.
    roster_css=ROOT/'panorama/styles/popups/citadel_popup_roster_select.vcss'
    assert roster_css.exists(), 'Roster picker CSS override not found'
    roster_dest=CONTENT/'panorama/styles/popups/citadel_popup_roster_select.vcss'
    roster_dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(roster_css,roster_dest)
    # The two countdown HUD stylesheets fire the dedicated pre-match and pause
    # tick events every time their number label gets the ShrinkCountdown class.
    for css in ['citadel_hud_pregame_countdown.vcss','hud_paused.vcss']:
        src=ROOT/'panorama/styles'/css
        assert src.exists(), f'{css} override not found'
        shutil.copy2(src,CONTENT/'panorama/styles'/css)
    prepare_events(rows)

def compile_all():
    GAME.mkdir(parents=True,exist_ok=True)
    # Resourcecompiler can preserve loop metadata from a previous compiled
    # asset when the WAV is replaced quickly. Clear only this addon’s own
    # compiled outputs so encoding.txt changes (notably the one-shot shop
    # track) are always reflected in the new VPK.
    for generated_root in (GAME/'sounds/aru', GAME/'soundevents', GAME/'scripts', GAME/'panorama/styles'):
        if generated_root.exists():
            for old in generated_root.rglob('*_c'):
                if old.is_file():
                    old.unlink()
    for pattern in ['sounds/aru/*.wav','soundevents/*.vsndevts','soundevents/vo/*.vsndevts','soundevents/mods/*.vsndevts','soundevents/npc/*.vsndevts','scripts/abilities.vdata','scripts/misc.vdata','panorama/styles/popups/citadel_popup_roster_select.vcss','panorama/styles/citadel_hud_pregame_countdown.vcss','panorama/styles/hud_paused.vcss']:
        text=run([RC,'-i',CONTENT/pattern,'-game',SDK/'game/citadel','-addon','aru_audio_pack','-nop4'], 'compile_'+pattern.replace('/','_').replace('*','all')+'.log')
        print(text[-2200:],flush=True)
        if re.search(r'(?im)^.*(?:COMPILE FAILED|Error compiling|Failed to compile).*$',text): raise RuntimeError('Compilation failure')
    expected=[GAME/Path(r['resource']+'_c') for r in json.loads((WORK/'converted.json').read_text(encoding='utf-8'))]
    expected += [GAME/'soundevents'/p.relative_to(CONTENT/'soundevents').with_suffix('.vsndevts_c') for p in (CONTENT/'soundevents').rglob('*.vsndevts')]
    expected += [GAME/'scripts/abilities.vdata_c', GAME/'scripts/misc.vdata_c',
                 GAME/'panorama/styles/popups/citadel_popup_roster_select.vcss_c',
                 GAME/'panorama/styles/citadel_hud_pregame_countdown.vcss_c',
                 GAME/'panorama/styles/hud_paused.vcss_c']
    assert all(p.exists() and p.stat().st_size>100 for p in expected),'Missing compiled output'
    # Build into a fresh staging directory so retired resources cannot leak
    # into the package from a previous run.
    stage=WORK/'stage_rebuild_v2'
    # OneDrive may mark prior staging directories as reparse points while it
    # is syncing them, so use a fresh directory name instead of deleting a
    # potentially locked tree.
    stage.mkdir(parents=True,exist_ok=True)
    for old in stage.rglob('*'):
        if old.is_file():
            old.unlink()
    for p in expected:
        out=stage/p.relative_to(GAME); out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,out)
    run([Path(sys.executable).parent/'Scripts/vpk.exe','-c',stage,WORK/'aru_audio_beta_dir.vpk'],'pack.log')
    print('Compiled and packed',len(expected),'resources')

if __name__=='__main__':
    action=sys.argv[1] if len(sys.argv)>1 else 'inventory'
    if action=='inventory':
        for row in inventory(): print(f"{row['folder']}: {row['duration']:.2f}s | {row['source']}")
    elif action=='prepare': prepare()
    elif action=='compile': compile_all()
    else: raise ValueError(action)
