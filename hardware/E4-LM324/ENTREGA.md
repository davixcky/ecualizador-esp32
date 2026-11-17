# Entrega única E.4-LM324

## Archivos que corresponden a la revisión actual

- `proyecto/ecualizador-E4-LM324.kicad_pro`: abrir este archivo en KiCad; contiene el esquema y la PCB de la misma revisión.
- `proyecto/ecualizador-E4-LM324.kicad_sch`: esquema físico E.4, retroanotado pin por pin.
- `proyecto/ecualizador-E4-LM324.kicad_pcb`: PCB E.4 de una cara.
- `proyecto/ecualizador-E4-LM324.pdf`: PDF exportado del esquema físico E.4.
- `fabricacion/`: Gerber B.Cu, contorno, archivo de taladros y planos PDF para la PCB E.4.
- `montaje/`: lista de materiales LM324, puentes, etiquetas de conectores y vistas.
- `validacion/`: DRC de KiCad, reglas CNC y resultados de simulación.

## Estado verificado

- Esquema: ERC con 0 errores; 23 avisos documentados corresponden exclusivamente a pines `NC-*` deliberadamente aislados.
- PCB: DRC con 0 errores y 0 conexiones abiertas.
- Paridad estricta esquema ↔ PCB: **0 diferencias**.
- Cobre ruteado: exclusivamente B.Cu; 0 pistas F.Cu y 0 vías.
- Pista mínima: 0,7 mm.
- Pad mínimo: 2,0 mm.
- Cruces de pistas entre pines a 2,54 mm: 0.
- Agujeros de puente superpuestos con pads de componentes: 0.

## Fuente única de verdad

El proyecto KiCad E.4 es la fuente de verdad de fabricación y montaje. El esquema ya muestra las mismas secciones físicas de LM324/74AHCT125, GPIO del ESP32, potenciómetros y orden de conectores que la PCB.

No actualizar ni fabricar desde revisiones D.2, D.3 lógica, E.2 o E.3. Abrir siempre `proyecto/ecualizador-E4-LM324.kicad_pro`.

La validación digital no sustituye la fabricación y medición de una primera unidad antes de una producción en serie. Este paquete contiene únicamente hardware; no incluye firmware.
