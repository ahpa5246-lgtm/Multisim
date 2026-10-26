"""Capture actual AM windows and retain raw solver evidence; not mockups."""
import argparse
import gzip
import json
import math
from pathlib import Path
import sys
from tkinter import ttk

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from workbench.app import Workbench
from workbench.course import BY_ID
from workbench.course_ui import load_experiment
from workbench.measurements import mean
from workbench.spice import Engine


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('reports/am-demo'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    app=Workbench()
    def capture(widget,name):
        app.update_idletasks();app.update()
        x,y=widget.winfo_rootx(),widget.winfo_rooty()
        ImageGrab.grab(bbox=(x,y,x+widget.winfo_width(),y+widget.winfo_height())).save(args.output/name)
    try:
        app.update();app.load_am();app.doc.save(args.output/'am-jfet.ocw.json')
        app.result=Engine().run(app.doc,app.analysis)
        result=app.result;result.export(args.output/'raw')
        for filename in ('samples.csv','raw-table.dat'):
            path=args.output/'raw'/filename
            path.with_suffix(path.suffix+'.gz').write_bytes(gzip.compress(path.read_bytes(),mtime=0));path.unlink()
        pairs=[(t,y) for t,y in zip(result.axis,result.voltages[result.labels['out']]) if t>=.005]
        times,values=map(list,zip(*pairs))
        def amplitude(f):
            return math.hypot(*(2*mean(times,[y*fn(2*math.pi*f*t) for t,y in pairs]) for fn in (math.sin,math.cos)))
        peaks={str(f):amplitude(f) for f in (9800,10000,10200)}
        report=dict(carrier_Hz=10000,message_Hz=200,gate_bias_V=-1.2,gate_peak_V=.4,
                    output_tone_peak_V=peaks,modulation_depth_from_lower_sideband=2*peaks['9800']/peaks['10000'],
                    method='Time-weighted sine/cosine projections from 5 ms to 25 ms; nonlinear AM includes harmonic distortion.',
                    samples=len(result.axis),model='BF245B from pinned Qucs-S JFETs.lib',engine='ngspice 42',NI_reference=False)
        (args.output/'am-measurements.json').write_text(json.dumps(report,indent=2)+'\n')
        app.report_tabs.select(2);app.fit();capture(app,'am-workbench.png')
        app.scope();app.update()
        win=next(w for w in app.winfo_children() if w.winfo_class()=='Toplevel')
        selectors=[w for w in descendants(win) if isinstance(w,ttk.Combobox)]
        selectors[1].set('Off');app.update()
        capture(win,'am-scope.png');win.destroy()
        app.spectrum_panel();app.update()
        win=next(w for w in app.winfo_children() if w.winfo_class()=='Toplevel')
        entry=next(w for w in descendants(win) if w.winfo_class()=='TEntry');entry.delete(0,'end');entry.insert(0,'12000')
        next(w for w in descendants(win) if isinstance(w,ttk.Button) and w.cget('text')=='Update').invoke()
        capture(win,'am-spectrum.png');win.destroy()
        app.selected='VM';app.generator();app.update()
        win=next(w for w in app.winfo_children() if w.winfo_class()=='Toplevel')
        capture(win,'am-generator.png');win.destroy()
        print(json.dumps(report,indent=2))
    finally:app.destroy()


if __name__=='__main__':main()
