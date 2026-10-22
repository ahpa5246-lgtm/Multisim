"""Extend the pinned GPL Qucs-S catalog for Electronics II student circuits.

JFET property order/exclusions: jfet.cpp, Michael Margraf (C) 2003.
MOS order/exclusions: mosfet_sub.cpp, Michael Margraf (C) 2003–2004.
Thyristor subcircuits and embedded notices retained verbatim.
Run import_qucs_devices.py first to reproduce the complete catalog.
"""
import gzip,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'prototype'))
from workbench.core import numeric

def build():
    path=ROOT/'prototype/workbench/data/qucs-devices.json.gz'
    data=json.loads(gzip.decompress(path.read_bytes()));models=data['models'];base=ROOT/'upstream/qucs-s'
    sets=[('JFETs.lib','jfet.cpp','JFET',{'Type','Area','Temp','Ffe','N','Isr','Nr','M','Xti','Betatce','UseGlobTemp','LibName','CompName'}, {'201','2N4341','2N5457','2N5458','BF245A','BF245B','J175','J176'}),
          ('MOSFETs.lib','mosfet_sub.cpp','_MOSFET',{'Type','Temp','L','W','Ad','As','Pd','Ps','Rg','N','Tt','Nrd','Nrs','Ffe','UseGlobTemp','LibName','CompName'}, {'BSS123','BSS84','2N7000','BS170'})]
    missing=[]
    for filename,cpp,tag,exclude,wanted in sets:
        seen=set()
        props=re.findall(r'new Property\("([^"]+)"',(base/'qucs/components'/cpp).read_text().split('::newOne')[0])
        for name,block in re.findall(r'<Component ([^>]+)>(.*?)</Component>',(base/'library'/filename).read_text(),re.S):
            if name not in wanted:continue
            seen.add(name)
            match=re.search(r'<'+tag+r'\b[^>]*>',block,re.S)
            if not match:raise ValueError(f'No {tag} model: {name}')
            vals=re.findall(r'"([^"]*)"',match[0]);values=dict(zip(props,vals));pol=values['Type'][0].upper()
            params={('Tcv' if k=='Vt0tc' else k):numeric(v) for k,v in values.items() if k not in exclude}
            if tag=='_MOSFET':
                for k in ('Nsub','Nss'):
                    if params.get(k)==0:params.pop(k)
            models[name]={'kind':pol+('JF' if tag=='JFET' else 'MOS'),'parameters':params,'description':re.search(r'<Description>(.*?)</Description>',block,re.S)[1].strip(),'source':'Qucs-S library/'+filename}
            if tag=='_MOSFET':models[name]['instance']={k:numeric(values[k]) for k in ('L','W','Ad','As','Pd','Ps')}
        missing.extend(sorted(wanted-seen))
    data['course_unavailable_models']=missing
    props=re.findall(r'new Property\("([^" ]+)"',(base/'qucs/components/diode.cpp').read_text().split('::newOne')[0])
    for name,block in re.findall(r'<Component ([^>]+)>(.*?)</Component>',(base/'library/Diodes.lib').read_text(),re.S):
        if name not in ('1N4148','1N4007'):continue
        vals=re.findall(r'"([^"]*)"',re.search(r'<Diode\b[^>]*>',block,re.S)[0])
        excluded={'Cp','Isr','Nr','Ffe','Temp','Area','Symbol','UseGlobTemp','LibName','CompName'}
        params={('CJO' if k=='Cj0' else 'VJ' if k=='Vj' else 'Tcv' if k=='Tbv' else k):numeric(v) for k,v in zip(props,vals) if k not in excluded}
        models[name]={'kind':'D','parameters':params,'description':re.search(r'<Description>(.*?)</Description>',block,re.S)[1].strip(),'source':'Qucs-S library/Diodes.lib'}
    for name,block in re.findall(r'<Component ([^>]+)>(.*?)</Component>',(base/'library/Thyristor.lib').read_text(),re.S):
        if name not in ('2N1595','DB3','L6008L6'):continue
        kind={'2N1595':'SCR','DB3':'DIAC','L6008L6':'TRIAC'}[name]
        spice=re.search(r'<Spice>(.*?)</Spice>',block,re.S)[1].strip()
        models[name]={'kind':kind,'spice':spice,'subckt':'Thyristor_'+name,'description':re.search(r'<Description>(.*?)</Description>',block,re.S)[1].strip(),'source':'Qucs-S library/Thyristor.lib'}
    path.write_bytes(gzip.compress((json.dumps(data,indent=2)+'\n').encode(),mtime=0));print('Course catalog:',len(models),'entries')
if __name__=='__main__':build()
