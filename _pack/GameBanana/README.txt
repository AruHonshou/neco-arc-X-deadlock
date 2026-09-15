ARU AUDIO PACK - Deadlock
=========================

Este mod reemplaza musica y avisos de audio del cliente de Deadlock. No
incluye ni modifica modelos 3D, iconos, balance, gameplay ni archivos del
servidor.

Instalacion
-----------
1. Importa `pak99_dir.vpk` en Deadlock Mod Manager.
2. Activa el mod y reinicia Deadlock cuando el gestor lo solicite.
3. Para una instalacion manual, copia el VPK a:
   ...\Deadlock\game\citadel\addons\
   usando un nombre libre con el formato `pak##_dir.vpk`.

Contenido de esta version
-------------------------
- Sala principal (sin buscar partida): `buscandoPartida`, en bucle.
- Inicio/titulo: `Inicio`, una sola reproduccion, sin bucle.
- Partida encontrada: `sonido encontro partida`, una sola reproduccion y con
  volumen elevado.
- Selector de heroe (la cuadricula de heroes, no la pantalla «Seleccionar modo
  de juego»): `SELECCIONAR PERSONAJE`, una sola reproduccion al abrirlo.
- Inicio real de la partida, despues de la cuenta atras: `INICIA PARTIDA`, una
  sola reproduccion y con volumen elevado.
- Reanudacion tras pausa: `contador/tree`, `contador/two` y `contador/one` en
  orden secuencial para 3, 2 y 1, con volumen alto; `contador/continue` al
  terminar la pausa, tambien con volumen alto.
- Cuenta atras de inicio de partida (del 10 al 1): `contador/ten` hasta
  `contador/one` en su numero correspondiente, con silencio el resto del
  temporizador y al arrancar la partida.
- Busqueda de partida: playlist aleatoria de `musicaMix`.
- Victoria y derrota: sus carpetas respectivas, una sola reproduccion y con
  volumen elevado.
- Midboss, anuncio de Urna y anuncio de Grieta.
- Urna en movimiento: `llevar urna`.
- Grieta en captura/carga: `cargar o estar dentro de la grieta`.
- Urna en el mapa: usa la musica normal de tienda cerca del objetivo, nunca
  la tienda secreta.
- Sinner's Sacrifice y campamentos Sinner/neutral en reposo: `musica del
  sinners`, con atenuacion 3D por distancia.
- Destruccion de torres: `caida torre aliada` para estructuras aliadas y
  `caida torre enemiga` para estructuras enemigas, sin bucle y con volumen
  elevado.
- Entrega de la Urna: `sonido cuando entregamos la urna`, sin bucle y con
  volumen elevado.
- Final de carga de la Grieta: las carpetas de equipo aliado y enemigo, sin
  bucle y con volumen elevado.
- Resultados posteriores a la partida: carpeta de musica de resultados.
- Killingstreak vuelve completamente al sonido original del juego.
- Tienda normal y tienda secreta usan las carpetas actuales respectivas, en
  bucle mientras el evento esta activo y con la misma persistencia al alejarse
  y volver. El sonido de entrada al menu de tienda vuelve al original del
  juego.
- Pausa usa solamente el audio actual de `pause`, en bucle mientras la pausa
  esta activa. Tambien se mantienen alfombra magica y Velo Walker.
- No se reemplazan las voces de la Urna, la Archimadre ni el Rey Oculto.

La playlist de `musicaMix` se selecciona aleatoriamente. Las pistas de
transporte/captura conservan el bucle del juego y se detienen cuando el evento
deja de estar activo. La musica ambiental de ambas tiendas permanece en bucle
mientras el estado correspondiente esta activo. Los avisos marcados como una
sola reproduccion no tienen metadatos de bucle. La ganancia de los nuevos
avisos se elevo con limitador de pico para evitar saturacion.

Compatibilidad y conflictos
---------------------------
Este build se entrega como `pak99_dir.vpk` para tener prioridad sobre packs de
audio antiguos. Desactiva cualquier otro mod que reemplace
`soundevents/music.vsndevts`, `soundevents/gameplay.vsndevts` o
`soundevents/ui.vsndevts`, porque un paquete con mayor prioridad puede ganar y
reproducir otros sonidos.

Distribucion
------------
Antes de publicarlo en GameBanana, confirma que tienes permiso para
redistribuir cada musica y audio incluido y completa los campos de licencia
que pida la pagina.
