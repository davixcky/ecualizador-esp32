// Dibuja las pantallas de la TFT en el PC con el mismo código del firmware (lib/interfaz y
// lib/dsp) a partir de una señal sintética de música, y las guarda como PPM de 320 × 170.
// Comprueba además que dibujar por franjas de 40 píxeles (como en el ESP32) da la misma imagen
// que dibujar sobre un lienzo completo.
//   make pantallas        # escribe salida/*.ppm y ../../img/ui-tft-*.png
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "interfaz.h"

using namespace interfaz;

// "Música": bajo de 82 Hz con armónicos, acorde en medios, platillo de 6 kHz (que el filtro
// antialiasing atenúa) y ruido, tal como llega al pin GPIO33 (VREF + señal, cuantizada a 12 bits).
static void senal(float* v, float t0) {
  const struct { float a, f; } tonos[] = {{0.30f, 82.4f}, {0.12f, 164.8f}, {0.07f, 247.2f}, {0.10f, 440.0f},
                                          {0.08f, 554.4f}, {0.06f, 659.3f}, {0.035f, 1318.5f}, {0.02f, 2637.0f},
                                          {0.012f, 3520.0f}};
  srand(11);
  for (int i = 0; i < dsp::N; ++i) {
    const double t = t0 + i / dsp::FS;
    double x = 1.65;
    for (auto& k : tonos) x += k.a * sin(2 * M_PI * k.f * t + k.f);
    x += 0.004 * ((rand() % 2001) / 1000.0 - 1.0);
    v[i] = lround(x / 3.3 * 4095) * 3.3f / 4095;
  }
}

static Datos ejemplo() {
  static float v[dsp::N], trabajo[2 * dsp::N];
  Datos d{};
  senal(v, 0.0f);
  dsp::analizar(v, d.esp, trabajo);
  // picos retenidos un poco por encima del nivel actual
  for (int j = 0; j < dsp::BARRAS; ++j) d.barras_pico_db[j] = d.esp.barras_db[j] + 3.0f + 3.0f * ((j * 7) % 5) / 4;
  const float mv[3] = {420.0f, 205.0f, 46.0f};
  for (int b = 0; b < 3; ++b) {
    d.banda_mv[b] = mv[b];
    d.banda_db[b] = dsp::nivel_db(mv[b]);
    d.banda_pico_db[b] = d.banda_db[b] + 4.0f;
  }
  int k0 = 0;
  for (int i = 1; i < dsp::N - ANCHO; ++i)
    if (v[i - 1] < 1.65f && v[i] >= 1.65f) {
      k0 = i;
      break;
    }
  for (int i = 0; i < ANCHO; ++i) d.onda_v[i] = v[k0 + i] - 1.65f;
  d.recorte = false;
  d.wifi = true;
  d.clientes = 1;
  d.ip = "192.168.4.1";
  d.version = "fw-v1.0.0";
  return d;
}

static bool guardar(const char* ruta, const uint16_t* px) {
  FILE* f = fopen(ruta, "wb");
  if (!f) return false;
  fprintf(f, "P6\n%d %d\n255\n", ANCHO, ALTO);
  for (int k = 0; k < ANCHO * ALTO; ++k) {
    uint16_t c = px[k];
    uint8_t rgb[3] = {(uint8_t)((c >> 11) * 255 / 31), (uint8_t)(((c >> 5) & 63) * 255 / 63),
                      (uint8_t)((c & 31) * 255 / 31)};
    fwrite(rgb, 1, 3, f);
  }
  fclose(f);
  return true;
}

int main(int argc, char** argv) {
  const char* dir = argc > 1 ? argv[1] : "salida";
  struct { Vista v; const char* nombre; bool clip; } lista[] = {
      {BANDAS, "bandas", false}, {ESPECTRO, "espectro", false}, {ONDA, "onda", false},
      {ARRANQUE, "arranque", false}, {BANDAS, "recorte", true}};
  Datos d = ejemplo();
  printf("Señal de ejemplo: %.1f dBFS, tono dominante %.1f Hz\n", d.esp.rms_dbfs, d.esp.pico_hz);
  GFXcanvas16 completo(ANCHO, ALTO);
  const int alto_franja = 34;
  Franja franja(alto_franja);
  static uint16_t compuesta[ANCHO * ALTO];
  int fallos = 0;
  for (auto& e : lista) {
    d.recorte = e.clip;
    dibujar(completo, e.v, d);
    for (int y0 = 0; y0 < ALTO; y0 += alto_franja) {
      franja.origen(y0);
      dibujar(franja, e.v, d);
      memcpy(compuesta + y0 * ANCHO, franja.getBuffer(), sizeof(uint16_t) * ANCHO * alto_franja);
    }
    const bool igual = memcmp(compuesta, completo.getBuffer(), sizeof compuesta) == 0;
    fallos += !igual;
    char ruta[256];
    snprintf(ruta, sizeof ruta, "%s/%s.ppm", dir, e.nombre);
    if (!guardar(ruta, completo.getBuffer())) {
      fprintf(stderr, "No se pudo escribir %s\n", ruta);
      return 1;
    }
    printf("%-9s franjas %s  %s\n", e.nombre, igual ? "iguales" : "DISTINTAS", ruta);
  }
  return fallos ? 1 : 0;
}
