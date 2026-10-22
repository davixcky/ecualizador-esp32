# PCB D.2 — una cara, con puentes de alambre

200 × 120 mm; 79 componentes y 59 redes. Participantes: Leo Rojas, David Orozco y Manuel Castilla.

La placa se fabrica únicamente por **B.Cu**. Las pistas tienen al menos **0,9 mm** y la separación entre cobres es de **1 mm**. El plano de GND ocupa el cobre libre y deja una reserva bajo la antena del ESP32. KiCad conserva dos capas internas para representar los pads pasantes; no se fabrica F.Cu.

- [Plano de montaje](../pcb-rev-D2.pdf): componentes, puentes y cobre visto desde abajo.
- [Archivos de fabricación](../fabricacion/ecualizador-D2-una-cara.zip): cobre inferior, máscara opcional, contorno y taladros.
- [Plano para tóner](toner-espejo-1a1.pdf): espejo, escala 1:1 y regla de 100 mm. Imprimir al 100 %, sin ajuste de página.
- [Lista explicada de puentes](../PUENTES.md): identifica también los terminales compartidos.
- [Puentes y coordenadas](puentes.csv): 80 tramos de alambre, agrupados en JP1–JP79. Las coordenadas se miden desde la esquina superior izquierda, mirando la cara de componentes.
- [Ruteo aprobado](../ruteo-validado.json): pistas y puntos de soldadura que reconstruye el generador.

La cara superior lleva 29 tramos de hasta 20 mm; los otros 51 se montan aislados por debajo. La cara asignada a cada cable está en `puentes.csv` y `../PUENTES.md`. Reservar 8 mm libres debajo de la PCB. El plano incluye una página independiente para el cableado inferior.

JP1–JP66 tienen puntos de soldadura propios. Montar los que quedan bajo los integrados antes de colocar los zócalos. JP67–JP79 unen terminales existentes: soldar sus extremos por la cara inferior, sin intentar introducir más conductores en los taladros ocupados. Usar alambre aislado y fijarlo para que no roce otros terminales. Los puntos compartidos son la misma unión eléctrica, no agujeros adicionales.

Los pads normales tienen 2 mm o más; en filas de 2,54 mm son ovalados, de 2,4 × 1,4 mm. Los taladros de componentes son de 1 mm y los de los puentes independientes de 0,8 mm. Los cuatro agujeros de fijación son M3. El plano de GND se conecta directamente a sus pads.

Los controles del panel van conectados por cable a sus cabeceras. Conservar la extensión USB, el cable de la pantalla y los soportes del gabinete. La pantalla prevista es la Waveshare de 1,9 pulgadas, 170 × 320 píxeles.

## Cómo se reconstruye

`python3 herramientas/generar_pcb.py` coloca las piezas con la API de KiCad, aplica `ruteo-validado.json`, crea los puentes y rellena GND. Después ejecuta el DRC y compara la placa con el esquema. Requiere el Python del sistema con `pcbnew` y KiCad CLI.

Freerouting se utilizó para el ruteo inicial; su sesión está en `hardware/ruteo-freerouting.ses`. Las conexiones restantes se cerraron con puentes y pistas de acceso. El JSON conserva el resultado completo aprobado, incluidas esas terminaciones: reproducir solo la sesión SES no basta para reconstruir la D.2.

Comprobación digital de D.2: **0 errores DRC, 0 conexiones abiertas y 0 diferencias con el esquema**. Los avisos de taladros de puente dentro del contorno de componentes se conservan como advertencias de montaje. Esta comprobación corresponde al diseño; no representa mediciones de una placa fabricada.
