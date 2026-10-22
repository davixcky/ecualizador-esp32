# Validación del 22 de octubre de 2026

Los registros contienen resultados de herramientas ejecutadas en computador. El estado y las limitaciones se explican en el informe LaTeX y su PDF.

- `netlist.txt`: comparación del esquema exportado con las 59 redes de la definición del circuito.
- `pruebas-firmware.txt`: comprobaciones DSP y equivalencia de las cinco vistas dibujadas por franjas.
- `compilacion-esp32.txt`: compilación PlatformIO, sin carga ni ejecución en una placa física.
- `ngspice.txt`: resultados nominales del modelo analógico; incluye el caso histórico que no cumple.
- `../../hardware/erc.rpt` y `../../hardware/drc.rpt`: informes KiCad. D.1: cero infracciones reportadas y continuidad comprobada incluyendo 84 puentes. Las limitaciones de montaje se detallan en `../../hardware/una-cara/LEEME.md`.
- `../../simulacion/velxio/validacion.json`: lecturas reales de los instrumentos del simulador web, tres casos.
- `../../cad/validacion.json`: validez de sólidos y 13 comprobaciones de ajuste nominal. No comprueba todas las interferencias del ensamblaje ni tolerancias de impresión.

Hay una captura del osciloscopio virtual de Velxio. No hay mediciones de osciloscopio físico ni evidencia de una placa construida.
