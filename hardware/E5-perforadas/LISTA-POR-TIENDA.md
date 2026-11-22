# Lista de compra por tienda · E.5 perforadas

> **Actualización del 20 de noviembre de 2026.** Esta lista es de planificación. Lo realmente comprado y respaldado por factura o albarán está en [`../COMPONENTES-COMPRADOS-VERIFICADOS.md`](../COMPONENTES-COMPRADOS-VERIFICADOS.md). Cambios respecto a lo escrito abajo: **parlantes** = conjunto WS-14595 (dos de 8 Ω / 5 W en un conector), no uno de 4 Ω / 3 W; **luces** = tira BTF-LIGHTING FCOB WS2811 de **12 V** (ASIN B0BW5T6HW4, un píxel cada 50 mm), no WS2812B de 5 V, por lo que falta definir la alimentación de 12 V; **RV1/RV5** = A10K sin comprar (hay dos P-20K logarítmicos como candidatos sin validar); **no hay potenciómetros deslizables**. **Pantalla** = se decidió sustituir la TFT de 1,9″ por una LilyGO T4-S3 enlazada por UART (sin comprar, sin esquema ni firmware todavía). **Tapa** = cierre con imanes de Ø6 × 2 mm, sin bisagras. El modelo 3D y sus pendientes están en [`3d/`](3d/README.md).

Revisada el **16 de noviembre de 2026**. Las cantidades de esta lista son cantidades de compra e incluyen repuestos; por eso pueden ser mayores que las cantidades netas de `BOM-precision.md`. Confirmar inventario y plazo de entrega antes de pagar.

## 1. Sigma Electrónica · pedido de integrados y controles

- [ ] **2 × 74HCT245 DIP-20** — uno para U6 y uno de repuesto: [producto](https://www.sigmaelectronica.net/producto/74hct245/).
- [ ] **5 × LM324N DIP-14** — se usan cuatro: [producto](https://www.sigmaelectronica.net/producto/lm324/).
- [ ] **4 × zócalo DIP-14** — U1–U4: [producto](https://www.sigmaelectronica.net/producto/base-14-pines/).
- [ ] **2 × zócalo DIP-20**, ancho 7,62 mm — se usa uno para U6: [conectores de inserción](https://www.sigmaelectronica.net/categoria-producto/conectores-y-cableado/conectores-pcb-de-insercion/).
- [ ] **3 × potenciómetro A10K logarítmico** — RV1, RV5 y uno de repuesto: [producto](https://www.sigmaelectronica.net/producto/pot1v-10k/).
- [ ] **1 × header hembra 1 × 40** — cortar dos secciones de 19 pines para el ESP32: [headers hembra](https://www.sigmaelectronica.net/categoria-producto/conectores-y-cableado/conectores-pcb-de-insercion/headers-hembra/).
- [ ] **10 × diodo 1N4148 THT/DO-35** — se usan tres; pedirlos del mismo lote.
- [ ] **6 × perillas**, únicamente si coinciden con el diámetro y tipo de eje de los potenciómetros.

No aceptar `74HC245`: el pedido debe decir **74HCT245**. El HCT245 es DIP-20 y no entra en un zócalo DIP-14.

## 2. Electronilab · conectores, cableado, alimentación y módulos

### Controles y conectores del equipo

- [ ] **4 × potenciómetro B10K lineal** — RV2–RV4 y uno de repuesto: [producto](https://electronilab.co/tienda/potenciometro-lineal-b-10k-ohm-15mm/).
- [ ] **3 × jack estéreo hembra 3,5 mm PJ313D THT** — se usan dos: [producto](https://electronilab.co/tienda/conector-jack-estereo-hembra-negro-pj313d-3-5-mm-para-pcb/).
- [ ] **2 × bornera 2 vías, paso 5,08 mm** — se usa una en J6: [producto](https://electronilab.co/tienda/terminal-bornera-2p-5-08mm/).
- [ ] **2 × pulsador momentáneo 6 × 6 mm THT** — se usa uno: [producto](https://electronilab.co/tienda/micro-boton-pulsador-switch-de-2-pines-angulo-recto/).
- [ ] **1 × header 1 × 4, paso 2,54 mm** — J3/PAM8403.
- [ ] **1 × header 1 × 3, paso 2,54 mm** — J5/NeoPixel.
- [ ] **1 × header o socket 1 × 8, paso 2,54 mm** — J4/pantalla; comprarlo después de revisar la pantalla física.

### Arnés entre las cuatro tarjetas

Todo debe ser de la misma familia y orientación: [familia JST-XH/XH2.54](https://electronilab.co/etiqueta-producto/jst-xh2-54/).

- [ ] **10 × cabezal macho XH de 4 vías**: [producto 4P](https://electronilab.co/tienda/conector-macho-xh2-54-2-54mm-4p/).
- [ ] **10 × carcasa hembra XH de 4 vías**.
- [ ] **2 × cabezal macho XH de 5 vías**.
- [ ] **2 × carcasa hembra XH de 5 vías**.
- [ ] **2 × cabezal macho XH de 2 vías**.
- [ ] **2 × carcasa hembra XH de 2 vías**.
- [ ] **70 × terminal crimp compatibles con las carcasas** — se usan 54.

Si no hay crimpadora:

- [ ] Pigtails prearmados de 4 vías: [cable XH 4P](https://electronilab.co/tienda/cable-conector-xh2-54-mm-4p-para-soldar/).
- [ ] Pigtails prearmados de 5 vías: [cable XH 5P](https://electronilab.co/tienda/cable-conector-xh2-54-2-54mm-5p-para-soldar/).

Un pigtail tiene conector solamente en un extremo. Para un cable desmontable en ambos extremos se requieren dos pigtails empalmados o un cable hembra–hembra ya fabricado.

### Alimentación, iluminación y audio

- [ ] **1 × PAM8403 5 V, 2 × 3 W**; comprar dos solo si se desea repuesto: [producto](https://electronilab.co/tienda/mini-amplificador-digital-pam8403-de-audio-dual-de-3w-clase-d/).
- [ ] **2 × barra de 8 LED WS2812**: [producto](https://electronilab.co/tienda/neopixel-stick-8-x-led-rgb-ws2812-drivers-integrados/). Se usarán 12 LED en total.
- [ ] **1 × fuente 5 V, 5 A**: [producto](https://electronilab.co/tienda/fuente-conmutada-5v-dc-5a-25w/).
- [ ] **3 m de cable flexible rojo 22 AWG** y **3 m negro 22 AWG** para las ramas en estrella de +5 V/GND: [cables](https://electronilab.co/categoria-producto/componentes/cable/).
- [ ] **5–10 m de cable flexible 26 AWG en varios colores** para señales y arneses.
- [ ] **4 m de alambre de cobre estañado rígido de 0,8–1,0 mm** para formar las barras locales de +5 V y GND en las cuatro tarjetas.
- [ ] **1 rollo de cable rígido estañado 24–26 AWG** para puentes cortos de señal; no usarlo como retorno principal del PAM8403 o los LED.
- [ ] **1 juego de tubo termorretráctil**.
- [ ] **2 × regleta/bloque de distribución de mínimo 7 posiciones y ≥5 A**: una exclusivamente para +5 V y otra para GND. Puede usarse una regleta atornillable de 8 o 12 polos y puentear internamente cada grupo: [opciones de borneras](https://listado.mercadolibre.com.co/bornera-wago).
- [ ] **1 × portafusible en línea + 2 fusibles de 3 A** para la salida de 5 V.
- [ ] **1 × interruptor general**, nominal mínimo 5 A DC.

La fuente metálica abierta requiere caja, fusible, interruptor y conexión segura a tierra. Si no la instalará una persona competente, reemplazarla por un adaptador cerrado certificado de 5 V y al menos 3 A.

La distribución debe salir en estrella desde los dos bloques: T1, T2, T3, T4, PAM8403 y WS2812B reciben pares rojo/negro propios. No encadenar la alimentación pasando primero por una tarjeta y después por otra. `VREF` no se conecta a la regleta de GND.

## 3. Didácticas Electrónicas · ESP32, parlante, capacitores y placas

### Módulos

- [ ] **1 × ESP32 DevKit WROOM-32D de 38 pines**; dos si se desea repuesto: [producto](https://www.didacticaselectronicas.com/shop/d-esp32-wr-32d-tarjeta-de-desarrollo-esp32-wroom-32d-14753).
- [ ] **1 × parlante 4 Ω, 3 W**: [producto](https://www.didacticaselectronicas.com/shop/productos-de-audio-parlante-524/parl-4-3w-2831-parlante-con-altavoz-de-cavidad-4-ohm-3w-54401).

### Capacitores de película

Pedir película de poliéster o polipropileno, **±5 %**, 50 V o más, en la [categoría de capacitores de poliéster](https://www.didacticaselectronicas.com/shop/category/capacitores-poliester-270):

- [ ] 3 × 2,2 nF.
- [ ] 4 × 4,7 nF.
- [ ] 8 × 10 nF.
- [ ] 3 × 47 nF.
- [ ] 6 × 100 nF.
- [ ] 3 × 1 µF; ±10 % máximo si no existe ±5 %.

Las cantidades usadas son 1, 2, 5, 1, 4 y 1 respectivamente; el resto son repuestos para medición y selección.

### Placas perforadas

Comprar placas de paso 2,54 mm con pads individuales en la [categoría de placas perforadas](https://www.didacticaselectronicas.com/shop/category/prototipado-fabricacion-de-productos-placas-de-prototipo-perforadas-362?view_mode=list):

- [ ] 1 × placa de al menos 90 × 70 mm para T1.
- [ ] 2 × placas de al menos 100 × 70 mm para T2 y T3.
- [ ] 1 × placa de al menos 100 × 80 mm para T4.

No cortar las placas hasta tener físicamente ESP32, potenciómetros, pantalla y zócalos.

## 4. CVR Electrónica · pantalla

- [ ] **1 × pantalla TFT IPS 1,9 pulgadas, 170 × 320, SPI, ST7789**: [producto](https://www.cvrelectronica.com/description/?product_id=1602).

Comprar solo una pantalla. Alternativa si CVR no entrega a tiempo: [Electrónica SFG · ST7789 170 × 320](https://www.electronicasafg.com/productos/pantalla-tft-ips-1-9-pulgadas-spi-st7789-170x320-arduino-1tl2w/).

No comprar todavía un cable GH1.25. Primero recibir la pantalla y comprobar si tiene header de 2,54 mm u otro conector. Cablear por los nombres `GND`, `VCC`, `SCL`, `SDA`, `RES`, `DC`, `CS` y `BLK`, no por colores ni por posición asumida.

## 5. Pasivos exactos · solicitar en Sigma, Electronilab o Didácticas

### Resistencias de película metálica

Pedir **1/4 W, 1 %**. Si la tienda vende paquetes de diez, comprar un paquete por valor. Electronilab tiene [resistencias de película metálica](https://electronilab.co/etiqueta-producto/resistencia/).

- [ ] 5 × 10 Ω.
- [ ] 5 × 100 Ω.
- [ ] 5 × 330 Ω.
- [ ] 5 × 2,7 kΩ.
- [ ] 5 × 5,6 kΩ.
- [ ] 15 × 10 kΩ, **0,1 % y 25 ppm/°C preferido**, para R2, R3 y R33–R40.
- [ ] 15 × 10 kΩ, 1 %, para las demás posiciones.
- [ ] 5 × 22 kΩ.
- [ ] 5 × 27 kΩ.
- [ ] 10 × 47 kΩ.
- [ ] 5 × 56 kΩ.
- [ ] 5 × 100 kΩ.
- [ ] 5 × 220 kΩ, del mismo lote.

Si no se encuentran las 10 kΩ de 0,1 %, comprar 30 unidades de 10 kΩ al 1 %, medirlas y formar parejas con una diferencia menor de 0,2 %.

### Desacople y electrolíticos

- [ ] 10 × 100 nF cerámico X7R, ±10 %, 50 V.
- [ ] 5 × 10 µF electrolítico polar, 16 V, 105 °C.
- [ ] 2 × 10 µF bipolar/no polar, 16 V; no reemplazar C10 por un polar común.
- [ ] 2 × 100 µF, 10 o 16 V, 105 °C.
- [ ] 2 × 470 µF, 10 o 16 V, 105 °C, baja ESR.
- [ ] 2 × 1000 µF, 10 o 16 V, 105 °C, baja ESR.

## 6. Ferretería y audio local

- [ ] 16 juegos de separadores M3, tornillos y tuercas; comprar 20 si se venden sueltos.
- [ ] Estaño para electrónica y flux no corrosivo.
- [ ] Cable de audio 3,5 mm macho–macho corto y apantallado.
- [ ] Cable USB correspondiente al ESP32 comprado: micro-USB para el modelo recomendado, USB-C únicamente si se compra esa variante.
- [ ] Caja, interruptor general y fusible en línea de 2–3 A.
- [ ] **2 × regletas atornillables de 8–12 polos, ≥5 A**, si no se compraron con Electronilab/Mercado Libre; identificar una roja `+5V` y una negra/azul `GND`.
- [ ] Terminales tubulares/férulas apropiados para 22 AWG y su herramienta de crimpado, o estañar cuidadosamente los extremos si la bornera lo permite.

## Resumen de pedidos

| Pedido | Contenido principal | Obligatorio |
|---|---|---|
| Sigma | 74HCT245, LM324, zócalos, A10K y headers ESP32 | Sí |
| Electronilab | B10K, conectores, arneses, PAM8403, WS2812, fuente y cables | Sí |
| Didácticas | ESP32, parlante, película y placas perforadas | Sí |
| CVR | Pantalla ST7789 170 × 320 | Sí; usar SFG solo como alternativa |
| Pasivos | Resistencias, cerámicos y electrolíticos exactos | Sí; se pueden repartir entre las tres tiendas |
| Ferretería/audio | Montaje, cable USB y cable de audio | Sí |

