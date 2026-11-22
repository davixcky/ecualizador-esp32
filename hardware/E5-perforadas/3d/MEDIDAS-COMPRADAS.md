# Medidas y pendientes del modelo E.5

`medidas-componentes.json` es la fuente mecánica. Cada pieza indica de dónde sale la
cota (`estado`) y qué respaldo tiene la compra (`compra`). La evidencia de compra es
`../../COMPONENTES-COMPRADOS-VERIFICADOS.md`; un carrito no es una compra.

## Medir con calibre antes de perforar o imprimir

| Pieza | Compra | Qué falta medir |
|---|---|---|
| Potenciómetros B10K (RV2–RV4) | Declarada por el comprador: 4 unidades (3 montadas + 1 repuesto); sin albarán en el repositorio | Cuerpo, largo y tipo de eje, rosca del buje, paso de terminales |
| Potenciómetros A10K (RV1, RV5) | **Pendiente.** Hay dos P-20K logarítmicos comprados como candidatos sin validar | Todo. El modelo usa la envolvente del B10K y reserva un cilindro libre de 24 × 14 mm |
| Parlantes WS-14595 (2) | Verificada | Si 100 × 45 × 21 mm es por parlante o del conjunto, tornillos, qué par rojo/negro es de cada parlante |
| Tira FCOB WS2811 12 V | Declarada por el comprador | Espesor, rotulado de las islas, orden de color real, paso de corte |
| ESP32S V1.1 USB-C | Declarada / carrito | Largo, ancho, altura con zócalos, posición del USB-C |
| LilyGO T4-S3 (pantalla) | **Pendiente** | Envolvente 56 × 44 × 13 mm publicada por la tienda (vidrio mayor que el PCB, alto con pines); PCB de 51,56 × 38,72 mm según el DXF oficial; espesor del vidrio y posición del área activa sin medir |
| PAM8403 | Carrito | Largo, ancho, altura, islas |
| Borneras puente 8P (2) | Verificada | Largo, ancho, alto, paso de tornillos |
| Portafusible CON-183AC | Verificada | Diámetro y largo cerrados |
| Perforadas 90 × 70 y 120 × 80 | Carrito | Confirmar medidas y agujeros de fijación |

## Sin comprar y con geometría supuesta

A10K × 2, perillas × 5, LilyGO T4-S3, 8 imanes de Ø6 × 2 mm, interruptor general de 5 A DC,
elevador de 5 a 12 V (o fuente de 12 V) para la tira, headers de J3/J5/J7.

## Asuntos eléctricos que el modelo deja a la vista

1. **La tira es de 12 V y el equipo solo tiene 5 V.** El elevador dibujado no está en el
   esquema ni comprado. Hay que decidir entre elevador, fuente de 12 V o cambiar de tira.
2. **Orden de color.** La tira publica BRG y el firmware usa `NEO_GRB`: probar en la tira real.
3. **Parlantes.** Dos de 8 Ω con cuatro hilos (dos rojos, dos negros): uno por canal del
   PAM8403. El esquema solo alimenta una entrada (AMP_IN): hay que puentear L y R en el
   módulo y reflejarlo en el esquema. No unir los negros entre sí ni a GND.
4. **+5 V duplicado.** La BOM y la lista por tienda piden un par propio desde las borneras
   para T1–T3; `conexiones-entre-tarjetas.csv` también lleva +5 V y GND por JBUS desde T4.
   El modelo dibuja ambos: hay que elegir uno.
5. **RV1/RV5.** Montar los P-20K cambia impedancias y cortes; no hacerlo sin simular.
6. **Pantalla T4-S3.** El enlace UART propuesto no está en el esquema y no hay firmware:
   el ESP32 debe enviar niveles y espectro, y la T4-S3 debe dibujarlos. La T4-S3 consume
   de 90 a más de 230 mA según el fabricante; sumarlo al presupuesto de 5 V.
7. **Imanes.** La retención con el peso de parlantes y pantalla en la tapa no está comprobada.

La lista completa y actualizada se regenera en `validacion-3d.json`
(`pendientes_y_supuestos`).
