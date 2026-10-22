#!/usr/bin/env python3
"""Incluye los VLX en la página local para descargar sin servidor ni fetch file://."""
from pathlib import Path
import base64,json,re
root=Path(__file__).resolve().parents[1]
p=root/'simulacion/velxio/index.html'
files={f.name:base64.b64encode(f.read_bytes()).decode() for f in p.parent.glob('*.vlx')}
script='''<!-- CASOS-INICIO --><script>
const proyectos=DATA;
for(const a of document.querySelectorAll('a[download]'))a.addEventListener('click',event=>{
event.preventDefault();const name=a.getAttribute('href');const bytes=Uint8Array.from(atob(proyectos[name]),x=>x.charCodeAt(0));
const url=URL.createObjectURL(new Blob([bytes],{type:'application/octet-stream'}));const link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
});
</script><!-- CASOS-FIN -->'''.replace('DATA',json.dumps(files))
s=p.read_text();s=re.sub(r'<!-- CASOS-INICIO -->.*?<!-- CASOS-FIN -->','',s,flags=re.S)
p.write_text(s.replace('</html>',script+'</html>'))
