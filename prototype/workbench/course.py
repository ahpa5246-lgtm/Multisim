"""Editable course-topology fixtures, not scans or NI native files.

Course page numbers below are PDF page numbers (printed page + 2).
Textbook ideal formulas and real model results are deliberately distinguished.
"""
from dataclasses import dataclass
from .core import Document,Part
from .spice import Analysis

@dataclass
class Experiment:
    id:str
    title:str
    chapter:str
    pages:str
    components:list
    analysis:Analysis
    checks:list
    note:str='Topology reproduction with explicit educational values; not an exact numerical homework reproduction.'

    def document(self):
        d=Document(self.title)
        # Labelled modular layout avoids hidden wire crossings in generated circuits.
        for j,(ref,kind,value,nodes) in enumerate(self.components):
            p=Part(ref,kind,160+(j%3)*380,140+(j//3)*240,value);d.parts.append(p)
            for xy,node in zip(p.pins(),nodes):
                dx,dy=xy[0]-p.x,xy[1]-p.y
                angle=(270 if dy<0 else 90) if abs(dy)>abs(dx) else (180 if dx<0 else 0)
                d.parts.append(Part(d.next_name('NET'),'NET',*xy,node,angle))
        ground=d.add('GND',80,60);d.parts.append(Part(d.next_name('NET'),'NET',*ground.pins()[0],'0'))
        return d

def R(ref,a,b,value):return (ref,'R',str(value),(a,b))
def V(ref,a,b,value):return (ref,'V',str(value),(a,b))
def C(ref,a,b,value):return (ref,'C',str(value),(a,b))
def Q(kind,model=''):
    return ('Q1',kind,model or ('Course_'+kind),('out','base','emitter'))
def F(kind,model=''):
    return ('J1' if kind in ('NJF','PJF') else 'M1',kind,model or 'Course_'+kind,('out','gate','source')+ (('source',) if kind in ('NMOS','PMOS') else ()))
def check(node,lo,hi,metric='last'):return dict(node=node,min=lo,max=hi,metric=metric)
OP=Analysis(kind='op');TRAN=Analysis(duration=.02,points=1600);AC=Analysis(kind='ac',start=1,stop=1e8,points=40,ac_source='VIN')
EXPERIMENTS=[]
def add(key,title,chapter,pages,parts,analysis=OP,checks=(),note=None):
    kwargs={} if note is None else {'note':note}
    e=Experiment(key,title,chapter,pages,parts,analysis,list(checks),**kwargs);EXPERIMENTS.append(e);return e

# 1–2: CE/CB/CC, characteristics and bias networks.
for polarity,sign in [('NPN',1),('PNP',-1)]:
    for state,vbase,limits in [('active',1.5,(2,11)),('cutoff',0,(11.8,12.1)),('saturation',5,(0,.3))]:
        add(f'{polarity.lower()}-{state}',f'{polarity}: {state}','1 BJT','6–15',[
            Q(polarity),V('VCC','supply','0',12*sign),V('VBB','drive','0',vbase*sign),R('RB','drive','base','10k'),R('RC','supply','out','1k'),R('RE','emitter','0','1m')],checks=[check('out',*(limits if sign==1 else (-limits[1],-limits[0])))])
add('bjt-characteristics','BJT collector characteristic','1 BJT','10, 13–15',[
    ('Q1','NPN','Course_NPN',('out','base','0')),V('VCC','out','0',5),V('VBE','base','0',.65)],Analysis(kind='dc',sweep_source='VCC',sweep_start=0,sweep_stop=10,sweep_step=.1),[check('I:VCC',-.00095,-.00085),check('I:VCC',.00075,.0009,'first')])
add('common-base','Common-base bias','1 BJT','16–19',[
    ('Q1','NPN','Course_NPN',('out','0','emitter')),V('VCC','supply','0',18),V('VEE','negative','0',-8),R('RC','supply','out','1.2k'),R('RE','emitter','negative','1.5k')],checks=[check('out',11,13.5)])
add('emitter-follower','Common-collector follower','1 BJT','9 (configuration overview)',[
    ('Q1','NPN','Course_NPN',('supply','base','out')),V('VCC','supply','0',12),V('VBB','base','0',5),R('RE','out','0','1k')],checks=[check('out',4.1,4.5)])
add('voltage-divider-bias','BJT voltage-divider bias','2 BJT bias','23–25',[
    Q('NPN'),V('VCC','supply','0',15),R('R1','supply','base','47k'),R('R2','base','0','10k'),R('RC','supply','out','2.2k'),R('RE','emitter','0','1k')],checks=[check('emitter',1.5,2),check('out',10,12)])
add('emitter-bias','BJT dual-supply emitter bias','2 BJT bias','26–28',[
    Q('NPN'),V('VCC','supply','0',15),V('VEE','negative','0',-15),R('RB','base','0','10k'),R('RE','emitter','negative','10k'),R('RC','supply','out','4.7k')],checks=[check('out',7,9.5)])
add('collector-feedback','BJT collector-feedback bias','2 BJT bias','28–30',[
    Q('NPN'),V('VCC','supply','0',12),R('RB','out','base','100k'),R('RC','supply','out','2.2k'),R('RE','emitter','0','1m')],checks=[check('out',3,5)])
# 3–5: polarity, transfer, bias and depletion/enhancement.
for kind,sign in [('NJF',1),('PJF',-1),('NMOS',1),('PMOS',-1)]:
    gate= -2 if 'JF' in kind else 4
    add(kind.lower()+'-transfer',kind+' transfer curve','3–5 FET','32–36, 45–50',[
        F(kind),V('VDS','out','0',10*sign),V('VGS','gate','0',gate*sign),R('RS','source','0','1m')],
        Analysis(kind='dc',sweep_source='VGS',sweep_start=(-4 if 'JF' in kind else 0) if sign==1 else (-6 if 'MOS' in kind else 0),sweep_stop=(0 if 'JF' in kind else 6) if sign==1 else (0 if 'MOS' in kind else 4),sweep_step=.1),
        [check('I:VDS',*( (-.01001,-.00999,'last') if sign==1 else (.00999,.01001,'first')))] if 'JF' in kind else [check('I:VDS',*( (-.0161,-.0159,'last') if sign==1 else (.0159,.0161,'first')))])
for kind,sign in [('NJF',1),('PJF',-1)]:
    add(kind.lower()+'-self-bias',kind+' self bias','4 JFET bias','37–39',[
        F(kind),V('VDD','supply','0',15*sign),R('RD','supply','out','1k'),R('RG','gate','0','1meg'),R('RS','source','0','1k')],checks=[check('source',*( (2,2.3) if sign==1 else (-2.3,-2)))])
add('jfet-divider','JFET voltage-divider bias','4 JFET bias','40–42',[
    F('NJF'),V('VDD','supply','0',20),R('RD','supply','out','1k'),R('R1','supply','gate','1meg'),R('R2','gate','0','100k'),R('RS','source','0','2.2k')],checks=[check('source',3,5)])
add('jfet-current-source','JFET with BJT current-source bias','4 JFET bias','42–43',[
    F('NJF'),('Q1','NPN','Course_NPN',('source','base','emitter')),V('VDD','supply','0',15),V('VEE','negative','0',-5),R('RD','supply','out','1k'),R('RB','base','0','10k'),R('RE','emitter','negative','2.2k'),R('RG','gate','0','1meg')],checks=[check('emitter',-.9,-.5),check('source',1,4)])
for kind,model,sign in [('NMOS','Course_NMOS',1),('PMOS','Course_PMOS',-1)]:
    add(kind.lower()+'-divider',kind+' voltage-divider bias','5 MOSFET','51–52',[
        F(kind,model),V('VDD','supply','0',15*sign),R('RD','supply','out','1k'),R('R1','supply','gate','100k'),R('R2','gate','0','33k'),R('RS','source','0','1m')],checks=[check('out',*( (10,14) if sign==1 else (-14,-10)))])
    add(kind.lower()+'-feedback',kind+' drain-feedback bias','5 MOSFET','51–52',[
        F(kind,model),V('VDD','supply','0',15*sign),R('RD','supply','out','1k'),R('RG','out','gate','1meg'),R('RS','source','0','1m')],checks=[check('out',*( (4,6) if sign==1 else (-6,-4)))])
for kind,model,sign in [('NMOS','Course_DNMOS',1),('PMOS','Course_DPMOS',-1)]:
    add('depletion-'+kind.lower(),kind+' depletion zero bias','5 MOSFET','47–50, 53–54',[
        F(kind,model),V('VDD','supply','0',20*sign),R('RD','supply','out','1k'),R('RG','gate','0','1meg'),R('RS','source','0','1m')],checks=[check('out',*( (9.9,10.1) if sign==1 else (-10.1,-9.9)))])
for gate in (0,10):
    add('igbt-'+str(gate),'IGBT equivalent, gate '+str(gate)+' V','5 IGBT','54–55',[
        ('U1','IGBT','Course_IGBT',('out','gate','0')),V('VCC','supply','0',20),V('VG','gate','0',gate),R('RL','supply','out','100')],checks=[check('out',*( (19.9,20.1) if gate==0 else (0,3)))])
# 6: full transistor circuit, not a renamed RC filter.
for kind in ('NPN','NJF'):
    parts=[V('VCC','supply','0',15),V('VIN','raw','0','SIN(0 .005 1000)'),R('RGEN','raw','input','1k'),C('CIN','input','drive','1u'),C('COUT','out','load','1u'),R('RL','load','0','10k')]
    if kind=='NPN':parts += [('Q1','NPN','Course_NPN',('out','drive','emitter')),R('R1','supply','drive','47k'),R('R2','drive','0','10k'),R('RC','supply','out','2.2k'),R('RE','emitter','0','1k'),C('CE','emitter','0','100u')]
    else:parts += [('J1','NJF','Course_NJF',('out','drive','source')),R('RG','drive','0','1meg'),R('RD','supply','out','2.2k'),R('RS','source','0','1k'),C('CS','source','0','100u')]
    add(kind.lower()+'-frequency',kind+' coupled amplifier frequency response','6 Frequency','56–75',parts,AC,[check('load',1,300,'ac_gain_peak')])
    add(kind.lower()+'-amplifier',kind+' coupled amplifier waveform','6 Frequency','56–75',parts,Analysis(duration=.2,points=20000),[check('load',.02,2,'pp')])
# 7: actual regenerative upstream thyristor models.
for kind,model,supply in [('SCR','2N1595',12),('TRIAC','L6008L6',24)]:
    for sign in ([1] if kind=='SCR' else [1,-1]):
        add(kind.lower()+('' if sign==1 else '-reverse'),kind+' gated conduction','7 Thyristors','76–85',[
            ('U1',kind,model,('out','gate','0')),V('VCC','supply','0',supply*sign),R('RL','supply','out','100'),V('VG','drive','0',f'PULSE(0 {5*sign} 2m 1u 1u 1m 30m)'),R('RG','drive','gate','100')],TRAN,[check('out',0 if sign==1 else -3,3 if sign==1 else 0)])
add('scr-half-wave','SCR half-wave power control','7 Thyristors','80–81',[
    ('U1','SCR','2N1595',('out','gate','0')),V('VIN','supply','0','SIN(0 24 50)'),R('RL','supply','out','100'),('RP1','POT','10k:0.1',('supply','0','wiper')),R('RG','wiper','gate','100')],Analysis(duration=.08,points=2400),[check('out',-25,3,'last')])
for sign in (1,-1):
    add('diac-'+str(sign),'DIAC breakover '+str(sign),'7 Thyristors','82–83',[
        ('U1','DIAC','DB3',('out','0')),V('VIN','supply','0',f'PULSE(0 {50*sign} 0 10m 1u 10m 30m)'),R('RL','supply','out','1k')],TRAN,[check('out',*( (1,20) if sign==1 else (-20,-1)))])
# 8–10: powered real op-amp model, not ideal arithmetic in place of simulation.
def opamp(inputs,feedback='10k',noninv=False,extra=()):
    parts=[('U1','OPAMP','LM358',('plus','minus','vcc','vee','out')),V('VP','vcc','0',15),V('VN','vee','0',-15),R('RL','out','0','10k')]
    for i,(value,resistance) in enumerate(inputs):
        node='plus' if noninv else 'in'+str(i);parts.append(V('VIN'+str(i),node,'0',value))
        if not noninv:parts.append(R('RI'+str(i),node,'minus',resistance))
    if noninv:parts.append(R('RG','minus','0','10k'))
    else:parts.append(R('RB','plus','0','1m'))
    if feedback:parts.append(R('RF','out','minus',feedback))
    return parts+list(extra)
add('noninverting','Noninverting op-amp','8 Op-amps','90–93',opamp([('0.2','10k')],noninv=True),checks=[check('out',.395,.405)])
add('inverting','Inverting op-amp','8 Op-amps','93–95',opamp([('0.2','10k')],feedback='100k'),checks=[check('out',-2.02,-1.98)])
for key,inputs,rf,target in [('summing',[('.2','10k'),('.3','10k')],'10k',-.5),('summing-gain',[('.2','10k'),('.3','10k')],'20k',-1),('averaging',[('.2','10k'),('.4','10k')],'5k',-.3),('scaling',[('.2','10k'),('.3','20k'),('.1','5k')],'10k',-.55)]:
    add(key,key.title()+' amplifier','9 Comparators / sums','101–105',opamp(inputs,rf),checks=[check('out',target-.015,target+.015)])
for ref in (0,1,-1):
    parts=[('U1','OPAMP','LM358',('input','ref','vcc','vee','out')),V('VP','vcc','0',15),V('VN','vee','0',-15),V('VIN','input','0','SIN(0 3 100)'),V('VREF','ref','0',ref),R('RL','out','0','10k')]
    add('comparator-'+str(ref),'Level detector '+str(ref)+' V','9 Comparators / sums','97–99',parts,Analysis(duration=.04,points=2400),[check('out',20,30,'pp')],note='LM358 used as course op-amp comparator; dedicated comparator timing is not implied.')
# Deterministic interference is a repeatable noise illustration, not stochastic noise analysis.
parts=[('U1','OPAMP','LM358',('input','0','vcc','vee','out')),V('VP','vcc','0',15),V('VN','vee','0',-15),V('VS','base','0','SIN(0 1 100)'),V('VNOISE','input','base','SIN(0 .15 5000)'),R('RL','out','0','10k')]
add('comparator-interference','Comparator with high-frequency interference','9 Comparators / sums','99–100',parts,Analysis(duration=.02,points=3000),[check('out',20,30,'pp')],note='Deterministic two-sine interference, not a noise-density or statistical simulation.')
for practical in (False,True):
    parts=opamp([('PULSE(-.25 .25 0 1u 1u 499u 1m)','10k')],feedback='1meg' if practical else None,extra=[C('CF','out','minus','100n')])
    add('integrator-'+str(practical).lower(),('Practical' if practical else 'Ideal-topology')+' integrator','10 Calculus','106–110',parts,Analysis(duration=.004,points=2000),[check('out',.07,1,'pp')],note='Real LM358 in the course topology. Startup, offset drift and saturation differ from an ideal op-amp formula.')
    parts=opamp([],feedback='10k',extra=[V('VIN','input','0','PULSE(-1 1 0 500u 500u 0 1m)'),C('CIN','input','series' if practical else 'minus','10n')])
    if practical:parts.extend([R('RS','series','minus','1k'),C('CF','out','minus','1n')])
    else:parts[0]=('U1','OPAMP','Course_IdealOpAmp',parts[0][3])
    add('differentiator-'+str(practical).lower(),('Practical' if practical else 'Ideal-topology')+' differentiator','10 Calculus','111–113',parts,Analysis(duration=.004,points=2000),[check('out',.6,1.2,'pp')])
# Additional standard student circuits from NI teaching outlines.
add('ohms-law','Ohm law / source current','Student essentials','NI teaching outline', [V('V1','input','0',5),R('R1','input','0','1k')],checks=[check('input',5,5)])
add('current-source','Independent current source','Student essentials','Circuit fundamentals',[('I1','I','1m',('0','out')),R('R1','out','0','1k')],checks=[check('out',.999,1.001)])
add('pot-divider','Adjustable potentiometer','Student essentials','Circuit fundamentals',[V('V1','input','0',10),('RP1','POT','10k:0.25',('input','0','out'))],checks=[check('out',7.49,7.51)])
for mode in ('half-wave','bridge','filtered-bridge','clipper','clamper','zener'):
    parts=[V('VIN','input','0','SIN(0 10 50)'),R('RL','out','0','1k')]
    if 'bridge' in mode:
        parts += [('D1','D','1N4148',('input','out')),('D2','D','1N4148',('0','out')),('D3','D','1N4148',('bottom','input')),('D4','D','1N4148',('bottom','0'))]
        parts[1]=R('RL','out','bottom','1k')
        parts.extend([R('RLEAK1','out','0','100meg'),R('RLEAK2','bottom','0','100meg')])
        if mode=='filtered-bridge':
            parts[0]=V('VIN','raw','0','SIN(0 10 50)');parts.extend([R('RS','raw','input','10'),C('CF','out','bottom','100u')])
    elif mode=='half-wave':parts.append(('D1','D','1N4148',('input','out')))
    elif mode=='clamper':parts += [C('C1','input','out','10u'),('D1','D','1N4148',('0','out'))]
    else:
        parts.append(R('RS','input','out','1k'));parts.append(('D1','D','Course_Zener5V1' if mode=='zener' else '1N4148',('0','out') if mode=='zener' else ('out','0')))
    add(mode,mode.title(),'Student essentials','NI diode/rectifier labs',parts,Analysis(duration=.12,points=2400,use_initial_conditions=False),[check('out/bottom' if 'bridge' in mode else 'out',.1,25,'pp')])
# Additional variants distinguish output families, commutation and equivalent RCs.
for current in (20,40,60):
    target=current*1e-6*100*1.1
    add('bjt-output-'+str(current),f'BJT output curve, IB={current} uA','1 BJT','10, 13–15, 20–22',[
        ('Q1','NPN','Course_NPN',('out','base','0')),('IB','I',str(current)+'u',('0','base')),V('VCC','out','0',5)],
        Analysis(kind='dc',sweep_source='VCC',sweep_start=0,sweep_stop=10,sweep_step=.1),[check('I:VCC',-target*1.05,-target*.95)])
for gate in (0,-1,-2):
    target=.000625*(gate+4)**2
    add('jfet-output-'+str(gate),f'JFET output curve, VGS={gate} V','3 FET','34–36, 39',[
        ('J1','NJF','Course_NJF',('out','gate','0')),V('VDS','out','0',10),V('VG','gate','0',gate)],
        Analysis(kind='dc',sweep_source='VDS',sweep_start=0,sweep_stop=10,sweep_step=.1),[check('I:VDS',-target*1.001,-target*.999)])
for name,r,c in [('input-coupling','10k','1u'),('output-coupling','12.2k','1u'),('bypass-equivalent','100','100u'),('miller-input','2k','100p'),('miller-output','2.2k','5p')]:
    high='miller' in name
    parts=[V('VIN','input','0','SIN(0 1 1000)')]
    parts += [R('R1','input','out',r),C('C1','out','0',c)] if high else [C('C1','input','out',c),R('R1','out','0',r)]
    add(name,name.replace('-',' ').title()+' RC equivalent','6 Frequency','62–75',parts,Analysis(kind='ac',start=1,stop=1e9,points=40,ac_source='VIN'),[check('out',.999,1.001,'ac_gain_peak')],note='Isolated textbook RC equivalent; full BJT/JFET amplifier fixtures are separate. Tests low/high-frequency attenuation as well as passband.')
add('scr-commutation','SCR current interruption and recovery','7 Thyristors','78–79',[
    ('U1','SCR','2N1595',('out','gate','0')),V('VS','supply','0','PULSE(12 0 8m 1u 1u 4m 30m)'),R('RL','supply','out','100'),V('VG','drive','0','PULSE(0 5 2m 1u 1u 1m 30m)'),R('RG','drive','gate','100')],TRAN,
    [dict(check('out',.3,2,'at'),time=.005),dict(check('out',11.8,12.1,'at'),time=.016)],note='Gate pulse latches SCR; supply interruption removes holding current; restored supply remains off without a new trigger.')
add('voltage-follower','Op-amp voltage follower','8 Op-amps','88–91',[
    ('U1','OPAMP','LM358',('input','out','vcc','vee','out')),V('VP','vcc','0',15),V('VN','vee','0',-15),V('VIN','input','0',.5),R('RL','out','0','10k')],checks=[check('out',.499,.501)])
for ref in ('divider','zener'):
    parts=[('U1','OPAMP','LM358',('input','ref','vcc','vee','out')),V('VP','vcc','0',15),V('VN','vee','0',-15),V('VIN','input','0','SIN(0 8 100)'),R('R1','vcc','ref','10k'),R('RL','out','0','10k')]
    parts.append(R('R2','ref','0','10k') if ref=='divider' else ('DZ','D','Course_Zener5V1',('0','ref')))
    add('comparator-'+ref,'Comparator '+ref+' reference','9 Comparators / sums','98',parts,Analysis(duration=.04,points=2400),[check('out',20,30,'pp')])
# Tight analytic checks independent of the simulator's output.
for e in EXPERIMENTS:
    if e.id.startswith('differentiator-'):
        e.checks.extend([dict(check('out',-.43,-.37,'at'),time=.00225),dict(check('out',.37,.43,'at'),time=.00275)])
    if e.id.startswith('integrator-'):
        e.checks.append(dict(check('out',-265,-235,'slope'),start=.0021,stop=.0023))
    if e.id.startswith('comparator-') and e.id not in ('comparator-interference','comparator-divider','comparator-zener'):
        e.checks.extend([dict(check('out',12,15,'at'),time=.0125),dict(check('out',-15,-12,'at'),time=.0175)])
    if e.id in ('scr','triac'):
        supply=12 if e.id=='scr' else 24
        e.checks.extend([dict(check('out',supply-.1,supply+.1,'at'),time=.001),dict(check('out',.2,2,'at'),time=.005)])
    if e.id.endswith('-frequency'):
        e.checks.extend([dict(check('load',1,300,'at_abs'),time=1000),dict(check('load',0,.8,'relative_to_peak'),time=1),dict(check('load',0,.8,'relative_to_peak'),time=1e8)])
    if e.id in ('input-coupling','output-coupling','bypass-equivalent'):
        e.checks.append(dict(check('out',0,.1,'at_abs'),time=1))
    if e.id in ('miller-input','miller-output'):
        e.checks.append(dict(check('out',0,.1,'at_abs'),time=1e9))

# Direct numerical examples: values transcribed from the supplied PDF diagrams.
add('pdf-p25-bias','PDF p25: 10 V divider-bias example','2 BJT bias','25',[
    Q('NPN'),V('VCC','supply','0',10),R('R1','supply','base','10k'),R('R2','base','0','5.6k'),R('RC','supply','out','1k'),R('RE','emitter','0','560')],
    checks=[check('out/emitter',1.8,2.7),check('emitter',2.5,3)],note='Exact resistor/supply values from Example 5–2. Textbook neglects base loading and fixes VBE=0.7 V (VCE≈1.95 V); the finite-beta SPICE model need not match that approximation exactly.')
add('pdf-p110-integrator','PDF p110: practical integrator example','10 Calculus','110',
    opamp([('PULSE(-2.5 2.5 0 1n 1n 499.999u 1m)','10k')],feedback='200k',extra=[C('CF','out','minus','47n')]),
    Analysis(duration=.12,points=20000),[dict(check('out',-5500,-5100,'slope'),start=.0381,stop=.0383),check('out',2.5,2.8,'pp')],
    note='Exact 10k/200k/0.047uF, 1 kHz and ±2.5 V from Example 13–10. Ideal slope −5319.15 V/s; real LM358 and finite feedback resistance included.')
parts=opamp([],feedback='2.2k',extra=[V('VIN','input','0','PULSE(-5 5 0 5u 5u 0 10u)'),C('CIN','input','series','1n'),R('RS','series','minus','150')])
parts[0]=('U1','OPAMP','Course_IdealOpAmp',parts[0][3])
add('pdf-p113-differentiator','PDF p113: differentiator example','10 Calculus','113',parts,
    Analysis(duration=.0001,points=4000),[dict(check('out',-4.45,-4.35,'at'),time=.0000725),dict(check('out',4.35,4.45,'at'),time=.0000775)],
    note='Exact 2.2k/150ohm/0.001uF and ±5 V triangle at 100 kHz from Example 13–11. Uses explicitly idealized op-amp for the textbook ±4.4 V prediction; does not validate a real op-amp at this speed.')

add('igbt-current-gain','IGBT equivalent current gain','5 IGBT','54–55',[
    ('U1','IGBT','Course_IGBT',('out','gate','0')),V('VCC','supply','0',20),V('VG','gate','0',5),R('RL','supply','out','5')],
    checks=[check('I:VCC',-2.2,-2.0),check('out',9,10.1)],note='Textbook MOSFET + PNP equivalent: channel current drives PNP base and receives bipolar current gain. No device rating, tail-current or thermal claim.')
add('series-current-probe','Ammeter / series current probe','Student essentials','Circuit measurement',[
    V('V1','input','0',5),R('R1','input','sense','1k'),('PR1','IPROBE','Current probe',('sense','0'))],checks=[check('I:PR1',.004999,.005001)],note='An ideal zero-volt source measures series branch current. Insert in series, never across a powered source.')
add('negative-clipper','Negative diode clipper','Student essentials','NI diode labs',[
    V('VIN','input','0','SIN(0 5 50)'),R('RS','input','out','1k'),R('RL','out','0','100k'),('D1','D','1N4148',('0','out'))],Analysis(duration=.08,points=2400),[check('out',-.9,-.4,'min'),check('out',4.9,5,'max')])
add('negative-clamper','Negative diode clamper','Student essentials','NI diode labs',[
    V('VIN','input','0','SIN(0 5 50)'),C('C1','input','out','10u'),R('RL','out','0','1meg'),('D1','D','1N4148',('out','0'))],Analysis(duration=.12,points=2400),[check('out',9.8,10.2,'pp')])
add('rc-charge','RC step / time constant','Student essentials','Circuit fundamentals',[
    V('V1','input','0',5),R('R1','input','out','1k'),C('C1','out','0','1u')],Analysis(duration=.01,points=1000),[dict(check('out',3.14,3.18,'at'),time=.001)])
add('rl-step','RL step / current growth','Student essentials','Circuit fundamentals',[
    V('V1','input','0',5),R('R1','input','out','100'),('L1','L','10m',('out','sense')),('PR1','IPROBE','Current probe',('sense','0'))],Analysis(duration=.001,points=1000),[dict(check('I:PR1',.0314,.0318,'at'),time=.0001)])
add('rlc-resonance','Series RLC resonance','Student essentials','Circuit fundamentals',[
    V('VIN','input','0',1),R('R1','input','series','100'),('L1','L','10m',('series','out')),C('C1','out','0','1u')],Analysis(kind='ac',ac_source='VIN',start=10,stop=1e5,points=80),[dict(check('out',.99,1.01,'at_abs'),time=1591.54943)])
add('led-resistor','LED series resistor and current','Student essentials','NI LED labs',[
    V('V1','input','0',5),R('R1','input','out','1k'),('D1','LED','Red',('out','0'))],checks=[check('I:V1',-.004,-.002)],note='Original generic red-LED electrical model. No physical brightness, spectrum or rated-current claim.')
BY_ID={e.id:e for e in EXPERIMENTS}

def node_vector(doc,result,name):
    p=next(p for p in doc.parts if p.kind=='NET' and p.value==name)
    return result.voltages[result.nets[(p.id,0)]]

def evaluate(experiment,doc,result):
    findings=[]
    for c in experiment.checks:
        node=c['node']
        if node.startswith('I:'):values=result.currents[node[2:]]
        elif '/' in node:
            a,b=node.split('/');values=[x-y for x,y in zip(node_vector(doc,result,a),node_vector(doc,result,b))]
        else:values=node_vector(doc,result,node)
        metric=c['metric']
        def at(t):
            if not result.axis[0]<=t<=result.axis[-1]:raise ValueError('Measurement time/frequency is outside the captured axis')
            from bisect import bisect_left
            j=bisect_left(result.axis,t)
            if j==0:return values[0]
            if j==len(values):return values[-1]
            a,b=result.axis[j-1:j+1];return values[j-1]+(values[j]-values[j-1])*(t-a)/(b-a)
        if metric=='at':actual=at(c['time'])
        elif metric=='at_abs':actual=abs(at(c['time']))
        elif metric=='relative_to_peak':actual=abs(at(c['time']))/max(map(abs,values))
        elif metric=='slope':actual=(at(c['stop'])-at(c['start']))/(c['stop']-c['start'])
        elif metric=='last':actual=values[-1]
        elif metric=='first':actual=values[0]
        elif metric=='abs_last':actual=abs(values[-1])
        elif metric=='max':actual=max(values)
        elif metric=='min':actual=min(values)
        elif metric=='pp':
            values=[v for t,v in zip(result.axis,values) if t>=(result.axis[0]+result.axis[-1])/2];actual=max(values)-min(values)
        elif metric=='ac_gain_peak':actual=max(map(abs,values))
        else:raise ValueError('Unknown check metric')
        passed=c['min']-1e-9<=actual<=c['max']+1e-9
        findings.append(dict(c,actual=actual,passed=passed))
    return findings
