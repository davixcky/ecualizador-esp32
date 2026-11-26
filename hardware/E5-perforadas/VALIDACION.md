# Validación de la variante modular E.5

- ERC del esquema maestro (regenerado el 2026-11-26 con U5 = ESP32 DevKit V1 de 30 pines, mapa `e5cyd`, sin J4/R30 y con J7): **0 errores y 7 avisos intencionales**, igual que la revisión anterior. Los siete avisos indican que las entradas A1–A7 no utilizadas del 74HCT245 están conectadas a GND; esto evita dejar entradas CMOS flotantes. Las salidas B1–B7 quedan sin conectar.
- El enlace de la pantalla ESP32-3248S035 queda dibujado como J7 (+5V/GND y UART2 de respaldo) marcado **PROPUESTO**: los datos viajan por ESP-NOW y ningún enlace se ha probado aún en el montaje real.
- Adaptación NeoPixel revisada con `74HCT245` DIP-20 a 5 V: DIR pin 1 = +5 V, /OE pin 19 = GND, A0 pin 2 = `LED_DATA` de 3,3 V y B0 pin 18 = `LED_5V`. La familia HCT tiene umbral TTL y reconoce la salida de 3,3 V del ESP32; no se sustituyó por HC.
- La división entre tarjetas no cambia la topología eléctrica ni los valores del modelo LM324.
- Simulación ngspice: los 25 casos del diseño vigente cumplen. El caso 13 conserva intencionalmente los valores históricos de Fase 1 y no cumple; se mantiene solo para documentar por qué se añadió el inversor de medios.
- VREF simulado: 1,6492 V.
- Respuesta plana simulada: rizado de 1,16 dB entre 20 Hz y 20 kHz.
- Entradas LM324 simuladas: 1,120 a 2,179 V, dentro del margen previsto con alimentación de 5 V.
- Atenuadores ADC simulados: RAW 1,121…2,179 V produce ADC 1,384…1,913 V.

La simulación y ERC no sustituyen la inspección de soldaduras ni las mediciones de cada tarjeta. La primera unidad debe probarse siguiendo la página 6 de `esquema-modular-perforadas.pdf`.
