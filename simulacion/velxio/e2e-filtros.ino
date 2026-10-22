#include <Adafruit_NeoPixel.h>
#include <math.h>
Adafruit_NeoPixel leds(12,25,NEO_GRB+NEO_KHZ800);
const int pins[3]={34,35,32};
void setup(){Serial.begin(115200);leds.begin();leds.setBrightness(32);analogReadResolution(12);analogSetAttenuation(ADC_11db);for(int p:pins)pinMode(p,INPUT);}
void loop(){
 double sum[3]={},sq[3]={};int n=2048;
 for(int i=0;i<n;i++){for(int k=0;k<3;k++){double v=analogRead(pins[k]);sum[k]+=v;sq[k]+=v*v;}delayMicroseconds(37);}
 float rms[3];int dominant=0;
 for(int k=0;k<3;k++){rms[k]=sqrt(fmax(0,sq[k]/n-pow(sum[k]/n,2)));if(rms[k]>rms[dominant])dominant=k;}
 for(int k=0;k<3;k++){int bars=constrain(lround(rms[k]/20),0,4);for(int j=0;j<4;j++){uint32_t c=k==0?leds.Color(255,100,0):k==1?leds.Color(0,255,60):leds.Color(0,180,255);leds.setPixelColor(k*4+j,j<bars?c:0);}}
 leds.show();Serial.printf("E2E RMS_ADC G=%.2f M=%.2f A=%.2f DOM=%d\n",rms[0],rms[1],rms[2],dominant);Serial.printf("MEAN %.0f %.0f %.0f\n",sum[0]/n,sum[1]/n,sum[2]/n);delay(80);
}
