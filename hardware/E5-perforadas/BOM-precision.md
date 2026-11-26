# Lista de materiales de precisión · E.5 perforadas

> **Actualización del 20 de noviembre de 2026.** Esta lista es de planificación. Lo realmente comprado y respaldado por factura o albarán está en [`../COMPONENTES-COMPRADOS-VERIFICADOS.md`](../COMPONENTES-COMPRADOS-VERIFICADOS.md). Cambios respecto a lo escrito abajo: **parlantes** = conjunto WS-14595 (dos de 8 Ω / 5 W en un conector), no uno de 4 Ω / 3 W; **luces** = tira BTF-LIGHTING FCOB WS2811 de **12 V** (ASIN B0BW5T6HW4, un píxel cada 50 mm), no WS2812B de 5 V, por lo que falta definir la alimentación de 12 V; **RV1/RV5** = A10K sin comprar (hay dos P-20K logarítmicos como candidatos sin validar); **no hay potenciómetros deslizables**. **Pantalla** = la TFT de 1,9″ se sustituyó por una ESP32-3248S035 de 3,5″ (recibida el 2026-11-24; se esperaba una LilyGO T4-S3): datos por ESP-NOW, +5V/GND por J7 y UART2 solo de respaldo (PROPUESTO); el esquema maestro ya la refleja junto con el ESP32 DevKit V1 de 30 pines. **Tapa** = cierre con imanes de Ø6 × 2 mm, sin bisagras. El modelo 3D y sus pendientes están en [`3d/`](3d/README.md).

Cantidades netas para las cuatro tarjetas. Para compra se recomienda añadir al menos dos unidades de cada valor pequeño y 10 % en los valores repetidos.

## Resistencias fijas

Todas deben ser **película metálica, 1/4 W, tolerancia de 1 % o mejor**. No usar resistencias de carbón de 5 % en filtros, ganancias o detectores.

| Valor | Cant. | Referencias | Especificación |
|---:|---:|---|---|
| 10 Ω | 1 | R1 | Película metálica, 1 %, 0,25 W |
| 100 Ω | 1 | R23 | Película metálica, 1 %, 0,25 W |
| 330 Ω | 1 | R31 | Película metálica, 1 %, 0,25 W |
| 2,7 kΩ | 1 | R15 | Película metálica, 1 %, 0,25 W |
| 5,6 kΩ | 1 | R16 | Película metálica, 1 %, 0,25 W |
| 10 kΩ | 10 | R2, R3, R33–R40 | **0,1 % recomendado**, 25 ppm/°C; divisores de VREF y ADC |
| 10 kΩ | 10 | R4, R5, R8–R10, R13, R14, R25, R26, R32 | Película metálica, 1 %, 0,25 W |
| 22 kΩ | 1 | R7 | Película metálica, 1 %, 0,25 W |
| 27 kΩ | 1 | R11 | Película metálica, 1 %, 0,25 W |
| 47 kΩ | 6 | R17–R21, R24 | Película metálica, 1 %, 0,25 W |
| 56 kΩ | 1 | R12 | Película metálica, 1 %, 0,25 W |
| 100 kΩ | 2 | R6, R22 | Película metálica, 1 %, 0,25 W |
| 220 kΩ | 3 | R27–R29 | Película metálica, 1 %, 0,25 W; usar el mismo lote |

Total: **40 resistencias**.

Para R2/R3 y cada pareja R33/R34, R35/R36, R37/R38 y R39/R40, lo más importante es que ambos valores estén bien emparejados. Si no se consiguen al 0,1 %, medir resistencias de 1 % con multímetro y formar parejas cuya diferencia sea menor de 0,2 %.

## Capacitores de precisión para señal y filtros

Usar **película de poliéster o polipropileno, tolerancia ±5 % o mejor**, tensión nominal de 50 V o superior. Evitar cerámicos Z5U/Y5V en estas posiciones.

| Valor | Cant. | Referencias | Especificación |
|---:|---:|---|---|
| 2,2 nF | 1 | C21 | Película, ±5 % |
| 4,7 nF | 2 | C16, C20 | Película, ±5 %; mismo lote |
| 10 nF | 5 | C13–C15, C17, C18 | Película, ±5 %; mismo lote |
| 47 nF | 1 | C12 | Película, ±5 % |
| 100 nF | 4 | C11, C22–C24 | Película, ±5 %; C22–C24 del mismo lote |
| 1 µF | 1 | C9 | Película, ±5 % preferido; ±10 % máximo |

Total: **14 capacitores de película de señal**.

## Desacople cerámico

| Valor | Cant. | Referencias | Especificación |
|---:|---:|---|---|
| 100 nF | 6 | C2, C4–C7, C25 | Cerámico X7R, ±10 %, 50 V |

C4–C7 deben soldarse directamente entre los pines 4 y 11 de cada LM324. C25 debe quedar junto a U6.

## Electrolíticos y reserva de energía

| Valor | Cant. | Referencias | Especificación |
|---:|---:|---|---|
| 10 µF | 2 | C8, C19 | Electrolítico polar, 16 V, 105 °C, ±20 % |
| 10 µF | 1 | C10 | **Bipolar/no polar preferido**, 16 V; alternativamente película |
| 100 µF | 1 | C1 | Electrolítico, 10 V o 16 V, 105 °C |
| 470 µF | 1 | C3 | Electrolítico, 10 V o 16 V, 105 °C, baja ESR preferida |
| 1000 µF | 1 | C26 | Electrolítico, 10 V o 16 V, 105 °C, baja ESR |

Los electrolíticos no necesitan tolerancia de precisión. Verificar polaridad antes de energizar.

## Semiconductores y controles

| Componente | Cant. | Referencias | Especificación |
|---|---:|---|---|
| LM324N DIP-14 | 4 | U1–U4 | Original de fabricante reconocido; usar zócalos DIP-14 |
| 74HCT245 DIP-20 | 1 | U6 | Sustitución local validada para el NeoPixel; alimentar a 5 V, DIR=1 y /OE=0 |
| ESP32 DevKit V1, 30 pines | 1 | U5 | En mano; montar en dos zócalos hembra 1 × 15 (filas a 22,86 mm) |
| 1N4148 | 3 | D1–D3 | Mismo fabricante/lote recomendado |
| Potenciómetro 10 kΩ lineal | 3 | RV2–RV4 | Misma serie y mismo lote; tolerancia típica ±20 % |
| Potenciómetro 10 kΩ logarítmico | 2 | RV1, RV5 | Audio/logarítmico |

## Conectores propios del equipo

| Componente | Cant. | Referencia/uso | Especificación |
|---|---:|---|---|
| Jack estéreo hembra 3,5 mm | 2 | J1, J2 | Con terminales identificables T/R/S; para placa perforada puede ser de panel |
| Bornera 2 vías, paso 5,08 mm | 1 | J6 | Entrada de fuente +5 V/GND; corriente nominal ≥3 A |
| Conector 1 × 4 | 1 | J3 | PAM8403: +5V, GND, AMP_IN, GND |
| Conector 1 × 3 | 1 | J5 | NeoPixel: +5V, DIN, GND |
| Conector 1 × 4 | 1 | J7 | Pantalla: +5V, GND y UART2 de respaldo (CYD_TX, CYD_RX); los datos van por ESP-NOW |
| Pulsador momentáneo 6 × 6 mm | 1 | SW1 | Normalmente abierto |

**Nota de la pantalla (2026-11-25):** desaparecen el conector J4 de 8 vías, el cable GH1.25 y la R30 de la TFT SPI. La pantalla ESP32-3248S035 va en la tapa y recibe los datos por ESP-NOW; J7 solo le lleva +5V/GND, y sus pines UART2 son un respaldo cableado **PROPUESTO** (aún sin probar en el montaje).

## Conectores entre las cuatro tarjetas

Se recomienda una familia con seguro, por ejemplo JST-XH de 2,50 mm auténtico o equivalente de 2,54 mm. No mezclar orientaciones entre cables.

| Conector | Machos de placa | Carcasas hembra | Uso |
|---|---:|---:|---|
| 4 vías | 10 | 10 | Tres cables JBUS, un JAB y un JC4 |
| 5 vías | 2 | 2 | JBC |
| 2 vías | 2 | 2 | JB4 |
| Terminales crimp | — | 70 recomendados | Se utilizan 54; comprar repuestos |

Para `+5V` y `GND` usar cable de 22 AWG. Para VREF y señales usar 26 AWG. Mantener los cables analógicos cortos y llevar un GND junto a cada arnés.

## Módulos, pantalla, sonido e iluminación

| Componente | Cant. | Especificación |
|---|---:|---|
| Pantalla ESP32-3248S035 de 3,5 pulgadas | 1 | 480 × 320, controlador ST7796, recibida; datos por ESP-NOW y +5V/GND desde J7 |
| Módulo amplificador PAM8403 | 1 | 5 V, 2 × 3 W; usar un solo canal según J3 |
| Parlante | 1 | 4 Ω, 3 W, diámetro aproximado 40–50 mm |
| Tira WS2812B | 12 LED | 5 V, tira de 10 mm; dos tramos de aproximadamente 100 mm |
| Fuente regulada | 1 | 5 V, 3 A, con protección contra cortocircuito |
| Cable USB para programación | 1 | No permitir que VBUS alimente simultáneamente con la fuente externa |
| Cable de audio 3,5 mm | 1 | Macho–macho, preferiblemente apantallado |
| Perillas | 5 | Compatibles con los ejes de RV1–RV5 |

## Material de montaje

| Material | Cant. | Especificación |
|---|---:|---|
| Tarjeta perforada T1 | 1 | Aproximadamente 90 × 70 mm, paso 2,54 mm, pads individuales |
| Tarjeta perforada T2 | 1 | Aproximadamente 100 × 70 mm, paso 2,54 mm, pads individuales |
| Tarjeta perforada T3 | 1 | Aproximadamente 100 × 70 mm, paso 2,54 mm, pads individuales |
| Tarjeta perforada T4 | 1 | Aproximadamente 100 × 80 mm, paso 2,54 mm, pads individuales |
| Zócalo DIP-14 | 4 | Para los cuatro LM324; preferiblemente torneados |
| Zócalo DIP-20 | 1 | Para el 74HCT245; preferiblemente torneado |
| Zócalo hembra 1 × 15 | 2 | Para el ESP32 DevKit V1 de 30 pines; filas a 22,86 mm |
| Espadines de prueba | 20 aprox. | VREF, PRE, bandas, EQ_OUT, ADC y alimentaciones |
| Alambre de cobre estañado | 4 m | Diámetro 0,8–1,0 mm para barras locales de +5V/GND |
| Cable rígido estañado | 1 rollo | 24–26 AWG solo para puentes cortos de señal |
| Cable flexible rojo/negro | 3 m de cada color | 22 AWG para ramas en estrella de +5V/GND |
| Cable flexible de señales | 1 juego | 26 AWG; varios colores |
| Regleta/bloque de distribución | 2 | Mínimo 7 posiciones y ≥5 A; una para +5V y otra para GND |
| Portafusible y fusible | 1 + repuesto | Fusible en línea de 3 A en la salida de +5 V |
| Interruptor general | 1 | Capacidad nominal mínima de 5 A DC |
| Separadores M3, tornillos y tuercas | 16 juegos | Cuatro apoyos por tarjeta |
| Estaño y flux | Según necesidad | Flux no corrosivo; limpiar residuos después de soldar |
| Tubo termorretráctil | Según necesidad | Aislar empalmes y terminales expuestos |

La distribución de +5 V y GND debe hacerse en estrella hacia T1, T2, T3, T4, PAM8403 y WS2812B. El interruptor general y el fusible aún no aparecen en el esquema eléctrico; se instalan antes de los bloques de distribución.

## Recomendación de compra

- Comprar resistencias metálicas de 1 % en cinta, no surtidos sin identificación.
- Comprar diez resistencias de 10 kΩ al 0,1 % para las referencias críticas, más dos repuestos.
- No mezclar tecnologías o tolerancias entre los componentes de un mismo filtro.
- Rotular cada bolsa con valor y referencias antes de comenzar el montaje.
- Comprar primero una unidad de cada módulo activo y comprobar sus dimensiones y pinout antes de cortar las tarjetas.
