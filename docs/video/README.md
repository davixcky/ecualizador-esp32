# Video del ecualizador E.5 con sonido

**[Reproducir el video](ecualizador-animado.mp4)** — 50 segundos, 1920 × 1080, 24 fps, H.264 con audio AAC de 48 kHz. Muestra el montaje vigente: **cuatro tarjetas perforadas y cinco controles rotativos**. No hay potenciómetros deslizables ni PCB única; el video anterior (revisión D.2) fue reemplazado.

![Portada](portada.jpg)

| Tiempo | Qué se ve y se escucha |
|---|---|
| 0–4 s | Producto cerrado: tapa con cinco perillas, pantalla T4-S3, dos rejillas de parlante y tres barras de luz. |
| 4–7 s | Detalle de los controles: NIVEL, GRAVES, MEDIOS, AGUDOS y VOLUMEN. |
| 7–14 s | GRAVES (RV2, B10K): centro, mínimo, máximo y vuelta al centro. |
| 14–21 s | La misma secuencia con MEDIOS (RV3, B10K). |
| 21–28 s | La misma secuencia con AGUDOS (RV4, B10K). |
| 28–31 s | Pulsador VISTA: la pantalla pasa de «TRES BANDAS» a «ESPECTRO». |
| 31–34 s | La tapa imantada se levanta basculando sobre su borde frontal; los arneses la siguen. |
| 34–44 s | Interior: cuatro tarjetas y arneses, T2 con LM324 y PAM8403, parlantes en la tapa, T4 con el ESP32S USB-C. |
| 44–50 s | Se cierra la tapa y termina con el producto cerrado. |

## Qué es fiel y qué no

- **Geometría.** Sale del CAD E.5 (`hardware/E5-perforadas/3d/`), que a su vez sale de `medidas-componentes.json`. Las piezas son envolventes; varias cotas siguen sin medir.
- **Controles.** Solo giran RV2, RV3 y RV4, los tres B10K de banda. NIVEL y VOLUMEN (A10K) **no se han comprado** y permanecen quietos; en el interior se dibujan en ámbar. El cuarto B10K es repuesto y no aparece.
- **Sonido.** `generar_audio.py` crea una composición original y la filtra con las respuestas AC que ngspice calcula para el circuito LM324 en once posiciones de cada potenciómetro. Es una aproximación cuasiestática de pequeña señal: no modela ruido de contacto, saturación, el PAM8403, los parlantes ni la acústica del gabinete. Hay una sola ganancia de reproducción para todo el clip. Los porcentajes del rótulo son recorrido del cursor, no ganancia en dB.
- **Difusores.** Relieve hexagonal impreso, de geometría propia e inspirado en el Duality Infinity 3DHex de Andy Huot. En el render las celdas (0,5 mm) se ven más claras que los nervios (1,1 mm); es una aproximación visual, no una simulación óptica.
- **Pantalla.** Es la LilyGO T4-S3 montada en vertical (450 × 600), con el vidrio negro de 56 × 44 mm al ras de la tapa. **No está comprada y no tiene firmware.** Lo que se ve es una propuesta de interfaz a pantalla completa dibujada por `generar_tft.py`. Los valores que muestra (dB por banda, picos, barras del espectro) sí los calcula el código real del firmware (`firmware/lib/dsp`) compilado en el PC, alimentado con el bloque de 1024 muestras a 20 kS/s y los picos por banda que resultan del modelo. Los niveles son bajos (−60 a −25 dB) porque así salen del modelo con 0,11 V de entrada.
- **Luces.** Como en `firmware/src/main.cpp`: 12 píxeles lógicos fijos —4 naranja, 4 verdes, 4 azules— con brillo moderado. **No reaccionan al audio.** Físicamente son tres tramos de 200 mm de la tira FCOB WS2811 de 12 V. El render no demuestra que el equipo pueda alimentarla: falta resolver los 12 V.
- **Tapa.** Cierra con imanes y no tiene bisagras: en el video queda abierta sin apoyo, cosa que en la realidad exige sostenerla.
- **Cableado.** Los 82 conductores van de terminal a terminal, pero su recorrido y longitud son ilustrativos.

Es un **render de un modelo de diseño con audio calculado**. No es una grabación del prototipo, no prueba que el firmware corra en la placa y no sustituye pruebas eléctricas ni mecánicas. La revisión visual y las métricas están en [REVIEW.md](REVIEW.md).

## Archivos

| Archivo | Contenido |
|---|---|
| `ecualizador-animado.mp4` | Video final con sonido |
| `ecualizador-animado.blend` | Escena editable de Blender 5.1 (rutas relativas) |
| `ecualizador-blender.zip` | Escena, audio y fotogramas de pantalla listos para abrir en otro equipo |
| `tft-fotogramas/` | 1200 PNG de 450 × 600: interfaz propuesta para la T4-S3 |
| `demo-audio.wav` · `demo-entrada.wav` | Audio procesado que lleva el video · composición antes del circuito (a otro nivel; no sirve para comparar ganancia) |
| `respuestas-spice.npz` | Respuestas complejas de ngspice: LINEA, G_W, M_W, A_W y ADC_FFT_RAW |
| `demo-timeline.json` | Posición de los controles, vista de pantalla y picos por banda en cada fotograma |
| `demo-subtitulos.ass` | Rótulos sincronizados |
| `validacion-audio.json` | Datos del modelo de audio |
| `hoja-de-contacto.jpg` | 24 fotogramas extraídos del MP4 final |
| `../validacion/video-dispositivo.json` | Validación de CAD, escena, MP4, audio y textos |

## Regenerar

Desde la raíz del repositorio. Requiere FreeCAD 1.1, Blender 5.1, FFmpeg, ngspice, g++, las bibliotecas de PlatformIO del firmware (`pio pkg install -d firmware`) y el entorno `.venv` con NumPy, SciPy y Pillow.

```sh
# 1. CAD y vistas fijas
freecadcmd hardware/E5-perforadas/3d/generar_modelo.py
blender -b -P hardware/E5-perforadas/3d/render_modelo.py -- cerrado abierto planta detalle

# 2. Audio, datos de pantalla y fotogramas de la TFT
.venv/bin/python hardware/E5-perforadas/video/generar_audio.py
.venv/bin/python hardware/E5-perforadas/video/generar_tft.py

# 3. Escena y fotogramas (unos 45 min en una RTX 5070; reanuda si se interrumpe)
rm -rf docs/video/frames
blender -b -P hardware/E5-perforadas/video/video_blender.py

# 4. MP4, validación y paquetes
bash hardware/E5-perforadas/video/exportar_video.sh
.venv/bin/python hardware/E5-perforadas/video/validar_entrega.py
.venv/bin/python hardware/E5-perforadas/video/empaquetar_blender.py
.venv/bin/python herramientas/empaquetar_exposicion.py
```

`BUILD_ONLY=1` guarda solo el `.blend`; `PREVIEW=1,300,860` saca fotogramas sueltos; `RANGO=1-300` renderiza un tramo. Los movimientos están en `hardware/E5-perforadas/video/timeline.py` y las cámaras en `video_blender.py`. `docs/video/frames/` no se versiona: hay que borrarla al cambiar la animación para no mezclar versiones.

Los guiones del video anterior siguen en `cad/`, archivados; ya no escriben en esta carpeta (ver `cad/LEEME-ARCHIVO.md`).
