#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
Adafruit_ILI9341 tft(5,21,22);
const int pins[3]={34,35,32};
const int N=1024;float re[N],im[N],lastHz=0;int fftSpan=0;
void spectrum(){
 int lo=4095,hi=0;double mean=0;uint32_t start=micros(),next=start;
 for(int i=0;i<N;i++){while((int32_t)(micros()-next)<0){};int v=analogRead(33);lo=min(lo,v);hi=max(hi,v);re[i]=v;mean+=v;im[i]=0;next+=50;}
 float fs=1e6f*N/(micros()-start);mean/=N;fftSpan=hi-lo;
 for(int i=0;i<N;i++)re[i]=(re[i]-mean)*(.5f-.5f*cosf(2*PI*i/(N-1)));
 for(int i=1,j=0;i<N;i++){int bit=N>>1;for(;j&bit;bit>>=1)j^=bit;j^=bit;if(i<j){float t=re[i];re[i]=re[j];re[j]=t;}}
 for(int len=2;len<=N;len*=2){float ar=cosf(-2*PI/len),ai=sinf(-2*PI/len);for(int base=0;base<N;base+=len){float wr=1,wi=0;for(int j=0;j<len/2;j++){int a=base+j,b=a+len/2;float vr=re[b]*wr-im[b]*wi,vi=re[b]*wi+im[b]*wr;re[b]=re[a]-vr;im[b]=im[a]-vi;re[a]+=vr;im[a]+=vi;float w=wr*ar-wi*ai;wi=wr*ai+wi*ar;wr=w;}}}
 int peak=1;for(int i=1;i<N/2;i++){re[i]=sqrtf(re[i]*re[i]+im[i]*im[i]);if(re[i]>re[peak])peak=i;}
 lastHz=fftSpan>3?peak*fs/N:0;
}
void setup(){Serial.begin(115200);analogReadResolution(12);analogSetAttenuation(ADC_11db);SPI.begin(18,-1,23,5);tft.begin();tft.setRotation(1);tft.fillScreen(ILI9341_BLACK);tft.setTextSize(2);tft.setTextColor(ILI9341_WHITE);tft.setCursor(8,8);tft.print("ECUALIZADOR / ESP32");
 const char*names[]={"GRAVES","MEDIOS","AGUDOS"};uint16_t colors[]={ILI9341_ORANGE,ILI9341_GREEN,ILI9341_CYAN};
 for(int k=0;k<3;k++){int y=38+k*38;tft.setCursor(8,y);tft.setTextColor(colors[k]);tft.print(names[k]);tft.drawRect(8,y+21,300,10,colors[k]);}
 tft.setCursor(8,215);tft.setTextColor(ILI9341_WHITE);tft.print("FFT: bins, sin calibrar");
}
void loop(){
 float ref=0,val[3]={};
 for(int i=0;i<64;i++){ref+=analogRead(36);for(int k=0;k<3;k++)val[k]+=analogRead(pins[k]);delayMicroseconds(100);}
 ref/=64;int dom=0;
 for(int k=0;k<3;k++){val[k]=(val[k]/64-ref)*3.3/4095;if(val[k]>val[dom])dom=k;}
 const char*names[]={"GRAVES","MEDIOS","AGUDOS"};uint16_t colors[]={ILI9341_ORANGE,ILI9341_GREEN,ILI9341_CYAN};
 for(int k=0;k<3;k++){int y=38+k*38;tft.setCursor(180,y);tft.setTextColor(colors[k],ILI9341_BLACK);char label[16];snprintf(label,sizeof(label),"%4.0f mV ",val[k]*1000);tft.print(label);tft.fillRect(9,y+22,298,8,ILI9341_BLACK);tft.fillRect(9,y+22,constrain(int(val[k]*900),0,298),8,colors[k]);}

 spectrum();
 tft.fillRect(0,156,320,53,ILI9341_BLACK);
 for(int bar=0;bar<32;bar++){int bin=1+bar*8;float mag=0;for(int j=bin;j<bin+8;j++)mag=max(mag,re[j]);int h=constrain(int(mag/300),0,48);tft.fillRect(8+bar*9,207-h,7,h,ILI9341_CYAN);}
 Serial.printf("CADENA G=%.5f M=%.5f A=%.5f DOM=%d REF=%.1f FFT_HZ=%.1f FFT_SPAN=%d TFT=OK\n",val[0],val[1],val[2],dom,ref,lastHz,fftSpan);delay(150);
}
