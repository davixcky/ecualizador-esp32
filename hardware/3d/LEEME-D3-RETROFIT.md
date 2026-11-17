# Modelo 3D D.3-LM324

`ecualizador-D3-retrofit.*` representa el montaje del circuito D.3 sobre una PCB D.2 ya fabricada:

- U1–U4 se muestran como LM324N.
- R33–R40 se muestran en la zona central libre de la placa.
- Los cortes de pista, pines 4 doblados y cables se ejecutan siguiendo [`../RETROFIT-LM324.md`](../RETROFIT-LM324.md).
- `ecualizador-D3-retrofit-inferior.png` muestra el reverso de la PCB y su cobre existente.

El archivo `../ecualizador-D3-retrofit-3d.kicad_pcb` es una fuente de visualización y ensamblaje. No es un ruteo D.3 aprobado ni debe usarse para generar Gerbers. La comprobación eléctrica vigente es el esquema D.3, su netlist y la simulación ngspice.
