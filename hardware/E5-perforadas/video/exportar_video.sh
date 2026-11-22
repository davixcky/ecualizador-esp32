#!/usr/bin/env bash
# MP4 final del video E.5: fotogramas de Blender + audio del modelo SPICE + rótulos.
set -euo pipefail
cd "$(dirname "$0")/../../.."
font=$(fc-match -f '%{file}' 'DejaVu Sans:bold')
n=$(ls docs/video/frames/frame-*.png | wc -l)
[ "$n" -eq 1200 ] || { echo "Faltan fotogramas: $n de 1200" >&2; exit 1; }
ffmpeg -v warning -y -framerate 24 -i docs/video/frames/frame-%04d.png -i docs/video/demo-audio.wav \
  -vf "drawtext=fontfile='$font':text='EQ / E.5':x=64:y=44:fontsize=32:fontcolor=white:borderw=2:bordercolor=0x101820,drawtext=fontfile='$font':text='TARJETAS PERFORADAS · CINCO CONTROLES ROTATIVOS':x=64:y=88:fontsize=18:fontcolor=0xC9D6DF:borderw=2:bordercolor=0x101820,drawtext=fontfile='$font':text='Render del modelo CAD · audio calculado con el modelo SPICE · no es una grabación del prototipo':x=64:y=h-45:fontsize=17:fontcolor=0xC9D6DF:borderw=2:bordercolor=0x101820,ass=docs/video/demo-subtitulos.ass" \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart docs/video/ecualizador-animado.mp4
ffmpeg -v warning -y -ss 12 -i docs/video/ecualizador-animado.mp4 -frames:v 1 -update 1 -q:v 3 docs/video/portada.jpg
echo docs/video/ecualizador-animado.mp4
