// Ecualizador de audio de tres bandas con visualizador — firmware del ESP32-DevKitC V4.
//
// Núcleo 0, tarea `adquisicion`: toma 1024 muestras de la salida ecualizada (GPIO33) a 20 kS/s,
// lee los tres detectores de pico y VREF, calcula la FFT y deja el resultado en `ultima`.
// Núcleo 1, `loop()`: dibuja la vista activa en la TFT por franjas, atiende el pulsador y la
// página web del punto de acceso Wi-Fi.
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <Arduino.h>
#include <SPI.h>
#include <WebServer.h>
#include <WiFi.h>
#include <driver/adc.h>
#include <esp_adc_cal.h>
#include <esp_timer.h>

#include "config.h"
#include "dsp.h"
#include "interfaz.h"
#include "web.h"

using interfaz::ALTO;
using interfaz::ANCHO;

static Adafruit_ILI9341 tft(TFT_CS, TFT_DC, TFT_RST);
static WebServer servidor(80);
static esp_adc_cal_characteristics_t cal;

// ---------------------------------------------------------------- resultado compartido
struct Medida {
  dsp::Espectro esp;
  float banda_mv[3];
  float onda_v[ANCHO];
  uint32_t n;            // número de bloque, para saber si hay datos nuevos
};
static Medida ultima;
static portMUX_TYPE candado = portMUX_INITIALIZER_UNLOCKED;

static constexpr adc1_channel_t CH_VREF = ADC1_CHANNEL_0;    // GPIO36
static constexpr adc1_channel_t CH_FFT = ADC1_CHANNEL_5;     // GPIO33
static constexpr adc1_channel_t CH_BANDA[3] = {ADC1_CHANNEL_6,   // GPIO34 graves
                                               ADC1_CHANNEL_7,   // GPIO35 medios
                                               ADC1_CHANNEL_4};  // GPIO32 agudos

static float leer_v(adc1_channel_t ch, int n) {
  uint32_t suma = 0;
  for (int i = 0; i < n; ++i) suma += adc1_get_raw(ch);
  return esp_adc_cal_raw_to_voltage(suma / n, &cal) / 1000.0f;
}

static void adquisicion(void*) {
  static uint16_t crudo[dsp::N];
  static float v[dsp::N];
  static float trabajo[2 * dsp::N];
  Medida m{};
  const int64_t periodo_us = 1000000 / MUESTREO_HZ;
  for (;;) {
    // 1) bloque de N muestras a ritmo fijo (51,2 ms)
    int64_t t = esp_timer_get_time();
    for (int i = 0; i < dsp::N; ++i) {
      while (esp_timer_get_time() < t) {
      }
      crudo[i] = adc1_get_raw(CH_FFT);
      t += periodo_us;
    }
    // 2) detectores de pico (tensiones casi continuas) y VREF
    const float vref = leer_v(CH_VREF, PROMEDIO_DET);
    for (int b = 0; b < 3; ++b) m.banda_mv[b] = dsp::nivel_mv(leer_v(CH_BANDA[b], PROMEDIO_DET), vref);
    // 3) espectro
    for (int i = 0; i < dsp::N; ++i) v[i] = esp_adc_cal_raw_to_voltage(crudo[i], &cal) / 1000.0f;
    dsp::analizar(v, m.esp, trabajo);
    // 4) forma de onda disparada en el primer cruce ascendente por VREF
    int k0 = 0;
    for (int i = 1; i < dsp::N - ANCHO; ++i)
      if (v[i - 1] < vref && v[i] >= vref) {
        k0 = i;
        break;
      }
    for (int i = 0; i < ANCHO; ++i) m.onda_v[i] = v[k0 + i] - vref;
    m.n++;
    portENTER_CRITICAL(&candado);
    ultima = m;
    portEXIT_CRITICAL(&candado);
    vTaskDelay(1);
  }
}

// ---------------------------------------------------------------- página web
static Medida web_m;

static void responder_datos() {
  portENTER_CRITICAL(&candado);
  web_m = ultima;
  portEXIT_CRITICAL(&candado);
  String j;
  j.reserve(600);
  j += "{\"b\":[";
  for (int i = 0; i < 3; ++i) {
    j += String(dsp::nivel_db(web_m.banda_mv[i]), 1);
    j += i < 2 ? "," : "],\"mv\":[";
  }
  for (int i = 0; i < 3; ++i) {
    j += String(web_m.banda_mv[i], 0);
    j += i < 2 ? "," : "],\"s\":[";
  }
  for (int i = 0; i < dsp::BARRAS; ++i) {
    j += String(web_m.esp.barras_db[i], 1);
    j += i < dsp::BARRAS - 1 ? "," : "],";
  }
  j += "\"rms\":" + String(web_m.esp.rms_dbfs, 1) + ",\"pico\":" + String(web_m.esp.pico_hz, 0) +
       ",\"clip\":" + (web_m.esp.recorte ? "true" : "false") + "}";
  servidor.send(200, "application/json", j);
}

// ---------------------------------------------------------------- pantalla
static interfaz::Franja franja(40);
static interfaz::Datos datos;
static dsp::Retencion ret_banda[3], ret_barra[dsp::BARRAS];
static int vista = interfaz::BANDAS;
static uint32_t recorte_hasta = 0;

static void mostrar(interfaz::Vista v) {
  for (int y0 = 0; y0 < ALTO; y0 += franja.alto()) {
    franja.origen(y0);
    interfaz::dibujar(franja, v, datos);
    tft.drawRGBBitmap(0, y0, franja.getBuffer(), ANCHO, franja.alto());
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BOTON, INPUT_PULLUP);

  adc1_config_width(ADC_WIDTH_BIT_12);
  adc1_config_channel_atten(CH_VREF, ADC_ATTEN_DB_12);
  adc1_config_channel_atten(CH_FFT, ADC_ATTEN_DB_12);
  for (auto ch : CH_BANDA) adc1_config_channel_atten(ch, ADC_ATTEN_DB_12);
  esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN_DB_12, ADC_WIDTH_BIT_12, 1100, &cal);

  SPI.begin(TFT_SCK, TFT_MISO, TFT_MOSI, TFT_CS);
  tft.begin(TFT_SPI_HZ);
  tft.setRotation(1);   // horizontal, 320 × 240
  datos.version = FW_VERSION;
  datos.ip = "192.168.4.1";
  mostrar(interfaz::ARRANQUE);

  WiFi.mode(WIFI_AP);
  datos.wifi = WiFi.softAP(WIFI_SSID, WIFI_CLAVE);
  servidor.on("/", [] { servidor.send_P(200, "text/html", PAGINA_WEB); });
  servidor.on("/datos", responder_datos);
  servidor.begin();
  Serial.printf("Ecualizador %s. Wi-Fi \"%s\", http://%s\n", FW_VERSION, WIFI_SSID,
                WiFi.softAPIP().toString().c_str());

  xTaskCreatePinnedToCore(adquisicion, "adquisicion", 8192, nullptr, 2, nullptr, 0);
  delay(1500);
}

void loop() {
  static uint32_t t_ant = millis(), t_boton = 0, ultimo_n = 0;
  static bool boton_ant = true;

  // pulsador con antirrebote: cada pulsación pasa a la siguiente vista
  const bool boton = digitalRead(PIN_BOTON);
  if (!boton && boton_ant && millis() - t_boton > 200) {
    vista = (vista + 1) % interfaz::NUM_VISTAS;
    t_boton = millis();
  }
  boton_ant = boton;

  servidor.handleClient();

  Medida m;
  portENTER_CRITICAL(&candado);
  m = ultima;
  portEXIT_CRITICAL(&candado);
  if (m.n == ultimo_n) {
    delay(2);
    return;
  }
  ultimo_n = m.n;

  const uint32_t ahora = millis();
  const float dt = (ahora - t_ant) / 1000.0f;
  t_ant = ahora;
  for (int b = 0; b < 3; ++b) {
    datos.banda_mv[b] = m.banda_mv[b];
    datos.banda_db[b] = dsp::nivel_db(m.banda_mv[b]);
    datos.banda_pico_db[b] = ret_banda[b].actualizar(datos.banda_db[b], dt);
  }
  datos.esp = m.esp;
  for (int j = 0; j < dsp::BARRAS; ++j) datos.barras_pico_db[j] = ret_barra[j].actualizar(m.esp.barras_db[j], dt);
  memcpy(datos.onda_v, m.onda_v, sizeof datos.onda_v);
  // el aviso de recorte (o una banda sobre 0,8 V) se mantiene un segundo
  if (m.esp.recorte || m.banda_mv[0] > 800 || m.banda_mv[1] > 800 || m.banda_mv[2] > 800) recorte_hasta = ahora + 1000;
  datos.recorte = ahora < recorte_hasta;
  datos.clientes = WiFi.softAPgetStationNum();

  mostrar((interfaz::Vista)vista);
}
