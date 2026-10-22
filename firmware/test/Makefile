prueba: prueba_dsp.cpp ../lib/dsp/dsp.cpp ../lib/dsp/dsp.h
	g++ -std=c++17 -O2 -Wall -I../lib/dsp -o prueba_dsp prueba_dsp.cpp ../lib/dsp/dsp.cpp
	./prueba_dsp

# Pantallas de la TFT dibujadas en el PC. Requiere las bibliotecas de PlatformIO (pio pkg install).
GFX ?= ../.pio/libdeps/esp32dev/Adafruit GFX Library
pantallas: pantallas.cpp ../lib/interfaz/interfaz.cpp ../lib/interfaz/interfaz.h ../lib/dsp/dsp.cpp
	g++ -std=c++17 -O2 -Wall -DARDUINO=100 -Iarduino -I"$(GFX)" -I../lib/interfaz -I../lib/dsp \
	    -o pantallas pantallas.cpp ../lib/interfaz/interfaz.cpp ../lib/dsp/dsp.cpp "$(GFX)/Adafruit_GFX.cpp"
	mkdir -p salida
	./pantallas salida
	python3 componer_pantallas.py salida ../../img
