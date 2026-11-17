# Adaptación D.2 → D.3-LM324

El esquema D.3 usa cuatro LM324N en DIP-14 alimentados con 5 V. VREF continúa generándose desde +3.3VA y permanece cerca de 1,65 V. La PCB D.2 existente fue ruteada para MCP6004 a 3,3 V y necesita las modificaciones siguientes; no basta con insertar los LM324 en los zócalos.

## Alimentación de U1–U4

En cada LM324N:

1. Doblar el pin 4 hacia afuera antes de insertar el integrado. El pin no debe tocar el terminal 4 del zócalo, que en D.2 pertenece a +3.3VA.
2. Insertar normalmente los otros trece pines. El pin 11 permanece conectado a GND.
3. Unir el pin 4 doblado al +5 V de J6.
4. Añadir un condensador cerámico de 100 nF directamente entre los pines 4 y 11.

No conectar +5 V al agujero 4 del zócalo: eso uniría +5 V con +3.3VA. Los C4–C7 originales de D.2 pueden quedarse sobre +3.3VA; los cuatro condensadores montados directamente sobre los LM324 cumplen el desacoplo de 5 V que muestra D.3.

## Protección de las entradas del ESP32

D.3 separa cada salida del operacional (`*_RAW`) de la entrada correspondiente del ESP32 mediante dos resistencias de 10 kΩ al 1 %:

| Señal | Serie desde la salida RAW | Desde el ADC a VREF |
|---|---:|---:|
| Graves | R33 | R34 |
| Medios | R35 | R36 |
| Agudos | R37 | R38 |
| FFT | R39 | R40 |

Para cada canal se corta o levanta la conexión directa hacia el ESP32, se instala la resistencia impar de 10 kΩ en serie y se conecta la resistencia par de 10 kΩ desde el lado ESP32 a VREF. La relación resultante es:

`VADC = VREF + (VRAW − VREF) / 2`

Así, una salida extrema de 0–5 V queda entre aproximadamente 0,825 y 3,325 V. El firmware D.3 aplica el factor inverso ×2 antes de calcular niveles y FFT.

## Comprobación antes de insertar el ESP32

Con el ESP32 retirado y los cuatro LM324 instalados:

1. Confirmar 5 V entre los pines 4 y 11 de U1–U4.
2. Confirmar aproximadamente 3,3 V en +3.3VA y 1,65 V en VREF.
3. Medir `ADC_G`, `ADC_M`, `ADC_A` y `ADC_FFT`; ninguna entrada debe superar 3,3 V durante la prueba.
4. Aplicar una entrada pequeña y verificar que PRE, EQ_OUT y las salidas RAW estén centradas cerca de VREF, sin oscilación ni recorte.

La simulación con entrada máxima de diseño obtuvo 1,12–2,18 V en las entradas de los LM324 y 1,38–1,91 V en las entradas ADC. Es una validación de diseño, no evidencia de una placa física medida.
