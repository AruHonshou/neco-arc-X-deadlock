# Neco Arc X Deadlock — Aru Audio Pack

Mod de audio para Deadlock que reemplaza música y avisos del cliente. No modifica modelos, balance ni archivos del servidor.

## Contenido incluido (build actual)

*   **Contador 10→1 y pausa 3→2→1** separados por panel (`CitadelPregameCountdown` / `CitadelPaused`) con `Aru.PreMatch` (32 slots: silencio + ten..one) y `Aru.Pause` (3 slots: tree/two/one).
*   4 avisos actualizados: `aparece la urna`, `Aparece midboss`, `avisoAparecelaGrieta`, `midboss herido` + `muerte midboss` (volumen 9.0).
*   Voces de urna: 32 diálogos de espera → 1 MP3, 257 diálogos de portador → 7 MP3 en aleatorio.

## Estructura

```
build_pack.py                # empaquetado reproducible
panorama/styles/             # overrides CSS (ShrinkCountdown → sound)
contador/                    # voces 10..1 + continue + silence
muerte midboss/              # 1 MP3
voz urna cuando esta esperando que alguien tome la urna/  # 1 MP3
voces aleatorias de la urna/ # 7 MP3
_pack/GameBanana/pak99_dir.vpk  # VPK listo para instalar
```

## Build

```powershell
python build_pack.py inventory
python build_pack.py prepare
python build_pack.py compile
python verify_pack.py
```

Requiere `C:\Modding\CSDK12\Reduced_CSDK_12` y `C:\Modding\aru_audit_current`.

## Instalación en el juego

1. Importa `_pack/GameBanana/pak99_dir.vpk` en Deadlock Mod Manager o copia a `.../Deadlock/game/citadel/addons/pak99_dir.vpk`.
2. Activa y reinicia Deadlock.

## Respaldo

Este repo guarda **todo el fuente** (código + audios fuente). Los VPK/ZIP se guardan vía Git LFS. Cada versión estable se publica como Release con el VPK adjunto.

## Licencia

Verifica permisos de cada audio antes de redistribuir en GameBanana.
