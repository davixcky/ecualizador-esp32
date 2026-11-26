# Auditoría de pines: ESP32 DevKit V1 de 30 pines (montaje E.5)

Decisión del 2026-11-24 (hardware/E5-perforadas/3d/README.md): el controlador principal pasa
del ESP32S de 38 pines al **ESP32 DevKit V1 de 30 pines**, y la pantalla SPI J4 se sustituye
por la placa CYD recibida (ESP32-3248S035 de 3,5"): los datos viajan por ESP-NOW y el UART2
queda solo de respaldo. Esta auditoría comprueba que todos los GPIO que usa el firmware
E.4/E.5 existen en el encabezado del DevKit V1 de 30 pines.

## GPIO expuestos en el DevKit V1 de 30 pines

Según los pinouts publicados del DOIT DevKit V1 ([projedefteri.com](https://projedefteri.com/en/blog/esp32-devkit-v1-pinout/),
[pinouthub.com](https://pinouthub.com/esp32-dev-kit-v1/), [prototypeguru.com](https://prototypeguru.com/esp32-pinout/)):

```
GPIO: 1 (TX0), 2, 3 (RX0), 4, 5, 12, 13, 14, 15, 16 (RX2), 17 (TX2),
      18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36 (VP), 39 (VN)
```

Respecto al de 38 pines **faltan GPIO0 y GPIO6–GPIO11**: GPIO0 queda solo en el botón BOOT
(sin pin de encabezado) y GPIO6–11 van al flash interno (tampoco eran usables en el de 38).

## Pines que usa la configuración E.4 (la que hereda `e5cyd`)

| GPIO | Función E.4 (`-e e4`) | Función E.5 (`-e e5cyd`) | ¿Existe en el 30 pines? |
|-----:|---|---|---|
| 35 | ADC VREF (1,65 V) | igual | Sí |
| 39 (VN) | ADC detector de graves | igual | Sí |
| 36 (VP) | ADC detector de medios | igual | Sí |
| 32 | ADC detector de agudos | igual | Sí |
| 34 | ADC salida ecualizada (FFT) | igual | Sí |
| 19 | TFT_CS (ST7789V2) | libre (sin TFT) | Sí |
| 21 | TFT_DC | libre | Sí |
| 25 | TFT_RST | libre | Sí |
| 23 | TFT_MOSI (VSPI) | libre | Sí |
| 18 | TFT_SCK (VSPI) | libre | Sí |
| 22 | TFT_BL | libre | Sí |
| 5 | NeoPixel (tira WS2811) | igual | Sí |
| 13 | Pulsador VISTA (SW1) | igual (sin efecto: la CYD tiene una sola vista) | Sí |
| 17 (TX2) | — libre — | UART2 TX → P1 RX (GPIO3) del CYD | Sí |
| 16 (RX2) | — libre — | UART2 RX ← P1 TX (GPIO1) del CYD | Sí |

Notas:

- **GPIO16 y GPIO17 quedan libres en E.4** (ningún `#define` los usa) y en `e5cyd` se
  reservan para el enlace UART2 con la CYD, como pide la decisión del 2026-11-24.
- Todas las entradas analógicas están en **ADC1** (35, 39, 36, 32, 34): siguen funcionando
  con el Wi-Fi activo y las cuatro de solo-entrada (34–39) se usan solo como entradas.
- **GPIO5 es pin de arranque (strapping)**: fija el flanco de la SDIO al arrancar. Como
  salida hacia la tira NeoPixel no da problema (igual que en E.3/E.4); solo hay que evitar
  que la tira lo cargue a nivel bajo durante el reinicio.
- **GPIO12 (strapping de MTDI)** no se usa: bien, porque alto en el arranque cambia la
  tensión del flash y la placa no arranca.
- **GPIO0 no tiene pin en el encabezado** del 30 pines, pero el firmware no lo usa; el
  botón BOOT de la placa lo cubre para programar.

## Conclusión

**Compatible sin reasignar nada.** Los 13 GPIO de la configuración E.4 y los 2 del enlace
UART existen todos en el encabezado del DevKit V1 de 30 pines; los GPIO ausentes respecto
al de 38 pines (0 y 6–11) no los usa el firmware. En `e5cyd` quedan además libres los seis
pines de la TFT (18, 19, 21, 22, 23, 25).

**Advertencia de honestidad:** el esquema maestro E.5
(`hardware/E5-perforadas/proyecto/ecualizador-perforadas.kicad_sch`) ya dibuja (2026-11-25) el
DevKit V1 de 30 pines con este mapa y el header J7 (+5V/GND + UART2 de respaldo, marcado
PROPUESTO porque el enlace no se ha probado en el montaje real). El esquemático histórico
D.3 (`hardware/ecualizador.kicad_sch`) sigue dibujando la Waveshare SPI en J4 y el ESP32 de
38 pines a propósito, como registro de esa revisión. La pantalla recibida es la
ESP32-3248S035 de 3,5" (no la ESP32-2432S028 prevista; firmware/include/enlace_cyd.h) y el
DevKit V1 ya está en mano, pendiente de medir con calibre
(hardware/E5-perforadas/3d/medidas-componentes.json).
