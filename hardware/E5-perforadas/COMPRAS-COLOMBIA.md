# Guía de compra en Colombia · E.5 perforadas

Enlaces y disponibilidad revisados el **16 de noviembre de 2026**. El inventario y los precios pueden cambiar; comprobarlos antes de pagar. Las cantidades indicadas incluyen repuestos razonables cuando una falla detendría el montaje.

Esta guía complementa `BOM-precision.md`: la BOM sigue siendo la autoridad para valores, cantidades netas y referencias eléctricas.

## Compra prioritaria

| Artículo | Comprar | Proveedor y enlace | Selección y observaciones |
|---|---:|---|---|
| LM324N | 5 | [Electronilab · LM324](https://electronilab.co/tienda/lm324-amplificador-operacional/) | Debe ser **PDIP/DIP-14**. Se usan cuatro y queda uno de repuesto. No comprar versión SMD. |
| 74HCT245 | 2 | [Sigma Electrónica · 74HCT245 DIP-20](https://www.sigmaelectronica.net/producto/74hct245/) | **Sustitución local seleccionada para U6.** Se usa uno y queda uno de repuesto. Es HCT, acepta 3,3 V como alto cuando trabaja a 5 V y entrega una salida de 5 V. |
| Zócalos DIP-14 | 4 | [Sigma Electrónica · base 14 pines](https://www.sigmaelectronica.net/producto/base-14-pines/) | Uno para cada LM324. Preferir contacto torneado si lo ofrecen. |
| Zócalo DIP-20 | 1 + 1 opcional | [Sigma Electrónica · bases para integrados](https://www.sigmaelectronica.net/categoria-producto/conectores-y-cableado/conectores-pcb-de-insercion/) | Para el 74HCT245. Confirmar 20 pines y ancho de 7,62 mm. |
| ESP32 DevKit, 38 pines | 1 + 1 opcional | [Didácticas · ESP32-WROOM-32D, 38 pines](https://www.didacticaselectronicas.com/shop/d-esp32-wr-32d-tarjeta-de-desarrollo-esp32-wroom-32d-14753) | Verificar **38 pines**, ancho y orden de pines contra T4 antes de soldar los zócalos. |
| Pantalla 1,9 pulgadas | 1 | [CVR Electrónica · ST7789 170 × 320 SPI](https://www.cvrelectronica.com/description/?product_id=1602) | Coincide en tamaño, resolución, controlador e interfaz. Sus pines visibles son `GND,VCC,SCL,SDA,RES,DC,CS,BLK`: cablear **por nombre**, no por posición de J4. |
| Pantalla, alternativa | 1 | [Electrónica SFG · ST7789 170 × 320](https://www.electronicasafg.com/productos/pantalla-tft-ips-1-9-pulgadas-spi-st7789-170x320-arduino-1tl2w/) | Misma condición: comprobar el pinout impreso antes de fabricar el cable. |
| Amplificador PAM8403 | 1 + 1 opcional | [Electronilab · PAM8403 2 × 3 W](https://electronilab.co/tienda/mini-amplificador-digital-pam8403-de-audio-dual-de-3w-clase-d/) | 5 V; el prototipo usa un canal. No unir entre sí las salidas negativas de parlante. |
| Parlante | 1 | [Didácticas · 4 Ω, 3 W con cable](https://www.didacticaselectronicas.com/shop/productos-de-audio-parlante-524/parl-4-3w-2831-parlante-con-altavoz-de-cavidad-4-ohm-3w-54401) | Es una carga adecuada para el PAM8403. El conector PH2.0 puede cortarse o adaptarse. |
| LED direccionables | 2 módulos | [Electronilab · barra de 8 WS2812](https://electronilab.co/tienda/neopixel-stick-8-x-led-rgb-ws2812-drivers-integrados/) | Solución más económica que un rollo de 5 m. Se pueden usar 6 LED de cada barra por software, o los 16 si se actualiza la configuración. Alimentar a 5 V. |
| Fuente | 1 | [Electronilab · 5 V, 5 A, 25 W](https://electronilab.co/tienda/fuente-conmutada-5v-dc-5a-25w/) | Supera el mínimo de 3 A y deja margen para audio y LED. Es una fuente abierta conectada a red: montarla dentro de caja aislante, con tierra de protección, fusible e interruptor. Si no se puede hacer esto de forma segura, usar un adaptador cerrado certificado de 5 V y ≥3 A. |

### Conexión de U6 con el 74HCT245 local

| Pin | Conexión |
|---:|---|
| 1, DIR | +5 V; selecciona dirección A→B |
| 2, A0 | `LED_DATA` desde GPIO25 del ESP32 |
| 18, B0 | `LED_5V`, luego R31 de 330 Ω y DIN de los WS2812B |
| 19, /OE | GND; habilita las salidas |
| 20, VCC | +5 V |
| 10, GND | GND |
| 3–9, A1–A7 | GND; no dejar entradas flotantes |
| 11–17, B7–B1 | Sin conexión |

C25 de 100 nF debe quedar directamente entre los pines 20 y 10. El pinout no coincide con el antiguo 74AHCT125 DIP-14; usar zócalo DIP-20 y seguir el esquema E.5 actualizado.

## Potenciómetros y mando

| Artículo | Comprar | Enlace | Observación |
|---|---:|---|---|
| Potenciómetro 10 kΩ lineal, `B10K` | 3 + 1 repuesto | [Electronilab · B10K lineal](https://electronilab.co/tienda/potenciometro-lineal-b-10k-ohm-15mm/) | Para RV2–RV4. Comprar los cuatro de la misma serie/lote. La letra `B` debe estar marcada en el cuerpo. |
| Potenciómetro 10 kΩ logarítmico, `A10K` | 2 + 1 repuesto | [Sigma · 10 kΩ logarítmico](https://www.sigmaelectronica.net/producto/pot1v-10k/) | Para RV1 y RV5. Confirmar curva de audio/logarítmica y diámetro del eje antes de comprar perillas. |
| Perillas | 5 + 1 | Comprar en la misma tienda que los potenciómetros | Deben coincidir con el eje: liso/estriado y diámetro, normalmente 6 mm. No comprarlas antes de confirmar los potenciómetros físicos. |
| Pulsador momentáneo THT | 2 | [Electronilab · pulsador lateral 6 × 6 mm](https://electronilab.co/tienda/micro-boton-pulsador-switch-de-2-pines-angulo-recto/) | Se usa uno en SW1; montaje pasante, normalmente abierto. |

Los potenciómetros comerciales suelen ser ±20 %; no hace falta que sean multivuelta ni de “precisión”. La precisión de las bandas la fijan las resistencias y capacitores del filtro. Para los tres controles de banda importa más usar la misma serie y verificar con multímetro que su resistencia total sea parecida.

## Conectores, bornera y arneses

La opción más fácil de ensamblar a mano es JST-XH/XH2.54 con cabezales de placa y cables ya crimpados. Para cables entre dos tarjetas se necesitan conectores en **ambos extremos**; no contar un pigtail de un solo extremo como cable terminado.

| Artículo | Cantidad mínima | Enlace | Uso |
|---|---:|---|---|
| Cabezal XH 4 vías | 10 | [Electronilab · macho XH2.54 4P](https://electronilab.co/tienda/conector-macho-xh2-54-2-54mm-4p/) | Tres JBUS, JAB y JC4, con ambos extremos contados. |
| Cabezal XH 5 vías | 2 | [Electronilab · familia JST-XH](https://electronilab.co/etiqueta-producto/jst-xh2-54/) | JBC. Elegir 5P de la misma familia y orientación. |
| Cabezal XH 2 vías | 2 | [Electronilab · familia JST-XH](https://electronilab.co/etiqueta-producto/jst-xh2-54/) | JB4. |
| Carcasa hembra 4 vías | 10 | [Electronilab · familia JST-XH](https://electronilab.co/etiqueta-producto/jst-xh2-54/) | Para los cinco cables de cuatro vías. |
| Carcasa hembra 5 vías | 2 | [Electronilab · familia JST-XH](https://electronilab.co/etiqueta-producto/jst-xh2-54/) | Para JBC. |
| Carcasa hembra 2 vías | 2 | [Electronilab · familia JST-XH](https://electronilab.co/etiqueta-producto/jst-xh2-54/) | Para JB4. |
| Terminal crimp XH | 70 | [Electronilab · familia JST-XH](https://electronilab.co/etiqueta-producto/jst-xh2-54/) | Se usan 54; los restantes cubren crimps fallidos. Confirmar que el terminal corresponda a la carcasa elegida. |
| Pigtail XH 4P, opcional | Según estrategia | [Electronilab · cable XH 4P para soldar](https://electronilab.co/tienda/cable-conector-xh2-54-mm-4p-para-soldar/) | Evita comprar crimpadora, pero trae conector solo en un extremo. Para un arnés desmontable completo hay que empalmar dos o conseguir cable hembra-hembra. |
| Pigtail XH 5P, opcional | Según estrategia | [Electronilab · cable XH 5P para soldar](https://electronilab.co/tienda/cable-conector-xh2-54-2-54mm-5p-para-soldar/) | Igual advertencia que el 4P. |
| Bornera 2 vías, 5,08 mm | 2 | [Electronilab · bornera 2P 5.08](https://electronilab.co/tienda/terminal-bornera-2p-5-08mm/) | Se usa una en J6. Confirmar capacidad ≥3 A; comprar una de repuesto. |
| Jack estéreo hembra 3,5 mm THT | 2 + 1 | [Electronilab · PJ313D 5 pines](https://electronilab.co/tienda/conector-jack-estereo-hembra-negro-pj313d-3-5-mm-para-pcb/) | Identificar con multímetro contactos T/R/S y contactos conmutados; el dibujo mecánico puede no caber directo en la perforada. También puede montarse fuera de la tarjeta y cablearse. |
| Header hembra 1 × 40 | 1 tira | [Sigma · headers hembra](https://www.sigmaelectronica.net/categoria-producto/conectores-y-cableado/conectores-pcb-de-insercion/headers-hembra/) | Cortar dos secciones 1 × 19 para el ESP32. Presentar el módulo antes de soldar. |
| Conector de pantalla 1 × 8 | 1 par | Comprar después de recibir la pantalla | La pantalla CVR propuesta tiene ocho pines de paso aparente 2,54 mm; usar header hembra o ocho cables Dupont. **No comprar GH1.25 a ciegas**: el conector depende de la pantalla física. |
| Cable 22 AWG rojo/negro | 3 m de cada color | [Electronilab · cables](https://electronilab.co/categoria-producto/componentes/cable/) | Ramas en estrella de +5 V y GND. |
| Cable 26 AWG, varios colores | 5–10 m total | [Electronilab · cables](https://electronilab.co/categoria-producto/componentes/cable/) | Señales, VREF y arneses; mantener señales analógicas cortas. |
| Cable audio 3,5 mm macho–macho | 1 | Tienda local de audio/computación | Preferir apantallado y corto. |
| Cable USB de programación | 1 | Comprar después de confirmar el ESP32 | El DevKit recomendado usa micro-USB; si se compra la variante USB-C, el cable cambia. No alimentar a la vez por USB y por la fuente externa. |

Para la distribución definitiva comprar **3 m rojos y 3 m negros de 22 AWG**, dos regletas de al menos siete posiciones y 5 A —una para +5 V y otra para GND—, 4 m de alambre de cobre estañado de 0,8–1,0 mm para las barras locales, un portafusible con fusible de 3 A y un interruptor de al menos 5 A DC. Las seis ramas de alimentación deben salir en estrella hacia T1, T2, T3, T4, PAM8403 y WS2812B.

### Si no se dispone de crimpadora

Comprar los pigtails prearmados, empalmar color por color y cubrir cada unión con termorretráctil. Es menos elegante, pero más fiable que prensar terminales XH con alicates. Antes de unir, comprobar continuidad y el orden de señales contra `conexiones-entre-tarjetas.csv`; los colores no son una especificación eléctrica.

## Tarjetas, montaje y módulos

| Artículo | Comprar | Enlace | Observación |
|---|---:|---|---|
| Placa perforada 7 × 9 cm | 1 o más | [Electronilab · placas universales](https://electronilab.co/categoria-producto/componentes/placas-universales/) | Adecuada para T1. Exigir paso 2,54 mm y pads individuales. |
| Placas perforadas mayores | 3 | [Didácticas · placas perforadas](https://www.didacticaselectronicas.com/shop/category/prototipado-fabricacion-de-productos-placas-de-prototipo-perforadas-362?view_mode=list) | Elegir al menos 10 × 8 cm para T2/T3 y 10 × 9 cm para T4, o comprar mayores y cortar después de presentar los componentes. |
| Separadores M3 | 16 juegos | [Electronilab · kit de separadores](https://electronilab.co/categoria-producto/raspberry-pi/accesorios/) | Cuatro apoyos por tarjeta; escoger longitud según la caja. |
| Cable rígido estañado 24–26 AWG | 1 rollo | Tienda de electrónica local | Puentes cortos sobre cada tarjeta. No reutilizar agujeros de patas de componentes como anclaje de puentes. |
| Termorretráctil, estaño y flux | 1 juego | Tienda de electrónica local | Flux no corrosivo; limpiar la placa tras soldar. |

## Resistencias y capacitores

No es conveniente sustituir estos elementos por “lo más parecido”. Ordenar los valores exactos de `BOM-precision.md`.

- Resistencias: película metálica, 1/4 W, **1 %**; las diez de 10 kΩ indicadas como críticas deben ser **0,1 %**, o se deben seleccionar y emparejar con multímetro.
- Capacitores de señal: película de poliéster o polipropileno, **±5 %**, 50 V o más. En Didácticas hay [capacitores de poliéster por valor](https://www.didacticaselectronicas.com/shop/category/capacitores-poliester-270).
- Desacople: 100 nF X7R, ±10 %, 50 V.
- Electrolíticos: 105 °C; 10/16 V. C10 debe ser bipolar/no polar o de película.
- Electronilab ofrece [resistencias de película metálica](https://electronilab.co/etiqueta-producto/resistencia/), pero se debe revisar existencia valor por valor. No comprar un surtido sin confirmar que contiene 2,7 kΩ, 5,6 kΩ, 22 kΩ, 27 kΩ y 56 kΩ.

## Semiconductores pequeños

| Artículo | Comprar | Proveedor | Observación |
|---|---:|---|---|
| 1N4148 THT | 10 | Electronilab, Sigma o Didácticas | Se usan tres; encapsulado axial DO-35, mismo lote. |

## Orden recomendado para no perder dinero

1. Comprar primero pantalla, ESP32, potenciómetros y módulos; son los que definen dimensiones y pinout físicos.
2. Confirmar con multímetro y fotografías el pinout real de cada uno.
3. Comprar y cortar las tarjetas perforadas después de presentar esos componentes.
4. Comprar los pasivos exactos de la BOM y medir los pares críticos.
5. Armar T1, probar VREF y audio; continuar con T2, T3 y T4 solo cuando la tarjeta anterior pase su prueba.

## Alternativas que no deben usarse

- `74HC125`, `74HC14` o un módulo nivelador BSS138: no garantizan reconocer 3,3 V cuando trabajan a 5 V. La revisión E.5 usa `74HCT245` local.
- LM358 como reemplazo: contiene solo dos amplificadores y no es pin a pin.
- LM324 SMD: no entra en los zócalos DIP-14.
- ESP32 de 30 pines: no coincide con el esquema mecánico de T4.
- Pantalla ST7735 de 128 × 160 o ST7789 de 240 × 240: no coincide con la pantalla configurada.
- Potenciómetros `A10K` en las bandas o `B10K` en los controles de audio sin revisar la función: las curvas no son equivalentes.

