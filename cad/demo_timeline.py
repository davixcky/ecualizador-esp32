"""Un reloj común para audio, controles, pantalla, luces y rótulos."""
import math
FPS=24
DURATION=36
FRAMES=FPS*DURATION
# Centro → mínimo → máximo → centro; cada control usa siete segundos.
KEYS=[(0,.5),(.9,0),(2,0),(3.8,1),(5,1),(6.5,.5),(7,.5)]
def state(t):
    values=[.5,.5,.5]
    active=next((i for i,start in enumerate((3,10,17)) if start<=t<start+7),None)
    if active is not None:
        x=t-(3+active*7)
        for (ta,a),(tb,b) in zip(KEYS,KEYS[1:]):
            if ta<=x<=tb:
                u=(x-ta)/(tb-ta);u=u*u*(3-2*u)
                values[active]=a+(b-a)*u
                break
    return values,active
