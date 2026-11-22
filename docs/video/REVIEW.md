# Revisión del video E.5 (2026-11-20)

Archivo revisado: `docs/video/ecualizador-animado.mp4`
SHA-256: `4c1bf2661b112ddf9cb6c7e5107352f08748e5a46bc1709b12b85722699bd85d`

Esta revisión la hizo el mismo proceso automático que generó el video. **Nadie escuchó el audio**: solo se midió.
El video es un render de un modelo de diseño y no sustituye pruebas eléctricas ni mecánicas.

Reproducir: `.venv/bin/python hardware/E5-perforadas/video/validar_entrega.py`
(resultado completo en `docs/validacion/video-dispositivo.json`).

> **Aviso (2026-11-21):** después de este video el CAD ganó encastres impresos (setas, ganchos, cuñas,
> pinzas), perdió los tornillos y movió el parlante derecho 4 mm y un imán trasero. El video y el archivo de Blender
> no se han vuelto a renderizar: muestran el interior anterior.

## Contenedor y decodificación

| Medida | Resultado |
|---|---|
| Resolución | 1920 x 1080 |
| Códec de video | H.264 High, yuv420p |
| Velocidad | 24 fps |
| Fotogramas decodificados | 1200 de 1200 |
| Duración | 50,0 s |
| Decodificación completa (`ffmpeg -xerror`) | sin errores |
| Audio | AAC, mono, 48 kHz, 50,0 s |
| Tamaño | 30,1 MB |

## Audio (solo métricas)

El audio no es una grabación del prototipo. Es una señal de prueba filtrada con las respuestas AC de ngspice
del circuito E.5 (macromodelo LM324), siguiendo la posición de cada control en la línea de tiempo.

| Medida | Resultado |
|---|---|
| Correlación del audio del MP4 con `demo-audio.wav` | 0,99908, desfase 0 muestras |
| Pico decodificado | 0,87 (0 muestras en recorte) |
| Sonoridad integrada | -20,79 LUFS |
| Pico real | -1,01 dBTP |
| Rango de sonoridad | 4,4 LU |
| Silencios de más de 0,5 s | 0 |

Efecto de cada control rotativo, medido en el audio decodificado del MP4:

| Control | Banda medida | Al mínimo | Al máximo | Diferencia |
|---|---|---|---|---|
| RV2 GRAVES | 20 a 300 Hz | -45,43 dB | -13,55 dB | 31,88 dB |
| RV3 MEDIOS | 300 a 3000 Hz | -46,84 dB | -22,11 dB | 24,73 dB |
| RV4 AGUDOS | 3 a 18 kHz | -56,53 dB | -29,55 dB | 26,99 dB |

## Inspección visual

Hecha sobre `docs/video/hoja-de-contacto.jpg`: 24 fotogramas extraídos del MP4 final.

| Instante | Qué se ve | Criterio |
|---|---|---|
| 0,0 y 2,0 s | Gabinete cerrado, cinco perillas metálicas, pantalla T4-S3 vertical de vidrio negro al ras, tres barras LED, dos rejillas | Producto cerrado desde el primer fotograma: cumple |
| 5,0 y 6,5 s | Paso cercano por NIVEL, GRAVES, MEDIOS, AGUDOS y VOLUMEN | Detalle de los cinco controles rotativos: cumple |
| 8,0 a 11,5 s | Gira solo la perilla de GRAVES (0 % y 100 %) y cambia la pantalla | Cumple |
| 15,5 a 18,5 s | Gira solo la perilla de MEDIOS | Cumple |
| 22,5 a 25,5 s | Gira solo la perilla de AGUDOS | Cumple |
| 28,7 y 30,0 s | Pulsador VISTA: la pantalla T4-S3 pasa de TRES BANDAS a ESPECTRO a pantalla completa; las barras LED no cambian | Cumple |
| 32,0 a 34,5 s | La tapa bascula sobre el borde frontal, sin bisagras | Cumple |
| 34,5 a 43,0 s | Cuatro tarjetas perforadas, arneses, borneras +5 V / GND, parlantes y potenciómetros en la tapa, ESP32S con USB-C, 74HCT245, LM324 | Cumple |
| 45,0 a 46,5 s | La tapa baja | Cumple |
| 48,0 y 49,9 s | Gabinete cerrado | Termina cerrado: cumple |

Comprobado además por script en el archivo de Blender:

- Ningún objeto con nombre de control lineal de carrera; cinco perillas rotativas.
- Tres B10K montados (RV2, RV3, RV4). El cuarto B10K comprado es repuesto y no aparece.
- RV1 y RV5 llevan el rótulo `A10K_log_PENDIENTE_COMPRA`.
- Solo giran RV2, RV3 y RV4, entre -150° y +150°. RV1 y RV5 no se mueven.
- Los difusores tienen relieve hexagonal (celdas más claras, nervios más oscuros) y extremos semicirculares.
- Las cinco perillas son metálicas.
- La emisión de los tres difusores LED es constante (1,1) en todo el video: los LED no reaccionan al audio.
- Dos parlantes WS-14595.
- Tapa cerrada en el primer y en el último fotograma.

## Observaciones

- Los rótulos de las perillas (NIVEL, GRAVES…) son pequeños en los planos generales; se leen en el paso cercano de 5 a 7 s.
- En los planos abiertos la tapa queda casi vertical y los parlantes y la placa de la T4-S3 se ven por detrás, parcialmente.
- En los planos finales (48 a 50 s) el vidrio de la pantalla refleja la luz y se ve más gris que negro.
  La vista `hardware/E5-perforadas/3d/ecualizador-E5-planta.png` los muestra completos.
- La pantalla es una propuesta de interfaz de 450 x 600 para la LilyGO T4-S3 en vertical; los valores salen de `firmware/lib/dsp`.
  El firmware de la T4-S3 no existe todavía.

## Lo que el video NO demuestra

1. Que la tira LED encienda: es de 12 V y el equipo solo tiene 5 V. El elevador del modelo es una propuesta.
2. Que el orden de color sea correcto: la tira publica BRG y el firmware usa `NEO_GRB`.
3. Que el enlace UART entre el ESP32 y la T4-S3 funcione: no está en el esquema ni en el firmware.
4. Que los dos parlantes suenen: falta decidir cómo se alimentan las entradas L y R del PAM8403.
5. Que los imanes sostengan la tapa con el peso de parlantes y pantalla.
6. Que las piezas quepan: varias cotas son conservadoras o supuestas (`hardware/E5-perforadas/3d/validacion-3d.json`).
7. Que RV1 y RV5 puedan ser los P-20K comprados: son de 20 kΩ, no de 10 kΩ.
