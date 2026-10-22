#include <Adafruit_NeoPixel.h>
// Ensayo visual: colores por banda, sin lectura de audio ni simulacion analogica.
Adafruit_NeoPixel leds(12, 25, NEO_GRB + NEO_KHZ800);
void setup() {
  Serial.begin(115200);
  leds.begin();
  leds.setBrightness(32);
  Serial.println("Ensayo de 12 LED / GPIO25 / brillo 32. Patron programado, sin audio.");
}
void loop() {
  for (int paso=0; paso<12; ++paso) {
    for (int i=0; i<12; ++i) {
      uint8_t nivel = i == paso ? 255 : 0;
      if (i<4) leds.setPixelColor(i, leds.Color(nivel, nivel*100/255, 0));
      else if (i<8) leds.setPixelColor(i, leds.Color(0, nivel, nivel*60/255));
      else leds.setPixelColor(i, leds.Color(0, nivel*180/255, nivel));
    }
    leds.show();
    Serial.printf("Paso %d: LED %d\n", paso, paso+1);
    delay(160);
  }
}
