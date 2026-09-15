from pathlib import Path
from mutagen.mp3 import MP3

for folder in sorted(Path('.').iterdir()):
    if not folder.is_dir():
        continue
    files = list(folder.glob('*.mp3'))
    if files:
        for path in files:
            info = MP3(path).info
            print(folder.name, '|', path.name, '|', round(info.length, 2), 's |', info.sample_rate, 'Hz |', info.channels, 'ch')
