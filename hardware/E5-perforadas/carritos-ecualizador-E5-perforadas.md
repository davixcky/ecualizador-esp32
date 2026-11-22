# Carritos — Ecualizador E.5 perforadas

> **Actualización del 20 de noviembre de 2026.** Esta lista es de planificación. Lo realmente comprado y respaldado por factura o albarán está en [`../COMPONENTES-COMPRADOS-VERIFICADOS.md`](../COMPONENTES-COMPRADOS-VERIFICADOS.md). Cambios respecto a lo escrito abajo: **parlantes** = conjunto WS-14595 (dos de 8 Ω / 5 W en un conector), no uno de 4 Ω / 3 W; **luces** = tira BTF-LIGHTING FCOB WS2811 de **12 V** (ASIN B0BW5T6HW4, un píxel cada 50 mm), no WS2812B de 5 V, por lo que falta definir la alimentación de 12 V; **RV1/RV5** = A10K sin comprar (hay dos P-20K logarítmicos como candidatos sin validar); **no hay potenciómetros deslizables**. **Pantalla** = se decidió sustituir la TFT de 1,9″ por una LilyGO T4-S3 enlazada por UART (sin comprar, sin esquema ni firmware todavía). **Tapa** = cierre con imanes de Ø6 × 2 mm, sin bisagras. El modelo 3D y sus pendientes están en [`3d/`](3d/README.md).

Fecha: 2026-11-16. Carritos de sesión en Chrome, sin login, **compartidos con el
medidor de energía**. Aquí solo se listan y suman las cantidades del ecualizador.
Reporte del medidor:
`medidor-energia-esp32/hardware/perforadas-modulares/carritos-medidor-E5-perforadas.md`.
Precios en COP, IVA incluido, sin envío.

## Sigma Electrónica — $29.572

| Producto | Cant. | P. unit. | Subtotal | Nota |
|---|---:|---:|---:|---|
| 74HCT245 DIP-20 | 2 | $4.998 | $9.996 | |
| LM324 DIP-14 | 5 | $2.737 | $13.685 | |
| Zócalo DIP-14 | 4 | $476 | $1.904 | |
| Zócalo DIP-20 | 2 | $714 | $1.428 | Ancho no indicado; foto estrecha |
| Regleta hembra 1×40 | 1 | $1.428 | $1.428 | ESP32 1×19 ×2 |
| 1N4148 DO-35 | 10 | $113 | $1.131 | |

## Electronilab — $67.600

| Producto | Cant. | P. unit. | Subtotal |
|---|---:|---:|---:|
| Potenciómetro B10K lineal | 4 | $1.500 | $6.000 |
| Jack PJ313D 3,5 mm | 3 | $1.000 | $3.000 |
| Bornera 2P 5,08 mm | 2 | $500 | $1.000 |
| Pulsador 6×6 THT | 2 | $200 | $400 |
| PAM8403 | 1 | $2.900 | $2.900 |
| Fuente 5 V 5 A | 1 | $48.900 | $48.900 |
| Resistencias 1 % ×10: 10 Ω, 100 Ω, 330 Ω, 47k, 100k, 220k | 6 paq. | $900 | $5.400 |

Se **retiraron** los cabezales XH macho 4P/5P/2P: los kits XH de Didácticas ya los incluyen.

**Reconstruido el 2026-11-16** tras el reinicio del carrito: se verificó vacío y se volvió a agregar
todo. El paquete de 330 Ω (×10) es ahora **uno solo compartido** con el medidor (5 + 5 piezas)
y se cuenta aquí. Sigma, Didácticas y CVR también se reconstruyeron con las mismas
cantidades; los totales no cambian.

## Didácticas Electrónicas — $156.301,74

| Producto (SKU) | Cant. | P. unit. | Subtotal | Nota |
|---|---:|---:|---:|---|
| ESP32 DevKit WROOM-32D 38 pines | 1 | $23.205 | $23.205 | Última unidad |
| Placa perforada 8×12 cm | 3 | $3.647,35 | $10.942,05 | |
| Placa perforada 7×9 cm | 1 | $2.541,84 | $2.541,84 | |
| Cable siliconado 22 AWG rojo (m) | 3 | $1.760,01 | $5.280,03 | |
| Cable siliconado 22 AWG negro (m) | 3 | $1.760,01 | $5.280,03 | |
| Dispensador de 5 colores 26 AWG | 1 | $33.440,19 | $33.440,19 | |
| Kit de termoencogibles, 392 piezas (KIT-TE) | 1 | $40.479,04 | $40.479,04 | |
| Portafusible aéreo 5×20 (CON-183AC) | 1 | $1.382,78 | $1.382,78 | |
| Fusible de vidrio 3 A 5×20 (FC-3A) | 2 | $216,58 | $433,16 | |
| Bornera puente de 8 posiciones (BOR-BRIG-8P-VE) | 2 | $8.063,44 | $16.126,88 | +5 V y GND; corriente no indicada |
| Kit XH 4P: macho + carcasa cableada | 10 | $1.256,64 | $12.566,40 | Sustituye macho + carcasa + crimp |
| Kit XH 5P | 2 | $1.299,48 | $2.598,96 | |
| Kit XH 2P | 2 | $649,74 | $1.299,48 | |
| Cerámico 100 nF 50 V | 10 | $72,59 | $725,90 | Dieléctrico no indicado |

## CVR Electrónica — $49.236

| Producto | Cant. | P. unit. | Subtotal | Nota |
|---|---:|---:|---:|---|
| TFT IPS 1,9" 170×320 ST7789 | 1 | $32.412 | $32.412 | |
| Parlante pasivo 3 W 4 Ω, 1,5" | 1 | $11.834 | $11.834 | Validado con codex (4–8 Ω, 3–5 W) |
| Electrolítico 10 µF 16 V | 5 | $350 | $1.750 | 105 °C no indicado |
| Electrolítico 100 µF 16 V | 2 | $760 | $1.520 | 105 °C no indicado |
| Electrolítico 1000 µF 16 V | 2 | $860 | $1.720 | Low-ESR y 105 °C no indicados |

**Total ecualizador: $302.709,74**

## Pendientes (no añadidos)

- **A10K logarítmico ×3:** la foto del de Sigma dice B10K; no hay otro A10K en las 4 tiendas.
- **WS2812 de 8 LED ×2:** agotado. La cinta WS2812B de 1 m de Didácticas, ya en el
  carrito para el medidor, alcanza para los 12–16 LED del ecualizador si se aprueba cortar tramos.
- **Resistencias 1 % de 2,7k, 5,6k, 22k, 27k, 56k y 10k:** no hay en película metálica
  (solo de carbón); no existe la de 10k al 0,1 %.
- **Película de 2,2 nF, 4,7 nF, 10 nF, 47 nF, 100 nF y 1 µF al 5 %:** no hay tolerancia publicada; faltan 2,2 nF y 4,7 nF.
- **Electrolíticos:** 470 µF/16 V low-ESR agotado; 10 µF bipolar no disponible.
- **Headers 1×4 y 1×3 (J3, J5) y 1×8 (J4):** se pueden cortar de la regleta 1×40.
- **Pendientes de compra local:** interruptor de 5 A DC, alambre estañado rígido de 0,8–1 mm y de 24–26 AWG, perillas y separadores.

NO SE REALIZÓ NINGUNA COMPRA
