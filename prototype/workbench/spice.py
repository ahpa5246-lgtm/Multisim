"""Restricted schematic-to-ngspice adapter. Requires a separately installed ngspice.

No third-party engine code is vendored. Catalog model cards derive from the
pinned Qucs-S source with notices; Course_* and generic primitives are explicitly
labelled educational approximations, not manufacturer-characterized devices.
"""
from dataclasses import dataclass,field
import csv
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
from .core import numeric
from .devices import device_model, MODELS


def number(value):
    out=numeric(value)
    if not math.isfinite(out):raise ValueError('Values must be finite')
    return out


def source_value(value):
    value=str(value).strip()
    if '\n' in value or '\r' in value:raise ValueError('Source cannot contain directives')
    match=re.fullmatch(r'(SIN|PULSE)\(([^()]*)\)',value,re.I)
    if not match:return f'DC {number(value):.12g} AC 1'
    kind=match[1].upper();vals=[number(x) for x in match[2].replace(',',' ').split()]
    if kind=='SIN':
        if len(vals)!=3 or vals[2]<=0:raise ValueError('Use SIN(offset amplitude positive_frequency)')
    elif len(vals)!=7 or min(vals[2:6])<0 or vals[6]<=0 or sum(vals[3:6])>vals[6]*(1+1e-10):
        raise ValueError('Use PULSE(low high delay rise fall width period); timing must fit the positive period')
    if kind=='PULSE' and vals[5]==0:
        # ngspice treats literal zero pulse width as its default, not a triangle.
        vals[5]=vals[6]*1e-6
        vals[4]=max(0,vals[4]-vals[5])
    return f"{kind}({' '.join(f'{x:.12g}' for x in vals)}) AC 1"

@dataclass(frozen=True)
class Analysis:
    kind:str='tran'
    duration:float=.012
    points:int=1000
    start:float=10
    stop:float=1e6
    ac_source:str=''
    use_initial_conditions:bool=True
    sweep_source:str=''
    sweep_start:float=0
    sweep_stop:float=5
    sweep_step:float=.1
    def validate(self):
        if self.kind not in ('tran','op','ac','dc'):raise ValueError('Unsupported analysis')
        if not isinstance(self.points,int) or not 2<=self.points<=20000:raise ValueError('Points must be 2–20000')
        if not all(math.isfinite(x) for x in (self.duration,self.start,self.stop)):raise ValueError('Analysis values must be finite')
        if self.kind=='dc':
            if not all(math.isfinite(x) for x in (self.sweep_start,self.sweep_stop,self.sweep_step)) or self.sweep_stop<=self.sweep_start or self.sweep_step<=0 or (self.sweep_stop-self.sweep_start)/self.sweep_step>20000:raise ValueError('DC sweep needs increasing finite bounds, positive step, at most 20001 points')
        if not 0<self.duration<=100 or not 0<self.start<self.stop:raise ValueError('Invalid time/frequency range')

@dataclass
class Result:
    analysis:Analysis
    axis:list
    voltages:dict
    currents:dict
    nets:dict
    deck:str
    log:str
    table:str
    labels:dict=field(default_factory=dict)
    def export(self,path):
        path=Path(path);path.mkdir(parents=True,exist_ok=True)
        (path/'circuit.cir').write_text(self.deck,encoding='utf-8')
        (path/'solver.log').write_text(self.log,encoding='utf-8')
        (path/'raw-table.dat').write_text(self.table,encoding='utf-8')
        with (path/'samples.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f);vectors={f'V({k})':v for k,v in self.voltages.items()}|{f'I({k})':v for k,v in self.currents.items()}
            writer.writerow(['frequency_Hz' if self.analysis.kind=='ac' else 'time_s' if self.analysis.kind=='tran' else 'source_voltage_V' if self.analysis.kind=='dc' else 'operating_point',*vectors])
            writer.writerows(zip(self.axis,*vectors.values()))


def compile_deck(doc,analysis):
    analysis.validate()
    if not any(p.kind=='GND' for p in doc.parts):raise ValueError('A ground reference is required')
    if len(doc.parts)>1000:raise ValueError('Circuit exceeds 1000 components')
    nets=doc.networks();nodes=sorted(set(nets.values())-{'0'},key=int)
    if not nodes:raise ValueError('Circuit has no non-ground nodes')
    lines=['Open Circuit Workbench - ngspice', '.options reltol=1e-5 abstol=1e-12 vntol=1e-6']
    sources=[];model_cards=[]
    voltage_refs=[p.id for p in doc.parts if p.kind=='V']
    excitation=analysis.ac_source or (voltage_refs[0] if voltage_refs else '')
    if analysis.kind=='ac' and excitation not in voltage_refs:raise ValueError('Select an existing voltage source for AC excitation')
    if len({p.id.lower() for p in doc.parts})!=len(doc.parts):raise ValueError('Component references must be unique ignoring case')
    for p in doc.parts:
        if p.kind in ('GND','NET'):continue
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',p.id):raise ValueError('Invalid component reference')
        if p.kind in ('NPN','PNP','NJF','PJF','NMOS','PMOS','OPAMP','SCR','TRIAC','DIAC','IGBT') or (p.kind=='D' and p.value in MODELS):
            model=device_model(p.kind,p.value);pins=[nets[(p.id,i)] for i in range(len(p.pins()))]
            if 'subckt' in model:
                if p.kind=='OPAMP' and pins[2]==pins[3]:raise ValueError('Op-amp supply pins must differ')
                lines.append(f'X{p.id} 0 '+ ' '.join(pins)+' '+model['subckt'])
                if model['spice'] not in model_cards:model_cards.append(model['spice'])
            else:
                prefix={'NPN':'Q','PNP':'Q','NJF':'J','PJF':'J','NMOS':'M','PMOS':'M','D':'D'}[p.kind]
                name=prefix+'MOD_'+p.id
                instance=' '.join(f'{k}={v:.15g}' for k,v in model.get('instance',{}).items())
                lines.append(f'{prefix}{p.id} '+ ' '.join(pins)+' '+name+' '+instance)
                params=' '.join(f'{k}={v:.15g}' for k,v in model['parameters'].items())
                model_cards.append(f'.model {name} {p.kind} ({params})')
            continue
        a,b=(nets[(p.id,i)] for i in (0,1))
        if a==b:raise ValueError(f'{p.id} has shorted pins')
        if p.kind in ('R','C','L'):
            v=number(p.value)
            if v<=0:raise ValueError(f'{p.id} requires a positive value')
            lines.append(f'{p.kind}{p.id} {a} {b} {v:.12g}')
        elif p.kind=='POT':
            try:resistance,position=map(number,p.value.split(':'))
            except ValueError as e:raise ValueError('Potentiometer: total_ohms:position (0 to 1)') from e
            if resistance<=0 or not 0<=position<=1:raise ValueError('Invalid potentiometer resistance/position')
            w=nets[(p.id,2)]
            lines.extend([f'R{p.id}A {a} {w} {max(.001,resistance*position):.12g}',f'R{p.id}B {w} {b} {max(.001,resistance*(1-position)):.12g}'])
        elif p.kind=='I':
            lines.append(f'I{p.id} {a} {b} '+source_value(p.value).replace('AC 1','AC 0'))
        elif p.kind=='IPROBE':
            lines.append(f'V{p.id} {a} {b} DC 0 AC 0');sources.append(p.id)
        elif p.kind=='V':
            value=source_value(p.value).replace('AC 1','AC 1' if p.id==excitation else 'AC 0')
            lines.append(f'V{p.id} {a} {b} {value}');sources.append(p.id)
        elif p.kind in ('D','LED'):
            if p.kind=='D' and p.value!='Generic':raise ValueError(f'Unknown diode model: {p.value}; select a library model or Generic')
            if p.kind=='LED' and p.value not in ('Red','Generic'):raise ValueError('LED supports Red / Generic educational model only')
            lines.append(f'D{p.id} {a} {b} OCW_{p.kind}')
        elif p.kind=='SW':
            if p.value.lower() not in ('open','closed'):raise ValueError('Switch value must be Open or Closed')
            lines.append(f'R{p.id} {a} {b} '+('1e12' if p.value.lower()=='open' else '0.001'))
        else:raise ValueError(f'Unsupported component: {p.kind}')
    lines+=model_cards
    lines+=['.model OCW_D D(Is=1e-14 N=1)', '.model OCW_LED D(Is=1e-20 N=2)', '.control','set noaskquit','set wr_singlescale','set wr_vecnames','set numdgt=15']
    if analysis.kind=='tran':lines.append(f'tran {analysis.duration/analysis.points:.12g} {analysis.duration:.12g}'+(' uic' if analysis.use_initial_conditions else ''))
    elif analysis.kind=='ac':lines.append(f'ac dec {analysis.points} {analysis.start:.12g} {analysis.stop:.12g}')
    elif analysis.kind=='dc':
        if not voltage_refs:raise ValueError('DC sweep requires a voltage source')
        source=analysis.sweep_source or voltage_refs[0]
        if source not in voltage_refs:raise ValueError('Select an existing voltage source for DC sweep')
        lines.append(f'dc V{source} {analysis.sweep_start:.12g} {analysis.sweep_stop:.12g} {analysis.sweep_step:.12g}')
    else:lines.append('op')
    vectors=[f'v({n})' for n in nodes]+[f'i(v{s})' for s in sources]
    lines+=['wrdata result.dat '+' '.join(vectors),'quit','.endc','.end']
    return '\n'.join(lines)+'\n',nets,nodes,sources


def parse_table(table,count,complex_values=False):
    rows=[]
    for line in table.splitlines()[1:]:
        if not line.strip():continue
        try:values=[float(v) for v in line.split()]
        except ValueError as e:raise ValueError('Invalid ngspice sample') from e
        if len(values)!=1+count*(2 if complex_values else 1) or not all(math.isfinite(x) for x in values):raise ValueError('Invalid ngspice sample dimensions/values')
        rows.append(values)
    if not rows:raise ValueError('ngspice returned no samples')
    axis=[row[0] for row in rows]
    if len(axis)>1 and any(b<=a for a,b in zip(axis,axis[1:])):raise ValueError('Nonmonotonic ngspice samples')
    vectors=[]
    for j in range(count):
        vectors.append([complex(row[1+2*j],row[2+2*j]) if complex_values else row[j+1] for row in rows])
    return axis,vectors

class Engine:
    def __init__(self,executable=None):
        self.executable=executable or os.environ.get('OCW_NGSPICE') or shutil.which('ngspice')
        self._lock=threading.Lock();self._process=None;self._cancelled=threading.Event()
    def cancel(self):
        self._cancelled.set()
        with self._lock:
            if self._process and self._process.poll() is None:self._process.terminate()
    def run(self,doc,analysis):
        if not self.executable or not Path(self.executable).is_file():raise ValueError('ngspice is required. Install it and add it to PATH, or set OCW_NGSPICE to the executable.')
        deck,nets,nodes,sources=compile_deck(doc,analysis)
        with tempfile.TemporaryDirectory(prefix='ocw spice ') as tmp:
            path=Path(tmp);(path/'circuit.cir').write_text(deck,encoding='utf-8')
            # Do not read arbitrary .spiceinit files from the project or user home.
            with self._lock:
                if self._cancelled.is_set():raise ValueError('Simulation cancelled')
                self._process=subprocess.Popen([str(self.executable),'-n','-b','circuit.cir'],cwd=tmp,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                proc=self._process
            try:log=proc.communicate(timeout=30)[0]
            except subprocess.TimeoutExpired:
                proc.kill();proc.communicate();raise ValueError('ngspice exceeded the 30 second limit')
            finally:
                with self._lock:self._process=None
            if self._cancelled.is_set():raise ValueError('Simulation cancelled')
            data=path/'result.dat'
            if proc.returncode or not data.is_file():raise ValueError('ngspice failed:\n'+log[-6000:])
            table=data.read_text();axis,vectors=parse_table(table,len(nodes)+len(sources),analysis.kind=='ac')
            if analysis.kind=='tran' and (len(axis)<2 or axis[-1]<analysis.duration*.999):raise ValueError('Incomplete transient data')
            if analysis.kind=='op':axis=[0.0]
            volts=dict(zip(nodes,vectors[:len(nodes)]));volts['0']=[0.0]*len(axis)
            return Result(analysis,axis,volts,dict(zip(sources,vectors[len(nodes):])),nets,deck,log,table,{p.value:nets[(p.id,0)] for p in doc.parts if p.kind=='NET'})
