"""Capture a genuine AM example run in the project's Tk/ngspice workbench.

Run with Xvfb, Pillow, and ngspice available. Fails when the solver or
actual scope rendering fails; never substitutes a synthetic chart.
"""
import argparse
import sys
import time
from pathlib import Path
from PIL import ImageGrab

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from workbench.app import Workbench

def capture(window,path):
    window.update_idletasks()
    x,y=window.winfo_rootx(),window.winfo_rooty()
    w,h=window.winfo_width(),window.winfo_height()
    if w<450 or h<350:raise RuntimeError(f'Unexpected application geometry: {w} x {h}')
    ImageGrab.grab(bbox=(x,y,x+w,y+h)).save(path)
    print('Captured real window:',path,w,h)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='reports/am-example1-scope.png')
    args=parser.parse_args()
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    app=Workbench()
    try:
        app.geometry('1460x900+20+20')
        app.load_demo('am-example1.ocw.json')
        app.update()
        capture(app,output.with_name('am-example1-schematic.png'))
        app.run()  # async ngspice transient; callback opens real Oscilloscope window.
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            app.update()
            scopes=[w for w in app.winfo_children() if w.winfo_class()=='Toplevel' and 'Oscilloscope' in w.title()]
            if app.result is not None and scopes:break
            if app._job is None and app.result is None:
                raise RuntimeError('AM solver failed: '+app.panel_simulation.get('1.0','end'))
            time.sleep(.05)
        else:raise RuntimeError('AM oscilloscope did not open with solver data in 30 seconds')
        scope=scopes[0]
        scope.geometry('960x620+100+100')
        app.update()
        capture(scope,output)
        app.result.export(output.parent/'am-example1-raw')
        values=app.result.voltages[app.result.nets[('V1',0)]]
        print('AM: samples',len(app.result.axis),'max',max(values),'min',min(values))
    finally:
        app.destroy()

if __name__=='__main__':main()
