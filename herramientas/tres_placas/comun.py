"""Shared: build a group's board with the U2D<->U4 section swap applied."""
import os,sys
HERR=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
sys.path.insert(0,HERR)
import pcbnew as k
import verificar_netlist
import pcb_freerouting as pf
_orig=verificar_netlist.netlist_kicad
def netlist_intercambio():
    pn,st=_orig();pn=dict(pn)
    # U2D (antialias) -> U4D ; U4C (inversor M_INV) -> U2D ; U4C queda como seguidor de VREF sin uso
    u2d={p:pn[('U2',p)] for p in ('12','13','14')}
    u4c={p:pn[('U4',p)] for p in ('8','9','10')}
    pn[('U4','12')],pn[('U4','13')],pn[('U4','14')]=u2d['12'],u2d['13'],u2d['14']
    pn[('U2','12')],pn[('U2','13')],pn[('U2','14')]=u4c['10'],u4c['9'],u4c['8']
    pn[('U4','10')]='/VREF';pn[('U4','9')]='Net-(U4C-out)';pn[('U4','8')]='Net-(U4C-out)'
    return pn,st
pf.netlist_kicad=netlist_intercambio
GRUPOS={g:None for g in 'ABC'}
def construir(g):
    os.environ['GRUPO']=g
    b=pf.construir()
    for f in list(b.GetFootprints()):
        if f.GetReference().startswith('H') and 'Mounting' in f.GetFPID().GetLibItemName().wx_str():b.Remove(f)
    for d in list(b.GetDrawings()):
        if d.GetLayer()==k.Edge_Cuts:b.Remove(d)
    return b
