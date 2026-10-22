"""Adapt Qucs-S BJT models/property ordering; GPL-2.0-or-later.

Property order and SPICE exclusions derived from Basic_BJT / BJT::spice_netlist
by Michael Margraf, (C) 2003–2004, in the pinned Qucs-S tree.
Library descriptions and contributor attributions are retained in generated data.
"""
import json,re,sys,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'prototype'))
from workbench.core import numeric

def build():
    base=ROOT/'upstream/qucs-s';text=(base/'qucs/components/bjtsub.cpp').read_text()
    text=text.split('BJTsub::BJTsub()')[0]
    props=re.findall(r'new Property\("([^"]+)"',text)
    excluded={'Type','Area','Temp','Ffe','Kb','Ab','Fb','UseGlobTemp','LibName','CompName'}
    models={};skipped=[]
    for filename in ('Transistors.lib','BJT_Extended.lib'):
        for name,block in re.findall(r'<Component ([^>]+)>(.*?)</Component>',(base/'library'/filename).read_text(),re.S):
            model=re.search(r'<_BJT\b[^>]*>',block,re.S)
            if not model:skipped.append(name);continue
            values=re.findall(r'"([^"]*)"',model[0]);polarity=values[0].upper()
            try:
                params={key:numeric(val) for key,val in zip(props,values) if key not in excluded}
                if polarity not in ('NPN','PNP'):raise ValueError('Unknown polarity')
            except ValueError:skipped.append(name);continue
            description=re.search(r'<Description>(.*?)</Description>',block,re.S)
            models[name]={'kind':polarity,'parameters':params,'description':description[1].strip() if description else '', 'source':'Qucs-S library/'+filename}
    for name,block in re.findall(r'<Component ([^>]+)>(.*?)</Component>',(base/'library/SpiceOpamp.lib').read_text(),re.S):
        if name not in ('LM324','LM358','NE5532'):continue
        spice=re.search(r'<Spice>(.*?)</Spice>',block,re.S)[1].strip()
        description=re.search(r'<Description>(.*?)</Description>',block,re.S)[1].strip()
        models[name]={'kind':'OPAMP','spice':spice,'description':description,'source':'Qucs-S library/SpiceOpamp.lib','subckt':'SpiceOpamp_'+name}
    data={'upstream_sha':'46e47e8fabe852a9d6aab41d8a612ff5a78370c1','license':'GPL-2.0-or-later; see THIRD_PARTY.md and COPYING.qucs-s','models':models,'skipped':skipped}
    target=ROOT/'prototype/workbench/data/qucs-devices.json.gz';target.write_bytes(gzip.compress((json.dumps(data,indent=2)+'\n').encode(),mtime=0))
    print(f'{len(models)} models adapted; {len(skipped)} skipped')
if __name__=='__main__':build()
