"""Native instrument panels backed by captured ngspice results."""
import cmath
import copy
import math
import queue
import threading
import tkinter as tk
from . import theme
from tkinter import ttk, messagebox, filedialog
from dataclasses import replace
from .spice import Analysis, Engine, number, source_value
from .measurements import readings, spectrum, mean

def node_options(result,include_ground=True):
    return [n+(' ('+', '.join(name for name,node in result.labels.items() if node==n)+')' if n in result.labels.values() else '') for n in sorted(result.voltages,key=int) if include_ground or n!='0']

def node_id(label):return label.split()[0]

class Instruments:
    def run(self):self.start_analysis(replace(self.analysis,kind='tran'),self.scope)
    def dc_sweep(self):
        sources=[p.id for p in self.doc.parts if p.kind=='V']
        if not sources:messagebox.showinfo('DC sweep','Add a voltage source first',parent=self);return
        win=tk.Toplevel(self);win.title('DC Sweep / I–V Analysis');win.transient(self)
        source=tk.StringVar(value=sources[0]);values=[tk.StringVar(value=x) for x in ('0','5','.1')]
        ttk.Label(win,text='Sweep voltage source').grid(row=0,column=0,padx=12,pady=8)
        ttk.Combobox(win,textvariable=source,values=sources,state='readonly').grid(row=0,column=1,padx=12,pady=8)
        for i,(title,var) in enumerate(zip(('Start (V)','Stop (V)','Step (V)'),values),1):
            ttk.Label(win,text=title).grid(row=i,column=0,padx=12,pady=8);ttk.Entry(win,textvariable=var).grid(row=i,column=1,padx=12,pady=8)
        def run():
            try:
                settings=replace(self.analysis,kind='dc',sweep_source=source.get(),sweep_start=number(values[0].get()),sweep_stop=number(values[1].get()),sweep_step=number(values[2].get()))
                settings.validate();win.destroy();self.start_analysis(settings,self.dc_plot)
            except ValueError as e:messagebox.showerror('DC sweep',str(e),parent=win)
        ttk.Button(win,text='Run sweep',command=run).grid(row=4,column=1,padx=12,pady=12)
    def dc_plot(self):
        result=self._captured('dc')
        if not result:return
        win=tk.Toplevel(self);win.title('DC Sweep — voltage / current curves');win.geometry('960x600');win.transient(self)
        vectors={f'V({n}) [V]':v for n,v in result.voltages.items()}|{f'I({n}) [A]':v for n,v in result.currents.items()}
        selected=tk.StringVar(value=next(iter(vectors)));bar=ttk.Frame(win);bar.pack(fill='x',padx=12,pady=8)
        ttk.Label(bar,text='Output vector').pack(side='left');ttk.Combobox(bar,textvariable=selected,values=list(vectors),state='readonly',width=30).pack(side='left',padx=8)
        area=tk.Canvas(win,bg='#111d26',highlightthickness=0);area.pack(fill='both',expand=True,padx=12,pady=8)
        def redraw(event=None):self._draw_plot(area,result.axis,[(selected.get(),vectors[selected.get()])],f'Swept source {result.analysis.sweep_source} (V)')
        selected.trace_add('write',lambda *_:redraw());area.bind('<Configure>',redraw)
        ttk.Label(win,text='Source current sign: positive into the positive voltage terminal. Completed-run snapshot.').pack(pady=8)
    def dc_analysis(self):self.start_analysis(replace(self.analysis,kind='op'),self.multimeter)
    def bode(self):self.start_analysis(replace(self.analysis,kind='ac'),lambda:self.trace_panel('Bode'))
    def start_analysis(self,analysis,callback):
        if self._job is not None:self.status('A simulation is running; Stop it before starting another');return
        try:analysis.validate()
        except ValueError as e:messagebox.showerror('Analysis settings',str(e),parent=self);return
        snapshot=copy.deepcopy(self.doc);self.engine=Engine(self.ngspice_path);self._job=queue.Queue();self._job_cancelled=False;self.result=None;self.timeline=None
        engine=self.engine;results=self._job
        def worker():
            try:results.put((engine.run(snapshot,analysis),None))
            except Exception as e:results.put((None,str(e)))
        threading.Thread(target=worker,daemon=True).start()
        self.status('ngspice running — '+analysis.kind.upper())
        self.after(30,lambda:self._poll_analysis(snapshot,callback))
    def _poll_analysis(self,snapshot,callback):
        if self._job is None:return
        try:result,error=self._job.get_nowait()
        except queue.Empty:self.after(30,lambda:self._poll_analysis(snapshot,callback));return
        self._job=None
        if getattr(self,'_job_cancelled',False):self.status('Simulation cancelled; result discarded');return
        if error:
            self.status(error.splitlines()[0]);self.write_panel('simulation',error)
            if 'cancelled' not in error.lower():messagebox.showerror('ngspice simulation',error,parent=self)
            return
        if snapshot.to_dict()!=self.doc.to_dict():self.status('Discarded result: circuit changed during simulation');return
        self.result=result
        if result.analysis.kind=='tran':self.timeline=(result.axis,result.voltages,result.nets)
        summary=f'ngspice {result.analysis.kind.upper()}: {len(result.axis)} samples\n'
        summary+='\n'.join(f'V({n}) = {v[-1]:.6g} V' for n,v in result.voltages.items() if n!='0')
        self.write_panel('results',summary);self.write_panel('simulation',result.log+'\n'+result.deck)
        self.report_tabs.select(0);self.status('ngspice completed — '+result.analysis.kind.upper());callback()
    def stop(self):
        if self._job is not None:self._job_cancelled=True;self.engine.cancel();self.status('Cancelling ngspice…')
        else:self.status('No simulation is running')
    def close_workbench(self):
        self.stop();self.destroy()
    def _captured(self,kind=None):
        if self.result is None or (kind and self.result.analysis.kind!=kind):
            messagebox.showinfo('Instrument','Run '+('a '+kind.upper()+' analysis' if kind else 'a simulation')+' first.',parent=self)
            return None
        return self.result
    def export_results(self):
        result=self._captured()
        if result:
            path=filedialog.askdirectory(title='Export netlist, raw samples, CSV and solver log',parent=self)
            if path:
                try:result.export(path);self.status('Simulation evidence exported to '+path)
                except OSError as e:messagebox.showerror('Export failed',str(e),parent=self)
    def locate_ngspice(self):
        path=filedialog.askopenfilename(title='Select ngspice / ngspice.exe',parent=self)
        if path:self.ngspice_path=path;self.status('ngspice executable selected for this session')
    def analysis_settings(self):
        win=tk.Toplevel(self);win.title('Analysis settings — ngspice');win.transient(self)
        fields={}
        for i,(name,value) in enumerate([('Duration (s)',self.analysis.duration),('Time steps / AC points per decade',self.analysis.points),('AC start (Hz)',self.analysis.start),('AC stop (Hz)',self.analysis.stop)]):
            ttk.Label(win,text=name).grid(row=i,column=0,padx=12,pady=8,sticky='w')
            var=tk.StringVar(value=str(value));fields[name]=var;ttk.Entry(win,textvariable=var,width=22).grid(row=i,column=1,padx=12,pady=8)
        ttk.Label(win,text='AC input source').grid(row=4,column=0,padx=12,pady=8,sticky='w')
        ac_source=tk.StringVar(value=self.analysis.ac_source or next((p.id for p in self.doc.parts if p.kind=='V'),''))
        ttk.Combobox(win,textvariable=ac_source,values=[p.id for p in self.doc.parts if p.kind=='V'],state='readonly').grid(row=4,column=1,padx=12,pady=8)
        def apply():
            try:
                vals=list(fields.values());settings=replace(self.analysis,ac_source=ac_source.get(),duration=number(vals[0].get()),points=int(vals[1].get()),start=number(vals[2].get()),stop=number(vals[3].get()))
                settings.validate();self.analysis=settings;win.destroy()
            except ValueError as e:messagebox.showerror('Invalid settings',str(e),parent=win)
        ttk.Button(win,text='Apply',command=apply).grid(row=5,column=1,padx=12,pady=10,sticky='e')
    def generator(self):
        """Live editing front panel; Apply still writes to a real SPICE source."""
        sources = [p for p in self.doc.parts if p.kind == 'V']
        if not sources:
            messagebox.showinfo('Function Generator','Place a voltage source first.',parent=self)
            return
        win = tk.Toplevel(self)
        win.title('XFG — Function Generator')
        win.geometry('715x420')
        win.minsize(615,390)
        win.configure(bg='#e4e8ed')
        win.transient(self)
        win.columnconfigure(0,weight=3)
        win.columnconfigure(1,weight=4)
        selected = tk.StringVar(value=self.selected if self.selected in [p.id for p in sources] else sources[0].id)
        form = tk.StringVar(value='Sine')
        fields = {}

        heading = tk.Frame(win,bg='#d8e3f1',bd=1,relief='groove')
        heading.grid(row=0,column=0,columnspan=2,sticky='ew')
        tk.Frame(heading,bg='#275d9b',width=5).pack(side='left',fill='y')
        tk.Label(heading,text='XFG  •  FUNCTION GENERATOR',bg='#d8e3f1',
                 fg='#1f4268',font=(theme.FAMILY,11,'bold'),padx=13,pady=10).pack(side='left')
        tk.Label(heading,text='SPICE voltage source',bg='#d8e3f1',
                 fg='#637791',font=(theme.FAMILY,9)).pack(side='right',padx=12)

        settings = ttk.LabelFrame(win,text='Signal configuration')
        settings.grid(row=1,column=0,sticky='nsew',padx=(12,7),pady=(12,8))
        settings.columnconfigure(1,weight=1)
        display = ttk.LabelFrame(win,text='Waveform preview')
        display.grid(row=1,column=1,sticky='nsew',padx=(7,12),pady=(12,8))
        display.columnconfigure(0,weight=1)
        display.rowconfigure(0,weight=1)
        win.rowconfigure(1,weight=1)

        def row(i,title,var,values=None):
            ttk.Label(settings,text=title).grid(row=i,column=0,padx=(12,5),pady=7,sticky='w')
            widget=(ttk.Combobox(settings,textvariable=var,values=values,
                                 state='readonly',width=17)
                    if values else ttk.Entry(settings,textvariable=var,width=18))
            widget.grid(row=i,column=1,padx=(3,12),pady=7,sticky='ew')
        row(0,'Source',selected,[p.id for p in sources])
        row(1,'Waveform',form,['DC','Sine','Square','Triangle'])
        for i,(name,value) in enumerate([
            ('Amplitude (V peak)','5'),('Offset (V)','0'),
            ('Frequency (Hz)','1000'),('Duty cycle (%)','50')],2):
            fields[name] = tk.StringVar(value=value)
            row(i,name,fields[name])

        screen = tk.Canvas(display,bg='#101b29',height=235,
                           highlightthickness=1,highlightbackground='#425a77')
        screen.grid(row=0,column=0,sticky='nsew',padx=9,pady=(9,6))
        display_caption = tk.StringVar(value='Preview • calculated display, not solver output')
        ttk.Label(display,textvariable=display_caption,justify='left').grid(
            row=1,column=0,sticky='w',padx=10,pady=(0,10))

        def preview(*_):
            screen.delete('all')
            w=max(270,screen.winfo_width());h=max(165,screen.winfo_height())
            left,right,top,bottom=28,w-15,25,h-27
            for i in range(6):
                x=left+(right-left)*i/5
                screen.create_line(x,top,x,bottom,fill='#253851')
            for i in range(5):
                y=top+(bottom-top)*i/4
                screen.create_line(left,y,right,y,fill='#253851')
            screen.create_line(left,(top+bottom)/2,right,(top+bottom)/2,
                               fill='#4b657e',dash=(4,4))
            try:
                amp=number(fields['Amplitude (V peak)'].get())
                offset=number(fields['Offset (V)'].get())
                duty=number(fields['Duty cycle (%)'].get())
                if amp<0 or not 0<duty<100:
                    raise ValueError('Invalid amplitude or duty cycle')
                wave=form.get()
                peak=max(1,abs(offset)+amp)*1.35
                coords=[]
                for i in range(401):
                    t=2*i/400
                    phase=t%1
                    if wave=='DC':
                        value=offset
                    elif wave=='Sine':
                        value=offset+amp*math.sin(2*math.pi*t)
                    elif wave=='Square':
                        value=offset+(amp if phase<duty/100 else -amp)
                    else:
                        value=offset+amp*(4*abs(phase-.5)-1)
                    x=left+(right-left)*i/400
                    y=(top+bottom)/2-(bottom-top)*.43*value/peak
                    coords.extend((x,y))
                screen.create_line(*coords,fill='#5ad7f6',width=2,
                                   smooth=False)
                screen.create_text(left+5,top+8,text=f'{wave.upper()}  •  {amp:g} Vpk',
                                   fill='#c9dded',anchor='w',font=(theme.MONO,9))
                display_caption.set('Calculated preview • apply source, then run ngspice')
            except (ValueError,OverflowError):
                display_caption.set('Enter valid signal settings to preview')
        screen.bind('<Configure>',preview)
        for var in [form,*fields.values()]:
            var.trace_add('write',preview)

        def apply():
            try:
                amp,offset,freq,duty=[number(x.get()) for x in fields.values()]
                if amp<0 or freq<=0 or not 0<duty<100:
                    raise ValueError('Amplitude must be nonnegative; frequency positive; duty 0–100%')
                if form.get()=='DC':value=str(offset)
                elif form.get()=='Sine':value=f'SIN({offset:g} {amp:g} {freq:g})'
                else:
                    period=1/freq
                    rise=period/2 if form.get()=='Triangle' else min(period*1e-4,period*duty/200,period*(1-duty/100)/2)
                    fall=rise;width=0 if form.get()=='Triangle' else max(0,period*duty/100-rise)
                    value=f'PULSE({offset-amp:.12g} {offset+amp:.12g} 0 {rise:.12g} {fall:.12g} {width:.12g} {period:.12g})'
                source_value(value)
                part=next(p for p in self.doc.parts if p.id==selected.get())
                self.checkpoint();part.value=value;self.render();win.destroy()
                self.status('Source waveform applied — run transient to measure it')
            except ValueError as e:
                messagebox.showerror('Generator settings',str(e),parent=win)

        ttk.Label(win,text='DC uses Offset. AC sweep uses the source selected in Analysis Settings.',
                  font=(theme.FAMILY,9)).grid(row=2,column=0,columnspan=2,
                                              sticky='w',padx=16,pady=(0,4))
        # Keep the apply button as a direct child: native keyboard focus and
        # existing instrument interaction tests continue to work.
        ttk.Button(win,text='Apply to source',command=apply).grid(
            row=3,column=1,sticky='e',padx=16,pady=(0,12))
        win.after_idle(preview)

    def multimeter(self):
        result=self._captured()
        if not result:return
        if result.analysis.kind not in ('tran','op'):messagebox.showinfo('Multimeter','Run transient or DC operating point for these readings.',parent=self);return
        win=tk.Toplevel(self);win.title('XMM — Differential Meter / Source Current');win.geometry('800x420');win.transient(self)
        nodes=node_options(result);a=tk.StringVar(value=next((n for n in nodes if node_id(n)!='0'),nodes[0]));b=tk.StringVar(value=next(n for n in nodes if node_id(n)=='0'))
        source=tk.StringVar(value=next(iter(result.currents),' '))
        bar=ttk.Frame(win);bar.pack(fill='x',padx=12,pady=12)
        for text,var,vals in [('V+',a,nodes),('V−',b,nodes),('Source',source,list(result.currents))]:
            ttk.Label(bar,text=text).pack(side='left',padx=4);ttk.Combobox(bar,textvariable=var,values=vals,state='readonly',width=16).pack(side='left')
        text=tk.Text(win,font=(theme.MONO,12),height=12,bg='#eef4e8');text.pack(fill='both',expand=True,padx=12,pady=5)
        def refresh():
            values=[x-y for x,y in zip(result.voltages[node_id(a.get())],result.voltages[node_id(b.get())])]
            data=readings(result.axis,values);lines=[f'{key}: {value:.7g}' if value is not None else f'{key}: no periodic crossings' for key,value in data.items()]
            if source.get() in result.currents:
                current=result.currents[source.get()];ref=source.get();pos=result.nets[(ref,0)];neg=result.nets[(ref,1)]
                source_v=[x-y for x,y in zip(result.voltages[pos],result.voltages[neg])]
                lines += [f'Source current mean (A): {mean(result.axis,current):.7g}',f'Source delivered mean power (W): {-mean(result.axis,[v*i for v,i in zip(source_v,current)]):.7g}']
            text.config(state='normal');text.delete('1.0','end');text.insert('end','\n'.join(lines));text.config(state='disabled')
        for var in (a,b,source):var.trace_add('write',lambda *_:refresh())
        ttk.Label(win,text='Snapshot of completed run. Current sign: into positive source terminal.').pack(pady=4)
        refresh()
    def scope(self):self.trace_panel('Oscilloscope')
    def probe(self):self.multimeter()
    def logic(self):self.trace_panel('Logic traces')
    def spectrum_panel(self):self.trace_panel('Voltage spectrum')
    def trace_panel(self,mode):
        result=self._captured('ac' if mode=='Bode' else 'tran')
        if not result:return
        win=tk.Toplevel(self);win.title(mode+' — ngspice snapshot');win.geometry('960x620');win.transient(self)
        nodes=node_options(result,False)
        output=tk.StringVar(value=next((n for n in nodes if node_id(n)==result.labels.get('out')),nodes[-1]));reference=tk.StringVar(value=next((n for n in nodes if node_id(n)==result.labels.get('input',result.labels.get('raw'))),nodes[0]));threshold=tk.StringVar(value='2.5');maxfreq=tk.StringVar(value='0')
        bar=ttk.Frame(win);bar.pack(fill='x',padx=10,pady=8)
        for text,var in [('Output node',output),('Input / CH2 node',reference)]:
            ttk.Label(bar,text=text).pack(side='left',padx=5);ttk.Combobox(bar,textvariable=var,values=nodes,state='readonly',width=19).pack(side='left')
        if mode=='Logic traces':ttk.Label(bar,text='Threshold (V)').pack(side='left',padx=5);ttk.Entry(bar,textvariable=threshold,width=8).pack(side='left')
        if mode=='Voltage spectrum':
            ttk.Label(bar,text='Max Hz (0=auto)').pack(side='left',padx=5);ttk.Entry(bar,textvariable=maxfreq,width=9).pack(side='left')
        area=tk.Canvas(win,bg='#111d26',highlightthickness=0);area.pack(fill='both',expand=True,padx=12,pady=5)
        footer=tk.StringVar();ttk.Label(win,textvariable=footer,wraplength=900).pack(fill='x',padx=12,pady=10)
        cursors={};active_cursor=tk.StringVar(value='A')
        if mode=='Oscilloscope':
            controls=ttk.Frame(win);controls.pack(fill='x',padx=12,pady=4)
            ttk.Label(controls,text='Click waveform to place cursor:').pack(side='left')
            for label in ('A','B'):ttk.Radiobutton(controls,text=label,variable=active_cursor,value=label).pack(side='left',padx=6)
        def redraw(event=None):
            try:
                axis=result.axis;values=result.voltages[node_id(output.get())];reference_values=result.voltages[node_id(reference.get())]
                if mode=='Bode':
                    if any(abs(v)<1e-14 for v in reference_values):raise ValueError('Input/reference is zero; select the driven node')
                    transfer=[v/i for v,i in zip(values,reference_values)]
                    sets=[('Gain (dB)',[20*math.log10(max(abs(x),1e-30)) for x in transfer]),('Phase (degrees)',[math.degrees(cmath.phase(x)) for x in transfer])]
                    axis=[math.log10(x) for x in axis];xlabel='Frequency (Hz, logarithmic)';info='AC small-signal transfer V(output) / V(input). Selected AC source excited; others AC=0.'
                elif mode=='Voltage spectrum':
                    axis,values=spectrum(axis,values);full_count=len(axis);nyquist=axis[-1];limit=number(maxfreq.get())
                    if limit<0:raise ValueError('Maximum frequency must be nonnegative')
                    if limit==0:
                        peak=max(range(1,len(values)),key=lambda i:values[i]);limit=max(5*axis[peak],5*axis[1])
                    pairs=[(f,v) for f,v in zip(axis,values) if f<=limit]
                    if len(pairs)<2:raise ValueError('Frequency range must include at least two bins')
                    axis,values=map(list,zip(*pairs));sets=[('Amplitude (V peak)',values)];xlabel='Frequency (Hz)';info=f'Hann window, DC removed, {2*(full_count-1)} uniform resamples; Nyquist {nyquist:.5g} Hz. No downsampling below original count. Input undersampling/interpolation still limit accuracy; not power spectral density.'
                elif mode=='Logic traces':
                    level=number(threshold.get());sets=[('Thresholded V('+output.get()+')',[float(v>=level) for v in values])];xlabel='Time (s)';info='Analog threshold view only; not a digital gate simulator. Threshold = '+str(level)+' V.'
                else:
                    sets=[('CH1 V('+output.get()+')',values),('CH2 V('+reference.get()+')',reference_values)];xlabel='Time (s)';info='Sample times come from ngspice adaptive integration. Both channels share the displayed vertical scale.'
                self._draw_plot(area,axis,sets,xlabel,mode=='Bode',mode=='Logic traces')
                if mode=='Oscilloscope':
                    for label,j in cursors.items():
                        x=65+(area.winfo_width()-90)*(result.axis[j]-result.axis[0])/(result.axis[-1]-result.axis[0])
                        area.create_line(x,24,x,area.winfo_height()-65,fill='#e9eef3',dash=(3,3))
                        info+=f'  {label}: {result.axis[j]:.7g} s, CH1={values[j]:.7g} V.'
                    if len(cursors)==2:
                        ja,jb=cursors['A'],cursors['B'];dt=result.axis[jb]-result.axis[ja]
                        info+=f'  Δt={dt:.7g} s; ΔCH1={values[jb]-values[ja]:.7g} V.'
                        if dt:info+=f'  1/|Δt|={1/abs(dt):.7g} Hz (cursor interval).'
                footer.set(info)
            except ValueError as e:footer.set(str(e));area.delete('all')
        for var in (output,reference):var.trace_add('write',lambda *_:redraw())
        ttk.Button(bar,text='Update',command=redraw).pack(side='right',padx=5)
        if mode=='Oscilloscope':
            def place_cursor(event):
                from bisect import bisect_left
                if area.winfo_width()<=90:return
                fraction=max(0,min(1,(event.x-65)/(area.winfo_width()-90)))
                target=result.axis[0]+fraction*(result.axis[-1]-result.axis[0]);j=min(len(result.axis)-1,bisect_left(result.axis,target))
                if j and target-result.axis[j-1]<result.axis[j]-target:j-=1
                cursors[active_cursor.get()]=j;redraw()
            area.bind('<Button-1>',place_cursor)
        area.bind('<Configure>',redraw);win.after_idle(redraw)
    @staticmethod
    def _draw_plot(area,x,sets,xlabel,separate=False,steps=False):
        area.delete('all');w=area.winfo_width();h=area.winfo_height()
        if w<150 or h<100:return
        xlo,xhi=x[0],x[-1]
        if xhi<=xlo:return
        bands=len(sets) if separate else 1
        for band in range(bands):
            top=24+band*(h-65)/bands;bottom=24+(band+1)*(h-65)/bands-12
            chosen=[sets[band]] if separate else sets
            values=[v for _,arr in chosen for v in arr];lo=min(0,min(values));hi=max(values)
            if hi-lo<1e-12:hi=lo+1
            pad=(hi-lo)*.08;lo-=pad;hi+=pad
            for k in range(6):
                y=top+(bottom-top)*k/5;area.create_line(65,y,w-25,y,fill='#2a3b47')
                area.create_text(56,y,text=f'{hi-(hi-lo)*k/5:.3g}',anchor='e',fill='#aebfcb',font=(theme.MONO,9))
            for idx,(label,arr) in enumerate(chosen):
                color=['#ffde69','#42dbce'][idx%2] if not separate else ['#ffde69','#42dbce'][band%2]
                pts=[];previous_y=None
                for t,v in zip(x,arr):
                    px=65+(w-90)*(t-xlo)/(xhi-xlo);py=top+(bottom-top)*(hi-v)/(hi-lo)
                    if steps and previous_y is not None:pts.extend([px,previous_y])
                    pts.extend([px,py]);previous_y=py
                area.create_line(*pts,fill=color,width=1.7)
                area.create_text(75+idx*180,top+8,text=label,anchor='w',fill=color,font=(theme.MONO,10,'bold'))
        for k in range(6):
            px=65+(w-90)*k/5;value=xlo+(xhi-xlo)*k/5
            area.create_text(px,h-26,text=f'{10**value if separate else value:.3g}',fill='#aebfcb',font=(theme.MONO,9))
        area.create_text(w/2,h-9,text=xlabel,fill='#aebfcb',font=(theme.FAMILY,9))
