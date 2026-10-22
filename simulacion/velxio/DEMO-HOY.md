# Ensayo de filtros para la exposición

Leo Rojas, David Orozco y Manuel Castilla · Electrónica II · CUC

## Abrir la demostración

1. Abrir https://velxio.dev/editor/ y elegir **File → Import project**.
2. Cargar `filtros-1000Hz.vlx`. Seleccionar **Circuit**. El circuito analógico se resuelve automáticamente; no necesita compilar firmware.
3. El generador superior entrega una senoidal de **0,1 V pico (0,2 Vpp), 1 kHz, offset 1,65 V** en PRE. El generador inferior representa VREF; no es una segunda entrada de audio.
4. Clic derecho sobre el cable que sale del generador superior → **Add to scope**. Repetir en la salida de U2A, antes del medidor de medios. Son CH1 = entrada y CH2 = salida. Los nombres de canal del simulador son nombres internos de red.
5. Usar 0,5 ms/div para 1 kHz. El osciloscopio integrado tiene una escala vertical amplia; para comparar amplitudes pequeñas, usar también los medidores RMS relativos a VREF.
6. Importar `filtros-100Hz.vlx` y `filtros-8000Hz.vlx` para comparar las otras bandas. Volver a añadir las sondas tras importar: los canales del osciloscopio no se guardan en el formato VLX.

## Qué decir mientras se muestra

«Inyectamos la señal en PRE para estudiar solo los filtros. Graves deja pasar las frecuencias bajas; agudos, las altas. Medios tiene dos etapas conectadas: primero elimina las bajas y después las altas. Comparamos entrada y salida, cambiamos la frecuencia y observamos cuál banda predomina».

A 1 kHz, en la captura validada, los medidores indican aproximadamente 6,11 mV RMS en graves, 63,23 mV en medios y 4,51 mV en agudos. Son resultados del modelo ideal y de la ventana transitoria del simulador, no medidas de una placa física.

## Repetir con instrumentos en el banco

- Alimentación de los MCP6004: 3,3 V; VREF aproximadamente 1,65 V. Verificar ambas con multímetro antes de inyectar señal.
- Generador: seno, 200 mVpp **medidos en PRE**, offset 1,65 V. Configurar carga Hi-Z si existe esa opción; algunos generadores muestran una amplitud para carga de 50 Ω que se duplica sobre alta impedancia.
- Conectar la masa del generador y las pinzas de masa del osciloscopio a **GND**, nunca a VREF. CH1 a PRE y CH2 a GRAVES, MEDIOS o AGUDOS. Usar sondas ×10 y ajustar el factor en el instrumento.
- Con acoplamiento DC, comprobar el centro de 1,65 V. Para comparar la componente alterna, usar AC o desplazar verticalmente la traza. Empezar con 50 mV/div y ajustar.
- Probar 100 Hz, 1 kHz y 8 kHz; usar aproximadamente 2 ms/div, 0,2 ms/div y 20 µs/div. Registrar Vpp de entrada y salida; calcular ganancia = Vpp salida / Vpp entrada.
- Medir el desfase a partir del desplazamiento temporal: fase = 360° × Δt / T, indicando qué señal adelanta. No atribuir una fase solo por comparar amplitudes.

No se requiere ESP32, pantalla ni tira LED para este ensayo. El modelo de Velxio usa operacionales ideales; el montaje físico permite comprobar recorte, ruido y las limitaciones reales del MCP6004.
