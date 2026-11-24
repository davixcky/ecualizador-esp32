// Pines y constantes del ecualizador. Los pines coinciden con el esquemático
// (hardware/ecualizador.kicad_sch) y con herramientas/circuito.py.
#pragma once

// ---- entradas analógicas (todas en ADC1: el ADC2 no funciona con Wi-Fi activo)
// PLACA_E2 (pio run -e e2): pines de la placa única E.2 (hardware/E2-placa-unica).
// PLACA_E5CYD (pio run -e e5cyd): montaje E.5 con DevKit V1 de 30 pines; conserva el mapa
// analógico de E.3/E.4 y sustituye la TFT SPI por el enlace UART con la pantalla CYD.
#if defined(PLACA_E3) || defined(PLACA_E4) || defined(PLACA_E5CYD)
#define PIN_VREF 35     // GPIO35, ADC1_CH7: VREF = 1,65 V
#define PIN_GRAVES 39   // GPIO39, ADC1_CH3: detector de graves (ADC_G)
#define PIN_MEDIOS 36   // GPIO36, ADC1_CH0: detector de medios (ADC_M)
#define PIN_AGUDOS 32   // GPIO32, ADC1_CH4: detector de agudos (ADC_A)
#define PIN_FFT 34      // GPIO34, ADC1_CH6: salida tras el antialiasing (ADC_FFT)
#elif defined(PLACA_E2)
#define PIN_VREF 32     // GPIO32, ADC1_CH4: VREF = 1,65 V
#define PIN_GRAVES 34   // GPIO34, ADC1_CH6: detector de graves (ADC_G)
#define PIN_MEDIOS 36   // GPIO36 (VP), ADC1_CH0: detector de medios (ADC_M)
#define PIN_AGUDOS 39   // GPIO39 (VN), ADC1_CH3: detector de agudos (ADC_A)
#define PIN_FFT 33      // GPIO33, ADC1_CH5: salida ecualizada tras el antialiasing (ADC_FFT)
#else
#define PIN_VREF 36     // GPIO36 (VP), ADC1_CH0: VREF = 1,65 V
#define PIN_GRAVES 34   // GPIO34, ADC1_CH6: detector de graves (ADC_G)
#define PIN_MEDIOS 35   // GPIO35, ADC1_CH7: detector de medios (ADC_M)
#define PIN_AGUDOS 32   // GPIO32, ADC1_CH4: detector de agudos (ADC_A)
#define PIN_FFT 33      // GPIO33, ADC1_CH5: salida ecualizada tras el antialiasing (ADC_FFT)
#endif

// ---- pantalla
// E.5 (PLACA_E5CYD): no hay TFT directa. La pantalla es la placa CYD en la tapa y recibe los
// datos por UART2 (ver enlace_cyd.h). PROPUESTA del 2026-11-24: el enlace aún no está en el
// esquemático, que sigue dibujando la Waveshare SPI en J4.
#ifdef PLACA_E5CYD
#define PIN_CYD_TX 17   // GPIO17, TX2 -> P1 RX (GPIO3) del CYD
#define PIN_CYD_RX 16   // GPIO16, RX2 <- P1 TX (GPIO1) del CYD
#else
// Pantalla Waveshare 1,9 pulgadas ST7789V2 (SPI por VSPI)
#if defined(PLACA_E3) || defined(PLACA_E4)
#define TFT_CS 19
#define TFT_DC 21
#define TFT_RST 25
#elif defined(PLACA_E2)
#define TFT_CS 25
#define TFT_DC 22
#define TFT_RST 5
#else
#define TFT_CS 5
#define TFT_DC 21
#define TFT_RST 22
#endif
#define TFT_MOSI 23
#define TFT_SCK 18
#if defined(PLACA_E3) || defined(PLACA_E4)
#define TFT_BL 22
#else
#define TFT_BL 19
#endif
#define TFT_MISO -1
#define TFT_SPI_HZ 40000000
#endif  // PLACA_E5CYD
#if defined(PLACA_E3) || defined(PLACA_E4) || defined(PLACA_E5CYD)
#define PIN_NEOPIXEL 5
#elif defined(PLACA_E2)
#define PIN_NEOPIXEL 21
#else
#define PIN_NEOPIXEL 25
#endif
#define NEOPIXEL_CANTIDAD 12
#define NEOPIXEL_BRILLO 32

// ---- pulsador de vista (a GND, pull-up interno)
#if defined(PLACA_E3) || defined(PLACA_E4) || defined(PLACA_E5CYD)
#define PIN_BOTON 13
#elif defined(PLACA_E2)
#define PIN_BOTON 4
#else
#define PIN_BOTON 27
#endif

// ---- Wi-Fi: punto de acceso propio (no necesita router)
#define WIFI_SSID "Ecualizador-ESP32"
#define WIFI_CLAVE "electronica2"

// ---- muestreo
#define MUESTREO_HZ 20000   // fs: Nyquist en 10 kHz; el filtro de 4,95 kHz atenúa 19 dB a 15 kHz
#define PROMEDIO_DET 8      // lecturas promediadas de cada detector

#ifndef FW_VERSION
#define FW_VERSION "fw-dev"
#endif
