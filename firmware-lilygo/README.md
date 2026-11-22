# Simulador LilyGO T4-S3 del ecualizador

Interfaz horizontal 600 × 450 construida con LVGL 9.6 y datos de audio
simulados. No modifica ni
reemplaza el firmware vigente de la pantalla Waveshare. Presenta cuatro vistas:
bandas, espectro, forma de onda y ajustes. Un deslizamiento horizontal en
cualquier parte de la pantalla cambia entre las tres vistas de audio. Un
deslizamiento vertical hacia abajo abre ajustes y uno hacia arriba regresa a
la última vista. LVGL gestiona el táctil, los gestos, los botones y las
transiciones animadas. Las pestañas superiores y el botón físico sirven como
alternativas; las vistas no cambian automáticamente.

`AJUSTES` permite iniciar o detener el portal cautivo, ver SSID e IP, guardar el
brillo en flash y reiniciar el controlador táctil. El portal crea la red
`Ecualizador-Setup`, contraseña `ecualizador`, en `192.168.4.1`, y se cierra a
los tres minutos. Estas operaciones no requieren recompilar.

```sh
pio run
pio run -t upload --upload-port /dev/ttyACM0
pio device monitor --port /dev/ttyACM0 --baud 115200 --filter printable
```

El simulador no afirma medir audio real. Los niveles, la frecuencia dominante,
el recorte y la forma de onda son animaciones coherentes para validar la
composición visual en la pantalla adquirida.
