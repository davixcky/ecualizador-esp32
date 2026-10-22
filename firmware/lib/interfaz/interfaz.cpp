#include "interfaz.h"
#include <Fonts/FreeSansBold9pt7b.h>
#include <math.h>
#include <stdio.h>
namespace interfaz {
static constexpr uint16_t rgb(int r,int g,int b){return ((r&248)<<8)|((g&252)<<3)|(b>>3);}
static constexpr uint16_t BG=rgb(15,19,23), FG=rgb(235,238,240), MUT=rgb(156,166,174), GRID=rgb(47,57,63);
static constexpr uint16_t C[3]={rgb(255,122,61),rgb(61,220,132),rgb(51,181,255)};
static const char* N[3]={"GRAVES","MEDIOS","AGUDOS"};
static void text(Adafruit_GFX&g,const char*s,int x,int y,uint16_t c=FG,bool title=false){
 g.setFont(title?&FreeSansBold9pt7b:nullptr);g.setTextSize(1);g.setTextColor(c);g.setCursor(x,y);g.print(s);
}
static void header(Adafruit_GFX&g,const char*s,const Datos&d){
 text(g,s,10,20,FG,true);text(g,d.recorte?"CLIP":(d.wifi?"Wi-Fi":"SIN RED"),266,11,d.recorte?rgb(255,65,65):MUT);
 g.drawFastHLine(10,28,300,GRID);
}
static void bands(Adafruit_GFX&g,const Datos&d){
 header(g,"TRES BANDAS",d);char b[40];
 for(int i=0;i<3;++i){int x=12+104*i;
  text(g,N[i],x,39,C[i]);snprintf(b,sizeof b,"%.0f dB",d.banda_db[i]);text(g,b,x,66,FG,true);
  for(int k=0;k<14;++k){bool on=(d.banda_db[i]+40)/40*14>k;g.fillRect(x,130-k*4,86,3,on?C[i]:GRID);}
  snprintf(b,sizeof b,"%.0f mV",d.banda_mv[i]);text(g,b,x,144,MUT);
 }
 text(g,"Pico por banda respecto a VREF",12,159,MUT);
}
static void spectrum(Adafruit_GFX&g,const Datos&d){
 header(g,"ESPECTRO",d);char b[40];
 const int x0=28,y0=40,y1=136;
 for(int k=0;k<=3;++k){int y=y0+k*32;g.drawFastHLine(x0,y,280,GRID);snprintf(b,sizeof b,"%d",-20*k);text(g,b,2,y-3,MUT);}
 for(int j=0;j<dsp::BARRAS;++j){
  float db=fmaxf(-60,fminf(0,d.esp.barras_db[j]));int h=lroundf((db+60)/60*96);int x=x0+j*280/dsp::BARRAS;
  float f=sqrtf(dsp::borde_barra(j)*dsp::borde_barra(j+1));g.fillRect(x+1,y1-h,6,h,C[f<300?0:f<3100?1:2]);
 }
 text(g,"40 Hz",28,143,MUT);text(g,"5 kHz",272,143,MUT);
 snprintf(b,sizeof b,"Pico %.0f Hz   %.1f dBFS",d.esp.pico_hz,d.esp.rms_dbfs);text(g,b,28,158);
}
static void wave(Adafruit_GFX&g,const Datos&d){
 header(g,"FORMA DE ONDA",d);
 for(int y=38;y<=142;y+=26)g.drawFastHLine(10,y,300,GRID);
 for(int x=10;x<=310;x+=30)g.drawFastVLine(x,38,104,GRID);
 int prev=90;
 for(int i=0;i<300;++i){int y=90-lroundf(d.onda_v[i]*52/dsp::PLENA_ESCALA_V);y=y<38?38:y>142?142:y;if(i)g.drawLine(9+i,prev,10+i,y,C[2]);prev=y;}
 text(g,"0,4 V/div    1,5 ms/div",10,154,MUT);
}
void dibujar(Adafruit_GFX&g,Vista v,const Datos&d){
 g.setTextWrap(false);g.fillScreen(BG);
 switch(v){case BANDAS:bands(g,d);break;case ESPECTRO:spectrum(g,d);break;case ONDA:wave(g,d);break;
 default:
  text(g,"ECUALIZADOR",24,48,FG,true);
  text(g,"3 bandas / ESP32",24,65,MUT);
  for(int i=0;i<3;++i)g.fillRect(24+i*94,87,82,3,C[i]);
  text(g,"Waveshare 1.9  /  320 x 170",24,108);
  text(g,"Boton: bandas, espectro y onda",24,128,MUT);
  text(g,d.version?d.version:"",24,148,MUT);break;
 }
}
} // namespace interfaz
