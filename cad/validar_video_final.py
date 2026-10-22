"""Valida MP4, audio multiplexado y copia del video en el paquete de exposición."""
import json,subprocess,hashlib
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from scipy.io import wavfile
from demo_timeline import FRAMES,DURATION,FPS
root=Path(__file__).resolve().parent.parent
video=root/'docs/video/ecualizador-animado.mp4'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'])==(1920,1080)
assert v['codec_name']=='h264' and int(v['nb_frames'])==FRAMES and v['r_frame_rate']==f'{FPS}/1'
assert a['codec_name']=='aac' and int(a['sample_rate'])==48000
assert abs(float(probe['format']['duration'])-DURATION)<.05
subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True)
decoded=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-map','0:a:0','-f','f32le','-acodec','pcm_f32le','-']),dtype=np.float32)
sr,original=wavfile.read(root/'docs/video/demo-audio.wav');original=original.astype(float)/32768
n=min(len(original),len(decoded));correlation=float(np.corrcoef(original[:n],decoded[:n])[0,1])
assert correlation>.99,correlation
assert np.max(abs(decoded))<1
assert abs(len(decoded)/sr-DURATION)<.05
with ZipFile(root/'docs/exposicion-portable.zip') as z:
    assert z.read('docs/video/ecualizador-animado.mp4')==video.read_bytes()
sync=subprocess.run(['blender','-b',str(root/'docs/video/ecualizador-animado.blend'),'-P',str(root/'cad/validar_demo_blender.py')],capture_output=True,text=True)
assert 'DEMO_SYNC_OK' in sync.stdout,sync.stdout+sync.stderr
report={'video':'docs/video/ecualizador-animado.mp4','video_codec':v['codec_name'],'audio_codec':a['codec_name'],'pixels':[1920,1080],'fps':FPS,'frames':FRAMES,'duration_seconds':DURATION,'audio_sample_rate':sr,'audio_correlation_to_wav':correlation,'decoded_audio_peak':float(np.max(abs(decoded))),'decode_errors':0,'portable_package_video_identical':True,'blender_slider_led_audio_sync':True,'audio_method':'SPICE AC quasi-static processing, not hardware recording','sha256':hashlib.sha256(video.read_bytes()).hexdigest()}
(root/'docs/validacion/video-dispositivo.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
