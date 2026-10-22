// Procesamiento de la señal del ecualizador. No depende de Arduino: se compila igual en el
// ESP32 y en el PC (test/prueba_dsp.cpp), donde se prueba con señales sintéticas.
#pragma once
#include <stdint.h>

namespace dsp {

constexpr int N = 1024;              // muestras por bloque de FFT
constexpr float FS = 20000.0f;       // frecuencia de muestreo (Hz)
constexpr float DF = FS / N;         // resolución espectral: 19,53 Hz por bin
constexpr int BARRAS = 32;           // barras del analizador de espectro
constexpr float F_MIN = 40.0f;       // borde inferior de la primera barra (Hz)
constexpr float F_MAX = 5000.0f;     // borde superior de la última barra (= corte del antialiasing)

// Zona lineal del ADC con 11 dB de atenuación y amplitud de plena escala alrededor de VREF.
constexpr float ADC_MIN_V = 0.15f;
constexpr float ADC_MAX_V = 2.45f;
constexpr float PLENA_ESCALA_V = 0.80f;   // pico de una senoidal de 0 dBFS (1,65 V ± 0,8 V)

constexpr float PISO_DB = -60.0f;         // lo que está por debajo se dibuja como barra vacía

struct Espectro {
  float barras_db[BARRAS];   // nivel de cada barra (dB respecto a la plena escala)
  float rms_dbfs;            // nivel eficaz del bloque (dBFS, 0 dBFS = senoidal de 0,8 V de pico)
  float pico_hz;             // frecuencia dominante (interpolada entre bins)
  float pico_db;             // nivel de la frecuencia dominante
  bool recorte;              // alguna muestra salió de la zona lineal del ADC
};

// FFT compleja radix-2 en el lugar (n potencia de 2).
void fft(float* re, float* im, int n);

// Borde inferior de la barra k en Hz (k = 0..BARRAS); el borde de BARRAS es el final de la última.
float borde_barra(int k);

// Analiza un bloque de N tensiones en el pin del ADC (V). `trabajo` debe tener 2·N floats.
void analizar(const float* v, Espectro& e, float* trabajo);

// Nivel de un detector de picos: tensión del pin menos VREF, en mV, y en dB respecto a la
// plena escala (0,8 V de pico).
float nivel_mv(float v_det, float v_ref);
float nivel_db(float mv);

// Retención de picos para las barras: mantiene el máximo `retencion_s` y luego cae a `caida_db_s`.
struct Retencion {
  float valor = PISO_DB;
  float tiempo = 0;
  float actualizar(float nuevo, float dt, float retencion_s = 0.8f, float caida_db_s = 20.0f);
};

}  // namespace dsp
