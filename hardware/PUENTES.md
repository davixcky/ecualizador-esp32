# Puentes D.2 — montaje por caras

29 tramos cortos arriba (hasta 20 mm entre extremos) y 51 cables aislados por debajo. Se mantienen 80 tramos en 79 grupos: este cambio ordena el montaje; no reduce el número de conexiones.

La PCB tiene cobre únicamente en B.Cu. La cara de montaje del cable no es una capa adicional de cobre. JP67–JP79 se sueldan a terminales existentes; los restantes tienen taladros propios.

## Montaje

1. Instalar los puentes superiores antes de los componentes que puedan taparlos. Usar cable aislado; no dejar conductor desnudo en los cruces.
2. Montar los componentes y después el cableado inferior. Identificar ambos extremos con el mismo número JP. Seguir la columna Cara, no una línea impresa sobre la placa.
3. Mantener los cables inferiores dentro del contorno, separados de los tornillos y sujetos con pequeños puntos de adhesivo apto para electrónica. Reservar 8 mm libres bajo la PCB; el gabinete dispone de 26 mm hasta el piso. Comprobar también la separación respecto al parlante y su cableado.
4. Evitar mazos compartidos entre señales de audio y alimentación LED/reloj de pantalla. Los cruces entre cables deben conservar su aislamiento. No prensarlos contra las soldaduras.
5. Antes de alimentar, comprobar continuidad de cada JP y ausencia de cortos entre alimentación y GND. La DRC comprueba las conexiones del diseño; no sustituye esta revisión del montaje.

Los modelos 3D muestran arcos orientativos de cable, no una longitud de corte ni un ensayo de colisiones. Los planos de cada cara y las coordenadas definen los extremos reales. Todas las coordenadas de la tabla se leen desde arriba; el plano inferior está reflejado para verlo desde abajo.

| Puente | Red | Inicio (x, y), mm | Fin (x, y), mm | Cara | Conexión |
|---|---|---|---|---|---|
| JP1 | Net-(D3-K) | 16.760, 25.740 | 23.380, 8.980 | superior | Taladros propios |
| JP2 | GND | 21.950, 80.690 | 40.050, 85.450 | superior | Taladros propios |
| JP3 | Net-(C9-Pad1) | 23.630, 103.240 | 23.630, 106.360 | superior | Taladros propios |
| JP4 | /M_INV | 24.260, 19.700 | 48.260, 7.530 | inferior | Taladros propios |
| JP5 | /ADC_G | 38.960, 70.940 | 48.090, 48.850 | inferior | Taladros propios |
| JP6 | Net-(C10-Pad1) | 46.800, 71.430 | 50.680, 83.250 | superior | Taladros propios |
| JP7 | Net-(D2-A) | 58.140, 39.050 | 59.940, 14.600 | inferior | Taladros propios |
| JP8/1 | /MEDIOS | 91.730, 78.910 | 91.730, 84.120 | inferior | Taladros propios |
| JP8/2 | /MEDIOS | 91.730, 78.910 | 143.640, 19.250 | inferior | Taladros propios |
| JP9 | /TFT_SCK | 97.080, 50.190 | 104.600, 50.190 | superior | Taladros propios |
| JP10 | /MED_HP | 101.140, 88.000 | 102.980, 76.260 | superior | Taladros propios |
| JP11 | Net-(U2D-+) | 104.410, 106.480 | 111.720, 87.820 | inferior | Taladros propios |
| JP12 | /IN_R | 105.400, 57.100 | 109.570, 53.630 | superior | Taladros propios |
| JP13 | /AGUDOS | 130.510, 66.450 | 136.290, 22.990 | inferior | Taladros propios |
| JP14 | /LED_DIN | 138.190, 42.420 | 193.560, 35.230 | inferior | Taladros propios |
| JP15 | /LINEA | 139.260, 87.240 | 155.960, 39.810 | inferior | Taladros propios |
| JP16 | Net-(R4-Pad2) | 141.580, 33.820 | 148.980, 7.670 | inferior | Taladros propios |
| JP17 | /A_W | 142.270, 91.050 | 168.440, 36.620 | inferior | Taladros propios |
| JP18 | /TFT_SCK | 142.850, 44.410 | 153.630, 44.160 | superior | Taladros propios |
| JP19 | /TFT_SCK | 166.520, 50.800 | 178.460, 84.740 | inferior | Taladros propios |
| JP20 | +5V | 112.202, 50.338 | 53.079, 56.884 | inferior | Taladros propios |
| JP21 | +5V | 116.550, 20.630 | 129.889, 21.402 | superior | Taladros propios |
| JP22 | GND | 45.390, 56.150 | 50.240, 86.357 | inferior | Taladros propios |
| JP23 | GND | 139.200, 27.478 | 152.030, 15.550 | superior | Taladros propios |
| JP24 | GND | 152.480, 93.792 | 144.711, 89.026 | superior | Taladros propios |
| JP25 | GND | 175.548, 65.385 | 177.601, 54.607 | superior | Taladros propios |
| JP26 | Net-(U1C-+) | 40.120, 90.480 | 24.113, 75.010 | inferior | Taladros propios |
| JP27 | Net-(U1C-+) | 46.725, 99.435 | 40.120, 95.480 | superior | Taladros propios |
| JP28 | /VREF | 30.110, 14.280 | 30.110, 19.360 | superior | Taladros propios |
| JP29 | /VREF | 40.227, 74.795 | 40.153, 33.173 | inferior | Taladros propios |
| JP30 | /VREF | 53.323, 88.170 | 46.700, 77.780 | superior | Taladros propios |
| JP31 | /VREF | 154.591, 27.293 | 154.650, 67.620 | inferior | Taladros propios |
| JP32 | /M_INV | 127.722, 87.722 | 68.748, 8.702 | inferior | Taladros propios |
| JP33 | /AGUDOS | 118.093, 72.470 | 109.415, 93.250 | inferior | Taladros propios |
| JP34 | +3.3VA | 41.893, 51.340 | 50.470, 41.140 | superior | Taladros propios |
| JP35 | +3.3VA | 58.320, 47.613 | 52.591, 43.261 | superior | Taladros propios |
| JP36 | +3.3VA | 64.208, 55.042 | 62.940, 49.527 | superior | Taladros propios |
| JP37 | +3.3VA | 104.620, 87.940 | 68.594, 55.616 | inferior | Taladros propios |
| JP38 | /AMP_IN | 147.030, 38.410 | 186.170, 70.160 | inferior | Taladros propios |
| JP39 | /MED_HP | 56.820, 80.780 | 46.430, 81.903 | superior | Taladros propios |
| JP40 | /A_W | 23.990, 14.280 | 138.563, 91.750 | inferior | Taladros propios |
| JP41 | Net-(U2B-+) | 103.641, 93.714 | 114.927, 71.200 | inferior | Taladros propios |
| JP42 | Net-(U1B-+) | 40.474, 98.872 | 34.000, 90.480 | superior | Taladros propios |
| JP43 | /PRE | 33.101, 79.363 | 43.477, 74.237 | superior | Taladros propios |
| JP44 | /PRE | 34.190, 96.517 | 32.559, 82.088 | superior | Taladros propios |
| JP45 | /GRAVES | 43.163, 93.250 | 21.030, 74.927 | inferior | Taladros propios |
| JP46 | /GRAVES | 46.430, 93.333 | 169.390, 10.470 | inferior | Taladros propios |
| JP47 | /LED_5V | 120.630, 42.220 | 114.050, 18.090 | inferior | Taladros propios |
| JP48 | /ADC_A | 19.990, 25.400 | 21.758, 22.672 | superior | Taladros propios |
| JP49 | /ADC_A | 23.289, 26.368 | 145.150, 77.780 | inferior | Taladros propios |
| JP50 | Net-(U4C--) | 66.023, 15.780 | 62.398, 12.238 | superior | Taladros propios |
| JP51 | Net-(C20-Pad1) | 115.011, 103.929 | 118.093, 105.950 | superior | Taladros propios |
| JP52 | Net-(D2-K) | 40.808, 16.322 | 37.690, 16.820 | superior | Taladros propios |
| JP53 | Net-(D2-K) | 46.162, 14.778 | 43.118, 15.365 | superior | Taladros propios |
| JP54 | +3V3 | 77.510, 12.033 | 75.708, 57.571 | inferior | Taladros propios |
| JP55 | /TFT_CS | 185.050, 85.400 | 107.540, 19.360 | inferior | Taladros propios |
| JP56 | /TFT_DC | 178.353, 71.014 | 108.317, 24.375 | inferior | Taladros propios |
| JP57 | /TFT_BL | 99.768, 28.128 | 39.500, 56.190 | inferior | Taladros propios |
| JP58 | /TFT_BL | 186.550, 80.320 | 107.683, 28.124 | inferior | Taladros propios |
| JP59 | /G_W | 164.390, 13.010 | 127.900, 91.750 | inferior | Taladros propios |
| JP60 | /ADC_M | 135.150, 75.240 | 58.550, 20.630 | inferior | Taladros propios |
| JP61 | /LED_DATA | 112.050, 15.550 | 121.820, 53.963 | inferior | Taladros propios |
| JP62 | /BTN | 176.290, 38.642 | 154.650, 87.940 | inferior | Taladros propios |
| JP63 | +5V | 115.738, 46.802 | 115.593, 22.940 | inferior | Taladros propios |
| JP64 | Net-(D2-K) | 58.050, 30.790 | 51.841, 18.214 | superior | Taladros propios |
| JP65 | /G_W | 44.150, 24.938 | 124.882, 89.982 | inferior | Taladros propios |
| JP66 | GND | 46.173, 53.248 | 44.979, 50.338 | superior | Taladros propios |
| JP67 | GND | 27.610, 16.820 | 55.550, 25.710 | inferior | Terminal existente |
| JP68 | Net-(U1D-+) | 44.120, 85.400 | 54.280, 98.100 | inferior | Terminal existente |
| JP69 | Net-(U1D-+) | 54.280, 68.890 | 44.120, 85.400 | inferior | Terminal existente |
| JP70 | +3.3VA | 30.150, 91.750 | 36.500, 87.940 | inferior | Terminal existente |
| JP71 | +3.3VA | 36.500, 87.940 | 47.930, 90.480 | inferior | Terminal existente |
| JP72 | +3.3VA | 42.850, 53.650 | 36.500, 87.940 | inferior | Terminal existente |
| JP73 | +3.3VA | 50.470, 37.140 | 47.930, 25.710 | inferior | Terminal existente |
| JP74 | +3.3VA | 119.050, 90.480 | 107.620, 87.940 | inferior | Terminal existente |
| JP75 | Net-(U4C--) | 60.630, 10.470 | 27.610, 21.900 | inferior | Terminal existente |
| JP76 | /LED_DATA | 157.150, 82.860 | 124.130, 54.920 | inferior | Terminal existente |
| JP77 | /M_W | 60.630, 18.090 | 55.550, 28.250 | inferior | Terminal existente |
| JP78 | /TFT_MOSI | 182.550, 65.080 | 102.540, 14.280 | inferior | Terminal existente |
| JP79 | /TFT_RST | 182.550, 67.620 | 102.540, 24.440 | inferior | Terminal existente |
