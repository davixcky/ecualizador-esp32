# Prácticas del modelo mecánico E.5

Estas reglas pertenecen al ecualizador. No se copian automáticamente a otros proyectos: cada
gabinete conserva sus propias restricciones, pruebas y medios de sujeción.

## Fuente de verdad

1. `medidas-componentes.json` registra cotas y el origen de cada dato.
2. `e5_layout.py` define la geometría y los encastres.
3. `generar_modelo.py` produce CAD, STL y `validacion-3d.json`.
4. Los PNG generados por `render_modelo.py` son la referencia visual vigente.
5. Los 3MF se generan desde los STL; una copia editada manualmente debe usar otro nombre.

Los videos son material histórico mientras no se regeneren explícitamente. No deben usarse para
decidir cómo fabricar o montar una revisión posterior del CAD.

## Diseño para servicio y fabricación

- Las piezas impresas del E.5 se retienen por encastre, presión o la tuerca/clip propio del componente;
  no se presupone pegamento. La pantalla 3,5″ se retiene con cuatro uñas fundidas
  en la tapa (entra corrida 3 mm y la cuna de GRAVES le cierra la salida), sin pieza impresa propia.
- Primero se imprimen las probetas con el mismo material, boquilla, orientación y perfil final. Un encastre
  nominal en CAD no se declara validado hasta probarlo físicamente.
- No se ocultan incertidumbres: cada cota se marca como medida, publicada, conservadora o supuesta.
- `E5-completo-generado.3mf` es regenerable; `E5-completo.3mf` queda reservado para cambios del usuario.
- Cuerpo y tapa de una pieza no caben acostados en 256 × 256 mm. La orientación de canto requiere soportes
  y revisión manual; `CAMA=350x320` es preferible. `MITADES=1` es una alternativa con junta visible.

## Separación mecánica y eléctrica

Que algo aparezca en el CAD no significa que esté resuelto eléctricamente. Siguen como propuestas el
elevador de 5 a 12 V para la tira, el enlace UART con la pantalla CYD y la entrada mono a ambos canales del
PAM8403. Los renders deben rotular o documentar esas condiciones, nunca presentarlas como hardware probado.

## Contrato de los renders

- Regenerar las cinco vistas después de cualquier cambio visible.
- Ejecutar `validar_renders.py`; este verifica archivos, resolución, decodificación, contenido no vacío y
  que sean posteriores a sus fuentes.
- Una imagen aprobada no demuestra tolerancias, óptica, resistencia ni funcionamiento. Esas propiedades se
  verifican con probetas, montaje e instrumentos.
