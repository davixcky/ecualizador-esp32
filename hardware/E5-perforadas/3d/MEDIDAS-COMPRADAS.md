# Medidas usadas por el modelo E.5

El gabinete se regeneró con las **cuatro placas compradas completas**: una de
90 × 70 × 1,6 mm y tres de 120 × 80 × 1,6 mm. No se supone que una placa fue
recortada. Por eso el gabinete crece respecto de la primera vista E.5.

`medidas-componentes.json` es la fuente mecánica del modelo. Cada pieza indica
si su cota fue publicada o si es una envolvente conservadora. Antes de imprimir
la caja definitiva hay que medir las piezas marcadas `por_medir`, especialmente
el ESP32 de 38 pines, el PAM8403, los potenciómetros y el ancho real de la cinta
IP65. Cambiar una envolvente conservadora por la medida física no cambia el
circuito; sí puede cambiar agujeros, ventanas y soportes.

La pantalla se reserva como módulo de 51,2 × 27,3 mm y el parlante como círculo
de 38,1 mm (1,5 pulgadas). La publicación del parlante no da profundidad ni
patrón de tornillos, así que esos dos datos siguen pendientes de calibre.
