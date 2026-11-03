# E.1 · Tres placas de una cara (alternativa)

El circuito de D.2 se reparte en tres placas CNC de una cara unidas por cables. Las tres pasan el DRC con 0 errores y 0 conexiones abiertas, y las netlists coinciden pin a pin con el esquema (59 redes).

| Placa | Tamaño (mm) | Puentes | Alambres directos | Total |
|---|---|---|---|---|
| A · audio | 110 × 78 | 21 | 9 | 30 |
| B · detectores | 70 × 55 | 5 | 4 | 9 |
| C · control | 100 × 75 | 5 | 0 | 5 |

En total son 44 alambres más los 15 cables entre placas de [`cables-entre-placas.csv`](cables-entre-placas.csv). Las tres placas necesitan un gabinete ampliado (220 × 143 mm por fuera), cuyas vistas están en `vistas/`.

Las placas se generan con `herramientas/tres_placas/`. Para la entrega se prefiere E.2: una sola placa, 33 alambres y el gabinete original.
