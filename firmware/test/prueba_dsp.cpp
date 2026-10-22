// Prueba del procesamiento en el PC con señales sintéticas que pasan por el mismo modelo del
// ADC del ESP32 (12 bits, 0 a 3,3 V, ruido de ±2 LSB).
//   make prueba
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include <initializer_list>

#include "dsp.h"

static int fallos = 0;

static void comprobar(bool ok, const char* que, double valor, const char* criterio) {
  printf("  [%s] %-46s %10.3f   (%s)\n", ok ? "ok" : "FALLA", que, valor, criterio);
  if (!ok) ++fallos;
}

// Bloque de N muestras en el pin: VREF + suma de senoidales, cuantizado como el ADC.
static void bloque(float* v, const float* amp, const float* hz, int n_tonos, unsigned semilla = 1) {
  srand(semilla);
  for (int i = 0; i < dsp::N; ++i) {
    double x = 1.65;
    for (int k = 0; k < n_tonos; ++k) x += amp[k] * sin(2 * M_PI * hz[k] * i / dsp::FS + 0.3 * k);
    int crudo = (int)lround(x / 3.3 * 4095) + (rand() % 5) - 2;
    crudo = crudo < 0 ? 0 : (crudo > 4095 ? 4095 : crudo);
    v[i] = crudo * 3.3f / 4095;
  }
}

static int barra_de(float hz) {
  for (int j = 0; j < dsp::BARRAS; ++j)
    if (hz >= dsp::borde_barra(j) && hz < dsp::borde_barra(j + 1)) return j;
  return -1;
}

static int barra_maxima(const dsp::Espectro& e) {
  int m = 0;
  for (int j = 1; j < dsp::BARRAS; ++j)
    if (e.barras_db[j] > e.barras_db[m]) m = j;
  return m;
}

int main() {
  static float v[dsp::N], trabajo[2 * dsp::N];
  dsp::Espectro e;

  printf("Resolución: %.2f Hz por bin; barras de %.0f Hz a %.0f Hz\n", dsp::DF, dsp::F_MIN, dsp::F_MAX);

  printf("\n1) Tono de 1 kHz a −6 dBFS (0,4 V de pico)\n");
  {
    float a[] = {0.4f}, f[] = {1000};
    bloque(v, a, f, 1);
    dsp::analizar(v, e, trabajo);
    comprobar(fabsf(e.pico_hz - 1000) < 5, "frecuencia dominante (Hz)", e.pico_hz, "1000 ± 5 Hz");
    comprobar(lroundf(1000 / dsp::DF) == 51, "bin del tono", lroundf(1000 / dsp::DF), "bin 51 (996 Hz)");
    comprobar(fabsf(e.pico_db + 6.02f) < 0.5f, "nivel del pico (dB)", e.pico_db, "−6,0 ± 0,5 dB");
    comprobar(fabsf(e.rms_dbfs + 6.02f) < 0.3f, "nivel eficaz (dBFS)", e.rms_dbfs, "−6,0 ± 0,3 dBFS");
    comprobar(barra_maxima(e) == barra_de(1000), "barra más alta", barra_maxima(e), "la que contiene 1 kHz");
    comprobar(!e.recorte, "sin recorte", e.recorte, "falso");
  }

  printf("\n2) Tonos de 100 Hz y 4 kHz por separado\n");
  for (float hz : {100.0f, 4000.0f}) {
    float a[] = {0.3f}, f[] = {hz};
    bloque(v, a, f, 1, 7);
    dsp::analizar(v, e, trabajo);
    char t[64];
    snprintf(t, sizeof t, "barra más alta con %.0f Hz", hz);
    comprobar(barra_maxima(e) == barra_de(hz), t, barra_maxima(e), "la que contiene el tono");
    comprobar(fabsf(e.pico_hz - hz) < 10, "frecuencia dominante (Hz)", e.pico_hz, "± 10 Hz");
  }

  printf("\n3) Separación de dos tonos (150 Hz a −6 dB y 2 kHz a −20 dB)\n");
  {
    float a[] = {0.4f, 0.08f}, f[] = {150, 2000};
    bloque(v, a, f, 2, 3);
    dsp::analizar(v, e, trabajo);
    const float d150 = e.barras_db[barra_de(150)], d2k = e.barras_db[barra_de(2000)];
    comprobar(fabsf(d150 - d2k - 14.0f) < 1.5f, "diferencia entre las dos barras (dB)", d150 - d2k, "14 ± 1,5 dB");
    comprobar(e.barras_db[barra_de(600)] < -45, "barra de 600 Hz (sin señal)", e.barras_db[barra_de(600)], "< −45 dB");
  }

  printf("\n4) Silencio (solo ruido del ADC)\n");
  {
    float a[] = {0.0f}, f[] = {1000};
    bloque(v, a, f, 1, 5);
    dsp::analizar(v, e, trabajo);
    comprobar(e.rms_dbfs < -50, "nivel eficaz (dBFS)", e.rms_dbfs, "< −50 dBFS");
  }

  printf("\n5) Recorte: senoidal de 0,9 V de pico (sale de 0,15–2,45 V)\n");
  {
    float a[] = {0.9f}, f[] = {440};
    bloque(v, a, f, 1);
    dsp::analizar(v, e, trabajo);
    comprobar(e.recorte, "aviso de recorte", e.recorte, "verdadero");
  }

  printf("\n6) Detector de picos\n");
  comprobar(fabsf(dsp::nivel_mv(2.05f, 1.65f) - 400) < 0.5f, "nivel_mv(2,05 V; VREF 1,65 V)", dsp::nivel_mv(2.05f, 1.65f), "400 mV");
  comprobar(fabsf(dsp::nivel_db(400) + 6.02f) < 0.05f, "nivel_db(400 mV)", dsp::nivel_db(400), "−6,02 dB");
  comprobar(dsp::nivel_mv(1.60f, 1.65f) == 0, "nivel bajo VREF", dsp::nivel_mv(1.60f, 1.65f), "0 (no negativo)");

  printf("\n7) Retención de picos\n");
  {
    dsp::Retencion r;
    r.actualizar(-10, 0.1f);
    float x = 0;
    for (int i = 0; i < 5; ++i) x = r.actualizar(-40, 0.1f);
    comprobar(fabsf(x + 10) < 0.01f, "pico retenido a los 0,5 s", x, "−10 dB");
    for (int i = 0; i < 10; ++i) x = r.actualizar(-40, 0.1f);
    comprobar(x < -10 && x > -40, "pico cayendo a los 1,5 s", x, "entre −40 y −10 dB");
  }

  printf("\n%s\n", fallos ? "HAY FALLAS" : "Todas las pruebas pasan");
  return fallos ? 1 : 0;
}
