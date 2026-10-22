#!/usr/bin/env bash
# MP4 con audio SPICE y rótulos sincronizados con los deslizadores.
set -euo pipefail
cd "$(dirname "$0")/.."
video_font=$(fc-match -f '%{file}' sans)
ffmpeg -y -framerate 24 -i docs/video/frames/frame-%04d.png -i docs/video/demo-audio.wav \
  -vf "drawtext=fontfile='$video_font':text='EQ / 03':x=64:y=44:fontsize=32:fontcolor=white,drawtext=fontfile='$video_font':text='DEMO DE AUDIO · TRES BANDAS':x=64:y=88:fontsize=18:fontcolor=0xB9CBD7,drawtext=fontfile='$video_font':text='Demo virtual · audio procesado con el modelo SPICE':x=64:y=h-45:fontsize=17:fontcolor=0xB9CBD7,ass=docs/video/demo-subtitulos.ass" \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart docs/video/ecualizador-animado.mp4
ffmpeg -y -ss 8 -i docs/video/ecualizador-animado.mp4 -frames:v 1 -update 1 docs/video/portada.jpg
