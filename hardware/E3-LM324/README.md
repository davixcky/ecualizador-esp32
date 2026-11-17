# E.3-LM324 · PCB CNC de una cara

Esta es la placa nueva para el esquema D.3-LM324. Sustituye la propuesta de retrofit cuando se fabrica una PCB desde cero: U1–U4 reciben 5 V directamente y R33–R40 protegen las entradas ADC del ESP32.

## Resultado

| Comprobación | Resultado |
|---|---:|
| Contorno | 200 × 120 mm |
| Cobre | solo B.Cu |
| Pista mínima | 0,7 mm |
| Pistas de alimentación | 1,0 mm |
| Dona/pad PTH mínimo | 1,9 mm |
| Separación configurada | 0,5 mm |
| Vías metalizadas | 0 |
| Pistas que pasan entre pines a 2,54 mm | 0 |
| Alambres aislados | 23 (20 ruteados + 3 pad a pad) |
| Longitud de alambre | 3,8–35,9 mm; mediana 12,9 mm |
| KiCad DRC | 0 errores, 0 conexiones abiertas |

La unión recta entre dos pines adyacentes que pertenecen a la misma red se permite: no es una pista que atraviesa el espacio para llegar a otro punto, sino la conexión directa entre esos terminales. Ninguna otra pista ocupa esos canales.

Con pads de 1,9 mm a paso de 2,54 mm quedan 0,64 mm entre cobres. Por eso la separación global se fijó en 0,5 mm. Una pista de 0,7 mm más sus separaciones no cabe en ese espacio, reforzando geométricamente la prohibición.

## Archivos

- [`placa/ecualizador-E3-LM324.kicad_pcb`](placa/ecualizador-E3-LM324.kicad_pcb): placa editable en KiCad.
- [`fabricacion/`](fabricacion/): Gerber inferior, contorno, taladros y planos PDF.
- [`alambres.csv`](alambres.csv): extremos y longitud de los 23 alambres.
- [`etiquetas-conectores.csv`](etiquetas-conectores.csv): orden físico de todos los conectores.
- [`validacion-cnc.json`](validacion-cnc.json): verificación automática de las tres reglas del taller.
- [`vistas/3d-top.png`](vistas/3d-top.png) y [`vistas/3d-bottom.png`](vistas/3d-bottom.png): vistas de montaje y cobre.

Los conectores y GPIO fueron reasignados para mejorar el ruteo. Se debe cablear por las etiquetas de serigrafía y compilar el firmware con `pio run -e e3`.

## Estado

La conectividad, geometría y reglas de fabricación se validaron digitalmente. Los avisos restantes de KiCad son de serigrafía de los alambres, huellas modificadas y pads de los enlaces pad a pad superpuestos intencionalmente; no hay errores de cobre. Todavía se requiere revisión del fabricante, fresado de una muestra y prueba eléctrica antes de montar el ESP32.
