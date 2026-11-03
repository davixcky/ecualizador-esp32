# E.2 · Placa única de una cara

PCB de una cara para la CNC del taller. Usa el mismo circuito, el mismo contorno y los mismos agujeros que D.2, y cabe en el gabinete original.

| | D.2 | E.1 (tres placas) | **E.2** |
|---|---|---|---|
| Placas | 1 | 3 | **1** |
| Alambres | 80 | 44 + 15 cables entre placas | **33** |

DRC: 0 errores y 0 conexiones abiertas. Los avisos de serigrafía se deben a las líneas que dibujan los puentes.

## Dimensiones

| | mm |
|---|---|
| Contorno | 200 × 120, espesor 1,6, cobre solo en B.Cu |
| Agujeros de montaje | 4 × Ø3,2 (M3) en (4, 4), (196, 4), (4, 116) y (196, 116); 192 × 112 entre centros |
| Taladros | 0,8 (puentes), 1,0 (terminales), 3,2 (montaje) |
| Pistas | 0,9 (alimentación 1,0); separación mínima 1,0 |
| Borde | El plano de GND queda a 1,0 mm del borde |
| Gabinete D.2 | Interior 203 × 123; exterior 208 × 128 (radio 8); 16,4 mm libres sobre la placa |

## Qué cambia respecto a D.2

1. **Pistas bajo los componentes.** Las resistencias y los diodos usan una separación de 10,16 mm y los cerámicos de 100 nF, de 7,5 mm. Son las mismas piezas con las patas más abiertas.
2. **Plano de GND.** El cobre libre es GND; en la CNC solo se fresa el contorno de las pistas.
3. **Asignación de pines** (el circuito es equivalente, verificado contra la netlist):
   - **Secciones del MCP6004.** U1–U4 son idénticos y las secciones se reparten entre ellos así:

     | Ubicación | Función |
     |---|---|
     | U1A | Filtro de graves (antes en U1C) |
     | U1C | Seguidor de VREF (antes en U1A) |
     | U2C | Antialiasing (antes en U2D) |
     | U2D | Sumador de salida (antes en U2C) |
     | U3A | Detector de medios (antes en U3C) |
     | U3B | Sección libre, como seguidor de VREF (antes en U4D) |
     | U3C | Inversor M_INV (antes en U4C) |
     | U3D | Detector de graves (antes en U3A) |
     | U4C | Seguidor ADC_M (antes en U3D) |
     | U4D | Seguidor ADC_G (antes en U3B) |

     Las demás secciones no cambian.
   - **ESP32.** Ver la tabla siguiente. El firmware se compila con `pio run -e e2`.
   - **Conectores de cable** (potenciómetros, jacks, PAM8403, NeoPixel, pulsador y pantalla). El orden de los pines cambia, pero cada pin lleva su etiqueta en la serigrafía. **Conecte cada cable según la etiqueta, no según la posición.** La lista está en [`etiquetas-conectores.csv`](etiquetas-conectores.csv).

| Señal | D.2 | E.2 |
|---|---|---|
| VREF (ADC) | GPIO36 | GPIO32 |
| ADC_M (medios) | GPIO35 | GPIO36 |
| ADC_A (agudos) | GPIO32 | GPIO39 |
| ADC_G / ADC_FFT | 34 / 33 | 34 / 33 (sin cambio) |
| TFT_CS / DC / RST | 5 / 21 / 22 | 25 / 22 / 5 |
| TFT_SCK / MOSI / BL | 18 / 23 / 19 | sin cambio |
| NeoPixel | 25 | 21 |
| Pulsador | 27 | 4 |

## Alambres

[`alambres.csv`](alambres.csv) lista los 33 alambres con su red, sus extremos y su longitud (de 5 a 38 mm; la mayoría mide menos de 20 mm).

- **20 puentes** (JP1–JP20) entre agujeros propios del puente.
- **13 enlaces de GND** pad a pad, que unen islas del plano. Sus agujeros coinciden con terminales existentes y se taladran una sola vez.

Los de menos de 15 mm pueden hacerse con patas recortadas de resistencias; los demás, con alambre aislado.

## Archivos

- `placa/`: placa KiCad (`ecualizador-E2.kicad_pcb`), proyecto, DRC y listas de puentes en JSON.
- `fabricacion/`: Gerber de B.Cu y Edge.Cuts, taladros sin duplicados, cobre 1:1 en PDF y plano de montaje.
- `vistas/`: cobre, montaje, cobre con alambres y renders 3D.
- `colocacion.json`: colocación y asignación de pines. Con ella se regenera la placa mediante `herramientas/placa_unica/`.

## Regenerar

```sh
cd herramientas/placa_unica
CONGND=1 CL=1.0 VIA_COST=60 python3 rutear3.py ../../hardware/E2-placa-unica/colocacion.json /tmp/e2-ruteo
python3 cerrar2.py /tmp/e2-ruteo /tmp/e2-final
python3 finalizar.py /tmp/e2-final ../../hardware/E2-placa-unica/colocacion.json /tmp/e2-paquete
```

Freerouting no es determinista. Una nueva ejecución puede producir otra cantidad de alambres; la placa entregada es la que está en `placa/`.

## Pendiente de verificar

- No se ha fresado ni montado.
- No se ha comprobado en 3D el ajuste en el gabinete con la nueva posición de las piezas altas (C26 y el ESP32 sobre su zócalo).
- El firmware E.2 compila, pero no se ha probado en hardware.
- El esquemático (`ecualizador.kicad_sch`) mantiene la asignación lógica de D.2; la asignación física de E.2 es la de las tablas anteriores.
