#include "dsp.h"

#include <math.h>

namespace dsp {

void fft(float* re, float* im, int n) {
  // reordenamiento por inversión de bits
  for (int i = 1, j = 0; i < n; ++i) {
    int bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      float t = re[i]; re[i] = re[j]; re[j] = t;
      t = im[i]; im[i] = im[j]; im[j] = t;
    }
  }
  // mariposas
  for (int largo = 2; largo <= n; largo <<= 1) {
    const float ang = -2.0f * (float)M_PI / largo;
    const float wr = cosf(ang), wi = sinf(ang);
    for (int i = 0; i < n; i += largo) {
      float cr = 1.0f, ci = 0.0f;
      for (int k = 0; k < largo / 2; ++k) {
        const int a = i + k, b = a + largo / 2;
        const float tr = re[b] * cr - im[b] * ci;
        const float ti = re[b] * ci + im[b] * cr;
        re[b] = re[a] - tr; im[b] = im[a] - ti;
        re[a] += tr; im[a] += ti;
        const float nr = cr * wr - ci * wi;
        ci = cr * wi + ci * wr;
        cr = nr;
      }
    }
  }
}

// Bordes de las barras en bins: escala logarítmica entre el bin 2 (39 Hz) y el 256 (5 kHz), con
// al menos un bin por barra. Por debajo de ~300 Hz cada barra es un solo bin (la resolución
// de 19,5 Hz no permite más), y de ahí para arriba las barras se ensanchan en escala logarítmica.
static int inicio_barra[BARRAS + 1];

static void preparar_barras() {
  if (inicio_barra[BARRAS]) return;
  const float b0 = F_MIN / DF, b1 = F_MAX / DF + 1;   // bins 2,05 y 257 (exclusivo)
  inicio_barra[0] = (int)lroundf(b0);
  for (int j = 1; j <= BARRAS; ++j) {
    const int objetivo = (int)lroundf(b0 * powf(b1 / b0, (float)j / BARRAS));
    inicio_barra[j] = objetivo > inicio_barra[j - 1] ? objetivo : inicio_barra[j - 1] + 1;
  }
}

float borde_barra(int k) {
  preparar_barras();
  return (inicio_barra[k] - 0.5f) * DF;
}

static float a_db(float amplitud) {
  const float db = 20.0f * log10f(amplitud / PLENA_ESCALA_V + 1e-9f);
  return db < PISO_DB ? PISO_DB : db;
}

void analizar(const float* v, Espectro& e, float* trabajo) {
  float* re = trabajo;
  float* im = trabajo + N;
  // valor medio (≈ VREF) y recorte
  double suma = 0;
  e.recorte = false;
  for (int i = 0; i < N; ++i) {
    suma += v[i];
    if (v[i] < ADC_MIN_V || v[i] > ADC_MAX_V) e.recorte = true;
  }
  const float media = (float)(suma / N);
  double cuad = 0;
  for (int i = 0; i < N; ++i) {
    const float x = v[i] - media;
    cuad += (double)x * x;
    // ventana de Hann
    re[i] = x * 0.5f * (1.0f - cosf(2.0f * (float)M_PI * i / (N - 1)));
    im[i] = 0.0f;
  }
  const float rms = sqrtf((float)(cuad / N));
  const float rms_fs = PLENA_ESCALA_V / sqrtf(2.0f);
  e.rms_dbfs = 20.0f * log10f(rms / rms_fs + 1e-9f);
  if (e.rms_dbfs < PISO_DB) e.rms_dbfs = PISO_DB;

  fft(re, im, N);
  // Amplitud de pico de cada bin: la ventana de Hann tiene ganancia coherente 0,5.
  const float escala = 2.0f / (N * 0.5f);
  for (int k = 0; k <= N / 2; ++k) re[k] = sqrtf(re[k] * re[k] + im[k] * im[k]) * escala;

  // frecuencia dominante (sin los primeros bins, que guardan restos de continua)
  int kmax = 2;
  for (int k = 3; k < N / 2; ++k)
    if (re[k] > re[kmax]) kmax = k;
  const float a = re[kmax - 1], b = re[kmax], c = re[kmax + 1];
  const float den = a - 2 * b + c;
  const float d = den != 0 ? 0.5f * (a - c) / den : 0.0f;
  e.pico_hz = (kmax + d) * DF;
  e.pico_db = a_db(b);

  // barras: máximo de los bins de cada barra
  preparar_barras();
  for (int j = 0; j < BARRAS; ++j) {
    float m = 0;
    for (int k = inicio_barra[j]; k < inicio_barra[j + 1] && k <= N / 2; ++k)
      if (re[k] > m) m = re[k];
    e.barras_db[j] = a_db(m);
  }
}

float nivel_mv(float v_det, float v_ref) {
  const float mv = (v_det - v_ref) * 1000.0f;
  return mv < 0 ? 0 : mv;
}

float nivel_db(float mv) {
  return a_db(mv / 1000.0f);
}

float Retencion::actualizar(float nuevo, float dt, float retencion_s, float caida_db_s) {
  if (nuevo >= valor) {
    valor = nuevo;
    tiempo = 0;
  } else {
    tiempo += dt;
    if (tiempo > retencion_s) valor -= caida_db_s * dt;
    if (valor < nuevo) valor = nuevo;
  }
  return valor;
}

}  // namespace dsp
