# `cad/` — archivo de la revisión D.2 (no vigente)

Esta carpeta conserva el gabinete y el video de la revisión **D.2**: una PCB grande de
una cara, tres potenciómetros deslizables y dos rotativos. **Ese hardware no se compró
ni se va a montar.** Se mantiene solo como historial del informe de la Fase 2.

- No usar `gabinete.py`, `stl/deslizable*.stl` ni `ecualizador-gabinete.step` como
  referencia mecánica.
- Los guiones de video de esta carpeta ya no escriben en `docs/video/`: su salida va a
  `cad/archivo-video-D2/` (sin versionar) para que no puedan pisar el video vigente.
- El modelo y el video vigentes son los de la variante **E.5 en tarjetas perforadas**,
  con cinco controles rotativos: `hardware/E5-perforadas/3d/` y
  `hardware/E5-perforadas/video/`.
