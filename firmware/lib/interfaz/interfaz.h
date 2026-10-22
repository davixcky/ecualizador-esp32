// Pantallas de la TFT de 320 × 170. Solo dibujan sobre un Adafruit_GFX: en el ESP32 se dibujan
// por franjas (clase Franja) que se envían una tras otra por SPI, y en el PC sobre un lienzo
// completo para generar las imágenes del documento (test/pantallas.cpp).
#pragma once
#include <Adafruit_GFX.h>

#include "dsp.h"

namespace interfaz {

constexpr int ANCHO = 320;
constexpr int ALTO = 170;

enum Vista { BANDAS, ESPECTRO, ONDA, ARRANQUE, NUM_VISTAS = 3 };

struct Datos {
  float banda_mv[3];           // pico de cada banda medido por los detectores (mV)
  float banda_db[3];           // el mismo nivel en dB respecto a 0,8 V
  float banda_pico_db[3];      // retención de picos de las barras de banda
  dsp::Espectro esp;           // espectro de la salida ecualizada
  float barras_pico_db[dsp::BARRAS];
  float onda_v[ANCHO];         // forma de onda (V respecto a VREF), una muestra por columna
  bool recorte;                // CLIP: señal fuera de la zona lineal del ADC
  bool wifi;
  int clientes;                // teléfonos conectados al punto de acceso
  const char* ip;
  const char* version;
};

// Dibuja la vista completa (fondo incluido) sobre g.
void dibujar(Adafruit_GFX& g, Vista v, const Datos& d);

// Lienzo de ANCHO × alto que representa la franja [y0, y0 + alto) de la pantalla. Se presenta
// ante Adafruit GFX con la altura completa (así no descarta el texto que cae fuera de la
// franja) y recorta cada píxel a la franja al escribirlo en su memoria.
class Franja : public GFXcanvas16 {
 public:
  explicit Franja(int16_t alto) : GFXcanvas16(ANCHO, alto), alto_(alto) { _height = ALTO; }
  void origen(int16_t y0) { y0_ = y0; }
  int16_t alto() const { return alto_; }
  void drawPixel(int16_t x, int16_t y, uint16_t c) override {
    y -= y0_;
    if (x >= 0 && x < ANCHO && y >= 0 && y < alto_) getBuffer()[y * ANCHO + x] = c;
  }
  void drawFastVLine(int16_t x, int16_t y, int16_t h, uint16_t c) override {
    for (int16_t i = 0; i < h; ++i) drawPixel(x, y + i, c);
  }
  void drawFastHLine(int16_t x, int16_t y, int16_t w, uint16_t c) override {
    y -= y0_;
    if (y < 0 || y >= alto_) return;
    const int16_t xa = x < 0 ? 0 : x, xb = x + w > ANCHO ? ANCHO : x + w;
    uint16_t* fila = getBuffer() + y * ANCHO;
    for (int16_t i = xa; i < xb; ++i) fila[i] = c;
  }
  void fillRect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t c) override {
    for (int16_t j = 0; j < h; ++j) drawFastHLine(x, y + j, w, c);
  }
  void fillScreen(uint16_t c) override {
    uint16_t* b = getBuffer();
    for (int32_t i = 0; i < (int32_t)ANCHO * alto_; ++i) b[i] = c;
  }

 private:
  int16_t y0_ = 0;
  int16_t alto_;
};

}  // namespace interfaz
