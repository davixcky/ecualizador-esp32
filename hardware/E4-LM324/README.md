# E.4-LM324 · una cara para soldadura manual

E.4 conserva el circuito validado D.3-LM324 y la topología de una sola cara, pero revisa la geometría pensando en fresado CNC y montaje con cautín. Es la revisión recomendada frente a E.3.

## Cambios para facilitar el montaje

- Todos los pads de componentes tienen al menos **2,4 × 2,0 mm**. En piezas sin restricción de paso, 132 pads son de 2,4 mm o mayores en ambos ejes.
- Los 44 pads propios de puentes son circulares de **2,4 mm**, con taladro de 0,8 mm.
- **Ningún puente reutiliza el agujero de un componente.** Cada extremo termina en un pad perforado propio; la comprobación automática aparece como `shared_bridge_holes: []`.
- El taladro propio de JP19 queda bajo el cuerpo de R25 por la isla de masa aislada de esa zona. Se suelda JP19 antes de montar R25; el agujero sigue siendo independiente de los dos pads de R25.
- El enlace largo de +5 V se sustituyó por una pista perimetral de 1,0 mm.
- No quedan ramales de cobre sueltos.

## Resultado verificado

| Regla | Resultado |
|---|---:|
| Cobre | solo B.Cu |
| Pista de señal mínima | 0,7 mm |
| Alimentación | 1,0 mm |
| Pad de componente mínimo real | 2,0 mm; eje largo ≥ 2,4 mm |
| Pad propio de puente | 2,4 mm |
| Vías metalizadas | 0 |
| Pistas de paso entre pines de 2,54 mm | 0 |
| Alambres | 25 |
| Longitud de alambre | mediana 13,8 mm; máximo 30,9 mm |
| KiCad DRC | 0 errores, 0 conexiones abiertas, 0 pistas colgantes |
| Paridad esquema ↔ PCB | 0 diferencias |
| ERC | 0 errores; 23 avisos `NC-*` intencionales |

El único aviso geométrico de taladro es `pth_inside_courtyard` para JP19/R25: identifica el orden de montaje descrito arriba, no un agujero compartido. Los avisos de serigrafía representan las líneas que identifican los alambres y no afectan el Gerber B.Cu.

## Orden de soldadura

1. Instalar los 25 alambres siguiendo [`alambres.csv`](alambres.csv). Soldar JP19 antes de R25. Todos los extremos usan agujeros propios; no insertar un puente en el agujero de otro componente.
2. Para que el desacoplo sea realmente local, no montar C4–C7 y C25 en sus posiciones remotas del dibujo. Soldar por la cara inferior, con las patas lo más cortas posible:
   - C4 entre U1-4 (+5 V) y U1-11 (GND).
   - C5 entre U2-4 y U2-11.
   - C6 entre U3-4 y U3-11.
   - C7 entre U4-4 y U4-11.
   - C25 entre U6-14 (+5 V) y U6-12 (GND en la asignación E.4).
   Usar cerámicos de 100 nF y reservar unos 3 mm bajo la PCB. Los agujeros rotulados C4–C7/C25 quedan sin poblar; sus pistas pueden permanecer.
3. Soldar resistencias, diodos y los demás capacitores pequeños.
4. Instalar los zócalos DIP, conectores y el zócalo del ESP32.
5. Instalar electrolíticos y piezas altas.
6. Sin insertar los integrados, comprobar continuidad, ausencia de corto entre +5 V/GND y +3.3VA/GND, y tensiones de alimentación.

## Archivos

- [`proyecto/ecualizador-E4-LM324.kicad_pro`](proyecto/ecualizador-E4-LM324.kicad_pro): **fuente única de verdad**; abre esquema y PCB juntos.
- [`proyecto/ecualizador-E4-LM324.pdf`](proyecto/ecualizador-E4-LM324.pdf): esquema físico E.4 exportado.
- [`fabricacion/`](fabricacion/): Gerber B.Cu, contorno, taladros y planos PDF.
- [`vistas/3d-top.png`](vistas/3d-top.png) y [`vistas/3d-bottom.png`](vistas/3d-bottom.png): montaje y cobre.
- [`validacion-cnc.json`](validacion-cnc.json): reglas geométricas automáticas.
- [`etiquetas-conectores.csv`](etiquetas-conectores.csv): orden físico de conectores.

Falta fabricar y medir una muestra; la validación digital no reemplaza esa prueba.
