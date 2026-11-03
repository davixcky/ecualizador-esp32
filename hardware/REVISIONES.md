# Revisiones

## E.2 · 3 de noviembre de 2026 · propuesta

Placa única de una cara, 200 × 120 mm, con el mismo contorno, los mismos agujeros y el mismo gabinete que D.2. Tiene 33 alambres: 20 puentes y 13 enlaces de GND. Usa plano de GND, resistencias y diodos a 10,16 mm, intercambio de secciones del MCP6004 y nuevos GPIO del ESP32 (firmware: `pio run -e e2`). Los conectores de cable llevan los pines etiquetados. DRC: cero errores y cero conexiones abiertas. Aún no se ha fabricado. Detalles en `E2-placa-unica/README.md`.

## E.1 · 2 de noviembre de 2026 · alternativa

Tres placas de una cara (audio, detectores y control) con 44 alambres y 15 cables entre placas. Necesita un gabinete ampliado. Detalles en `E1-tres-placas/README.md`.

## D.2 · 22 de octubre de 2026

PCB de una cara, 200 × 120 mm. Pistas de al menos 0,9 mm, separación de 1 mm, plano de GND y 80 tramos de alambre agrupados en JP1–JP79. Se genera con Python y KiCad; el ruteo inicial procede de Freerouting y la terminación validada se conserva en `ruteo-validado.json`. JP67–JP79 se sueldan a terminales existentes. DRC: cero errores, cero conexiones abiertas y cero diferencias con el esquema.

Fabricación: `fabricacion/ecualizador-D2-una-cara.zip`. Plano: `pcb-rev-D2.pdf`.

## D.1 · histórica

La primera PCB de una cara utilizaba una rejilla de ruteo y separaciones menores. Se conserva en `archivo/D1/`; no corresponde a las reglas CNC de la entrega D.2.

## B.1 · histórica

El diseño anterior de dos caras está archivado en `archivo/B1-dos-caras-no-fabricar.zip`. No fabricar para esta entrega.
