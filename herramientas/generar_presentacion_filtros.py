"""Edición corta para explicar los filtros y medirlos en la exposición."""
from pathlib import Path
import re
r=Path(__file__).resolve().parents[1];s=(r/'docs/latex/presentacion.tex').read_text();pre=s.split(r'\begin{document}')[0];frames=re.findall(r'\\begin\{frame\}.*?\\end\{frame\}',s,re.S)
titles = [
'Ecualizador de audio de tres bandas',
'3,3 V de alimentación; 1,65 V de referencia',
'Filtro de graves: U1C, R9, R10, C11 y C12',
'Medios: dos filtros conectados en cascada',
'Agudos: pasa altas con U2B',
'Frecuencias calculadas y simuladas',
'Ensayo de hoy: generador y osciloscopio',
'Velxio: tres tonos, tres bandas',
'Abrir la simulación durante la exposición',
]
by_title = {re.search(r"\\begin\{frame\}\[t\]\{([^}]+)\}", frame)[1]: frame for frame in frames}
chosen = [by_title[title] for title in titles]
chosen[0]=chosen[0].replace('Ecualizador de audio de tres bandas','Filtros de audio: demostración de laboratorio')
chosen.insert(8,r'''\begin{frame}[t]{Entrada y salida de medios en el osciloscopio}
\centering\includegraphics[width=\linewidth,height=5.5cm,keepaspectratio]{velxio-osciloscopio.png}
\note{Las sondas están en PRE y en la salida de medios. Es una captura del motor SPICE de Velxio, no una fotografía del osciloscopio del laboratorio. Comparar amplitud y desplazamiento temporal.}
\end{frame}''')
(r/'docs/latex/presentacion-filtros.tex').write_text(pre+r'\begin{document}'+'\n'+'\n'.join(chosen)+'\n'+r'\end{document}'+'\n')
