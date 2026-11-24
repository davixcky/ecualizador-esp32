// Enlace entre el ESP32 principal y la pantalla del ecualizador E.5. La placa recibida
// resultó ser una ESP32-3248S035 de 3,5 pulgadas (ST7796, entorno `cyd35`), no la
// ESP32-2432S028 prevista; el protocolo es el mismo.
//
// COPIA COMPARTIDA: este archivo existe por duplicado en
//   firmware/include/enlace_cyd.h   y   firmware-cyd/include/enlace_cyd.h
// y las dos copias deben mantenerse IDENTICAS (comprobar con `cmp`).
//
// Dos transportes llevan la MISMA línea $EQ5 (el receptor valida ambas con este parser):
//   1) ESP-NOW por difusión (decisión del usuario, 2026-11-24): el ESP32 principal emite
//      cada línea (sin el '\n' final) a FF:FF:FF:FF:FF:FF por el canal 1; la pantalla
//      escucha como estación en ese canal con el ahorro de energía desactivado
//      (WIFI_PS_NONE). La línea de ~230 bytes cabe en los 250 de una trama ESP-NOW.
//   2) UART como respaldo cableado: ESP32 GPIO17 (TX2) -> P1 RX (GPIO3) y
//      ESP32 GPIO16 (RX2) <- P1 TX (GPIO1), +5 V al VIN de P1 y GND común (arnés de
//      cuatro hilos). P1 es el UART0 de la pantalla, compartido con su puente USB-serie
//      y su log de arranque: las tramas conviven con ese tráfico.
// PROPUESTA: ninguno de los dos enlaces está en el esquemático
// (hardware/ecualizador.kicad_sch sigue dibujando la pantalla SPI J4); la pantalla sigue
// necesitando +5 V y GND aunque se use solo ESP-NOW.
// Por eso el protocolo es de líneas ASCII con suma de verificación y el receptor descarta
// en silencio todo lo que no valide.
//
// Protocolo: una línea por bloque de FFT (~19,5 por segundo; a 115200 baudios cada línea
// de ~230 caracteres tarda ~20 ms, así que no se acumula atraso):
//
//   $EQ5,<mv_g>,<mv_m>,<mv_a>,<db_g>,<db_m>,<db_a>,<clip>,<s0>,...,<s31>*HH\n
//
//   - mv_g/mv_m/mv_a: pico de cada detector (graves, medios, agudos) en mV, entero.
//   - db_g/db_m/db_a: el mismo nivel en dB respecto a la plena escala (0,8 V de pico),
//     con un decimal y acotado a [-99,9, +99,9] para que el ancho quede acotado.
//   - clip: 1 si la señal salió de la zona lineal del ADC (o una banda superó 800 mV), 0 si no.
//   - s0..s31: barras del espectro en dB (el receptor puede ignorarlas si solo muestra bandas).
//   - HH: XOR de todos los caracteres entre '$' y '*', en dos dígitos hexadecimales
//     (la misma suma de verificación de NMEA 0183).
#pragma once
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace enlace_cyd {

constexpr long BAUDIOS = 115200;  // igual en Serial2 del ESP32 y en el UART0 del CYD
constexpr int BANDAS = 3;         // graves, medios, agudos
constexpr int BARRAS = 32;        // barras del espectro (= dsp::BARRAS)
constexpr int LINEA_MAX = 320;    // tamaño de buffer que garantiza una línea completa

struct Trama {
  float banda_mv[BANDAS];   // pico de cada detector (mV)
  float banda_db[BANDAS];   // el mismo nivel en dB respecto a 0,8 V de pico
  float barras_db[BARRAS];  // espectro de la salida ecualizada (dB)
  bool recorte;             // señal fuera de la zona lineal del ADC
};

// XOR de n caracteres: la suma de verificación estilo NMEA.
inline uint8_t suma_verificacion(const char* s, int n) {
  uint8_t x = 0;
  for (int i = 0; i < n; ++i) x ^= (uint8_t)s[i];
  return x;
}

inline float acotar_db(float db) { return db < -99.9f ? -99.9f : (db > 99.9f ? 99.9f : db); }

// Escribe la línea completa (con '\n' y terminador) en buf. Devuelve su longitud, o 0 si no cabe.
inline int componer(const Trama& t, char* buf, int cap) {
  char cuerpo[LINEA_MAX];
  int n = snprintf(cuerpo, sizeof cuerpo, "EQ5,%d,%d,%d,%.1f,%.1f,%.1f,%d",
                   (int)(t.banda_mv[0] + 0.5f), (int)(t.banda_mv[1] + 0.5f),
                   (int)(t.banda_mv[2] + 0.5f), (double)acotar_db(t.banda_db[0]),
                   (double)acotar_db(t.banda_db[1]), (double)acotar_db(t.banda_db[2]),
                   t.recorte ? 1 : 0);
  for (int j = 0; j < BARRAS && n > 0 && n < (int)sizeof cuerpo; ++j)
    n += snprintf(cuerpo + n, sizeof cuerpo - n, ",%.1f", (double)acotar_db(t.barras_db[j]));
  if (n <= 0 || n >= (int)sizeof cuerpo) return 0;
  const int total = snprintf(buf, cap, "$%s*%02X\n", cuerpo, suma_verificacion(cuerpo, n));
  return (total > 0 && total < cap) ? total : 0;
}

// Interpreta una línea recibida (con o sin fin de línea). Llena t y devuelve true solo si
// la línea trae el prefijo $EQ5, exactamente los campos esperados y la suma correcta;
// cualquier otra cosa (log de arranque, ruido, línea cortada) devuelve false sin tocar t.
inline bool parsear(const char* linea, Trama& t) {
  const char* ini = strchr(linea, '$');
  if (!ini) return false;
  const char* ast = strchr(ini, '*');
  if (!ast || strncmp(ini + 1, "EQ5,", 4) != 0) return false;
  char* fin = nullptr;
  const uint8_t declarada = (uint8_t)strtoul(ast + 1, &fin, 16);
  if (fin != ast + 3) return false;  // exige exactamente dos dígitos hexadecimales
  if (suma_verificacion(ini + 1, (int)(ast - ini - 1)) != declarada) return false;

  constexpr int CAMPOS = 2 * BANDAS + 1 + BARRAS;  // mv, dB, clip, barras
  float campo[CAMPOS];
  const char* p = ini + 5;  // tras "$EQ5,"
  for (int i = 0; i < CAMPOS; ++i) {
    char* sig = nullptr;
    campo[i] = strtof(p, &sig);
    if (sig == p) return false;  // campo vacío o no numérico
    p = sig;
    if (*p == ',')
      ++p;
    else if (i + 1 < CAMPOS)
      return false;  // faltan campos
  }
  if (p != ast) return false;  // sobran campos o caracteres

  Trama nueva{};
  for (int b = 0; b < BANDAS; ++b) {
    nueva.banda_mv[b] = campo[b];
    nueva.banda_db[b] = campo[BANDAS + b];
  }
  nueva.recorte = campo[2 * BANDAS] != 0.0f;
  for (int j = 0; j < BARRAS; ++j) nueva.barras_db[j] = campo[2 * BANDAS + 1 + j];
  t = nueva;
  return true;
}

}  // namespace enlace_cyd
