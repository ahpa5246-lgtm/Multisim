"""Native instrument panels backed by captured ngspice results."""
import cmath
import copy
import math
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import replace
from .spice import Analysis, Engine, number, source_value
from .measurements import readings, spectrum, mean

class Instruments:
    def run(self):self.start_analysis(replace(self.analysis,kind='tran'),self.scope)
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
        def apply():
            try:
                vals=list(fields.values());settings=Analysis(duration=number(vals[0].get()),points=int(vals[1].get()),start=number(vals[2].get()),stop=number(vals[3].get()))
                settings.validate();self.analysis=settings;win.destroy()
            except ValueError as e:messagebox.showerror('Invalid settings',str(e),parent=win)
        ttk.Button(win,text='Apply',command=apply).grid(row=4,column=1,padx=12,pady=10,sticky='e')
    def generator(self):
        sources=[p for p in self.doc.parts if p.kind=='V']
        if not sources:messagebox.showinfo('Function Generator','Place a voltage source first.',parent=self);return
        win=tk.Toplevel(self);win.title('XFG — Function Generator');win.transient(self)
        selected=tk.StringVar(value=self.selected if self.selected in [p.id for p in sources] else sources[0].id)
        form=tk.StringVar(value='Sine');fields={}
        def row(i,title,var,values=None):
            ttk.Label(win,text=title).grid(row=i,column=0,padx=12,pady=6,sticky='w')
            widget=ttk.Combobox(win,textvariable=var,values=values,state='readonly') if values else ttk.Entry(win,textvariable=var)
            widget.grid(row=i,column=1,padx=12,pady=6)
        row(0,'Source',selected,[p.id for p in sources]);row(1,'Waveform',form,['DC','Sine','Square','Triangle'])
        for i,(name,value) in enumerate([('Amplitude (V peak)','5'),('Offset (V)','0'),('Frequency (Hz)','1000'),('Duty cycle (%)','50')],2):
            fields[name]=tk.StringVar(value=value);row(i,name,fields[name])
        def apply():
            try:
                amp,offset,freq,duty=[number(x.get()) for x in fields.values()]
                if amp<0 or freq<=0 or not 0<duty<100:raise ValueError('Amplitude must be nonnegative; frequency positive; duty 0–100%')
                if form.get()=='DC':value=str(offset)
                elif form.get()=='Sine':value=f'SIN({offset:g} {amp:g} {freq:g})'
                else:
                    period=1/freq
                    rise=period/2 if form.get()=='Triangle' else min(period*1e-4,period*duty/200,period*(1-duty/100)/2)
                    fall=rise;width=0 if form.get()=='Triangle' else max(0,period*duty/100-rise)
                    value=f'PULSE({offset-amp:.12g} {offset+amp:.12g} 0 {rise:.12g} {fall:.12g} {width:.12g} {period:.12g})'
                source_value(value)
                part=next(p for p in self.doc.parts if p.id==selected.get());self.checkpoint();part.value=value;self.render();win.destroy()
                self.status('Source waveform applied — run transient to measure it')
            except ValueError as e:messagebox.showerror('Generator settings',str(e),parent=win)
        ttk.Label(win,text='DC uses Offset. Amplitude is peak about Offset.\nAC analysis excites the first voltage source with 1 V.',justify='left').grid(row=6,column=0,columnspan=2,padx=12,pady=8)
        ttk.Button(win,text='Apply to source',command=apply).grid(row=7,column=1,padx=12,pady=10,sticky='e')
    def multimeter(self):
        result=self._captured()
        if not result:return
        if result.analysis.kind=='ac':messagebox.showinfo('Multimeter','Run transient or DC operating point for these readings.',parent=self);return
        win=tk.Toplevel(self);win.title('XMM — Differential Meter / Source Current');win.geometry('600x400');win.transient(self)
        nodes=sorted(result.voltages,key=int);a=tk.StringVar(value=next((n for n in nodes if n!='0'),'0'));b=tk.StringVar(value='0')
        source=tk.StringVar(value=next(iter(result.currents),' '))
        bar=ttk.Frame(win);bar.pack(fill='x',padx=12,pady=12)
        for text,var,vals in [('V+',a,nodes),('V−',b,nodes),('Source',source,list(result.currents))]:
            ttk.Label(bar,text=text).pack(side='left',padx=4);ttk.Combobox(bar,textvariable=var,values=vals,state='readonly',width=8).pack(side='left')
        text=tk.Text(win,font=('Consolas',12),height=12,bg='#eef4e8');text.pack(fill='both',expand=True,padx=12,pady=5)
        def refresh():
            values=[x-y for x,y in zip(result.voltages[a.get()],result.voltages[b.get()])]
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
        nodes=sorted(set(result.voltages)-{'0'},key=int)
        output=tk.StringVar(value=nodes[-1]);reference=tk.StringVar(value=nodes[0]);threshold=tk.StringVar(value='2.5');maxfreq=tk.StringVar(value='0')
        bar=ttk.Frame(win);bar.pack(fill='x',padx=10,pady=8)
        for text,var in [('Output node',output),('Input / CH2 node',reference)]:
            ttk.Label(bar,text=text).pack(side='left',padx=5);ttk.Combobox(bar,textvariable=var,values=nodes,state='readonly',width=7).pack(side='left')
        if mode=='Logic traces':ttk.Label(bar,text='Threshold (V)').pack(side='left',padx=5);ttk.Entry(bar,textvariable=threshold,width=8).pack(side='left')
        if mode=='Voltage spectrum':
            ttk.Label(bar,text='Max Hz (0=auto)').pack(side='left',padx=5);ttk.Entry(bar,textvariable=maxfreq,width=9).pack(side='left')
        area=tk.Canvas(win,bg='#111d26',highlightthickness=0);area.pack(fill='both',expand=True,padx=12,pady=5)
        footer=tk.StringVar();ttk.Label(win,textvariable=footer,wraplength=900).pack(fill='x',padx=12,pady=10)
        def redraw(event=None):
            try:
                axis=result.axis;values=result.voltages[output.get()];reference_values=result.voltages[reference.get()]
                if mode=='Bode':
                    if any(abs(v)<1e-14 for v in reference_values):raise ValueError('Input/reference is zero; select the driven node')
                    transfer=[v/i for v,i in zip(values,reference_values)]
                    sets=[('Gain (dB)',[20*math.log10(max(abs(x),1e-30)) for x in transfer]),('Phase (degrees)',[math.degrees(cmath.phase(x)) for x in transfer])]
                    axis=[math.log10(x) for x in axis];xlabel='Frequency (Hz, logarithmic)';info='AC small-signal transfer V(output) / V(input). First source excited; others AC=0.'
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
                self._draw_plot(area,axis,sets,xlabel,mode=='Bode',mode=='Logic traces');footer.set(info)
            except ValueError as e:footer.set(str(e));area.delete('all')
        for var in (output,reference):var.trace_add('write',lambda *_:redraw())
        ttk.Button(bar,text='Update',command=redraw).pack(side='right',padx=5)
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
                area.create_text(56,y,text=f'{hi-(hi-lo)*k/5:.3g}',anchor='e',fill='#aebfcb',font=('Consolas',9))
            for idx,(label,arr) in enumerate(chosen):
                color=['#ffde69','#42dbce'][idx%2] if not separate else ['#ffde69','#42dbce'][band%2]
                pts=[];previous_y=None
                for t,v in zip(x,arr):
                    px=65+(w-90)*(t-xlo)/(xhi-xlo);py=top+(bottom-top)*(hi-v)/(hi-lo)
                    if steps and previous_y is not None:pts.extend([px,previous_y])
                    pts.extend([px,py]);previous_y=py
                area.create_line(*pts,fill=color,width=1.7)
                area.create_text(75+idx*180,top+8,text=label,anchor='w',fill=color,font=('Consolas',10,'bold'))
        for k in range(6):
            px=65+(w-90)*k/5;value=xlo+(xhi-xlo)*k/5
            area.create_text(px,h-26,text=f'{10**value if separate else value:.3g}',fill='#aebfcb',font=('Consolas',9))
        area.create_text(w/2,h-9,text=xlabel,fill='#aebfcb',font=('Segoe UI',9))
