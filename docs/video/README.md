# Demo del ecualizador con sonido

**[Reproducir el video](ecualizador-animado.mp4)** — 36 segundos, Full HD, 24 fps, H.264 con audio AAC de 48 kHz. Se puede insertar en PowerPoint o abrir en VLC. Activar el sonido para comparar las bandas.

| Tiempo | Qué se ve y se escucha |
|---|---|
| 0–3 s | Los tres controles al 50 %, con una composición original de bajo, melodía y percusión. |
| 3–10 s | Graves: centro, mínimo, máximo y vuelta al centro. |
| 10–17 s | La misma comparación con medios. |
| 17–24 s | La misma comparación con agudos. |
| 24–28 s | Regreso a los tres controles al 50 %. |
| 28–36 s | Apertura de la tapa imantada, vista de la PCB y cierre. |

El audio cambia según la posición del deslizador; la pantalla muestra el espectro y la energía del audio procesado. Los NeoPixel toman el color de la banda que se está ajustando y su intensidad sigue la energía del sonido. Los porcentajes del rótulo indican recorrido del control, no ganancia en dB.

## Cómo se produce el sonido

`cad/generar_demo_audio.py` genera una composición original y obtiene con ngspice 33 respuestas complejas de la cadena hasta `LINEA`, usando la netlist de `herramientas/circuito.py` y el macromodelo de `herramientas/simulacion.py`. Para cada banda se calculan once posiciones del potenciómetro; los otros controles permanecen al 50 %.

El audio se procesa por ventanas con esas respuestas, interpolando entre posiciones. Es una aproximación cuasiestática de pequeña señal: representa el cambio de filtrado, pero no modela ruido de contacto, saturación durante movimientos, altavoz, acústica del gabinete ni la ejecución del firmware. Hay una sola ganancia de reproducción para todo el clip: no se normaliza cada segmento por separado. La pista de entrada no usa música comercial.

Es una **demo virtual con audio del modelo**, no una grabación del prototipo físico ni una prueba de que el ESP32 esté ejecutando el firmware. El espectro de la pantalla se calcula desde el WAV de la demo. La vista abierta es un despiece y no muestra todo el cableado del panel. El CAD conserva el parlante y el PAM8403 bajo la PCB; el audio corresponde a la salida de línea, que también permite conectar un equipo externo.

## Archivos

- `ecualizador-animado.mp4`: demo para exponer, con sonido.
- `ecualizador-blender.zip`: escena, audio y texturas con rutas relativas. Extraer completo y abrir `docs/video/ecualizador-animado.blend` en Blender 5.1.
- `demo-audio.wav`: audio procesado que se usa en el video.
- `demo-entrada.wav`: composición antes del filtrado, a un nivel de reproducción independiente; no sirve para comparar ganancia absoluta.
- `demo-timeline.json`: posiciones, niveles y espectro por fotograma.
- `respuestas-spice.npz`: respuestas complejas calculadas por ngspice.
- `validacion-audio.json`: cambios de respuesta entre extremos, pico y ausencia de recorte digital.

## Regenerar

Desde la raíz del repositorio, con ngspice, Blender 5.1, FFmpeg, NumPy, SciPy y Pillow instalados:

```sh
.venv/bin/python cad/generar_demo_audio.py
.venv/bin/python cad/validar_demo_audio.py
.venv/bin/python cad/generar_video_texturas.py
blender -b -P cad/video_blender.py
bash cad/exportar_video.sh
.venv/bin/python cad/empaquetar_video.py
```

El render usa Cycles/OptiX en una GPU NVIDIA. En otro equipo, seleccionar el dispositivo disponible. `BUILD_ONLY=1` construye la escena sin renderizar; `cad/render_video_lote.py` permite renderizar tramos y omitir los fotogramas existentes. Al cambiar la animación, borrar antes los PNG intermedios de `docs/video/frames/` para no mezclar versiones.
