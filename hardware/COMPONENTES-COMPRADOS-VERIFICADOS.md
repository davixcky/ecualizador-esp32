# Componentes comprados verificados · Ecualizador E.5

Este archivo es entrada obligatoria para cualquier agente que modifique el esquema, las tarjetas perforadas, el gabinete, el CAD o el video. No confundir una línea de un carrito con una compra: aquí solo aparecen artículos respaldados por el pedido Sigma `2140187`, el albarán I+D `BV/OUT/31035` y las aclaraciones del comprador.

## Componentes asignados al ecualizador

| Tienda | Producto y enlace | Compra verificada | Uso previsto | Condición de diseño |
|---|---|---:|---|---|
| Sigma | [LM324N DIP-14](https://www.sigmaelectronica.net/producto/lm324/) | 5 | U1–U4; queda 1 repuesto | Alimentar según el esquema E.5; respetar desacople local y zócalo DIP-14. |
| Sigma | [Zócalo DIP-14](https://www.sigmaelectronica.net/producto/base-14-pines/) | 4 | U1–U4 | Modelar zócalo e integrado; no soldar el LM324 directamente. |
| Sigma | [74HCT245 DIP-20](https://www.sigmaelectronica.net/producto/74hct245/) | 4 compartidos | 1 para el ecualizador | No sustituir visual ni eléctricamente por `74HC245`. |
| Sigma | [Zócalo DIP-20](https://www.sigmaelectronica.net/categoria-producto/conectores-y-cableado/conectores-pcb-de-insercion/) | 2 compartidos | 1 para el ecualizador | Confirmar ancho 7,62 mm antes de perforar. |
| Sigma | [Regleta hembra 1×40, 2,54 mm](https://www.sigmaelectronica.net/categoria-producto/conectores-y-cableado/conectores-pcb-de-insercion/headers-hembra/) | 4 compartidas | Cortar las secciones requeridas | El ESP32 debe quedar removible. |
| Sigma | [1N4148 THT](https://www.sigmaelectronica.net/producto/1n4148/) | 10 | D1–D3; sobran 7 | Respetar polaridad y encapsulado axial DO-35. |
| I+D | [Capacitor cerámico 100 nF/50 V, `CC0.1UF50V`](https://www.didacticaselectronicas.com/shop/cc0-1uf50v-capacitor-ceramico-0-1uf-50v-104-10717) | 20 compartidos | Desacoples del ecualizador y medidor | La publicación no especifica dieléctrico/tolerancia; no describirlo como X7R verificado. |
| I+D | [Potenciómetro logarítmico 20 kΩ, `P-20K`](https://www.didacticaselectronicas.com/shop/p-20k-potenciometro-rotativo-de-20k-6295) | 2 | Candidatos para entrada y volumen | Son A20K/log, no A10K. No cambiar RV1/RV5 sin validar la impedancia, ganancia y cortes del circuito. |
| I+D | [Conjunto `WS-14595`, parlantes 8 Ω/5 W](https://www.didacticaselectronicas.com/shop/ws-14595-parlante-8%CF%89-5w-11102) | 1 conjunto | Salida del PAM8403 | El conjunto contiene **2 parlantes físicos conectados a un mismo conector**. Modelar ambos. |
| I+D | [Portafusible 5×20 mm, `CON-183AC`](https://www.didacticaselectronicas.com/shop/con-183ac-portafusible-aereo-corto-5x20mm-17096) | 1 | Protección de alimentación | Debe quedar accesible, aislado y sujeto; no flotando dentro del gabinete. |
| I+D | [Fusible rápido 3 A/250 V, `FC-3A`](https://www.didacticaselectronicas.com/shop/fc-3a-fusible-corto-de-vidrio-3a-250v-13601) | 2 | 1 instalado + 1 repuesto | Es rápido de 5×20 mm. No confundir con el fusible lento de la zona de red del medidor. |
| I+D | [Bornera puente verde 8 posiciones, `BOR-BRIG-8P-VE`](https://www.didacticaselectronicas.com/shop/bor-brig-8p-ve-bornera-en-puente-terminal-a-tierra-8-posiciones-verde-23667) | 2 | Distribución estrella de +5 V y GND | Aunque ambas piezas sean verdes, rotular físicamente una `+5V` y otra `GND`; nunca conectar VREF a esta barra. |

## Parlantes: geometría y conexión obligatorias

- Producto facturado: una unidad comercial `WS-14595`.
- Contenido confirmado por el comprador: dos parlantes en un mismo conector.
- Especificación por parlante/conjunto publicada: 8 Ω, 5 W; envolvente publicada 100 × 45 × 21 mm.
- El CAD debe mostrar dos transductores y un solo arnés/conector, con rejillas y fijación real.
- Antes de cerrar el esquema del PAM8403 hay que inspeccionar el conector:
  - cuatro conductores: usar `L+`, `L−`, `R+`, `R−`, un parlante por canal;
  - tres conductores con retorno común: no conectar directamente al PAM8403 BTL;
  - dos conductores: medir la impedancia del conjunto y usar un solo canal solo después de conocer si están en serie o paralelo.
- Las salidas negativas del PAM8403 no se unen entre sí ni a GND.

## Controles rotativos

- No se compraron potenciómetros deslizables para este montaje.
- El diseño vigente debe usar controles rotativos.
- Los dos `P-20K` comprados son logarítmicos de 20 kΩ; no demuestran la compra de A10K.
- Las compras B10K/A10K mencionadas en carritos anteriores siguen sin quedar verificadas por los documentos recibidos. No afirmar que están compradas hasta tener factura o albarán.

## Elementos compartidos y repuestos

- De los cuatro 74HCT245, se asigna uno a cada proyecto; los otros dos son repuestos.
- De los dos zócalos DIP-20, se asigna uno a cada proyecto.
- Las cuatro regletas 1×40 se reparten según los sockets del ESP32/LCD de ambos proyectos.
- Los 20 capacitores de 100 nF se reparten según BOM; no modelar los veinte dentro del ecualizador.

## Pendiente de evidencia

Los artículos de Electronilab, CVR y otros pedidos solo pueden marcarse como comprados cuando exista factura, albarán o confirmación explícita equivalente. Las listas de carritos siguen siendo útiles como enlaces y planificación, pero no son prueba de compra.

