# Resultados de la simulación (ngspice)

Generado por `herramientas/simulacion.py`.

| # | Caso | Resultado de la simulación | Criterio | Estado |
|---:|---|---|---|---|
| 1 | VREF en reposo | 1,6412 V | +3.3VA / 2 ± 0,5 % | Cumple |
| 2 | Salidas en reposo (PRE, EQ_OUT, ADC_FFT) | 1,641 V, 1,641 V, 1,641 V | VREF ± 10 mV | Cumple |
| 3 | Detector de graves sin señal (ADC_G) | 1,641 V | VREF a VREF + 50 mV | Cumple |
| 4 | Alimentación analógica +3.3VA (4 × MCP6004) | 3,282 V | ≥ 3,25 V (caída en R1 < 50 mV) | Cumple |
| 5 | Ganancia del preamplificador a 1 kHz | 3,20 (10,10 dB) | 3,2 ± 5 % (1 + 22k/10k) | Cumple |
| 6 | Frecuencia de corte: graves, pasa bajas | 239 Hz | 232 Hz ± 10 % | Cumple |
| 7 | Frecuencia de corte: medios, pasa altas | 403 Hz | 409 Hz ± 10 % | Cumple |
| 8 | Frecuencia de corte: medios, pasa bajas | 2388 Hz | 2322 Hz ± 10 % | Cumple |
| 9 | Frecuencia de corte: agudos, pasa altas | 4026 Hz | 4093 Hz ± 10 % | Cumple |
| 10 | Frecuencia de corte: antialiasing, pasa bajas | 5101 Hz | 4949 Hz ± 10 % | Cumple |
| 11 | Antialiasing: atenuación a 15 kHz | -19,3 dB | ≤ −15 dB (señal plegada sobre 5 kHz) | Cumple |
| 12 | Respuesta plana (deslizables al 50 %), 20 Hz–20 kHz | -0,27 a +0,88 dB (rizado 1,16 dB) | rizado ≤ 1,5 dB | Cumple |
| 13 | Valores de la Fase 1 (sin inversor), deslizables al 50 % | -11,0 a +0,1 dB (rizado 11,1 dB) | rizado ≤ 1,5 dB | No cumple: motivó el rediseño |
| 14 | Rango de ajuste de graves en 60 Hz | +6,4 dB al 100 %, -5,7 dB al 25 % | ≥ +5 dB y ≤ −5 dB respecto al 50 % | Cumple |
| 15 | Rango de ajuste de medios en 1000 Hz | +6,0 dB al 100 %, -5,1 dB al 25 % | ≥ +5 dB y ≤ −5 dB respecto al 50 % | Cumple |
| 16 | Rango de ajuste de agudos en 12000 Hz | +6,3 dB al 100 %, -5,6 dB al 25 % | ≥ +5 dB y ≤ −5 dB respecto al 50 % | Cumple |
| 17 | Selectividad: tono de 100 Hz | G 255 mV · M 16 mV · A 0 mV | solo sube la barra de graves (≥ 4 veces las otras) | Cumple |
| 18 | Selectividad: tono de 1000 Hz | G 15 mV · M 304 mV · A 17 mV | solo sube la barra de medios (≥ 4 veces las otras) | Cumple |
| 19 | Selectividad: tono de 8000 Hz | G 0 mV · M 12 mV · A 265 mV | solo sube la barra de agudos (≥ 4 veces las otras) | Cumple |
| 20 | Detector de medios: linealidad entre 0,1 y 0,5 V de pico | error máximo 2,0 % | ≤ 10 % (descarga entre picos incluida) | Cumple |
| 21 | Detector: tiempo de ataque (90 %) | 1,17 ms | ≤ 5 ms (sigue la música) | Cumple |
| 22 | Detector: descarga 22 ms después del silencio | 36 % del pico | ≈ 37 % (τ = Rd·Ch = 22 ms) | Cumple |
| 23 | Entrada de 0,11 V de pico (máxima), deslizables al 100 %: ADC_M | 1,878 V | ≤ 2,45 V (zona lineal del ADC) | Cumple |
| 24 | Ídem: ADC_FFT | 1,113 a 2,171 V | 0,15 a 2,45 V | Cumple |
