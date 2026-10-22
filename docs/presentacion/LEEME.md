# Presentación CUC

Las fuentes editables siguen en `../latex/presentacion.tex`. Se compila con LuaLaTeX para incorporar Red Hat Display y el logo vectorial oficial.

- **Para entregar:** `presentacion-fase2.pdf`, 36 diapositivas completas, sin estados intermedios.
- **Para exponer con movimiento:** `presentacion-animada.pptx`. Abrir en PowerPoint, iniciar con F5 y avanzar con clic o flecha derecha. El avance es manual. Cada estado de Beamer se convierte en una diapositiva con transición de fundido y notas del orador. El contador visible conserva las 36 diapositivas temáticas.
- **Alternativa en PDF:** `presentacion-animada.pdf`. Incluye los mismos pasos y transiciones PDF. El revelado por páginas funciona al avanzar; el fundido depende del visor y puede omitirse en navegadores. Para transiciones consistentes, usar el PowerPoint.
- **Notas:** `presentacion-notas.pdf` muestra la diapositiva junto al guion. `presentacion-fase2.pptx` contiene las 36 diapositivas completas y un fundido entre ellas.

Movimiento incluido: objetivos por pasos; explicación antes de imagen en alimentación, FFT y NeoPixel; aparición de la respuesta corregida sobre la curva de Fase 1. No hay avance automático ni elementos en movimiento continuo durante la lectura.

El PowerPoint contiene imágenes de los estados de LaTeX: editar el `.tex` y ejecutar `bash herramientas/compilar_documentos.sh` para regenerarlo. Las notas se extraen de `\note{}`. La identidad aplicada y la procedencia del logo están documentadas en `../../img/marca/README.md`.

La versión animada tiene **46 pasos para las 36 diapositivas temáticas**. La versión de entrega permanece en 36 páginas. Las fuentes tipográficas están incluidas y se incrustan en los PDF; PowerPoint conserva la apariencia mediante imágenes de las páginas.

Los botones de Velxio y planos conservan sus hipervínculos en PowerPoint. El esquema y el plano D.2 se adjuntan a los PDF junto con los casos `.vlx`. Los enlaces locales requieren conservar la estructura de carpetas; los adjuntos pueden extraerse con un visor que admita archivos incorporados.

Las diapositivas de circuitos muestran las referencias y valores principales. Medios se dibuja como una cascada conectada; los diagramas de bloques no llevan etiquetas sobre las flechas. El ensayo `led-animado.vlx` se inicia con Run y es independiente de los tres casos de filtros.

Para la explicación de hoy: `presentacion-filtros-hoy.pdf` y `presentacion-filtros-hoy.pptx` con notas, 10 diapositivas centradas en filtros, generador y osciloscopio. Fuente: `../latex/presentacion-filtros.tex`. La prueba integrada ADC→LED aún falla en Velxio; los ensayos de filtros y LED se presentan por separado.

El estado del arte compara Sallen-Key, ADAU1701 y WLED Audio Reactive. El marco teórico explica filtros activos y suma de bandas; las diapositivas de detectores y FFT completan la adquisición y visualización.

Copiar `../exposicion-portable.zip` y extraerlo completo. El botón del esquema salta al anexo interno del PDF y PowerPoint; `esquema.pdf` también se ofrece independiente. La edición corta de laboratorio conserva diez diapositivas.

## Demo con sonido

Abrir [el video del dispositivo](../video/ecualizador-animado.mp4) y activar el sonido. Dura 36 segundos: graves, medios y agudos bajan y suben por separado, con audio procesado mediante el modelo SPICE del circuito. Es una demo virtual; la pantalla y los LED se sincronizan con esa pista. El MP4 también está incluido en `docs/exposicion-portable.zip`.
