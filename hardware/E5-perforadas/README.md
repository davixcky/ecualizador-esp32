# Variante E.5 para tarjetas perforadas

Esta variante conserva el circuito eléctrico D.3/E.4, pero lo divide para montaje y diagnóstico manual. No reemplaza la PCB E.4: es una alternativa de prototipo con cuatro tarjetas perforadas y cableado por señales nombradas.

## Archivos

- `esquema-modular-perforadas.pdf`: documento principal por tarjetas, conectores y orden de prueba.
- `proyecto/ecualizador-perforadas.kicad_sch`: esquema maestro editable con las referencias originales.
- `conexiones-entre-tarjetas.csv`: pinout único de los arneses.
- `lista-por-tarjeta.csv`: asignación de componentes a cada tarjeta.
- `BOM-precision.md` y `BOM-precision.csv`: lista de compra completa: pasivos de precisión, integrados, conectores, módulos, cables y material mecánico.
- `COMPRAS-COLOMBIA.md`: enlaces de compra colombianos, cantidades con repuestos y advertencias de compatibilidad.
- `LISTA-POR-TIENDA.md`: lista operativa con casillas, agrupada por proveedor para reducir pedidos y fletes.
- `3d/ecualizador-E5-perforadas.FCStd` y `.step`: ensamble mecánico actualizado con
  las cuatro tarjetas, arneses y dos barras WS2812B.
- `3d/ecualizador-E5-{cerrado,abierto,planta}.png`: vistas para revisar
  volumen, montaje y accesibilidad.

## División propuesta

| Tarjeta | Tamaño inicial sugerido | Integrados | Función |
|---|---:|---|---|
| T1 | 90 × 70 mm | U1 LM324 | Alimentación analógica, VREF, entrada, preamplificador, graves y pasa-altas de medios |
| T2 | 100 × 70 mm | U2 LM324 | Pasa-bajas de medios, agudos, potenciómetros, sumador, salida y antialiasing |
| T3 | 100 × 70 mm | U3 y U4 LM324 | Inversor de medios y tres detectores de pico |
| T4 | 100 × 80 mm | ESP32 y U6 | Protección ADC, pantalla, pulsador y adaptación NeoPixel |

Las medidas son una reserva para placa perforada de paso 2,54 mm. El modelo 3D
define la envolvente y los soportes, pero no sustituye la colocación agujero por
agujero. Antes de cortar, presentar físicamente zócalos, capacitores y conectores.

## Reglas importantes

- U1, U2, U3 y U4 se montan completos en una sola tarjeta; nunca se reparte un mismo DIP entre módulos.
- Cada LM324 lleva 100 nF directamente entre pin 4 (+5 V) y pin 11 (GND).
- `VREF` es referencia de señal de 1,65 V; no es retorno de potencia.
- La alimentación se distribuye en estrella desde T4 mediante `JBUS`, no encadenada por pistas finas.
- Los cables `PRE`, `MED_HP`, `G_W`, `M_W`, `A_W` y los cuatro `ADC_*_RAW` deben ser cortos. Para más de 10 cm, llevar una masa junto a las señales.
- R33–R40 deben quedar en T4, junto al ESP32, porque protegen sus entradas ADC.
- No conectar simultáneamente VBUS del USB y la fuente externa de +5 V.

## Estado

La división no cambia valores ni topología analógica; reutiliza el modelo simulado de la revisión LM324. Falta realizar la colocación agujero por agujero y validar físicamente una tarjeta a la vez antes de montar el conjunto.
