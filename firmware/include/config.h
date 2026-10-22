// Pines y constantes del ecualizador. Los pines coinciden con el esquemático
// (hardware/ecualizador.kicad_sch) y con herramientas/circuito.py.
#pragma once

// ---- entradas analógicas (todas en ADC1: el ADC2 no funciona con Wi-Fi activo)
#define PIN_VREF 36     // GPIO36 (VP), ADC1_CH0: VREF = 1,65 V
#define PIN_GRAVES 34   // GPIO34, ADC1_CH6: detector de graves (ADC_G)
#define PIN_MEDIOS 35   // GPIO35, ADC1_CH7: detector de medios (ADC_M)
#define PIN_AGUDOS 32   // GPIO32, ADC1_CH4: detector de agudos (ADC_A)
#define PIN_FFT 33      // GPIO33, ADC1_CH5: salida ecualizada tras el antialiasing (ADC_FFT)

// ---- pantalla Waveshare 1,9 pulgadas ST7789V2 (SPI por VSPI)
#define TFT_CS 5
#define TFT_DC 21
#define TFT_RST 22
#define TFT_MOSI 23
#define TFT_SCK 18
#define TFT_BL 19
#define TFT_MISO -1
#define PIN_NEOPIXEL 25
#define NEOPIXEL_CANTIDAD 12
#define NEOPIXEL_BRILLO 32
#define TFT_SPI_HZ 40000000

// ---- pulsador de vista (a GND, pull-up interno)
#define PIN_BOTON 27

// ---- Wi-Fi: punto de acceso propio (no necesita router)
#define WIFI_SSID "Ecualizador-ESP32"
#define WIFI_CLAVE "electronica2"

// ---- muestreo
#define MUESTREO_HZ 20000   // fs: Nyquist en 10 kHz; el filtro de 4,95 kHz atenúa 19 dB a 15 kHz
#define PROMEDIO_DET 8      // lecturas promediadas de cada detector

#ifndef FW_VERSION
#define FW_VERSION "fw-dev"
#endif
