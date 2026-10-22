"""Demo audible: música original → respuesta AC SPICE variable → WAV y datos visuales.
Es una aproximación cuasiestática de pequeña señal, no audio grabado del prototipo.
"""
import sys,json,subprocess,tempfile,hashlib
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile
ROOT=Path(__file__).resolve().parent;OUT=ROOT.parent/'docs/video';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT.parent/'herramientas'))
from simulacion import netlist,OPAMP_LIB
from demo_timeline import FPS,DURATION,FRAMES,state
SR=48000
# Obtener respuestas complejas del circuito completo hasta la salida de línea.
responses=[]
with tempfile.TemporaryDirectory(prefix='eq-demo-spice-') as tmp:
    tmp=Path(tmp);(tmp/'mcp6004.lib').write_text(OPAMP_LIB)
    for band in range(3):
        bank=[]
        for pos in np.linspace(0,1,11):
            pots={'RV1':.5,'RV2':.5,'RV3':.5,'RV4':.5,'RV5':.5};pots[f'RV{band+2}']=float(pos)
            circuit=netlist(pots)
            (tmp/'audio.cir').write_text('* Demo de audio: salida LINEA\n'+circuit+'\n.control\nset wr_singlescale\nset wr_vecnames\nac dec 100 5 24000\nwrdata respuesta.dat real(v(LINEA)) imag(v(LINEA))\n.endc\n.end\n')
            result=subprocess.run(['ngspice','-b','audio.cir'],cwd=tmp,capture_output=True,text=True)
            if result.returncode:raise RuntimeError(result.stdout+result.stderr)
            d=np.loadtxt(tmp/'respuesta.dat',skiprows=1)
            assert d.shape[1]==3,d.shape
            freq=d[:,0];bank.append(d[:,1]+1j*d[:,2])
        responses.append(bank)
H=np.array(responses);assert np.all(np.isfinite(H))
np.savez_compressed(OUT/'respuestas-spice.npz',frecuencia=freq,respuesta=H,posiciones=np.linspace(0,1,11))
# Composición original, reproducible, sin pista comercial. El motivo se repite cada 7 s.
t=np.arange(SR*DURATION)/SR;beat=.4375;phase=t%7
rng=np.random.default_rng(2048)
noise=rng.normal(0,1,len(t))
high=signal.sosfilt(signal.butter(3,4500,fs=SR,btype='high',output='sos'),noise)
x=np.zeros(len(t))
notes=[82.4069,98,110,73.4162]
for onset in np.arange(0,DURATION,beat):
    age=t-onset;mask=(age>=0)&(age<beat)
    k=int(round(onset/beat));f=notes[(k//4)%4]
    a=age[mask]
    bass=(np.sin(2*np.pi*f*a)+.2*np.sin(2*np.pi*2*f*a))*np.exp(-a*4)*(1-np.exp(-a*180))
    melody=(np.sin(2*np.pi*f*8*a)+.28*np.sin(2*np.pi*f*12*a))*np.exp(-a*9)*(1-np.exp(-a*250))
    kick=np.sin(2*np.pi*(48*a+4*(1-np.exp(-a*25))))*np.exp(-a*20)
    x[mask]+=.34*bass+.18*melody+(.22*kick if k%2==0 else 0)
for onset in np.arange(0,DURATION,beat/2):
    age=t-onset;mask=(age>=0)&(age<.12)
    x[mask]+=.13*high[mask]*np.exp(-age[mask]*42)
# Entrada pequeña para mantener el modelo en régimen lineal.
x=x/max(abs(x))*.03
f,tt,Z=signal.stft(x,fs=SR,nperseg=4096,noverlap=3616,boundary='zeros')
interp=np.empty((3,11,len(f)),complex)
for b in range(3):
    for p in range(11):
        interp[b,p]=np.interp(f,freq,H[b,p].real)+1j*np.interp(f,freq,H[b,p].imag)
        interp[b,p,0]=0
Y=np.empty_like(Z)
for j,tj in enumerate(tt):
    values,active=state(float(tj));band=active if active is not None else 0
    p=values[band]*10;lo=min(9,int(p));u=p-lo
    response=interp[band,lo]*(1-u)+interp[band,lo+1]*u
    Y[:,j]=Z[:,j]*response
_,y=signal.istft(Y,fs=SR,nperseg=4096,noverlap=3616,boundary=True)
y=y[:len(x)]
# Un único nivel de reproducción para toda la demo: no borrar el efecto con normalización por tramo.
gain=.87/max(abs(y));y*=gain
fade=np.minimum(1,t/.12)*np.minimum(1,(DURATION-t)/.5);y*=fade
wavfile.write(OUT/'demo-audio.wav',SR,np.round(y*32767).astype(np.int16))
wavfile.write(OUT/'demo-entrada.wav',SR,np.round(x/.03*.7*32767).astype(np.int16))
# Espectro y energía de cada banda derivados del mismo WAV, un estado por fotograma.
visual=[];edges=np.geomspace(40,18000,41);ff=np.fft.rfftfreq(4096,1/SR)
for frame in range(FRAMES):
    center=round(frame/FPS*SR);indices=np.arange(center-2048,center+2048)
    segment=y[np.clip(indices,0,len(y)-1)]*np.hanning(4096)
    power=abs(np.fft.rfft(segment))**2
    bands=[np.sqrt(power[(ff>=lo)&(ff<hi)].sum()) for lo,hi in [(20,300),(300,3000),(3000,20000)]]
    spectrum=[np.sqrt(power[(ff>=lo)&(ff<hi)].sum()) for lo,hi in zip(edges,edges[1:])]
    values,active=state(frame/FPS)
    visual.append({'time':frame/FPS,'sliders':values,'active':active,'bands':bands,'spectrum':spectrum})
scale=max(max(row['bands']) for row in visual);sp=max(max(row['spectrum']) for row in visual)
for row in visual:
    row['bands']=[float(v/scale) for v in row['bands']]
    row['spectrum']=[float(np.log1p(v/sp*30)/np.log(31)) for v in row['spectrum']]
(OUT/'demo-timeline.json').write_text(json.dumps(visual,separators=(',',':')))
checks=[]
for band,fx in enumerate((100,1000,8000)):
    low=abs(np.interp(fx,freq,H[band,0].real)+1j*np.interp(fx,freq,H[band,0].imag))
    high=abs(np.interp(fx,freq,H[band,10].real)+1j*np.interp(fx,freq,H[band,10].imag))
    delta=float(20*np.log10(high/low));assert delta>6,(band,delta)
    checks.append({'band':band,'frequency_Hz':fx,'max_vs_min_dB':delta})
report={'method':'SPICE AC LINEA + STFT quasi-static interpolation','duration_s':DURATION,'sample_rate':SR,'samples':len(y),'peak':float(max(abs(y))),'clipped_samples':int(np.sum(abs(y)>=1)),'single_playback_gain':float(gain),'slider_tests':checks,'source':'original procedural composition','hardware_recording':False,'circuit_sha256':hashlib.sha256((ROOT.parent/'herramientas/circuito.py').read_bytes()).hexdigest()}
(OUT/'validacion-audio.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
