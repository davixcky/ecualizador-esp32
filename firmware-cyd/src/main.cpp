// Interfaz del ecualizador E.5 en la pantalla "CYD" montada en VERTICAL.
// Placa recibida (2026-11-24): ESP32-3248S035, panel ST7796 de 320 x 480 (env cyd35).
//
// TRES VISTAS, navegadas con la PANTALLA TÁCTIL (un toque en la cabecera pasa a la
// siguiente; el pulsador BOOT de la placa sigue sirviendo de respaldo):
//   BANDAS:   tres tarjetas GRAVES/MEDIOS/AGUDOS con barra de nivel, dB y mV.
//   ESPECTRO: 32 barras de la FFT coloreadas por banda.
//   LUCES:    mando de la tira NeoPixel del ESP32 principal: encendido, brillo,
//             modo (NIVELES/ARCOIRIS/FIJO) y color. Cada cambio se envía como trama
//             $EQ5L por ESP-NOW (y por el UART de respaldo).
//
// Táctil con DETECCIÓN AUTOMÁTICA de la variante (por medir cuál llegó):
//   S035C: GT911 capacitivo por I2C (SDA 33, SCL 32, INT 21, RST 25, supuestos).
//   S035R: XPT2046 resistivo en el mismo SPI del panel (CS 33); calibración por defecto
//          de TFT_eSPI, suficiente porque los controles son grandes. Calibrar si desvía.
//
// Enlace con el ESP32 principal (PROPUESTA, aún sin esquemático): protocolo $EQ5/$EQ5L de
// include/enlace_cyd.h por ESP-NOW en difusión (canal 1) y UART0/P1 como respaldo.
// Sin tramas de niveles durante 2 s se vuelve a los VALORES DE EJEMPLO ("EJEMPLO").
#include <Arduino.h>
#include <SD.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <WiFi.h>
#include <Wire.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <TAMC_GT911.h>

#include "enlace_cyd.h"

TFT_eSPI tft;

// La CYD trae un LED RGB de ánodo común en 4/16/17: apagarlo (nivel alto).
static const int LED_R = 4, LED_G = 16, LED_B = 17;
static const int BTN_BOOT = 0;     // respaldo del táctil para cambiar de vista

// GT911 (variante capacitiva, pines supuestos)
static const int TP_SDA = 33, TP_SCL = 32, TP_INT = 21, TP_RST = 25;
static TAMC_GT911 gt(TP_SDA, TP_SCL, TP_INT, TP_RST, TFT_WIDTH, TFT_HEIGHT);
static bool tactil_capacitivo = false;

struct Banda {
  const char *nombre;
  float db;        // valor de ejemplo
  int mv;
  uint16_t color;
  uint16_t fondo;  // color * 0.13
  uint16_t borde;  // color * 0.45
};

static Banda bandas[3];
static uint16_t FG, MUTED, BAR_BG, BG, PANEL;

static uint16_t escala(uint8_t r, uint8_t g, uint8_t b, float f) {
  return tft.color565(uint8_t(r * f), uint8_t(g * f), uint8_t(b * f));
}

// Geometría base en retrato 240 x 320, escalada en compilación al panel del env activo.
#define SX(v) ((v) * TFT_WIDTH / 240)
#define SY(v) ((v) * TFT_HEIGHT / 320)
static const int CARD_X = SX(12), CARD_W = SX(216), CARD_H = SY(72), CARD_Y0 = SY(52), CARD_PASO = SY(80);
static const int BAR_X = SX(20), BAR_W = SX(200), BAR_H = SY(17), BAR_DY = SY(27);

// ---------------------------------------------------------------- vista BANDAS
static void tarjeta(int i) {
  const Banda &b = bandas[i];
  int y = CARD_Y0 + i * CARD_PASO;
  tft.fillRoundRect(CARD_X, y, CARD_W, CARD_H, 6, b.fondo);
  tft.drawRoundRect(CARD_X, y, CARD_W, CARD_H, 6, b.borde);
  tft.setTextFont(2);
  tft.setTextColor(b.color, b.fondo);
  tft.setTextDatum(TL_DATUM);
  tft.drawString(b.nombre, BAR_X, y + SY(6));
  tft.setTextColor(MUTED, b.fondo);
  tft.setTextDatum(BR_DATUM);
  tft.drawString("PICO", BAR_X + BAR_W, y + CARD_H - SY(6));
}

// Dibujo sin parpadeo: la barra solo pinta la franja que cambió y las cifras solo se
// reescriben cuando su valor entero cambia.
static int prev_nivel[3];
static int prev_db[3];
static int prev_mv[3];

static void valores(int i, float db, int mv) {
  const Banda &b = bandas[i];
  int y = CARD_Y0 + i * CARD_PASO;
  int nivel = constrain(int(BAR_W * (db + 60.0f) / 60.0f), 6, BAR_W);
  const int by = y + BAR_DY;
  if (prev_nivel[i] < 0) {
    tft.fillRoundRect(BAR_X, by, BAR_W, BAR_H, 4, BAR_BG);
    tft.fillRect(BAR_X + 2, by + 2, nivel - 4, BAR_H - 4, b.color);
  } else if (nivel > prev_nivel[i]) {
    tft.fillRect(BAR_X + prev_nivel[i] - 2, by + 2, nivel - prev_nivel[i], BAR_H - 4, b.color);
  } else if (nivel < prev_nivel[i]) {
    tft.fillRect(BAR_X + nivel - 2, by + 2, prev_nivel[i] - nivel, BAR_H - 4, BAR_BG);
  }
  prev_nivel[i] = nivel;
  char txt[16];
  const int db_i = int(roundf(db));
  if (db_i != prev_db[i]) {
    prev_db[i] = db_i;
    tft.setTextFont(4);
    tft.setTextColor(FG, b.fondo);
    tft.setTextDatum(TR_DATUM);
    snprintf(txt, sizeof txt, "%d dB", db_i);
    tft.setTextPadding(SX(76));
    tft.drawString(txt, CARD_X + CARD_W - SX(8), y + SY(5));
    tft.setTextPadding(0);
  }
  if (mv != prev_mv[i]) {
    prev_mv[i] = mv;
    tft.setTextFont(2);
    tft.setTextColor(FG, b.fondo);
    tft.setTextDatum(BL_DATUM);
    snprintf(txt, sizeof txt, "%d mV", mv);
    tft.setTextPadding(SX(64));
    tft.drawString(txt, BAR_X, y + CARD_H - SY(5));
    tft.setTextPadding(0);
  }
}

// ---------------------------------------------------------------- vista ESPECTRO
static const int ESP_X0 = SX(12), ESP_W = SX(216);
static const int ESP_BASE = SY(284), ESP_HMAX = SY(226);
static const int ESP_BW = ESP_W / enlace_cyd::BARRAS;
static int prev_h[enlace_cyd::BARRAS];

static uint16_t color_barra(int i) {
  if (i < 11) return bandas[0].color;
  if (i < 22) return bandas[1].color;
  return bandas[2].color;
}

static void marco_espectro() {
  tft.drawFastHLine(ESP_X0, ESP_BASE + 1, ESP_BW * enlace_cyd::BARRAS, tft.color565(60, 68, 76));
  tft.setTextFont(2);
  tft.setTextDatum(TC_DATUM);
  const char *rot[3] = {"GRAVES", "MEDIOS", "AGUDOS"};
  for (int g = 0; g < 3; g++) {
    tft.setTextColor(bandas[g].color, BG);
    tft.drawString(rot[g], ESP_X0 + ESP_BW * (g * 11 + 5) + ESP_BW / 2, ESP_BASE + SY(6));
  }
}

static void barra_espectro(int i, float db) {
  int h = constrain(int(ESP_HMAX * (db + 60.0f) / 60.0f), 2, ESP_HMAX);
  if (h == prev_h[i]) return;
  const int x = ESP_X0 + i * ESP_BW;
  if (prev_h[i] < 0) {
    tft.fillRect(x, ESP_BASE - ESP_HMAX, ESP_BW - 2, ESP_HMAX - h, BG);
    tft.fillRect(x, ESP_BASE - h, ESP_BW - 2, h, color_barra(i));
  } else if (h > prev_h[i]) {
    tft.fillRect(x, ESP_BASE - h, ESP_BW - 2, h - prev_h[i], color_barra(i));
  } else {
    tft.fillRect(x, ESP_BASE - prev_h[i], ESP_BW - 2, prev_h[i] - h, BG);
  }
  prev_h[i] = h;
}

// ---------------------------------------------------------------- vista LUCES
// Mando de la tira NeoPixel del ESP32 principal. Estado local; cada cambio se transmite.
static enlace_cyd::Luces luces;
static const uint16_t SWATCH_RGB[6][3] = {{255, 122, 51}, {64, 214, 128}, {64, 164, 255},
                                          {235, 235, 225}, {170, 80, 255}, {255, 210, 40}};
// Zonas (coordenadas base): fila encendido, corredera de brillo, 3 modos, 6 colores.
static const int LZ_ON_Y = 56, LZ_ON_H = 30;
static const int LZ_BR_Y = 100, LZ_BR_H = 34, LZ_BR_X = 20, LZ_BR_W = 200;
static const int LZ_MD_Y = 150, LZ_MD_H = 26, LZ_MD_PASO = 30;
static const int LZ_CO_Y = 250, LZ_CO_H = 28;

static void fila_on() {
  const int y = SY(LZ_ON_Y);
  tft.setTextFont(2);
  tft.setTextColor(FG, BG);
  tft.setTextDatum(ML_DATUM);
  tft.setTextPadding(0);
  tft.drawString("TIRA DE LUZ", SX(20), y + SY(LZ_ON_H) / 2);
  const uint16_t col = luces.encendido ? tft.color565(64, 214, 128) : tft.color565(70, 76, 84);
  tft.fillRoundRect(SX(150), y, SX(70), SY(LZ_ON_H), 8, escala(64, 214, 128, luces.encendido ? .25f : .0f) | (luces.encendido ? 0 : PANEL));
  tft.drawRoundRect(SX(150), y, SX(70), SY(LZ_ON_H), 8, col);
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(col, luces.encendido ? escala(64, 214, 128, .25f) : PANEL);
  tft.drawString(luces.encendido ? "ENCENDIDA" : "APAGADA", SX(185), y + SY(LZ_ON_H) / 2);
}

static void fila_brillo() {
  const int y = SY(LZ_BR_Y);
  tft.setTextFont(2);
  tft.setTextColor(MUTED, BG);
  tft.setTextDatum(TL_DATUM);
  tft.drawString("BRILLO", SX(20), y - SY(16));
  char txt[8];
  snprintf(txt, sizeof txt, "%d", luces.brillo);
  tft.setTextDatum(TR_DATUM);
  tft.setTextColor(FG, BG);
  tft.setTextPadding(SX(40));
  tft.drawString(txt, SX(220), y - SY(16));
  tft.setTextPadding(0);
  tft.fillRoundRect(SX(LZ_BR_X), y, SX(LZ_BR_W), SY(LZ_BR_H) / 2, 6, BAR_BG);
  const int w = SX(LZ_BR_W) * luces.brillo / 255;
  if (w > 4) tft.fillRoundRect(SX(LZ_BR_X), y, w, SY(LZ_BR_H) / 2, 6, tft.color565(255, 210, 40));
}

static void fila_modos() {
  const char *noms[3] = {"NIVELES (sigue el audio)", "ARCOIRIS", "COLOR FIJO"};
  tft.setTextFont(2);
  for (int m = 0; m < 3; m++) {
    const int y = SY(LZ_MD_Y + m * LZ_MD_PASO);
    const bool sel = luces.modo == m;
    tft.fillRoundRect(SX(20), y, SX(200), SY(LZ_MD_H), 6, sel ? escala(64, 164, 255, .25f) : PANEL);
    tft.drawRoundRect(SX(20), y, SX(200), SY(LZ_MD_H), 6, sel ? tft.color565(64, 164, 255) : tft.color565(60, 68, 76));
    tft.setTextDatum(ML_DATUM);
    tft.setTextColor(sel ? FG : MUTED, sel ? escala(64, 164, 255, .25f) : PANEL);
    tft.drawString(noms[m], SX(30), y + SY(LZ_MD_H) / 2);
  }
}

static void fila_colores() {
  const int y = SY(LZ_CO_Y);
  tft.setTextFont(2);
  tft.setTextColor(MUTED, BG);
  tft.setTextDatum(TL_DATUM);
  tft.drawString("COLOR (modo fijo)", SX(20), y - SY(16));
  for (int c = 0; c < 6; c++) {
    const int x = SX(20 + c * 34);
    const uint16_t col = tft.color565(SWATCH_RGB[c][0], SWATCH_RGB[c][1], SWATCH_RGB[c][2]);
    const bool sel = luces.r == SWATCH_RGB[c][0] && luces.g == SWATCH_RGB[c][1] && luces.b == SWATCH_RGB[c][2];
    tft.fillRoundRect(x, y, SX(28), SY(LZ_CO_H), 5, col);
    tft.drawRoundRect(x, y, SX(28), SY(LZ_CO_H), 5, sel ? FG : BG);
    if (sel) tft.drawRoundRect(x + 1, y + 1, SX(28) - 2, SY(LZ_CO_H) - 2, 5, FG);
  }
}

static void vista_luces() {
  fila_on();
  fila_brillo();
  fila_modos();
  fila_colores();
  tft.setTextFont(2);
  tft.setTextColor(MUTED, BG);
  tft.setTextDatum(TC_DATUM);
  tft.drawString("Los cambios van al ESP32 por ESP-NOW", SX(120), SY(284));
}

// ---------------------------------------------------------------- transmisión del mando
static void enviar_luces() {
  char buf[enlace_cyd::LINEA_MAX];
  const int n = enlace_cyd::componer_luces(luces, buf, sizeof buf);
  if (n <= 1) return;
  static const uint8_t DIFUSION[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
  esp_now_send(DIFUSION, (const uint8_t *)buf, n - 1);   // sin el salto de línea
  Serial.print(buf);                                     // respaldo por UART0/P1 (y registro)
}

// ---------------------------------------------------------------- recepción de tramas
enum Transporte { T_NINGUNO, T_UART, T_ESPNOW };
static enlace_cyd::Trama trama;
static uint32_t t_trama = 0;
static Transporte transporte = T_NINGUNO;
static bool en_vivo = false;

static volatile bool espnow_listo = false;
static char espnow_buf[enlace_cyd::LINEA_MAX];

static void espnow_rx(const uint8_t *, const uint8_t *datos, int n) {
  if (espnow_listo || n <= 0 || n >= (int)sizeof espnow_buf) return;
  memcpy(espnow_buf, datos, n);
  espnow_buf[n] = '\0';
  espnow_listo = true;
}

static void recibir() {
  if (espnow_listo) {
    if (enlace_cyd::parsear(espnow_buf, trama)) { t_trama = millis(); transporte = T_ESPNOW; }
    espnow_listo = false;
  }
  static char linea[enlace_cyd::LINEA_MAX];
  static int n = 0;
  while (Serial.available() > 0) {
    const char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      linea[n] = '\0';
      if (n > 0 && enlace_cyd::parsear(linea, trama)) { t_trama = millis(); transporte = T_UART; }
      n = 0;
    } else if (n < (int)sizeof linea - 1) {
      linea[n++] = c;
    } else {
      n = 0;
    }
  }
}

static void indicador(bool vivo) {
  tft.setTextFont(2);
  tft.setTextDatum(TC_DATUM);
  tft.setTextPadding(SX(226));
  if (vivo) {
    tft.setTextColor(tft.color565(64, 214, 128), BG);
    tft.drawString(transporte == T_ESPNOW ? "EN VIVO - ESP-NOW" : "EN VIVO - UART P1", SX(120), SY(300));
  } else {
    tft.setTextColor(MUTED, BG);
    tft.drawString("EJEMPLO - sin enlace", SX(120), SY(300));
  }
  tft.setTextPadding(0);
}

// ---------------------------------------------------------------- vistas y entrada
enum Vista { V_BANDAS, V_ESPECTRO, V_LUCES, V_TOTAL };
static Vista vista = V_BANDAS;

static void abrir_vista() {
  tft.fillScreen(BG);
  tft.setTextFont(2);
  tft.setTextColor(MUTED, BG);
  tft.setTextDatum(TL_DATUM);
  tft.drawString("ECUALIZADOR E.5", SX(12), SY(8));
  tft.setTextDatum(TR_DATUM);
  tft.drawString("toca aqui: cambiar vista", SX(228), SY(8));
  tft.setTextFont(4);
  tft.setTextColor(FG, BG);
  tft.setTextDatum(TL_DATUM);
  const char *tit[V_TOTAL] = {"TRES BANDAS", "ESPECTRO", "LUCES"};
  tft.drawString(tit[vista], SX(12), SY(22));
  tft.drawFastHLine(SX(12), SY(46), SX(216), tft.color565(35, 43, 50));
  for (int i = 0; i < 3; i++) { prev_nivel[i] = -1; prev_db[i] = 999; prev_mv[i] = -1; }
  for (int i = 0; i < enlace_cyd::BARRAS; i++) prev_h[i] = -1;
  if (vista == V_BANDAS) {
    for (int i = 0; i < 3; i++) tarjeta(i);
  } else if (vista == V_ESPECTRO) {
    marco_espectro();
  } else {
    vista_luces();
  }
  indicador(en_vivo);
}

static void siguiente_vista() {
  vista = Vista((vista + 1) % V_TOTAL);
  abrir_vista();
}

// Lectura unificada del táctil (GT911 o XPT2046). Devuelve true con coordenadas de panel.
static bool toque(int &x, int &y) {
  if (tactil_capacitivo) {
    gt.read();
    if (!gt.isTouched) return false;
    x = gt.points[0].x;
    y = gt.points[0].y;
    return true;
  }
#ifdef TOUCH_CS
  uint16_t tx, ty;
  if (tft.getTouch(&tx, &ty, 600)) { x = tx; y = ty; return true; }
#endif
  return false;
}

static void tactil() {
  static bool antes = false;
  static uint32_t t_envio = 0;
  int x = 0, y = 0;
  const bool ahora = toque(x, y);
  const bool flanco = ahora && !antes;
  antes = ahora;
  if (!ahora) return;

  if (flanco && y < SY(48)) {         // cabecera: cambiar de vista
    siguiente_vista();
    return;
  }
  if (vista != V_LUCES) return;

  bool cambio = false;
  // Corredera de brillo: responde también al arrastre (limitado a 10 envíos/s).
  if (y >= SY(LZ_BR_Y) - SY(6) && y <= SY(LZ_BR_Y + LZ_BR_H) && x >= SX(LZ_BR_X) - SX(6) && x <= SX(LZ_BR_X + LZ_BR_W) + SX(6)) {
    const int v = constrain((x - SX(LZ_BR_X)) * 255 / SX(LZ_BR_W), 0, 255);
    if (v != luces.brillo) { luces.brillo = (uint8_t)v; fila_brillo(); cambio = millis() - t_envio > 100; }
  } else if (flanco && y >= SY(LZ_ON_Y) && y <= SY(LZ_ON_Y + LZ_ON_H)) {
    luces.encendido = !luces.encendido;
    fila_on();
    cambio = true;
  } else if (flanco && y >= SY(LZ_MD_Y) && y <= SY(LZ_MD_Y + 2 * LZ_MD_PASO + LZ_MD_H)) {
    const int m = (y - SY(LZ_MD_Y)) / SY(LZ_MD_PASO);
    if (m >= 0 && m <= 2 && m != luces.modo) { luces.modo = (uint8_t)m; fila_modos(); cambio = true; }
  } else if (flanco && y >= SY(LZ_CO_Y) && y <= SY(LZ_CO_Y + LZ_CO_H)) {
    const int c = (x - SX(20)) / SX(34);
    if (c >= 0 && c <= 5) {
      luces.r = SWATCH_RGB[c][0]; luces.g = SWATCH_RGB[c][1]; luces.b = SWATCH_RGB[c][2];
      if (luces.modo != enlace_cyd::LUCES_FIJO) { luces.modo = enlace_cyd::LUCES_FIJO; fila_modos(); }
      fila_colores();
      cambio = true;
    }
  }
  if (cambio) {
    t_envio = millis();
    enviar_luces();
  }
}

static void boton() {
  static bool antes = true;
  static uint32_t t_cambio = 0;
  const bool ahora = digitalRead(BTN_BOOT);
  if (antes && !ahora && millis() - t_cambio > 250) {
    t_cambio = millis();
    siguiente_vista();
  }
  antes = ahora;
}

static float espectro_ejemplo(int i, float t) {
  static const float centro[3] = {5.0f, 16.0f, 27.0f};
  float db = -60.0f;
  for (int g = 0; g < 3; g++) {
    const float osc = 2.5f * sinf(t * (1.1f + .35f * g) + g * 2.1f);
    const float cima = bandas[g].db + osc;
    const float d = i - centro[g];
    const float loma = -60.0f + (cima + 60.0f) * expf(-d * d / 16.0f);
    if (loma > db) db = loma;
  }
  return db + 1.2f * sinf(t * 2.7f + i * 1.9f);
}

void setup() {
  Serial.begin(enlace_cyd::BAUDIOS);
  Serial.println("Ecualizador E.5 - interfaz CYD (tactil; vistas BANDAS/ESPECTRO/LUCES)");
  Serial.printf("Panel: %d x %d\n", TFT_WIDTH, TFT_HEIGHT);
  for (int p : {LED_R, LED_G, LED_B}) { pinMode(p, OUTPUT); digitalWrite(p, HIGH); }
  pinMode(BTN_BOOT, INPUT_PULLUP);

  // Deteccion del tactil: si hay un GT911 en el I2C (variante capacitiva), se usa; si no,
  // se asume el XPT2046 resistivo del SPI del panel. OJO: el pin 33 es a la vez el SDA del
  // GT911 y el CS del XPT2046 que TFT_eSPI configura en tft.init(); por eso la deteccion se
  // hace aqui pero el Wire/gt911 definitivos se levantan DESPUES de tft.init().
  Wire.begin(TP_SDA, TP_SCL);
  Wire.beginTransmission(0x5D);
  tactil_capacitivo = Wire.endTransmission() == 0;
  if (!tactil_capacitivo) {
    Wire.beginTransmission(0x14);
    tactil_capacitivo = Wire.endTransmission() == 0;
  }
  Wire.end();
  Serial.println(tactil_capacitivo ? "Tactil: GT911 capacitivo (S035C)"
                                   : "Tactil: XPT2046 resistivo asumido (S035R); calibracion por defecto");

  // ESP-NOW en difusión por el canal 1: recibe niveles y envía el mando de luces.
  WiFi.mode(WIFI_STA);
  esp_wifi_set_ps(WIFI_PS_NONE);
  if (esp_now_init() == ESP_OK) {
    esp_now_register_recv_cb(espnow_rx);
    esp_now_peer_info_t par{};
    memset(par.peer_addr, 0xFF, 6);
    par.channel = 0;                 // el canal actual (1 por defecto en STA)
    par.encrypt = false;
    esp_now_add_peer(&par);
    Serial.printf("ESP-NOW listo; MAC de esta pantalla: %s\n", WiFi.macAddress().c_str());
  } else {
    Serial.println("ESP-NOW NO disponible; queda solo el enlace UART");
  }

  tft.init();
  tft.setRotation(0);               // retrato; si queda cabeza abajo en la tapa, usar 2
  if (tactil_capacitivo) {
    // Recuperar el pin 33 como SDA (tft.init lo dejó como CS del tactil resistivo) y
    // arrancar el GT911 ya con el bus definitivo.
    Wire.begin(TP_SDA, TP_SCL);
    gt.begin();
  }
  // Tarjeta TF (SPI propio en 18/19/23, CS 5 segun la comunidad; pines supuestos): se prueba
  // al arrancar y se informa por serie. Sin tarjeta insertada solo imprime el aviso.
  {
    static SPIClass sd_spi(HSPI);
    sd_spi.begin(18, 19, 23, 5);
    if (SD.begin(5, sd_spi)) {
      Serial.printf("Tarjeta TF: detectada, %.1f GB (tipo %d)\n", SD.cardSize() / 1073741824.0, (int)SD.cardType());
    } else {
      Serial.println("Tarjeta TF: sin tarjeta o sin respuesta (pines supuestos 18/19/23, CS 5)");
    }
  }
  BG = tft.color565(2, 5, 8);
  FG = tft.color565(238, 242, 245);
  MUTED = tft.color565(115, 128, 140);
  BAR_BG = tft.color565(18, 23, 28);
  PANEL = tft.color565(10, 14, 18);
  bandas[0] = {"GRAVES", -32, 152, tft.color565(255, 122, 51), escala(255, 122, 51, .13f), escala(255, 122, 51, .45f)};
  bandas[1] = {"MEDIOS", -19, 196, tft.color565(64, 214, 128), escala(64, 214, 128, .13f), escala(64, 214, 128, .45f)};
  bandas[2] = {"AGUDOS", -28, 168, tft.color565(64, 164, 255), escala(64, 164, 255, .13f), escala(64, 164, 255, .45f)};
  abrir_vista();
}

void loop() {
  recibir();
  tactil();
  boton();
  const bool vivo = t_trama != 0 && millis() - t_trama <= 2000;
  if (vivo != en_vivo) {
    en_vivo = vivo;
    indicador(vivo);
  }
  const float t = millis() / 1000.0f;
  if (vista == V_BANDAS) {
    if (vivo) {
      for (int i = 0; i < 3; i++) valores(i, trama.banda_db[i], int(trama.banda_mv[i] + 0.5f));
    } else {
      for (int i = 0; i < 3; i++) {
        float osc = 2.5f * sinf(t * (1.1f + .35f * i) + i * 2.1f);
        valores(i, bandas[i].db + osc, bandas[i].mv + int(osc * 4));
      }
    }
  } else if (vista == V_ESPECTRO) {
    for (int i = 0; i < enlace_cyd::BARRAS; i++)
      barra_espectro(i, vivo ? trama.barras_db[i] : espectro_ejemplo(i, t));
  }
  delay(30);
}
