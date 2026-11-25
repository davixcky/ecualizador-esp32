"""Local Velxio cases using the project's own MCP6004 macro-model."""
import json
from ordenar_velxio import arrange
from potenciometros_velxio import add_controls, multitone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'simulacion/velxio'
for hz in (100,1000,8000):
    payload=json.loads((OUT/f'integrado-{hz}Hz.vlx').read_text())
    payload['name']=f'EQ03 LOCAL / macromodelo MCP6004 / {hz} Hz'
    for part in payload['components']:
        if part['metadataId'] == 'opamp-ideal':
            part['properties']['model']='eq03-mcp6004'
            part['properties']['detector']=part['id'] in ('U3A','U3C','U4A')
    payload=arrange(payload)
    routes=OUT/'local/rutas-presentacion.json'
    if routes.exists():
        from ordenar_velxio import partitions
        saved=json.loads(routes.read_text())
        if partitions(saved)!=partitions(payload['wires']):
            raise ValueError('Regenerar rutas: cambió la conectividad.')
        payload['wires']=saved
    (OUT/f'integrado-local-{hz}Hz.vlx').write_text(json.dumps(add_controls(payload),indent=2))
(OUT/'integrado-local-multitono.vlx').write_text(json.dumps(multitone(json.loads((OUT/'integrado-local-1000Hz.vlx').read_text())),indent=2))
print('Tres casos locales; requieren el parche limites-operacional.patch.')
