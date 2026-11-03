// Pines y constantes del ecualizador. Los pines coinciden con el esquemático
// (hardware/ecualizador.kicad_sch) y con herramientas/circuito.py.
#pragma once

// ---- entradas analógicas (todas en ADC1: el ADC2 no funciona con Wi-Fi activo)
// PLACA_E2 (pio run -e e2): pines de la placa única E.2 (hardware/E2-placa-unica).
#ifdef PLACA_E2
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

// ---- pantalla Waveshare 1,9 pulgadas ST7789V2 (SPI por VSPI)
#ifdef PLACA_E2
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
#define TFT_BL 19
#define TFT_MISO -1
#ifdef PLACA_E2
#define PIN_NEOPIXEL 21
#else
#define PIN_NEOPIXEL 25
#endif
#define NEOPIXEL_CANTIDAD 12
#define NEOPIXEL_BRILLO 32
#define TFT_SPI_HZ 40000000

// ---- pulsador de vista (a GND, pull-up interno)
#ifdef PLACA_E2
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
