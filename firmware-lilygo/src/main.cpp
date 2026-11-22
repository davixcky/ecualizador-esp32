#include <Arduino.h>
#include <Preferences.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <LilyGo_AMOLED.h>
#include <LV_Helper.h>
#include <lvgl.h>

namespace {
constexpr int BUTTON_PIN = 0;
constexpr int VIEW_COUNT = 4;
constexpr int CONTENT_VIEW_COUNT = 3;

const lv_color_t BG = lv_color_hex(0x050607);
const lv_color_t PANEL = lv_color_hex(0x171A1E);
const lv_color_t PANEL2 = lv_color_hex(0x24282E);
const lv_color_t MUTED = lv_color_hex(0x8B929B);
const lv_color_t WHITE = lv_color_hex(0xF4F2EC);
const lv_color_t RED_CUC = lv_color_hex(0xC8102E);
const lv_color_t ORANGE = lv_color_hex(0xFF9F43);
const lv_color_t GREEN = lv_color_hex(0x38D996);
const lv_color_t BLUE = lv_color_hex(0x4D9FFF);
const lv_color_t BAND_COLORS[] = {ORANGE, GREEN, BLUE};

LilyGo_Class amoled;
Preferences preferences;
WiFiManager wifi_manager;

lv_obj_t *screens[VIEW_COUNT] = {};
lv_obj_t *band_values[3] = {};
lv_obj_t *band_bars[3] = {};
lv_obj_t *spectrum_bars[24] = {};
lv_obj_t *wave_chart = nullptr;
lv_chart_series_t *wave_series = nullptr;
int32_t wave_points[100] = {};
lv_obj_t *wifi_name = nullptr;
lv_obj_t *wifi_ip = nullptr;
lv_obj_t *portal_label = nullptr;
lv_obj_t *portal_button = nullptr;
lv_obj_t *brightness_label = nullptr;

int active_view = 0;
int last_content_view = 0;
int brightness = 190;
bool portal_active = false;
uint32_t portal_started = 0;

lv_obj_t *label(lv_obj_t *parent, const char *text, const lv_font_t *font, lv_color_t color) {
  lv_obj_t *obj = lv_label_create(parent);
  lv_label_set_text(obj, text);
  lv_obj_set_style_text_font(obj, font, 0);
  lv_obj_set_style_text_color(obj, color, 0);
  return obj;
}

lv_obj_t *panel(lv_obj_t *parent, int x, int y, int w, int h) {
  lv_obj_t *obj = lv_obj_create(parent);
  lv_obj_set_pos(obj, x, y);
  lv_obj_set_size(obj, w, h);
  lv_obj_set_style_bg_color(obj, PANEL, 0);
  lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);
  lv_obj_set_style_border_width(obj, 0, 0);
  lv_obj_set_style_radius(obj, 18, 0);
  lv_obj_set_style_pad_all(obj, 0, 0);
  lv_obj_set_scrollable(obj, false);
  lv_obj_set_gesture_bubble(obj, true);
  return obj;
}

void showView(int view, lv_screen_load_anim_t animation) {
  view = constrain(view, 0, VIEW_COUNT - 1);
  if (view == active_view && lv_screen_active() == screens[view]) return;
  active_view = view;
  if (view < CONTENT_VIEW_COUNT) last_content_view = view;
  lv_screen_load_anim(screens[view], animation, 220, 0, false);
  Serial.printf("LVGL view -> %d\n", view);
}

void tabEvent(lv_event_t *event) {
  if (lv_event_get_code(event) != LV_EVENT_CLICKED) return;
  const int view = static_cast<int>(reinterpret_cast<intptr_t>(lv_event_get_user_data(event)));
  showView(view, LV_SCR_LOAD_ANIM_FADE_IN);
}

void gestureEvent(lv_event_t *event) {
  if (lv_event_get_code(event) != LV_EVENT_GESTURE) return;
  lv_indev_t *indev = lv_indev_active();
  if (!indev) return;
  const lv_dir_t direction = lv_indev_get_gesture_dir(indev);
  lv_indev_wait_release(indev);
  if (direction == LV_DIR_LEFT && active_view < CONTENT_VIEW_COUNT) {
    showView((active_view + 1) % CONTENT_VIEW_COUNT, LV_SCR_LOAD_ANIM_MOVE_LEFT);
  } else if (direction == LV_DIR_RIGHT && active_view < CONTENT_VIEW_COUNT) {
    showView((active_view + CONTENT_VIEW_COUNT - 1) % CONTENT_VIEW_COUNT,
             LV_SCR_LOAD_ANIM_MOVE_RIGHT);
  } else if (direction == LV_DIR_BOTTOM && active_view != 3) {
    showView(3, LV_SCR_LOAD_ANIM_MOVE_BOTTOM);
  } else if (direction == LV_DIR_TOP && active_view == 3) {
    showView(last_content_view, LV_SCR_LOAD_ANIM_MOVE_TOP);
  }
  Serial.printf("LVGL gesture dir=%d active=%d\n", direction, active_view);
}

void addHeader(lv_obj_t *screen, const char *title, int selected) {
  lv_obj_t *head = panel(screen, 15, 12, 570, 82);
  lv_obj_t *logo = lv_obj_create(head);
  lv_obj_set_pos(logo, 13, 12);
  lv_obj_set_size(logo, 58, 31);
  lv_obj_set_style_bg_color(logo, lv_color_black(), 0);
  lv_obj_set_style_bg_opa(logo, LV_OPA_COVER, 0);
  lv_obj_set_style_border_width(logo, 0, 0);
  lv_obj_set_style_radius(logo, 8, 0);
  lv_obj_set_style_pad_all(logo, 0, 0);
  lv_obj_set_gesture_bubble(logo, true);
  lv_obj_t *cuc = label(logo, "CUC", &lv_font_montserrat_20, RED_CUC);
  lv_obj_center(cuc);
  lv_obj_t *heading = label(head, title, &lv_font_montserrat_24, WHITE);
  lv_obj_set_pos(heading, 88, 8);
  lv_obj_t *sub = label(head, "ECUALIZADOR E.5  /  SIMULACION LVGL", &lv_font_montserrat_14, MUTED);
  lv_obj_set_pos(sub, 89, 39);

  const char *names[] = {"BANDAS", "ESPECTRO", "ONDA", "AJUSTES"};
  for (int i = 0; i < VIEW_COUNT; ++i) {
    lv_obj_t *tab = lv_button_create(head);
    lv_obj_set_pos(tab, 13 + i * 91, 53);
    lv_obj_set_size(tab, 85, 21);
    lv_obj_set_style_radius(tab, 9, 0);
    lv_obj_set_style_shadow_width(tab, 0, 0);
    lv_obj_set_style_bg_color(tab, i == selected ? WHITE : PANEL2, 0);
    lv_obj_set_style_bg_opa(tab, LV_OPA_COVER, 0);
    lv_obj_set_style_pad_all(tab, 0, 0);
    lv_obj_set_gesture_bubble(tab, true);
    lv_obj_add_event_cb(tab, tabEvent, LV_EVENT_CLICKED, reinterpret_cast<void *>(i));
    lv_obj_t *text = label(tab, names[i], &lv_font_montserrat_14, i == selected ? BG : MUTED);
    lv_obj_center(text);
  }
}

lv_obj_t *makeScreen(const char *title, int selected) {
  lv_obj_t *screen = lv_obj_create(nullptr);
  lv_obj_remove_style_all(screen);
  lv_obj_set_style_bg_color(screen, BG, 0);
  lv_obj_set_style_bg_opa(screen, LV_OPA_COVER, 0);
  lv_obj_set_scrollable(screen, false);
  lv_obj_set_clickable(screen, true);
  lv_obj_add_event_cb(screen, gestureEvent, LV_EVENT_GESTURE, nullptr);
  addHeader(screen, title, selected);
  screens[selected] = screen;
  return screen;
}

void buildBands() {
  lv_obj_t *screen = makeScreen("TRES BANDAS", 0);
  const char *names[] = {"GRAVES", "MEDIOS", "AGUDOS"};
  const char *ranges[] = {"40 - 300 Hz", "300 Hz - 3.1 kHz", "3.1 - 5 kHz"};
  for (int i = 0; i < 3; ++i) {
    lv_obj_t *card = panel(screen, 20 + i * 193, 112, 174, 305);
    lv_obj_set_style_border_width(card, 1, 0);
    lv_obj_set_style_border_color(card, BAND_COLORS[i], 0);
    lv_obj_t *name = label(card, names[i], &lv_font_montserrat_18, BAND_COLORS[i]);
    lv_obj_set_pos(name, 18, 18);
    band_values[i] = label(card, "-00.0", &lv_font_montserrat_32, WHITE);
    lv_obj_set_pos(band_values[i], 18, 58);
    lv_obj_t *unit = label(card, "dBFS", &lv_font_montserrat_14, MUTED);
    lv_obj_set_pos(unit, 113, 82);
    band_bars[i] = lv_bar_create(card);
    lv_obj_set_pos(band_bars[i], 18, 124);
    lv_obj_set_size(band_bars[i], 138, 24);
    lv_bar_set_range(band_bars[i], -42, 0);
    lv_obj_set_style_bg_color(band_bars[i], PANEL2, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(band_bars[i], LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_bg_color(band_bars[i], BAND_COLORS[i], LV_PART_INDICATOR);
    lv_obj_set_style_radius(band_bars[i], 10, LV_PART_MAIN | LV_PART_INDICATOR);
    lv_obj_set_gesture_bubble(band_bars[i], true);
    lv_obj_t *range = label(card, ranges[i], &lv_font_montserrat_14, MUTED);
    lv_obj_align(range, LV_ALIGN_BOTTOM_MID, 0, -18);
  }
}

void buildSpectrum() {
  lv_obj_t *screen = makeScreen("ESPECTRO", 1);
  lv_obj_t *area = panel(screen, 28, 108, 544, 292);
  for (int i = 0; i < 24; ++i) {
    spectrum_bars[i] = lv_bar_create(area);
    lv_obj_set_pos(spectrum_bars[i], 18 + i * 21, 18);
    lv_obj_set_size(spectrum_bars[i], 13, 230);
    lv_bar_set_range(spectrum_bars[i], 0, 60);
    lv_obj_set_style_bg_color(spectrum_bars[i], PANEL2, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(spectrum_bars[i], LV_OPA_COVER, LV_PART_MAIN);
    const lv_color_t color = i < 8 ? ORANGE : (i < 18 ? GREEN : BLUE);
    lv_obj_set_style_bg_color(spectrum_bars[i], color, LV_PART_INDICATOR);
    lv_obj_set_style_radius(spectrum_bars[i], 4, LV_PART_MAIN | LV_PART_INDICATOR);
    lv_obj_set_gesture_bubble(spectrum_bars[i], true);
  }
  lv_obj_t *low = label(area, "40 Hz", &lv_font_montserrat_14, MUTED);
  lv_obj_set_pos(low, 18, 260);
  lv_obj_t *high = label(area, "5 kHz", &lv_font_montserrat_14, MUTED);
  lv_obj_align(high, LV_ALIGN_BOTTOM_RIGHT, -18, -12);
  lv_obj_t *hint = label(screen, "DESLIZA  <  CAMBIAR VISTA  >", &lv_font_montserrat_14, WHITE);
  lv_obj_align(hint, LV_ALIGN_BOTTOM_MID, 0, -16);
}

void buildWave() {
  lv_obj_t *screen = makeScreen("FORMA DE ONDA", 2);
  lv_obj_t *area = panel(screen, 20, 106, 560, 290);
  wave_chart = lv_chart_create(area);
  lv_obj_set_pos(wave_chart, 18, 18);
  lv_obj_set_size(wave_chart, 524, 230);
  lv_chart_set_type(wave_chart, LV_CHART_TYPE_LINE);
  lv_chart_set_point_count(wave_chart, 100);
  lv_chart_set_range(wave_chart, LV_CHART_AXIS_PRIMARY_Y, -100, 100);
  lv_obj_set_style_bg_color(wave_chart, PANEL, LV_PART_MAIN);
  lv_obj_set_style_bg_opa(wave_chart, LV_OPA_COVER, LV_PART_MAIN);
  lv_obj_set_style_border_color(wave_chart, PANEL2, LV_PART_MAIN);
  lv_obj_set_style_line_color(wave_chart, PANEL2, LV_PART_MAIN);
  lv_obj_set_style_line_width(wave_chart, 1, LV_PART_MAIN);
  lv_obj_set_style_line_width(wave_chart, 3, LV_PART_ITEMS);
  lv_obj_set_style_size(wave_chart, 0, 0, LV_PART_INDICATOR);
  lv_obj_set_gesture_bubble(wave_chart, true);
  lv_chart_set_div_line_count(wave_chart, 7, 9);
  wave_series = lv_chart_add_series(wave_chart, BLUE, LV_CHART_AXIS_PRIMARY_Y);
  lv_obj_t *scale = label(area, "0.4 V/div     1.5 ms/div", &lv_font_montserrat_14, MUTED);
  lv_obj_set_pos(scale, 18, 260);
  lv_obj_t *clean = label(area, "SENAL LIMPIA", &lv_font_montserrat_14, GREEN);
  lv_obj_align(clean, LV_ALIGN_BOTTOM_RIGHT, -18, -14);
}

void startPortal();
void stopPortal();

void portalEvent(lv_event_t *event) {
  if (lv_event_get_code(event) != LV_EVENT_CLICKED) return;
  if (portal_active) stopPortal(); else startPortal();
}

void brightnessEvent(lv_event_t *event) {
  if (lv_event_get_code(event) != LV_EVENT_CLICKED) return;
  const int delta = static_cast<int>(reinterpret_cast<intptr_t>(lv_event_get_user_data(event)));
  brightness = constrain(brightness + delta, 30, 255);
  amoled.setBrightness(brightness);
  preferences.putUChar("brightness", brightness);
  lv_label_set_text_fmt(brightness_label, "%d / 255", brightness);
  Serial.printf("BRIGHTNESS %d\n", brightness);
}

lv_obj_t *settingsButton(lv_obj_t *parent, int x, int y, int w, const char *text,
                         lv_color_t color) {
  lv_obj_t *button = lv_button_create(parent);
  lv_obj_set_pos(button, x, y);
  lv_obj_set_size(button, w, 42);
  lv_obj_set_style_bg_color(button, color, 0);
  lv_obj_set_style_bg_opa(button, LV_OPA_COVER, 0);
  lv_obj_set_style_radius(button, 13, 0);
  lv_obj_set_style_shadow_width(button, 0, 0);
  lv_obj_set_style_pad_all(button, 0, 0);
  lv_obj_set_gesture_bubble(button, true);
  lv_obj_t *caption = label(button, text, &lv_font_montserrat_14,
                            lv_color_eq(color, WHITE) ? BG : WHITE);
  lv_obj_center(caption);
  return button;
}

void buildSettings() {
  lv_obj_t *screen = makeScreen("AJUSTES", 3);
  lv_obj_t *network = panel(screen, 20, 112, 270, 124);
  lv_obj_t *network_title = label(network, "RED", &lv_font_montserrat_14, MUTED);
  lv_obj_set_pos(network_title, 18, 16);
  wifi_name = label(network, "Sin conexion", &lv_font_montserrat_20, WHITE);
  lv_obj_set_pos(wifi_name, 18, 47);
  wifi_ip = label(network, "Configura desde el portal", &lv_font_montserrat_14, MUTED);
  lv_obj_set_pos(wifi_ip, 18, 86);

  lv_obj_t *portal = panel(screen, 310, 112, 270, 124);
  lv_obj_t *portal_title = label(portal, "PORTAL CAUTIVO", &lv_font_montserrat_14, MUTED);
  lv_obj_set_pos(portal_title, 18, 16);
  portal_label = label(portal, "Configurar Wi-Fi", &lv_font_montserrat_18, WHITE);
  lv_obj_set_pos(portal_label, 18, 44);
  portal_button = settingsButton(portal, 18, 74, 234, "INICIAR PORTAL", BLUE);
  lv_obj_add_event_cb(portal_button, portalEvent, LV_EVENT_CLICKED, nullptr);

  lv_obj_t *bright = panel(screen, 20, 254, 270, 164);
  lv_obj_t *bright_title = label(bright, "BRILLO", &lv_font_montserrat_14, MUTED);
  lv_obj_set_pos(bright_title, 18, 18);
  brightness_label = label(bright, "", &lv_font_montserrat_24, WHITE);
  lv_obj_set_pos(brightness_label, 18, 51);
  lv_label_set_text_fmt(brightness_label, "%d / 255", brightness);
  lv_obj_t *minus = settingsButton(bright, 18, 100, 92, "-", PANEL2);
  lv_obj_t *plus = settingsButton(bright, 160, 100, 92, "+", WHITE);
  lv_obj_add_event_cb(minus, brightnessEvent, LV_EVENT_CLICKED, reinterpret_cast<void *>(-25));
  lv_obj_add_event_cb(plus, brightnessEvent, LV_EVENT_CLICKED, reinterpret_cast<void *>(25));

  lv_obj_t *touch = panel(screen, 310, 254, 270, 164);
  lv_obj_t *touch_title = label(touch, "PANTALLA TACTIL", &lv_font_montserrat_14, MUTED);
  lv_obj_set_pos(touch_title, 18, 18);
  lv_obj_t *touch_state = label(touch, amoled.hasTouch() ? "CST226 + LVGL" : "No detectado",
                                &lv_font_montserrat_18, amoled.hasTouch() ? GREEN : ORANGE);
  lv_obj_set_pos(touch_state, 18, 55);
  lv_obj_t *hint = label(touch, "Desliza arriba para volver", &lv_font_montserrat_14, MUTED);
  lv_obj_set_pos(hint, 18, 105);
}

void startPortal() {
  wifi_manager.setConfigPortalBlocking(false);
  wifi_manager.setConfigPortalTimeout(180);
  portal_active = true;
  portal_started = millis();
  wifi_manager.startConfigPortal("Ecualizador-Setup", "ecualizador");
  lv_label_set_text(portal_label, "Ecualizador-Setup activo");
  lv_label_set_text(lv_obj_get_child(portal_button, 0), "DETENER PORTAL");
  lv_obj_set_style_bg_color(portal_button, ORANGE, 0);
  Serial.println("PORTAL START: SSID=Ecualizador-Setup password=ecualizador IP=192.168.4.1");
}

void stopPortal() {
  wifi_manager.stopConfigPortal();
  portal_active = false;
  lv_label_set_text(portal_label, "Configurar Wi-Fi");
  lv_label_set_text(lv_obj_get_child(portal_button, 0), "INICIAR PORTAL");
  lv_obj_set_style_bg_color(portal_button, BLUE, 0);
  Serial.println("PORTAL STOP");
}

float bandLevel(int band, float t) {
  const float base[] = {-13.0f, -20.0f, -27.0f};
  return constrain(base[band] + 8.0f * sinf(t * (0.75f + band * 0.13f) + band * 1.8f) +
                   2.5f * sinf(t * 2.7f + band), -42.0f, -2.0f);
}

void animationTimer(lv_timer_t *) {
  const float t = millis() / 1000.0f;
  for (int i = 0; i < 3; ++i) {
    const float db = bandLevel(i, t);
    lv_label_set_text_fmt(band_values[i], "%.1f", db);
    lv_bar_set_value(band_bars[i], static_cast<int>(db), LV_ANIM_ON);
  }
  for (int i = 0; i < 24; ++i) {
    const float envelope = 14 + 36 * expf(-powf((i - (6 + 4 * sinf(t * .35f))) / 4.2f, 2));
    const int value = constrain(static_cast<int>(envelope + 7 * sinf(t * 2.0f + i * .67f)), 2, 60);
    lv_bar_set_value(spectrum_bars[i], value, LV_ANIM_ON);
  }
  if (wave_series) {
    for (int i = 0; i < 100; ++i) {
      const float p = i / 99.0f * 8.0f * PI;
      wave_points[i] = static_cast<int32_t>(
          64 * sinf(p + t * 3.1f) + 21 * sinf(p * 2.7f + t * 1.4f));
    }
    lv_chart_set_series_values(wave_chart, wave_series, wave_points, 100);
  }
  static uint32_t last_network_update = 0;
  if (millis() - last_network_update > 1000) {
    last_network_update = millis();
    const bool connected = WiFi.status() == WL_CONNECTED;
    lv_label_set_text(wifi_name, connected ? WiFi.SSID().c_str() : "Sin conexion");
    lv_label_set_text(wifi_ip, connected ? WiFi.localIP().toString().c_str() :
                                      "Configura desde el portal");
    lv_obj_set_style_text_color(wifi_name, connected ? GREEN : WHITE, 0);
  }
}
}  // namespace

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  if (!amoled.beginAMOLED_241(true, true)) while (true) delay(1000);
  amoled.setRotation(0);
  amoled.enableTouch();
  preferences.begin("eq-ui", false);
  brightness = preferences.getUChar("brightness", 190);
  amoled.setBrightness(brightness);
  WiFi.mode(WIFI_STA);
  WiFi.begin();
  beginLvglHelper(amoled);
  buildBands();
  buildSpectrum();
  buildWave();
  buildSettings();
  lv_screen_load(screens[0]);
  lv_timer_create(animationTimer, 60, nullptr);
  Serial.printf("ECUALIZADOR LVGL READY: %ux%u LVGL=%d.%d MAC=%s TOUCH=%s\n",
                amoled.width(), amoled.height(), LVGL_VERSION_MAJOR, LVGL_VERSION_MINOR,
                WiFi.macAddress().c_str(), amoled.hasTouch() ? "OK" : "NO");
}

void loop() {
  const uint32_t now = millis();
  static bool last_button = true;
  const bool button = digitalRead(BUTTON_PIN);
  if (last_button && !button) {
    if (active_view == 3) showView(last_content_view, LV_SCR_LOAD_ANIM_MOVE_TOP);
    else showView((active_view + 1) % CONTENT_VIEW_COUNT, LV_SCR_LOAD_ANIM_MOVE_LEFT);
  }
  last_button = button;
  if (portal_active) {
    wifi_manager.process();
    if (now - portal_started > 180000) stopPortal();
  }
  lv_timer_handler();
  delay(5);
}
