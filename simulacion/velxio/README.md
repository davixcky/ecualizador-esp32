# Demostración de filtros en Velxio

1. Abrir https://velxio.dev/editor y cerrar el selector inicial con Cancel.
2. Elegir **File → Import project** y abrir uno de los tres `.vlx`.
3. Seleccionar **Circuit** y minimizar el panel lateral si hace falta. El motor SPICE arranca con el circuito analógico; no hay firmware que compilar.
4. Leer de arriba hacia abajo: graves, medios y agudos. El generador superior excita PRE; el inferior fija VREF en 1,65 V.
5. Cambiar entre los archivos de 100 Hz, 1 kHz y 8 kHz. También se puede editar la frecuencia del generador PRE con sus propiedades.

Los tres casos se ejecutaron en velxio.dev el 22 de octubre de 2026. Las capturas están en `../../img/velxio-*Hz.png`; `validacion.json` conserva lecturas y fecha. La prueba exige predominio de la banda correspondiente.

| Tono | Graves RMS | Medios RMS | Agudos RMS |
|---|---:|---:|---:|
| 100 Hz | 63,17 mV | 4,65 mV | 0,22 mV |
| 1 kHz | 6,11 mV | 63,23 mV | 4,51 mV |
| 8 kHz | 0,64 mV | 6,15 mV | 68,31 mV |

**Alcance:** R y C corresponden al esquema, pero los operacionales son ideales. Las lecturas son las que muestra la ventana transitoria del simulador; no son medidas físicas ni un patrón de amplitud estacionaria. No se simulan aquí el ESP32, la Waveshare, la tira ni la cadena completa. No se encontró un modelo ST7789V2 de 170 × 320 en el catálogo de código abierto inspeccionado. El firmware real está compilado y su interfaz se prueba por separado.

Regenerar los archivos: `python3 herramientas/generar_velxio.py` desde la raíz del repositorio. La validación del MCP6004 aproximado y de la cadena completa se ejecuta con `.venv/bin/python herramientas/simulacion.py`.

## Ensayo de los NeoPixel

Importar `led-animado.vlx` y pulsar Run. Velxio compila el programa ESP32 con Adafruit NeoPixel y recorre 12 LED por GPIO25, un paso cada 160 ms. Cuatro posiciones son naranjas, cuatro verdes y cuatro cian. El brillo es 32/255. El código editable también está en `led-ensayo.ino`.

Es un patrón de prueba sin audio. La adaptación AHCT y el consumo de la tira no están modelados; usar el esquema real para el montaje. El firmware principal conserva su iluminación fija durante la adquisición. `validacion-led.json` registra la ejecución de los 12 pasos y el cambio de estado de los LED.

## Cadena integrada con ESP32 y pantalla

Los casos `integrado-100Hz.vlx`, `integrado-1000Hz.vlx` e `integrado-8000Hz.vlx` conectan la cadena analógica al ESP32 y una TFT ILI9341. Abrir **https://velxio.dev/editor?esp32sim=qemu**, importar y ejecutar. La [guía INTEGRADO.md](INTEGRADO.md) explica las equivalencias con el esquema y las mediciones. La selectividad se comprueba hasta la pantalla; la FFT no está calibrada en frecuencia y el modelo no incluye potencia ni adaptación LED.

### Diagnóstico anterior del motor JavaScript

Los archivos `e2e-*.vlx` conectan filtros a un programa de diagnóstico RMS y a la tira. La ejecución inicial con el motor JavaScript devolvía 2047 constante; `validacion-e2e.json` conserva ese resultado histórico. Se identificó que ese motor aproxima la onda del ADC a una sola muestra. Usar QEMU para la adquisición de ondas. Los proyectos `integrado-*.vlx` y sus registros son la prueba actual con pantalla.
