# Circuito → ESP32 → pantalla

Abrir **https://velxio.dev/editor?esp32sim=qemu**. Importar `integrado-1000Hz.vlx` con File → Import project y pulsar Run. Para cambiar el tono, importar los casos de 100 Hz y 8000 Hz. La TFT muestra lecturas reales del ADC emulado; no contiene valores de banda precargados.

La cadena ensayada incluye entrada, preamplificador, filtros, controles al centro, inversión de medios, sumador, salida de línea, detectores, filtro previo al ADC, ESP32 y pantalla. La TFT ILI9341 de 240 × 320 sustituye a la Waveshare únicamente en el simulador. Usa SCK 18, MOSI 23, CS 5, DC 21 y RESET 22. El equipo físico conserva su Waveshare de 170 × 320.

## Qué comprobar

- 100 Hz: la barra de graves debe superar las otras dos.
- 1 kHz: debe predominar medios.
- 8 kHz: debe predominar agudos.
- El monitor serie imprime `CADENA`, las tres lecturas, la banda dominante (0/1/2) y la variación de ADC_FFT.

El criterio automático exige dos lecturas consecutivas con la banda esperada, más de 5 mV y una relación superior a 2 respecto a las otras bandas. Los registros `validacion-integrado-*.json` conservan las lecturas, el resultado y el estado de SPICE.

## Alcance del modelo

Los R y C y las conexiones de las etapas proceden de `herramientas/circuito.py`. `correspondencia-esquema.json` relaciona referencias y redes. Los potenciómetros al centro se representan mediante dos resistencias iguales: el terminal GND del widget de potenciómetro de Velxio se asocia a masa global y no permite conservar VREF en estas etapas.

Se usan operacionales ideales y diodos genéricos sin ruptura inversa. Combinar un operacional sin límites de alimentación con el modelo de ruptura de la 1N4148 producía un comportamiento incorrecto del detector. Esta aproximación comprueba la conexión funcional; no valida saturación, ruido, distorsión, ancho de banda ni tolerancias del MCP6004.

La entrada izquierda recibe 0,2 V de pico sin offset. La entrada derecha está a 0 V. En CANAL_R, amplitud 0 y frecuencia 10 Hz mantienen una ventana transitoria de 0,4 s en el cálculo automático de Velxio; no se inyecta un segundo tono. Las lecturas incluyen el comportamiento transitorio y no son un patrón de amplitud estacionaria.

**La FFT no está calibrada en frecuencia en esta emulación.** Se calcula con las muestras del ADC, pero el valor de frecuencia del diagnóstico no coincide de forma fiable con el generador. La pantalla indica «bins, sin calibrar». No usarla como frecuencímetro ni presentar este ensayo como validación completa del analizador espectral.

El modelo no incluye el PAM8403/parlante ni el adaptador AHCT y la tira LED. El ensayo `led-animado.vlx` es independiente. Usar el esquema físico para esas etapas.

## Si no arranca

Comprobar que la URL contiene `esp32sim=qemu`. El motor JavaScript conserva únicamente una muestra de la forma de onda del ADC y no sirve para esta prueba. Esperar a que SPICE termine de resolver después de importar. Si aparece una advertencia de circuito incompleto, comprobar primero que el estado actual de SPICE converge; no continuar ante un error persistente del solver. La compilación inicial puede tardar.

Para ver todo el circuito, usar Reset view y reducir el zoom. Para leer la TFT, ampliar esa zona. Los archivos funcionan mediante importación; no se ha publicado un proyecto compartido en una cuenta de Velxio.
