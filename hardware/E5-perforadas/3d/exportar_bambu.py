#!/usr/bin/env python3
"""Proyectos 3MF de las piezas imprimibles del E.5, listos para abrir en Bambu Studio.

    freecadcmd hardware/E5-perforadas/3d/generar_modelo.py      # antes: genera stl/
    python3 hardware/E5-perforadas/3d/exportar_bambu.py

Escribe en bambu/ estos proyectos 3MF (en milímetros, un objeto con nombre por pieza). Si `bambu-studio`
está instalado, su CLI los convierte a proyecto nativo; la interfaz gráfica no abre el 3MF genérico:

    E5-piezas-pequenas.3mf   difusores, cunas, capuchón y placa trasera desmontable de la T4-S3
    E5-cuerpo-izquierda/-derecha.3mf   mitades del cuerpo (color A y color B)
    E5-tapa-izquierda/-derecha.3mf     mitades de la tapa, con la cara exterior en la cama
    E5-pruebas-de-ajuste.3mf           probetas pequeñas para comprobar encajes ANTES de imprimir lo demás
    E5-completo-generado.3mf           todas las camas en un solo proyecto con dos filamentos (requiere bambu-studio)

La cama por defecto es de 256 x 256 mm (Bambu Lab P2S, P1, X1, A1). El cuerpo y la tapa miden 278 x 192 mm
y no caben acostados: van de una pieza, de canto y en diagonal, con soportes activados (E5-cuerpo.3mf y
E5-tapa.3mf). Con CAMA=350x320 (H2D) van acostados y sin soportes. Con MITADES=1 se usan dos mitades con
cola de milano, acostadas, una por filamento.

Bambu Studio solo respeta varias camas si el proyecto trae sus ajustes; por eso E5-completo-generado.3mf sí
lleva impresora, proceso y filamento de sistema (se cambian en Bambu Studio o con las variables
IMPRESORA, PROCESO, FILAMENTO y COLORES). Los demás no llevan ajustes y usan los que estén abiertos.
"""
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import struct
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STL = HERE / "stl"
OUT = HERE / "bambu"
BED = tuple(float(v) for v in os.environ.get("CAMA", "256x256").lower().split("x"))
MARGIN = 6.0


def read_stl(path):
    """STL binario -> (vértices únicos, triángulos)."""
    data = path.read_bytes()
    n = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + 50 * n, f"{path.name}: no es STL binario"
    index, verts, tris = {}, [], []
    for i in range(n):
        f = struct.unpack_from("<12f", data, 84 + 50 * i)
        tri = []
        for k in (3, 6, 9):
            key = (round(f[k], 4), round(f[k + 1], 4), round(f[k + 2], 4))
            if key not in index:
                index[key] = len(verts)
                verts.append(key)
            tri.append(index[key])
        if len(set(tri)) == 3:
            tris.append(tuple(tri))
    return verts, tris


def open_edges(tris):
    """Aristas que no pertenecen a exactamente dos triángulos (0 = malla cerrada)."""
    count = {}
    for a, b, c in tris:
        for e in ((a, b), (b, c), (c, a)):
            k = (min(e), max(e))
            count[k] = count.get(k, 0) + 1
    return sum(1 for v in count.values() if v != 2)


def bbox(verts):
    return [min(v[i] for v in verts) for i in range(3)], [max(v[i] for v in verts) for i in range(3)]


def on_edge(verts):
    """Pone la pieza de canto: su cara trasera (y máxima) pasa a apoyar en la cama."""
    ymax = max(v[1] for v in verts)
    return [(x, z, ymax - y) for x, y, z in verts]


def rot_z(verts, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(c * x - s * y, s * x + c * y, z) for x, y, z in verts]


def place(verts, cx, cy):
    """Centra en (cx, cy) y apoya en z = 0."""
    lo, hi = bbox(verts)
    dx, dy = cx - (lo[0] + hi[0]) / 2, cy - (lo[1] + hi[1]) / 2
    return [(x + dx, y + dy, z - lo[2]) for x, y, z in verts]


def write_3mf(path, objects, title):
    parts, items = [], []
    for oid, (name, verts, tris) in enumerate(objects, 1):
        v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in verts)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
        parts.append(f'<object id="{oid}" type="model" name="{name}"><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
        items.append(f'<item objectid="{oid}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="es" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">{title}</metadata><metadata name="Application">exportar_bambu.py (E.5)</metadata>'
             f'<resources>{"".join(parts)}</resources><build>{"".join(items)}</build></model>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)


def summary(objects):
    lo = [min(v[i] for _, vs, _ in objects for v in vs) for i in range(3)]
    hi = [max(v[i] for _, vs, _ in objects for v in vs) for i in range(3)]
    fits = lo[0] >= 0 and lo[1] >= 0 and hi[0] <= BED[0] and hi[1] <= BED[1] and hi[2] <= 256
    return {"piezas": [{"nombre": n, "triangulos": len(t), "aristas_abiertas": open_edges(t),
                        "tamano_mm": [round(b - a, 1) for a, b in zip(*bbox(v))]} for n, v, t in objects],
            "ocupa_mm": [round(hi[i] - lo[i], 1) for i in range(3)], "cabe_en_la_cama": fits}


def big(stl_name, name):
    """Cuerpo o tapa: acostado si cabe; si no, de canto y en diagonal."""
    verts, tris = read_stl(STL / stl_name)
    lo, hi = bbox(verts)
    flat = hi[0] - lo[0] + 2 * MARGIN <= BED[0] and hi[1] - lo[1] + 2 * MARGIN <= BED[1]
    if flat:
        if name.startswith("Tapa"):          # cara exterior contra la cama
            verts, tris = [(x, -y, -z) for x, y, z in verts], tris
    else:
        verts = rot_z(on_edge(verts), 45)
    return [(name + ("" if flat else "_de_canto_en_diagonal"), place(verts, BED[0] / 2, BED[1] / 2), tris)], flat


def half(stl_name, name):
    """Media pieza acostada; las de tapa, con la cara exterior en la cama."""
    verts, tris = read_stl(STL / stl_name)
    if name.startswith("Tapa"):
        verts = [(x, -y, -z) for x, y, z in verts]
    return [(name, place(verts, BED[0] / 2, BED[1] / 2), tris)], True


def flip(verts):
    """Boca abajo: la cara que toca la tapa pasa a apoyar en la cama."""
    return [(x, -y, -z) for x, y, z in verts]


def small_plate():
    """Piezas sueltas. Las cunas se imprimen boca abajo (orejas y paredes en la cama); el resto, como está modelado."""
    rows = [("difusor_opalino_graves", "Difusor_hexagonal_GRAVES", False), ("difusor_opalino_medios", "Difusor_hexagonal_MEDIOS", False),
            ("difusor_opalino_agudos", "Difusor_hexagonal_AGUDOS", False), ("cuna_tira_graves", "Cuna_tira_GRAVES", True),
            ("cuna_tira_medios", "Cuna_tira_MEDIOS", True), ("cuna_tira_agudos", "Cuna_tira_AGUDOS", True)]
    objects, y = [], 10.0
    for stl_name, name, upside in rows:
        verts, tris = read_stl(STL / f"{stl_name}.stl")
        verts = flip(verts) if upside else verts
        lo, hi = bbox(verts)
        objects.append((name, place(verts, BED[0] / 2, y + (hi[1] - lo[1]) / 2), tris))
        y += hi[1] - lo[1] + 5.0
    x, row = 10.0, 0.0
    for stl_name, name, upside in (("placa_trasera_desmontable_lilygo_t4s3", "Placa_trasera_desmontable_T4S3", False),
                                   ("cuna_sw1", "Cuna_SW1", True), ("cuna_conector_parlantes", "Cuna_conector_parlantes", True),
                                   ("sw1_capuchon_vista", "Capuchon_SW1_VISTA", False)):
        verts, tris = read_stl(STL / f"{stl_name}.stl")
        verts = flip(verts) if upside else verts
        lo, hi = bbox(verts)
        if x + hi[0] - lo[0] > BED[0] - 10.0:
            x, y, row = 10.0, y + row + 5.0, 0.0
        objects.append((name, place(verts, x + (hi[0] - lo[0]) / 2, y + (hi[1] - lo[1]) / 2), tris))
        x, row = x + hi[0] - lo[0] + 8.0, max(row, hi[1] - lo[1])
    return objects


def plates_config(config, groups, names):
    """Reparte los objetos en una cama por grupo dentro de Metadata/model_settings.config."""
    ids = {}
    for oid, body in re.findall(r'<object id="(\d+)">(.*?)</object>', config, re.S):
        ids[re.search(r'key="name" value="([^"]*)"', body).group(1)] = oid
    blocks = []
    for n, (group, label) in enumerate(zip(groups, names), 1):
        inst = "".join(f'    <model_instance>\n      <metadata key="object_id" value="{ids[name]}"/>\n      <metadata key="instance_id" value="0"/>\n'
                       f'      <metadata key="identify_id" value="{100 + int(ids[name])}"/>\n    </model_instance>\n' for name, _, _ in group)
        blocks.append(f'  <plate>\n    <metadata key="plater_id" value="{n}"/>\n    <metadata key="plater_name" value="{label}"/>\n'
                      f'    <metadata key="locked" value="false"/>\n    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
                      f'    <metadata key="gcode_file" value=""/>\n{inst}  </plate>\n')
    return re.sub(r'  <plate>.*?</plate>\n', lambda m: "".join(blocks), config, count=1, flags=re.S)


def plate_origin(i, count):
    """Origen de la cama i en Bambu Studio: rejilla con paso de 1,2 veces la cama."""
    cols = math.ceil(math.sqrt(count))
    return (i % cols) * BED[0] * 1.2, -(i // cols) * BED[1] * 1.2


MITADES = os.environ.get("MITADES") == "1"   # opción: cuerpo y tapa en dos mitades acostadas
GENERADO = "E5-completo-generado.3mf"      # nombre propio: E5-completo.3mf queda para lo que guarde el usuario
COLORES = os.environ.get("COLORES", "#A8452B,#E6E3DC").split(",")      # A: terracota, B: blanco mármol

PRESETS = (("machine", os.environ.get("IMPRESORA", "Bambu Lab P2S 0.2 nozzle")),
           ("process", os.environ.get("PROCESO", "0.10mm Standard @BBL P2S 0.2 nozzle")),
           ("filament", os.environ.get("FILAMENTO", "Bambu PLA Basic @BBL P2S 0.2 nozzle")))


def flat_preset(root, kind, name):
    """Ajuste de sistema de Bambu Studio con su herencia resuelta (la CLI no la resuelve)."""
    d = json.loads((root / kind / f"{name}.json").read_text(encoding="utf-8"))
    out = flat_preset(root, kind, d["inherits"]) if d.get("inherits") else {}
    for inc in d.get("include", []):
        out.update({k: v for k, v in flat_preset(root, kind, inc).items() if k not in ("name", "type", "from", "instantiation", "setting_id", "filament_id")})
    out.update(d)
    out.pop("include", None)
    return out


def preset_args(exe, tmp):
    root = Path(exe).resolve()
    if root.stat().st_size < 4096:           # lanzador: la instalación real está en la ruta que ejecuta
        root = Path(re.search(r'"(/[^"]+)/AppRun"', root.read_text()).group(1)) / "bin/x"
    root = root.parents[1] / "resources/profiles/BBL"
    paths = {}
    for kind, name in PRESETS:
        d = dict(flat_preset(root, kind, name), inherits="", name=name)
        d["from"] = "system"
        paths[kind] = Path(tmp) / f"{kind}.json"
        paths[kind].write_text(json.dumps(d), encoding="utf-8")
    return ["--load-settings", f"{paths['machine']};{paths['process']}", "--load-filaments", ";".join([str(paths["filament"])] * (2 if MITADES else 1))]


def fit_plate():
    """Probetas de ajuste: las de tapa con la cara exterior en la cama; las de pared, acostadas."""
    objects, x, y, row = [], MARGIN, MARGIN, 0.0
    for path in sorted((HERE / "pruebas-de-ajuste").glob("*.stl")):
        if path.stem.startswith("union_") and not MITADES:
            continue
        verts, tris = read_stl(path)
        if path.stem.startswith(("tapa_", "barra_cuna")):
            verts = flip(verts)
        elif path.stem.startswith("pared_der"):
            verts = [(-y_, z_, -x_) for x_, y_, z_ in verts]
        elif path.stem.startswith("pared_izq"):
            verts = [(y_, z_, x_) for x_, y_, z_ in verts]
        lo, hi = bbox(verts)
        dx, dy = hi[0] - lo[0], hi[1] - lo[1]
        if x + dx > BED[0] - MARGIN:
            x, y, row = MARGIN, y + row + 8.0, 0.0
        objects.append(("Prueba_" + path.stem, place(verts, x + dx / 2, y + dy / 2), tris))
        x, row = x + dx + 8.0, max(row, dy)
    return objects


def to_bambu(objects, dest, title, groups=None, names=None):
    """Escribe el 3MF. Si Bambu Studio está instalado, su CLI lo reescribe como proyecto nativo:
    la interfaz gráfica de Bambu Studio rechaza el 3MF genérico ("no contiene geometría")."""
    exe = shutil.which("bambu-studio")
    if not exe:
        write_3mf(dest, objects, title)
        return "3MF genérico (sin Bambu Studio instalado; si la interfaz no lo abre, importar stl/)"
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "generico.3mf"
        write_3mf(src, objects, title)
        extra = preset_args(exe, tmp) if groups else []
        run = subprocess.run([exe, "--arrange", "0", *extra, "--outputdir", tmp, "--export-3mf", "nativo.3mf", str(src)], capture_output=True, text=True)
        out = Path(tmp) / "nativo.3mf"
        result = json.loads((Path(tmp) / "result.json").read_text()) if (Path(tmp) / "result.json").exists() else {}
        assert out.exists() and result.get("return_code") == 0, run.stdout[-2000:] + run.stderr[-2000:]
        # Se quita la configuración de proyecto que escribe la CLI (impresora vacía, cama de 200 mm):
        # así Bambu Studio conserva la impresora, el filamento y el proceso que el usuario tenga elegidos.
        with zipfile.ZipFile(out) as zin, zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                if info.filename == "Metadata/project_settings.config" and not groups:
                    continue
                data = zin.read(info.filename)
                if groups and info.filename == "Metadata/model_settings.config":
                    text = plates_config(data.decode("utf-8"), groups, names)
                    # Las piezas del color B (mitades derechas y hembra de la probeta de unión) van con el filamento 2.
                    text = re.sub(r'(<metadata key="name" value="[^"]*(?:COLOR_B|milano_hembra)"/>\s*<metadata key="extruder" value=")1"', r'\g<1>2"', text)
                    # Las piezas de canto llevan soportes de árbol y borde de adherencia como ajuste del objeto:
                    # la interfaz descarta el ajuste global de un proyecto con perfil de sistema.
                    extra = ('<metadata key="enable_support" value="1"/>\n    <metadata key="support_type" value="tree(auto)"/>\n'
                             '    <metadata key="brim_type" value="outer_only"/>\n    <metadata key="brim_width" value="8"/>\n    ')
                    text = re.sub(r'(<metadata key="name" value="[^"]*_de_canto_en_diagonal"/>\s*)(<metadata key="extruder")', r'\g<1>' + extra + r'\g<2>', text, count=2)
                    data = text.encode("utf-8")
                if groups and info.filename == "Metadata/project_settings.config":
                    cfg = json.loads(data)
                    cfg["filament_colour"] = COLORES[:2 if MITADES else 1]
                    data = json.dumps(cfg, indent=4).encode("utf-8")
                if groups and info.filename == "Metadata/filament_sequence.json":
                    data = json.dumps({f"plate_{n}": {"sequence": []} for n in range(1, len(groups) + 1)}).encode()
                zout.writestr(info, data)
    if groups:
        return "proyecto de Bambu Studio con ajustes: " + ", ".join(n for _, n in PRESETS)
    return "proyecto de Bambu Studio, solo geometría (usa los ajustes que tenga abiertos el usuario)"


def main():
    OUT.mkdir(exist_ok=True)
    report = {"cama_mm": list(BED), "archivos": {}}
    plates = {"E5-pruebas-de-ajuste.3mf": (fit_plate(), True), "E5-piezas-pequenas.3mf": (small_plate(), True)}
    names = ["Pruebas de ajuste", "Piezas pequenas"]
    if not MITADES:                                     # de una pieza: acostados si caben; si no, de canto con soportes
        plates["E5-cuerpo.3mf"] = big("gabinete_e5_cuerpo.stl", "Gabinete_E5_cuerpo")
        plates["E5-tapa.3mf"] = big("tapa_e5_imantada.stl", "Tapa_E5_imantada")
        names += ["Cuerpo", "Tapa"]
    else:                                               # dos mitades con cola de milano, una por color
        for piece, stl_name, label in (("Cuerpo", "gabinete_e5_cuerpo", "Gabinete_E5_cuerpo"), ("Tapa", "tapa_e5_imantada", "Tapa_E5_imantada")):
            for side, tone in (("izquierda", "A"), ("derecha", "B")):
                plates[f"E5-{piece.lower()}-{side}.3mf"] = half(f"{stl_name}_mitad_{side}.stl", f"{label}_mitad_{side}_COLOR_{tone}")
                names.append(f"{piece} {side} (color {tone})")
    # Solo se reemplazan los archivos que genera este script. Cualquier otro .3mf de bambu/ (por ejemplo un
    # proyecto guardado desde Bambu Studio) no se toca.
    for old in OUT.glob("E5-*.3mf"):
        if old.name not in plates and old.name != GENERADO and re.fullmatch(r"E5-(cuerpo|tapa)(-izquierda|-derecha)?\.3mf", old.name):
            old.unlink()
    for fname, (objects, flat) in plates.items():
        report["archivos"][fname] = dict(summary(objects), acostado=flat, formato=to_bambu(objects, OUT / fname, fname[:-4]))
    if shutil.which("bambu-studio"):
        groups = [g for g, _ in plates.values()]
        moved = []
        for i, group in enumerate(groups):
            ox, oy = plate_origin(i, len(groups))
            moved += [(n, [(x + ox, y + oy, z) for x, y, z in v], t) for n, v, t in group]
        fmt = to_bambu(moved, OUT / GENERADO, GENERADO[:-4], groups, names)
        report["archivos"][GENERADO] = {"camas": names, "piezas": len(moved), "formato": fmt}
    (OUT / "contenido.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
