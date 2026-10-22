"""Comprueba cambios audibles contra la misma entrada con controles al 50 %."""
from pathlib import Path
import json
import numpy as np
from scipy import signal
from scipy.io import wavfile
root=Path(__file__).resolve().parent.parent/'docs/video'
report=json.loads((root/'validacion-audio.json').read_text())
sr,x=wavfile.read(root/'demo-entrada.wav');x=x.astype(float)/32767*(.03/.7)
sr,y=wavfile.read(root/'demo-audio.wav');y=y.astype(float)/32767
model=np.load(root/'respuestas-spice.npz');freq=model['frecuencia'];h=model['respuesta'][0,5]
f,t,z=signal.stft(x,fs=sr,nperseg=4096,noverlap=3616,boundary='zeros')
response=np.interp(f,freq,h.real)+1j*np.interp(f,freq,h.imag);response[0]=0
_,baseline=signal.istft(z*response[:,None],fs=sr,nperseg=4096,noverlap=3616,boundary=True)
baseline=baseline[:len(y)]*report['single_playback_gain']
checks=[]
for band,(lo,hi) in enumerate([(20,300),(300,3000),(3000,18000)]):
    sos=signal.butter(4,[lo,hi],fs=sr,btype='bandpass',output='sos')
    actual=signal.sosfilt(sos,y);reference=signal.sosfilt(sos,baseline)
    ratios=[]
    for a,b in [(1.2,1.8),(4.1,4.7)]:
        start=3+7*band;sl=slice(round((start+a)*sr),round((start+b)*sr))
        ratios.append(float(10*np.log10(np.mean(actual[sl]**2)/np.mean(reference[sl]**2))))
    assert ratios[1]-ratios[0]>5,(band,ratios)
    checks.append({'band':band,'low_vs_center_dB':ratios[0],'high_vs_center_dB':ratios[1],'difference_dB':ratios[1]-ratios[0]})
report['wav_band_comparisons']=checks
(root/'validacion-audio.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(checks,indent=2))
