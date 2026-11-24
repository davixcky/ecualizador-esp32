// Interfaz del ecualizador E.5 en la pantalla "CYD" montada en VERTICAL.
// Placa recibida (2026-11-24): ESP32-3248S035, panel ST7796 de 320 x 480 (env cyd35).
//
// Dos vistas, alternadas con el pulsador BOOT de la propia placa (GPIO0):
//   BANDAS:   tres tarjetas GRAVES/MEDIOS/AGUDOS con barra de nivel, dB y mV.
//   ESPECTRO: 32 barras de la FFT coloreadas por banda.
//
// Enlace con el ESP32 principal (PROPUESTA del 2026-11-24, aún sin esquemático). El mismo
// protocolo $EQ5 de include/enlace_cyd.h llega por DOS transportes y alimenta el mismo
// analizador; gana el que entregue tramas:
//   - ESP-NOW (decisión del usuario): difusión en 2,4 GHz, sin cables de datos — la pantalla
//     solo necesitaría +5 V y GND. La trama ASCII (~231 B) cabe en un paquete (máx. 250 B).
//   - UART0 / conector P1 (GPIO3 RX): se conserva como respaldo y para pruebas por cable.
// Sin tramas durante 2 s se vuelve a los VALORES DE EJEMPLO animados ("EJEMPLO").
#include <Arduino.h>
#include <TFT_eSPI.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

#include "enlace_cyd.h"

TFT_eSPI tft;

// La CYD trae un LED RGB de ánodo común en 4/16/17: apagarlo (nivel alto).
static const int LED_R = 4, LED_G = 16, LED_B = 17;
static const int BTN_BOOT = 0;     // pulsador BOOT de la placa: cambia de vista

struct Banda {
  const char *nombre;
  float db;        // valor de ejemplo
  int mv;
  uint16_t color;
  uint16_t fondo;  // color * 0.13
  uint16_t borde;  // color * 0.45
};

static Banda bandas[3];
static uint16_t FG, MUTED, BAR_BG, BG;

static uint16_t escala(uint8_t r, uint8_t g, uint8_t b, float f) {
  return tft.color565(uint8_t(r * f), uint8_t(g * f), uint8_t(b * f));
}

// Geometría base en retrato 240 x 320 (mitad del render de 480 x 640), escalada en tiempo de
// compilación al panel del env activo: SX/SY la llevan p. ej. a los 320 x 480 de la 3248S035.
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
// reescriben cuando su valor entero cambia (drawString con relleno pinta glifo y fondo
// en una sola pasada, así que tampoco parpadean).
static int prev_nivel[3];
static int prev_db[3];
static int prev_mv[3];

static void valores(int i, float db, int mv) {
  const Banda &b = bandas[i];
  int y = CARD_Y0 + i * CARD_PASO;
  int nivel = constrain(int(BAR_W * (db + 60.0f) / 60.0f), 6, BAR_W);
  const int by = y + BAR_DY;
  if (prev_nivel[i] < 0) {            // primera vez: cubeta completa y relleno
    tft.fillRoundRect(BAR_X, by, BAR_W, BAR_H, 4, BAR_BG);
    tft.fillRect(BAR_X + 2, by + 2, nivel - 4, BAR_H - 4, b.color);
  } else if (nivel > prev_nivel[i]) { // crece: pintar solo la franja nueva
    tft.fillRect(BAR_X + prev_nivel[i] - 2, by + 2, nivel - prev_nivel[i], BAR_H - 4, b.color);
  } else if (nivel < prev_nivel[i]) { // decrece: borrar solo la franja sobrante
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
// 32 barras entre CARD_Y0 y la línea base, coloreadas por banda (11 + 11 + 10),
// con el mismo dibujo por diferencias que las barras de nivel.
static const int ESP_X0 = SX(12), ESP_W = SX(216);
static const int ESP_BASE = SY(284), ESP_HMAX = SY(226);
static const int ESP_BW = ESP_W / enlace_cyd::BARRAS;        // ancho de columna
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

// ---------------------------------------------------------------- recepción de tramas
// Los dos transportes alimentan el mismo analizador; se recuerda cuál entregó la última trama.
enum Transporte { T_NINGUNO, T_UART, T_ESPNOW };
static enlace_cyd::Trama trama;    // última trama válida recibida
static uint32_t t_trama = 0;       // millis() de esa trama (0 = nunca llegó ninguna)
static Transporte transporte = T_NINGUNO;
static bool en_vivo = false;

// ESP-NOW: el callback corre en la tarea de WiFi; solo copia el paquete y avisa.
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
      n = 0;  // línea demasiado larga (ruido): descartar y resincronizar
    }
  }
}

// Indicador del pie: transporte activo o modo de ejemplo.
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
enum Vista { V_BANDAS, V_ESPECTRO };
static Vista vista = V_BANDAS;

static void abrir_vista() {
  tft.fillScreen(BG);
  tft.setTextFont(2);
  tft.setTextColor(MUTED, BG);
  tft.setTextDatum(TL_DATUM);
  tft.drawString("ECUALIZADOR E.5", SX(12), SY(8));
  tft.setTextFont(4);
  tft.setTextColor(FG, BG);
  tft.drawString(vista == V_BANDAS ? "TRES BANDAS" : "ESPECTRO", SX(12), SY(22));
  tft.drawFastHLine(SX(12), SY(46), SX(216), tft.color565(35, 43, 50));
  for (int i = 0; i < 3; i++) { prev_nivel[i] = -1; prev_db[i] = 999; prev_mv[i] = -1; }
  for (int i = 0; i < enlace_cyd::BARRAS; i++) prev_h[i] = -1;
  if (vista == V_BANDAS) {
    for (int i = 0; i < 3; i++) tarjeta(i);
  } else {
    marco_espectro();
  }
  indicador(en_vivo);
}

// Pulsador BOOT con antirrebote: flanco de bajada cambia de vista.
static void boton() {
  static bool antes = true;
  static uint32_t t_cambio = 0;
  const bool ahora = digitalRead(BTN_BOOT);
  if (antes && !ahora && millis() - t_cambio > 250) {
    t_cambio = millis();
    vista = vista == V_BANDAS ? V_ESPECTRO : V_BANDAS;
    abrir_vista();
  }
  antes = ahora;
}

// Espectro de ejemplo: tres lomas que respiran con los valores de muestra.
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
  Serial.begin(enlace_cyd::BAUDIOS);  // UART0: monitor USB y, en la tapa, el enlace por P1
  Serial.println("Ecualizador E.5 - interfaz CYD (retrato, vistas BANDAS/ESPECTRO con BOOT)");
  Serial.printf("Panel: %d x %d\n", TFT_WIDTH, TFT_HEIGHT);
  for (int p : {LED_R, LED_G, LED_B}) { pinMode(p, OUTPUT); digitalWrite(p, HIGH); }
  pinMode(BTN_BOOT, INPUT_PULLUP);

  // ESP-NOW en difusión: el emisor debe usar el canal 1 (el predeterminado de STA).
  WiFi.mode(WIFI_STA);
  esp_wifi_set_ps(WIFI_PS_NONE);
  if (esp_now_init() == ESP_OK) {
    esp_now_register_recv_cb(espnow_rx);
    Serial.printf("ESP-NOW listo; MAC de esta pantalla: %s\n", WiFi.macAddress().c_str());
  } else {
    Serial.println("ESP-NOW NO disponible; queda solo el enlace UART");
  }

  tft.init();
  tft.setRotation(0);               // retrato; si queda cabeza abajo en la tapa, usar 2
  BG = tft.color565(2, 5, 8);
  FG = tft.color565(238, 242, 245);
  MUTED = tft.color565(115, 128, 140);
  BAR_BG = tft.color565(18, 23, 28);
  bandas[0] = {"GRAVES", -32, 152, tft.color565(255, 122, 51), escala(255, 122, 51, .13f), escala(255, 122, 51, .45f)};
  bandas[1] = {"MEDIOS", -19, 196, tft.color565(64, 214, 128), escala(64, 214, 128, .13f), escala(64, 214, 128, .45f)};
  bandas[2] = {"AGUDOS", -28, 168, tft.color565(64, 164, 255), escala(64, 164, 255, .13f), escala(64, 164, 255, .45f)};
  abrir_vista();
}

void loop() {
  recibir();
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
  } else {
    for (int i = 0; i < enlace_cyd::BARRAS; i++)
      barra_espectro(i, vivo ? trama.barras_db[i] : espectro_ejemplo(i, t));
  }
  delay(40);  // ~25 refrescos/s; recibir() vacía todo lo pendiente en cada vuelta
}
