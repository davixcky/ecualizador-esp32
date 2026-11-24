// Sonda de diagnóstico del CYD: identifica el controlador del panel y el pin de luz de fondo.
// La pantalla quedó NEGRA con ILI9341 y ST7789 en GPIO21: aquí se prueban GPIO21 y GPIO27
// por fases, se lee el ID del controlador por SPI y se informa todo por el puerto serie.
// Fases (el LED RGB de la placa acompaña): ROJO = luz en 21, VERDE = luz en 27, AZUL = ambas.
#include <Arduino.h>
#include <TFT_eSPI.h>

TFT_eSPI tft;
static const int LED_R = 4, LED_G = 16, LED_B = 17;   // ánodo común: LOW enciende
static const int BL_A = 21, BL_B = 27;

static void led(bool r, bool g, bool b) {
  digitalWrite(LED_R, r ? LOW : HIGH);
  digitalWrite(LED_G, g ? LOW : HIGH);
  digitalWrite(LED_B, b ? LOW : HIGH);
}

void setup() {
  Serial.begin(115200);
  for (int p : {LED_R, LED_G, LED_B}) { pinMode(p, OUTPUT); digitalWrite(p, HIGH); }
  pinMode(BL_A, OUTPUT); pinMode(BL_B, OUTPUT);
  digitalWrite(BL_A, LOW); digitalWrite(BL_B, LOW);

  tft.init();
  tft.setRotation(0);
  tft.fillScreen(TFT_RED);   // si alguna luz enciende, se debe ver ROJO (o un color si el driver no coincide)

  Serial.println();
  Serial.println("=== SONDA CYD: identificacion del panel ===");
  // RDDID (0x04): ST7789 tipico 85 85 52; ST7796 via 0xD3: 00 77 96; ILI9341 via 0xD3: 00 93 41
  uint8_t id04[4], idd3[4];
  for (int i = 0; i < 4; i++) id04[i] = tft.readcommand8(0x04, i);
  for (int i = 0; i < 4; i++) idd3[i] = tft.readcommand8(0xD3, i);
  Serial.printf("RDDID 0x04: %02X %02X %02X %02X\n", id04[0], id04[1], id04[2], id04[3]);
  Serial.printf("RDID4 0xD3: %02X %02X %02X %02X\n", idd3[0], idd3[1], idd3[2], idd3[3]);
  if (idd3[2] == 0x93 && idd3[3] == 0x41) Serial.println("Controlador: ILI9341");
  else if (idd3[2] == 0x77 && idd3[3] == 0x96) Serial.println("Controlador: ST7796 (panel de 3,2 pulgadas S032)");
  else if (id04[1] == 0x85 && id04[2] == 0x85) Serial.println("Controlador: ST7789");
  else Serial.println("Controlador: NO identificado (bus SPI sin respuesta o pines distintos)");
  Serial.println("Fases de luz de fondo: LED ROJO = GPIO21, LED VERDE = GPIO27, LED AZUL = ambas.");
  Serial.println("Observar en cual fase la pantalla se ilumina.");
}

void loop() {
  struct { bool a, b; bool r, g, bl; const char *msg; } fases[] = {
    {true,  false, true,  false, false, "FASE 1: luz en GPIO21 (LED rojo)"},
    {false, true,  false, true,  false, "FASE 2: luz en GPIO27 (LED verde)"},
    {true,  true,  false, false, true,  "FASE 3: luz en 21 y 27 (LED azul)"},
    {false, false, false, false, false, "FASE 4: todo apagado (LED apagado)"},
  };
  for (auto &f : fases) {
    digitalWrite(BL_A, f.a ? HIGH : LOW);
    digitalWrite(BL_B, f.b ? HIGH : LOW);
    led(f.r, f.g, f.bl);
    Serial.println(f.msg);
    delay(3000);
  }
}
