"""DSN edit: pads of parts that cannot be soldered on the component side get copper only on B.Cu."""
import re
import os
REFS = re.compile(r'UnaCara_(' + os.environ.get('RESTR', r'U\d|J\d|RV\d|SW1|C1|C3|C8|C10|C19|C26') + r')$')
def restringir(t):
    usados = set(); out = []; dentro = False
    for line in t.split('\n'):
        m = re.match(r'\s*\(image (\S+)', line)
        if m: dentro = bool(REFS.search(m.group(1).strip('"')))
        elif dentro:
            mp = re.match(r'(\s*\(pin )(\S+)( .*)', line)
            if mp: usados.add(mp.group(2)); line = mp.group(1) + mp.group(2).rstrip('"') + '_B' + ('"' if mp.group(2).startswith('"') else '') + mp.group(3)
        out.append(line)
    t = '\n'.join(out)
    nuevos = []
    for name in usados:
        i = t.index(f'(padstack {name}\n'); j = t.index('\n    )', i) + 6
        blk = t[i:j]
        blk = re.sub(r'\n\s*\(shape \([^\n]*F\.Cu[^\n]*\)\)', '', blk)
        nb = name.rstrip('"') + '_B' + ('"' if name.startswith('"') else '')
        nuevos.append(blk.replace(f'(padstack {name}\n', f'(padstack {nb}\n', 1))
    k = t.index('    (padstack ')
    return t[:k] + '\n'.join('    ' + n.lstrip() if not n.startswith('    ') else n for n in nuevos) + '\n' + t[k:]
