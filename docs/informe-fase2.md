---
title: "Ecualizador de 3 bandas con analizador de espectro en ESP32 — Informe de la Fase 2"
author: "David Orozco · Jose Torres · Leo Rojas"
date: "22 de octubre de 2026"
lang: es
---

# Ecualizador de 3 bandas con analizador de espectro en ESP32 — Informe de la Fase 2

Electrónica II · Universidad de la Costa (CUC) · 2026-2 · David Orozco, Jose Torres, Leo Rojas. Repositorio: [github.com/davixcky/ecualizador-esp32](https://github.com/davixcky/ecualizador-esp32)

Se desarrolló la Propuesta 2 de la Fase 1, un ecualizador analógico de tres bandas con 15 amplificadores operacionales a 3,3 V, y se le sumó el analizador de espectro de la Propuesta 1 en un ESP32 con pantalla TFT. La simulación confirmó los cálculos en 23 de 24 casos y encontró un error de la propuesta original que se corrigió.

## Trabajo inicial: Fase 1

En la Fase 1 se presentaron tres alternativas para acondicionar con amplificadores operacionales una señal de bajo nivel y entregarla a un ESP32, dentro de dos líneas de negocio: audio de alta fidelidad y adquisición de señales electrofisiológicas. Las tres compartían los mismos criterios: fuente única de 3,3 V, amplificadores riel a riel (MCP6004), señal centrada en VREF = 1,65 V, lectura por el ADC1 del ESP32 y pantalla TFT ILI9341. El documento original está en [`Propuestas_Electronica_II.pdf`](fase1/Propuestas_Electronica_II.pdf).

| Propuesta | Qué hacía | Temas de Electrónica II | Papel del ESP32 | Dificultad y riesgo |
| --- | --- | --- | --- | --- |
| 1. Preamplificador con analizador de espectro | Micrófono o línea → preamplificador no inversor → Sallen-Key de 5 kHz → FFT en la TFT | No inversor, Sallen-Key, polarización | Alto: FFT y vúmetro | Baja; poco contenido de la asignatura |
| 2. Ecualizador de 3 bandas con medidor | Preamplificador → tres filtros activos → ganancia por banda → sumador; detectores de pico hacia el ESP32 | Filtros LP, HP y pasa banda, sumador, detector de picos de precisión | Medio: lee tres canales y dibuja barras | Media; ajuste fino de filtros y detector |
| 3. Monitor de ECG | Amplificador de instrumentación → pasa altas → ganancia → pasa bajas → notch de 60 Hz | Instrumentación, CMRR, notch | Alto: picos R y BPM | Alta; ruido, electrodos y seguridad |

**Decisión.** Se eligió la **Propuesta 2**, que ya era la candidata de la Fase 1: reúne más contenido de la asignatura (13 amplificadores en la versión original) con un riesgo técnico medio. Se le agregó el **analizador de espectro de la Propuesta 1**, que solo exige un filtro antialiasing más: así, al mover un control, se ve en la pantalla cómo cambia la banda y el espectro. La Propuesta 3 se descartó por su riesgo (ruido, CMRR) y porque conecta electrodos a una persona.

**Qué cambió respecto a la Fase 1**

1. Ganancia del preamplificador: de 10,2 a 3,2 (R8 de 2,4 kΩ a 10 kΩ), con un control de nivel a la entrada; la salida de un celular satura las etapas de 3,3 V con ganancia 10.
2. Banda de medios invertida (U4C) y cortes de medios en 409 Hz y 2,32 kHz: con los valores originales la suma tenía huecos de −11 dB en los cruces (ver Simulación).
3. Analizador de espectro: filtro antialiasing de 4,95 kHz (U2D) y FFT de 1024 puntos en el ESP32.
4. Salida de audio: jack de línea, módulo PAM8403 con parlante y control de volumen.

## Introducción y problema

El equipo toma el audio de un celular o un PC, lo separa en graves, medios y agudos con filtros activos, deja ajustar cada banda con un deslizable y vuelve a sumarlas. La salida se escucha por un parlante interno o por un jack de línea. Al mismo tiempo, un ESP32 muestra en una pantalla TFT el nivel de cada banda y el espectro de la señal ecualizada, y lo publica por Wi-Fi para verlo en el teléfono.

Los ecualizadores comerciales ajustan pero no muestran qué pasa en cada banda, y los digitales esconden el filtrado en un DSP. Digitalizar el audio directo en el ESP32 tampoco sirve: su ADC de 12 bits tiene poca resolución para cientos de milivoltios, no tiene filtro antialiasing y el procesamiento agrega latencia. Hacen falta etapas que centren la señal en 0–3,3 V, filtros que se sumen sin huecos, un indicador de nivel por banda que el ESP32 lea despacio y un filtro antes del ADC.

**Pregunta del proyecto:** ¿cómo separar, ajustar y volver a sumar tres bandas de audio con amplificadores operacionales a 3,3 V, y medir cada banda y el espectro con un ESP32, de modo que con los controles al centro la respuesta sea plana?

## Objetivos

**Objetivo general.** Diseñar, simular y construir un ecualizador de audio de tres bandas con filtros activos de amplificadores operacionales alimentados con 3,3 V, que muestre en una pantalla TFT controlada por un ESP32 el nivel de cada banda y el espectro de la señal ecualizada.

**Objetivos específicos**

1. **Diseñar y simular** la cadena analógica (preamplificador, filtros Sallen-Key de segundo orden, sumador y detectores de pico de precisión) de modo que, con los deslizables al 50 %, la respuesta sea plana dentro de ±1 dB entre 20 Hz y 20 kHz, los cortes queden a ±10 % del cálculo y cada banda se ajuste al menos ±5 dB.
2. **Construir** el prototipo en protoboard con más del 70 % de los dispositivos y **diseñar** su PCB de dos capas y su gabinete, verificados con el ERC y el DRC de KiCad.
3. **Programar y validar** el ESP32 para muestrear a 20 kS/s, calcular una FFT de 1024 puntos y mostrar bandas y espectro con al menos 5 imágenes por segundo: un tono de 1 kHz debe caer en el bin 51 (996 Hz) y un tono de 100 Hz, 1 kHz u 8 kHz debe encender solo la barra de su banda.

## Estado del arte

Las soluciones existentes ajustan el audio o lo muestran, pero no ambas cosas con un circuito observable.

| Solución | Tipo | Bandas | Visualización | Circuito accesible |
| --- | --- | --- | --- | --- |
| Ecualizador gráfico de rack (Behringer FBQ1502HD) | Analógico, comercial | 15 por canal | LED por banda | No |
| Control de tonos Baxandall | Analógico | 2 (graves y agudos) | No | Sí |
| Integrado MSGEQ7 | Analizador analógico | 7 | Salida multiplexada al microcontrolador | No; solo mide |
| WLED *audio reactive* (ESP32) | Digital, micrófono I²S + FFT | 16 | Tiras LED | Firmware abierto; no ecualiza |
| Placa DSP ADAU1701 | Digital (SigmaDSP) | Programables | Requiere PC | No observable |
| Room EQ Wizard | Software en PC | Continuo | Pantalla del PC | — |
| **Este proyecto** | **Analógico + ESP32** | **3 ajustables + 32 de análisis** | **TFT 2,8" y teléfono** | **Sí, etapa por etapa** |

El MSGEQ7 confirma la idea que usa este diseño: filtro, detector de pico y lectura lenta del ADC es la forma económica de medir bandas con un microcontrolador.

## Marco teórico

**Amplificador operacional a 3,3 V.** El MCP6004 tiene GBW de 1 MHz, rapidez de cambio de 0,6 V/µs, entrada y salida riel a riel y 100 µA por amplificador. Con una sola fuente, la señal bipolar se monta sobre una tierra de señal VREF = 1,65 V, hecha con un divisor y un seguidor.

**No inversor con ganancia unitaria en continua.** Un condensador en serie con Rg deja la ganancia en 1 para continua y en 1 + Rf/Rg para audio.

$$A_v = 1 + \frac{R_f}{R_g}$$

**Sallen-Key de segundo orden.** Pasa bajas con resistencias iguales R y pasa altas con condensadores iguales C:

$$f_c = \frac{1}{2\pi R\sqrt{C_1 C_2}},\quad Q = \tfrac{1}{2}\sqrt{C_1/C_2} \qquad\qquad f_c = \frac{1}{2\pi C\sqrt{R_1 R_2}},\quad Q = \tfrac{1}{2}\sqrt{R_2/R_1}$$

Con Q ≈ 0,707 la banda de paso es plana (Butterworth) y la caída fuera de banda es de 40 dB por década. Un pasa banda es un pasa altas en cascada con un pasa bajas, de centro √(fL·fH).

**Fase en los cruces.** Un pasa bajas de segundo orden tiene −90° en su corte y un pasa altas +90°. Si dos bandas vecinas se cruzan así, llegan al sumador a 180° y se cancelan. Invertir la banda del medio las pone en fase, igual que en los cruces Linkwitz-Riley de los altavoces.

**Sumador inversor.** Con Rf/Ri = 100 k/47 k = 2,13 y cada deslizable como divisor hacia VREF, al 50 % la banda llega con ganancia ≈ 1 y al 100 % sube ≈ 6 dB.

**Detector de picos de precisión.** Con el diodo dentro del lazo, el amplificador compensa su caída de 0,6 V y el condensador se carga al pico real; Rd lo descarga con τ = 220 kΩ × 100 nF = 22 ms.

**Muestreo y FFT.** A fs = 20 kS/s con N = 1024, la resolución es fs/N ≈ 19,5 Hz. El filtro de 4,95 kHz evita el aliasing y una ventana de Hann reduce la fuga espectral. Los niveles se dan en dBFS respecto a una senoidal de 0,8 V de pico.

**ADC del ESP32.** Se usa solo el ADC1 (GPIO32–39), porque el ADC2 no funciona con Wi-Fi activo; su zona lineal con 11 dB de atenuación va de 0,15 a 2,45 V.

## Arquitectura

La señal pasa por el preamplificador, se reparte en tres filtros, cada banda pasa por su deslizable y se suma en U2C (con medios invertidos por U4C). La salida va al parlante, al jack de línea y, por el antialiasing, al ESP32; de cada deslizable sale también un detector de pico.

![Diagrama de bloques del ecualizador](../img/diagrama-de-bloques.png)

| CI | Unidad A | Unidad B | Unidad C | Unidad D |
| --- | --- | --- | --- | --- |
| U1 | Seguidor de VREF | Preamplificador (G = 3,2) | Pasa bajas graves 232 Hz | Pasa altas medios 409 Hz |
| U2 | Pasa bajas medios 2,32 kHz | Pasa altas agudos 4,1 kHz | Sumador inversor | Antialiasing 4,95 kHz |
| U3 | Detector de graves | Seguidor de graves | Detector de medios | Seguidor de medios |
| U4 | Detector de agudos | Seguidor de agudos | Inversor de medios | Libre |

![Esquemático completo en KiCad 9 (ERC sin errores ni advertencias)](../img/esquematico.png)

## Lista de materiales

| Componente | Valor o referencia | Cant. |
| --- | --- | ---: |
| Amplificador operacional cuádruple riel a riel + zócalo | MCP6004-I/P, DIP-14 | 4 |
| Microcontrolador + zócalos 1 × 19 | ESP32-DevKitC V4, 38 pines | 1 |
| Pantalla | TFT ILI9341 2,8", 320 × 240, SPI | 1 |
| Resistencias de película metálica 1/4 W | 10 Ω a 220 kΩ; las de filtros al 1 % | 30 |
| Condensadores de película | 2,2 nF a 1 µF | 14 |
| Condensadores cerámicos de desacople | 100 nF | 5 |
| Condensadores electrolíticos | 10 µF (3), 100 µF (1), 470 µF (1) | 5 |
| Potenciómetros deslizables lineales | 10 kΩ, 30 mm (graves, medios, agudos) | 3 |
| Potenciómetros rotativos logarítmicos | 10 kΩ (nivel y volumen) | 2 |
| Diodos de señal | 1N4148 | 3 |
| Jacks estéreo 3,5 mm | Entrada y salida | 2 |
| Pulsador 6 × 6 mm | Cambio de vista | 1 |
| Amplificador de audio + parlante | Módulo PAM8403 + parlante 3 W, 4 Ω | 1 |
| Montaje | 2 protoboards de 830 puntos, cables Dupont, separadores M3 | — |

La lista completa por referencia está en el README del repositorio y en `hardware/fabricacion/bom.csv`.

## Simulación

La cadena completa se simuló en ngspice con un macromodelo del MCP6004: 23 de 24 casos cumplen, y el que no cumple es el diseño original de la Fase 1, que motivó el cambio.

| Caso | Resultado | Criterio |
| --- | --- | --- |
| VREF en reposo | 1,641 V | 3,3 VA / 2 ± 0,5 % |
| Ganancia del preamplificador a 1 kHz | 3,20 (10,1 dB) | 3,2 ± 5 % |
| Cortes: graves / medios HP / medios LP / agudos | 239 Hz / 403 Hz / 2,39 kHz / 4,03 kHz | ± 10 % del cálculo |
| Antialiasing: corte y atenuación a 15 kHz | 5,10 kHz; −19,3 dB | ± 10 %; ≤ −15 dB |
| Respuesta con deslizables al 50 % | −0,27 a +0,88 dB | rizado ≤ 1,5 dB |
| Mismo caso con valores de la Fase 1 | −11,0 a +0,1 dB | **No cumple: motivó el rediseño** |
| Rango de ajuste (graves, medios, agudos) | +6,4 / +6,0 / +6,3 dB al 100 % | ≥ +5 dB |
| Selectividad 100 Hz / 1 kHz / 8 kHz | solo sube la barra de su banda | ≥ 4 veces las otras |
| Linealidad y ataque del detector | error 2,0 %; 1,17 ms | ≤ 10 %; ≤ 5 ms |
| Margen del ADC con entrada de 0,11 V y todo al máximo | 1,11 a 2,17 V | 0,15 a 2,45 V |

**Cambio de diseño.** Con los valores de la Fase 1, la suma con los controles al centro tenía dos huecos de −11 dB, cerca de 300 Hz y 3 kHz: en cada cruce la banda de medios y su vecina llegaban en contrafase. Al invertir los medios con la unidad libre U4C y mover sus cortes a 409 Hz y 2,32 kHz, la respuesta quedó plana sin agregar integrados.

![Respuesta de cada banda, suma plana frente a la Fase 1, familia de curvas al mover cada deslizable y detector de picos](../img/sim-ecualizador.png)

![Selectividad de los detectores y linealidad del detector de medios](../img/sim-detectores.png)

**Demostración en vivo.** Abrir `simulacion/ac_plano.cir` en ngspice o LTspice y graficar `vdb(EQ_OUT)-vdb(PRE)`; con `tran_tono_1000.cir`, graficar `v(ADC_G) v(ADC_M) v(ADC_A)` para ver que solo sube la barra de medios.

## PCB, protoboard y gabinete

**PCB.** Placa de dos capas de 200 × 120 mm en KiCad 9, con componentes de inserción y ruteada con Freerouting: 0 pads sin conectar y 0 diferencias con el esquemático. La placa es también el panel: pantalla, deslizables, perillas y pulsador quedan arriba, y los jacks y el USB salen por el borde derecho. Quedan 9 avisos no eléctricos de serigrafía y conexiones térmicas.

![Modelo 3D de la PCB en KiCad](../img/3d-placa-iso.png)

**Protoboard.** El prototipo se arma en dos protoboards de 830 puntos, en el orden de la señal y probando cada etapa antes de seguir. Van en la protoboard los integrados, pasivos, diodos y el ESP32: 62 de los 72 componentes (86 %, por encima del 70 % exigido). Jacks, potenciómetros y pantalla se conectan con cables Dupont.

![Distribución en las protoboards y orden de montaje](../img/protoboard-zonas.png)

| Paso | Etapa | Prueba | Esperado |
| --: | --- | --- | --- |
| 1 | Alimentación y VREF | Multímetro en VREF | 1,64–1,66 V |
| 2 | Preamplificador | 100 mV a 1 kHz en la entrada | 320 mV de pico en PRE |
| 3 | Cada filtro | Barrido de 20 Hz a 20 kHz | Cortes ± 10 % |
| 4 | Deslizables y sumador | Barrido con controles al 50 % | Salida plana ± 1 dB |
| 5 | Detectores | Tonos de 100 Hz, 1 kHz y 8 kHz | Solo sube su barra |
| 6 | ESP32 y pantalla | Tono de 1 kHz | Pico en 996 Hz |

**Prototipo (gabinete).** Caja de 208 × 128 × 46,5 mm en PLA impreso, con tapa-panel de acrílico negro de 3 mm cortado con láser que se atornilla a cuatro separadores de latón. La tapa lleva la ventana de la pantalla, las ranuras de los deslizables con escala y los textos grabados; el parlante va en el fondo con su rejilla. Se modeló en CadQuery con las mismas coordenadas de la PCB, así cada agujero cae sobre su pieza.

![Gabinete cerrado](../img/3d-gabinete-cerrado.png)

![Gabinete con la tapa levantada: PCB, ESP32 y pantalla en su zócalo](../img/3d-gabinete-abierto.png)

## Firmware y pantallas

El firmware compila en PlatformIO (RAM 19,7 %, flash 62,8 %) y sus 19 pruebas de procesamiento pasan en el PC.

- **Núcleo 0:** toma 1024 muestras a 20 kS/s, lee los tres detectores y VREF, calcula la FFT con ventana de Hann y arma 32 barras de 40 Hz a 5 kHz, el nivel en dBFS, el tono dominante y el aviso de recorte (CLIP).
- **Núcleo 1:** dibuja la vista activa por franjas de 320 × 40 píxeles, atiende el pulsador y sirve una página web en la red Wi-Fi propia *Ecualizador-ESP32*.
- Las pruebas encontraron que bajo 300 Hz dos barras leían el mismo bin de la FFT; ahora cada barra tiene al menos un bin.

![Vistas de la pantalla: arranque, bandas, espectro y osciloscopio](../img/ui-tft-vistas.png)

## Pendiente y referencias

Todo lo anterior es diseño, simulación y código que compila: el circuito todavía no se ha armado ni medido.

- [ ] Armar el montaje en protoboard siguiendo los seis pasos y medir cada etapa con generador y osciloscopio
- [ ] Repetir con el equipo físico las pruebas de la simulación (cortes, respuesta plana, selectividad)
- [ ] Cargar el firmware y comprobar el tono de 1 kHz en 996 Hz y al menos 5 imágenes por segundo
- [ ] Medir los agujeros reales del módulo TFT antes de fabricar la PCB o cortar la tapa
- [ ] Hacer los bocetos a mano del prototipo que pide la rúbrica

**Referencias**

1. A. S. Sedra y K. C. Smith, *Microelectronic Circuits*, 7.ª ed. Oxford University Press, 2015.
2. S. Franco, *Design with Operational Amplifiers and Analog Integrated Circuits*, 4.ª ed. McGraw-Hill, 2015.
3. P. Horowitz y W. Hill, *The Art of Electronics*, 3.ª ed. Cambridge University Press, 2015.
4. J. Karki, "Analysis of the Sallen-Key Architecture," Texas Instruments, SLOA024B, 2002.
5. Microchip Technology, "MCP6001/2/4: 1 MHz, Low-Power Op Amp," hoja de datos DS20001733.
6. S. H. Linkwitz, "Active Crossover Networks for Noncoincident Drivers," *J. Audio Eng. Soc.*, vol. 24, n.º 1, pp. 2–8, 1976.
7. A. V. Oppenheim y R. W. Schafer, *Discrete-Time Signal Processing*, 3.ª ed. Pearson, 2010.
8. F. J. Harris, "On the Use of Windows for Harmonic Analysis with the DFT," *Proc. IEEE*, vol. 66, n.º 1, pp. 51–83, 1978.
9. Espressif Systems, *ESP32 Technical Reference Manual* y guía del ADC en ESP-IDF.
10. Repositorio del proyecto: [github.com/davixcky/ecualizador-esp32](https://github.com/davixcky/ecualizador-esp32)
