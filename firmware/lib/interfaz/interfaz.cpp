#include "interfaz.h"

#include <Fonts/FreeSans9pt7b.h>
#include <Fonts/FreeSansBold12pt7b.h>
#include <Fonts/FreeSansBold9pt7b.h>
#include <math.h>
#include <stdio.h>

namespace interfaz {

// ---------------------------------------------------------------- colores (RGB565)
static constexpr uint16_t rgb(uint8_t r, uint8_t g, uint8_t b) {
  return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
}
static constexpr uint16_t FONDO = rgb(8, 10, 20);
static constexpr uint16_t CABECERA = rgb(18, 22, 40);
static constexpr uint16_t REJILLA = rgb(38, 44, 66);
static constexpr uint16_t TENUE = rgb(120, 128, 150);
static constexpr uint16_t TEXTO = rgb(235, 238, 245);
static constexpr uint16_t ROJO = rgb(235, 60, 60);

struct ColorBanda {
  uint8_t r, g, b;
};
static constexpr ColorBanda BANDA[3] = {{255, 122, 61}, {61, 220, 132}, {51, 181, 255}};
static const char* const NOMBRE[3] = {"GRAVES", "MEDIOS", "AGUDOS"};
static const char* const RANGO[3] = {"< 230 Hz", "0,4-2,3 kHz", "> 4,1 kHz"};

static uint16_t escalar(ColorBanda c, float k) {
  return rgb((uint8_t)(c.r * k), (uint8_t)(c.g * k), (uint8_t)(c.b * k));
}

// Color de una frecuencia: mezcla los colores de las bandas en escala logarítmica.
static ColorBanda color_frecuencia(float hz) {
  const float t = (log10f(hz) - log10f(60.0f)) / (log10f(5000.0f) - log10f(60.0f));
  const float u = t < 0 ? 0 : (t > 1 ? 1 : t);
  const ColorBanda& a = u < 0.5f ? BANDA[0] : BANDA[1];
  const ColorBanda& b = u < 0.5f ? BANDA[1] : BANDA[2];
  const float k = u < 0.5f ? u * 2 : (u - 0.5f) * 2;
  return {(uint8_t)(a.r + (b.r - a.r) * k), (uint8_t)(a.g + (b.g - a.g) * k), (uint8_t)(a.b + (b.b - a.b) * k)};
}

// ---------------------------------------------------------------- texto
static void texto(Adafruit_GFX& g, const char* t, int x, int y, uint16_t color, const GFXfont* f = nullptr,
                  uint8_t tam = 1) {
  g.setFont(f);
  g.setTextSize(tam);
  g.setTextColor(color);
  g.setCursor(x, y);
  g.print(t);
}

static int ancho_texto(Adafruit_GFX& g, const char* t, const GFXfont* f, uint8_t tam = 1) {
  int16_t x1, y1;
  uint16_t w, h;
  g.setFont(f);
  g.setTextSize(tam);
  g.getTextBounds(t, 0, 0, &x1, &y1, &w, &h);
  return w;
}

static void texto_centrado(Adafruit_GFX& g, const char* t, int xc, int y, uint16_t color, const GFXfont* f = nullptr,
                           uint8_t tam = 1) {
  texto(g, t, xc - ancho_texto(g, t, f, tam) / 2, y, color, f, tam);
}

static void texto_derecha(Adafruit_GFX& g, const char* t, int xd, int y, uint16_t color, const GFXfont* f = nullptr,
                          uint8_t tam = 1) {
  texto(g, t, xd - ancho_texto(g, t, f, tam), y, color, f, tam);
}

// número con coma decimal
static void fmt(char* b, size_t n, const char* f, float v) {
  snprintf(b, n, f, v);
  for (char* p = b; *p; ++p)
    if (*p == '.') *p = ',';
}

// ---------------------------------------------------------------- piezas comunes
static void icono_wifi(Adafruit_GFX& g, int x, int y, bool activo, int clientes) {
  const uint16_t c = activo ? (clientes > 0 ? rgb(61, 220, 132) : TEXTO) : REJILLA;
  for (int r = 4; r <= 12; r += 4) {
    for (int a = -45; a <= 45; a += 3) {
      const float ang = (a - 90) * (float)M_PI / 180.0f;
      g.drawPixel(x + (int)lroundf(r * cosf(ang)), y + (int)lroundf(r * sinf(ang)), c);
    }
  }
  g.fillCircle(x, y, 1, c);
}

static void cabecera(Adafruit_GFX& g, const char* titulo, const char* subtitulo, const Datos& d) {
  g.fillRect(0, 0, ANCHO, 26, CABECERA);
  // logotipo: tres barras de colores
  for (int i = 0; i < 3; ++i) g.fillRoundRect(8 + i * 6, 16 - (i == 1 ? 10 : (i == 0 ? 6 : 8)), 4,
                                              (i == 1 ? 12 : (i == 0 ? 8 : 10)), 1, escalar(BANDA[i], 1));
  texto(g, titulo, 30, 19, TEXTO, &FreeSansBold9pt7b);
  if (subtitulo) texto(g, subtitulo, 30 + ancho_texto(g, titulo, &FreeSansBold9pt7b) + 8, 11, TENUE);
  if (d.recorte) {
    g.fillRoundRect(244, 5, 40, 16, 4, ROJO);
    texto_centrado(g, "CLIP", 264, 9, TEXTO, nullptr, 1);
  }
  icono_wifi(g, 302, 19, d.wifi, d.clientes);
  g.drawFastHLine(0, 26, ANCHO, REJILLA);
}

// Barra de segmentos tipo LED: nivel y pico en dB entre db_min y 0.
static void barra_segmentos(Adafruit_GFX& g, int x, int y_abajo, int w, int segs, int alto_seg, float db,
                            float pico_db, float db_min, ColorBanda c) {
  const float frac = (db - db_min) / -db_min;
  const int encendidos = (int)lroundf((frac < 0 ? 0 : (frac > 1 ? 1 : frac)) * segs);
  const float fp = (pico_db - db_min) / -db_min;
  const int pico = (int)lroundf((fp < 0 ? 0 : (fp > 1 ? 1 : fp)) * segs) - 1;
  for (int s = 0; s < segs; ++s) {
    const int yy = y_abajo - (s + 1) * (alto_seg + 1) + 1;
    uint16_t col;
    if (s < encendidos)
      col = escalar(c, 0.55f + 0.45f * s / (segs - 1));
    else
      col = escalar(c, 0.13f);
    if (s == pico && pico >= encendidos) col = TEXTO;
    g.fillRect(x, yy, w, alto_seg, col);
  }
}

// ---------------------------------------------------------------- vista de bandas
static void vista_bandas(Adafruit_GFX& g, const Datos& d) {
  char b[32];
  cabecera(g, "ECUALIZADOR", "3 bandas", d);
  const int y_abajo = 196, segs = 22, alto_seg = 5;
  for (int i = 0; i < 3; ++i) {
    const int x = 12 + i * 70;
    fmt(b, sizeof b, "%.0f dB", d.banda_db[i]);
    texto_centrado(g, d.banda_db[i] <= dsp::PISO_DB ? "--" : b, x + 29, 50, TEXTO, &FreeSansBold9pt7b);
    barra_segmentos(g, x + 6, y_abajo, 46, segs, alto_seg, d.banda_db[i], d.banda_pico_db[i], -40.0f, BANDA[i]);
    texto_centrado(g, NOMBRE[i], x + 29, 202, escalar(BANDA[i], 1));
    texto_centrado(g, RANGO[i], x + 29, 214, TENUE);
    fmt(b, sizeof b, "%.0f mV", d.banda_mv[i]);
    texto_centrado(g, b, x + 29, 226, TEXTO);
  }
  // panel derecho: nivel global y tono dominante
  const int xp = 222;
  g.drawFastVLine(xp - 6, 32, 202, REJILLA);
  texto(g, "NIVEL", xp, 42, TENUE);
  const ColorBanda vu = {230, 230, 230};
  for (int s = 0; s < 20; ++s) {
    const float db = -40.0f + 2.0f * (s + 1);
    const int yy = 200 - (s + 1) * 7;
    const bool on = d.esp.rms_dbfs >= db - 1.0f;
    const ColorBanda c = s >= 18 ? ColorBanda{235, 60, 60} : (s >= 15 ? ColorBanda{240, 200, 60} : ColorBanda{61, 220, 132});
    g.fillRect(xp, yy, 14, 6, on ? escalar(c, 1) : escalar(c, 0.13f));
    (void)vu;
  }
  fmt(b, sizeof b, "%.1f", d.esp.rms_dbfs);
  texto(g, b, xp + 22, 70, TEXTO, &FreeSansBold12pt7b);
  texto(g, "dBFS", xp + 22, 84, TENUE);
  texto(g, "TONO", xp + 22, 110, TENUE);
  if (d.esp.pico_db > -50.0f) {
    if (d.esp.pico_hz >= 1000.0f)
      fmt(b, sizeof b, "%.2f", d.esp.pico_hz / 1000.0f);
    else
      fmt(b, sizeof b, "%.0f", d.esp.pico_hz);
    texto(g, b, xp + 22, 132, TEXTO, &FreeSansBold9pt7b);
    texto(g, d.esp.pico_hz >= 1000.0f ? "kHz" : "Hz", xp + 22, 146, TENUE);
  } else {
    texto(g, "--", xp + 22, 132, TEXTO, &FreeSansBold9pt7b);
  }
  // mini espectro
  for (int j = 0; j < dsp::BARRAS; j += 2) {
    const float db = fmaxf(d.esp.barras_db[j], d.esp.barras_db[j + 1]);
    const int h = (int)lroundf(fmaxf(0, (db + 60.0f) / 60.0f) * 40);
    const ColorBanda c = color_frecuencia(sqrtf(dsp::borde_barra(j) * dsp::borde_barra(j + 2)));
    g.fillRect(xp + 22 + (j / 2) * 5, 200 - h, 4, h, escalar(c, 1));
  }
  g.drawFastHLine(xp + 22, 201, 80, REJILLA);
  texto(g, "ESPECTRO", xp + 22, 206, TENUE);
}

// ---------------------------------------------------------------- vista de espectro
// Posición de una frecuencia sobre el eje de barras (las barras no son exactamente logarítmicas
// por debajo de 300 Hz: cada una ocupa un bin de la FFT).
static int x_frecuencia(float hz, int x0, int x1) {
  const float paso = (float)(x1 - x0) / dsp::BARRAS;
  for (int j = 0; j < dsp::BARRAS; ++j) {
    const float a = dsp::borde_barra(j), b = dsp::borde_barra(j + 1);
    if (hz < b || j == dsp::BARRAS - 1) {
      float t = (log10f(hz) - log10f(a)) / (log10f(b) - log10f(a));
      t = t < 0 ? 0 : (t > 1 ? 1 : t);
      return x0 + (int)lroundf((j + t) * paso);
    }
  }
  return x1;
}

static void vista_espectro(Adafruit_GFX& g, const Datos& d) {
  char b[48];
  char hz[16];
  if (d.esp.pico_hz >= 1000.0f)
    fmt(hz, sizeof hz, "%.2f kHz", d.esp.pico_hz / 1000.0f);
  else
    fmt(hz, sizeof hz, "%.0f Hz", d.esp.pico_hz);
  snprintf(b, sizeof b, "pico %s", d.esp.pico_db > -50.0f ? hz : "--");
  cabecera(g, "ESPECTRO", b, d);
  const int x0 = 30, x1 = 314, ya = 36, yb = 206;
  // fondos de las tres bandas del ecualizador
  const float cortes[4] = {dsp::F_MIN, 300.0f, 3100.0f, dsp::F_MAX};
  for (int i = 0; i < 3; ++i) {
    const int xa = x_frecuencia(cortes[i], x0, x1), xb = x_frecuencia(cortes[i + 1], x0, x1);
    g.fillRect(xa, ya, xb - xa, yb - ya, escalar(BANDA[i], 0.07f));
    texto_centrado(g, NOMBRE[i], (xa + xb) / 2, ya + 10, escalar(BANDA[i], 0.6f));
  }
  // rejilla de dB
  for (int db = 0; db >= -60; db -= 10) {
    const int y = ya + (int)lroundf(-db / 60.0f * (yb - ya));
    for (int x = x0; x < x1; x += 4) g.drawPixel(x, y, REJILLA);
    snprintf(b, sizeof b, "%d", db);
    texto_derecha(g, b, x0 - 4, y + 3, TENUE);
  }
  // barras
  const float paso = (float)(x1 - x0) / dsp::BARRAS;
  const int segs = 34, alto_seg = (yb - ya) / segs - 1;
  for (int j = 0; j < dsp::BARRAS; ++j) {
    const int x = x0 + (int)lroundf(j * paso) + 1;
    const ColorBanda c = color_frecuencia(sqrtf(dsp::borde_barra(j) * dsp::borde_barra(j + 1)));
    const float frac = (d.esp.barras_db[j] + 60.0f) / 60.0f;
    const int n = (int)lroundf((frac < 0 ? 0 : (frac > 1 ? 1 : frac)) * segs);
    for (int s = 0; s < n; ++s) {
      const int yy = yb - (s + 1) * (alto_seg + 1);
      g.fillRect(x, yy, (int)paso - 2, alto_seg, escalar(c, 0.5f + 0.5f * s / segs));
    }
    const float fp = (d.barras_pico_db[j] + 60.0f) / 60.0f;
    if (fp > 0.02f) {
      const int yy = yb - (int)lroundf((fp > 1 ? 1 : fp) * (yb - ya));
      g.fillRect(x, yy, (int)paso - 2, 2, TEXTO);
    }
  }
  g.drawFastHLine(x0, yb + 1, x1 - x0, TENUE);
  // eje de frecuencia
  const struct { float f; const char* t; } marcas[] = {{50, "50"},   {100, "100"}, {200, "200"}, {500, "500"},
                                                        {1000, "1k"}, {2000, "2k"},  {4900, "5k"}};
  for (auto& m : marcas) {
    const int x = x_frecuencia(m.f, x0, x1);
    g.drawFastVLine(x, yb + 1, 4, TENUE);
    texto_centrado(g, m.t, x, yb + 7, TENUE);
  }
  texto(g, "Hz", x1 - 12, yb + 20, TENUE);
  texto(g, "dB", 4, ya - 1, TENUE);
  fmt(b, sizeof b, "%.1f dBFS", d.esp.rms_dbfs);
  texto(g, b, x0, yb + 20, TEXTO);
}

// ---------------------------------------------------------------- vista de forma de onda
static void vista_onda(Adafruit_GFX& g, const Datos& d) {
  char b[48];
  float vmin = 1e9f, vmax = -1e9f;
  for (int i = 0; i < ANCHO; ++i) {
    vmin = fminf(vmin, d.onda_v[i]);
    vmax = fmaxf(vmax, d.onda_v[i]);
  }
  fmt(b, sizeof b, "%.2f Vpp", vmax - vmin);
  cabecera(g, "OSCILOSCOPIO", b, d);
  const int x0 = 10, x1 = 310, ya = 34, yb = 214, ym = (ya + yb) / 2;
  for (int k = 0; k <= 10; ++k) {
    const int x = x0 + k * (x1 - x0) / 10;
    for (int y = ya; y <= yb; y += 3) g.drawPixel(x, y, REJILLA);
  }
  for (int k = 0; k <= 8; ++k) {
    const int y = ya + k * (yb - ya) / 8;
    for (int x = x0; x <= x1; x += 3) g.drawPixel(x, y, k == 4 ? TENUE : REJILLA);
  }
  // ±0,8 V a toda la altura; la onda se dibuja con un trazo de 2 píxeles
  const float esc = (yb - ya) / 2 / dsp::PLENA_ESCALA_V;
  int xa = x0, ya_ = ym - (int)lroundf(d.onda_v[0] * esc);
  for (int i = 1; i <= x1 - x0; ++i) {
    const int x = x0 + i;
    const int y = ym - (int)lroundf(d.onda_v[i] * esc);
    const ColorBanda c = {51, 181, 255};
    g.drawLine(xa, ya_, x, y, escalar(c, 1));
    g.drawLine(xa, ya_ + 1, x, y + 1, escalar(c, 0.6f));
    xa = x;
    ya_ = y;
  }
  texto(g, "0,2 V/div", x0, yb + 10, TENUE);
  texto(g, "1,5 ms/div", x0 + 80, yb + 10, TENUE);
  fmt(b, sizeof b, "%.1f dBFS", d.esp.rms_dbfs);
  texto_derecha(g, b, x1, yb + 10, TEXTO);
}

// ---------------------------------------------------------------- arranque
static void vista_arranque(Adafruit_GFX& g, const Datos& d) {
  // ecualizador decorativo de fondo
  for (int j = 0; j < 24; ++j) {
    const float h = 0.35f + 0.3f * sinf(j * 0.55f) + 0.2f * sinf(j * 1.7f);
    const ColorBanda c = color_frecuencia(60.0f * powf(5000.0f / 60.0f, j / 23.0f));
    const int x = 16 + j * 12;
    const int alto = (int)(h * 70);
    for (int s = 0; s < alto / 6; ++s) g.fillRect(x, 150 - s * 6, 9, 4, escalar(c, 0.35f + 0.65f * s * 6 / 70.0f));
  }
  texto_centrado(g, "ECUALIZADOR", ANCHO / 2, 70, TEXTO, &FreeSansBold12pt7b);
  texto_centrado(g, "3 bandas + analizador de espectro", ANCHO / 2, 92, TENUE, &FreeSans9pt7b);
  texto_centrado(g, "Electronica II  -  Universidad de la Costa", ANCHO / 2, 182, TENUE);
  char b[64];
  snprintf(b, sizeof b, "Wi-Fi: %s   %s", "Ecualizador-ESP32", d.version ? d.version : "");
  texto_centrado(g, b, ANCHO / 2, 198, TENUE);
  texto_centrado(g, "Boton: cambia la vista", ANCHO / 2, 222, escalar(BANDA[1], 1));
}

void dibujar(Adafruit_GFX& g, Vista v, const Datos& d) {
  g.fillScreen(FONDO);
  switch (v) {
    case BANDAS: vista_bandas(g, d); break;
    case ESPECTRO: vista_espectro(g, d); break;
    case ONDA: vista_onda(g, d); break;
    default: vista_arranque(g, d); break;
  }
}

}  // namespace interfaz
