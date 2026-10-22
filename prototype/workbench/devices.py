"""Pinned Qucs-S model catalog. See data/THIRD_PARTY.md for source and license."""
import json,gzip
from pathlib import Path
MODELS=json.loads(gzip.decompress((Path(__file__).parent/'data/qucs-devices.json.gz').read_bytes()))['models']

def device_model(kind,name):
    model=MODELS.get(name)
    if model is None or model['kind']!=kind:raise ValueError(f'Unknown {kind} library model: {name}')
    return model

# Original textbook fixtures. These are not manufacturer models.
for name,kind,params in [
    ('Course_NPN','NPN',{'IS':1e-14,'BF':100,'VAF':100,'CJE':20e-12,'CJC':5e-12,'TF':.3e-9}),
    ('Course_PNP','PNP',{'IS':1e-14,'BF':100,'VAF':100,'CJE':20e-12,'CJC':5e-12,'TF':.3e-9}),
    ('Course_NJF','NJF',{'VTO':-4,'BETA':.000625,'LAMBDA':0,'CGS':5e-12,'CGD':2e-12}),
    ('Course_PJF','PJF',{'VTO':-4,'BETA':.000625,'LAMBDA':0,'CGS':5e-12,'CGD':2e-12}),
    ('Course_NMOS','NMOS',{'LEVEL':1,'VTO':2,'KP':.002,'LAMBDA':0}),
    ('Course_PMOS','PMOS',{'LEVEL':1,'VTO':-2,'KP':.002,'LAMBDA':0}),
    ('Course_DNMOS','NMOS',{'LEVEL':1,'VTO':-4,'KP':.00125,'LAMBDA':0}),
    ('Course_DPMOS','PMOS',{'LEVEL':1,'VTO':4,'KP':.00125,'LAMBDA':0}),
    ('Course_Zener5V1','D',{'IS':1e-14,'N':1,'BV':5.1,'IBV':.001,'RS':2}),
]:
    MODELS[name]={'kind':kind,'parameters':params,'source':'Original educational model',
                  'description':'Textbook demonstration model; not manufacturer-characterized or rated for hardware design.'}
    if kind in ('NMOS','PMOS'):MODELS[name]['instance']={'L':1e-6,'W':1e-6}
MODELS['Course_IGBT']={'kind':'IGBT','subckt':'OCW_IGBT','source':'Original educational equivalent',
    'description':'MOSFET + PNP equivalent from the course topology. DC switching demonstration only; no tail-current, thermal or breakdown validation.',
    'spice':'.subckt OCW_IGBT gnd c g e\nQ1 e n c QIG\nM1 n g e e MIG L=1u W=1u\n.model QIG PNP(IS=1e-14 BF=20)\n.model MIG NMOS(LEVEL=1 VTO=3 KP=.05)\n.ends OCW_IGBT'}

MODELS['Course_IdealOpAmp']={'kind':'OPAMP','subckt':'OCW_IDEAL_OP','source':'Original idealized teaching model',
    'description':'Algebraic 1e6 V/V gain with supply clipping; no bandwidth, slew, noise, input offset or current limit. Use to compare ideal textbook calculus only.',
    'spice':'.subckt OCW_IDEAL_OP gnd plus minus vp vn out\nRIN plus minus 1e12\nBGAIN out gnd V=min(max(1e6*(v(plus)-v(minus)),v(vn)),v(vp))\n.ends OCW_IDEAL_OP'}
