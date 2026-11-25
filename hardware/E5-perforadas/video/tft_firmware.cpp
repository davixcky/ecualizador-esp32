// Calcula, con el MISMO código del firmware (lib/dsp y los tipos de lib/interfaz), los valores que
// la pantalla muestra en cada fotograma. Entrada: .trabajo/tft-entrada.bin (por fotograma: int32 vista,
// 3 float mV de los detectores, 1024 float con las tensiones del bloque ADC a 20 kS/s).
// Salida: binario de float32 con los 33 bordes de barra y una fila por fotograma.
// Lo compila y ejecuta generar_tft.py, que dibuja la interfaz de la ESP32-3248S035 de 3,5"
// (320 x 480 en vertical, dibujada a 1,5x: 480 x 720).
#include <stdio.h>
#include <string.h>

#include "interfaz.h"

using namespace interfaz;

int main(int argc, char** argv) {
  if (argc < 4) return 2;
  FILE* f = fopen(argv[1], "rb");
  if (!f) return 3;
  const float dt = 1.0f / atof(argv[3]);
  static float v[dsp::N], trabajo[2 * dsp::N];
  static dsp::Retencion ret_banda[3], ret_barra[dsp::BARRAS];
  Datos d{};
  d.wifi = true;
  d.clientes = 0;
  d.ip = "192.168.4.1";
  d.version = "fw-dev";
  int32_t vista;
  float mv[3];
  int n = 0;
  FILE* o = fopen(argv[2], "wb");
  if (!o) return 4;
  float bordes[dsp::BARRAS + 1];
  for (int j = 0; j <= dsp::BARRAS; ++j) bordes[j] = dsp::borde_barra(j);
  fwrite(bordes, sizeof(float), dsp::BARRAS + 1, o);
  while (fread(&vista, 4, 1, f) == 1 && fread(mv, 4, 3, f) == 3 && fread(v, 4, dsp::N, f) == (size_t)dsp::N) {
    const float vref = 1.65f;
    for (int b = 0; b < 3; ++b) {
      d.banda_mv[b] = dsp::nivel_mv(vref + mv[b] / 1000.0f, vref);
      d.banda_db[b] = dsp::nivel_db(d.banda_mv[b]);
      d.banda_pico_db[b] = ret_banda[b].actualizar(d.banda_db[b], dt);
    }
    dsp::analizar(v, d.esp, trabajo);
    for (int j = 0; j < dsp::BARRAS; ++j) d.barras_pico_db[j] = ret_barra[j].actualizar(d.esp.barras_db[j], dt);
    int k0 = 0;
    for (int i = 1; i < dsp::N - ANCHO; ++i)
      if (v[i - 1] < vref && v[i] >= vref) { k0 = i; break; }
    for (int i = 0; i < ANCHO; ++i) d.onda_v[i] = v[k0 + i] - vref;
    d.recorte = d.esp.recorte;
    // Fila de valores: vista, recorte, 3 dB, 3 picos, 3 mV, 32 barras, 32 picos, pico_hz, rms_dbfs.
    float fila[2 + 9 + 2 * dsp::BARRAS + 2];
    int k = 0;
    fila[k++] = (float)vista;
    fila[k++] = d.recorte ? 1.0f : 0.0f;
    for (int b = 0; b < 3; ++b) fila[k++] = d.banda_db[b];
    for (int b = 0; b < 3; ++b) fila[k++] = d.banda_pico_db[b];
    for (int b = 0; b < 3; ++b) fila[k++] = d.banda_mv[b];
    for (int j = 0; j < dsp::BARRAS; ++j) fila[k++] = d.esp.barras_db[j];
    for (int j = 0; j < dsp::BARRAS; ++j) fila[k++] = d.barras_pico_db[j];
    fila[k++] = d.esp.pico_hz;
    fila[k++] = d.esp.rms_dbfs;
    fwrite(fila, sizeof(float), k, o);
    ++n;
  }
  fclose(o);
  fclose(f);
  printf("%d fotogramas de pantalla\n", n);
  return 0;
}
