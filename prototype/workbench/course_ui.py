"""Course experiment selection and measured acceptance results."""
import tkinter as tk
from tkinter import ttk,messagebox
from .course import EXPERIMENTS,BY_ID,evaluate

def load_experiment(app,key):
    experiment=BY_ID[key]
    if app._job is not None:
        messagebox.showinfo('Experiment','Stop the running simulation before loading an experiment.',parent=app);return False
    app.checkpoint();app.doc=experiment.document();app.filepath=None;app.selected=None
    app.analysis=experiment.analysis;app.active_experiment=key
    app.cancel();app.fit()
    app.analysis_mode.set({'op':'DC Operating Point','tran':'Transient','ac':'AC Sweep','dc':'DC Sweep'}[experiment.analysis.kind])
    app.write_panel('simulation',f'{experiment.title}\nPDF pages: {experiment.pages.replace(chr(8211),'-')}\n{experiment.note}\n\nNamed terminals join electrically. Edit and save this circuit normally.\nUse Run Selected Analysis, then Tools > Check Experiment Results.')
    app.report_tabs.select(3);app.status('Loaded experiment: '+experiment.title)
    return True

def check_experiment(app):
    key=getattr(app,'active_experiment',None)
    if key not in BY_ID:messagebox.showinfo('Experiment','Load an experiment from the course browser first.',parent=app);return
    result=app._captured()
    if result is None:return
    experiment=BY_ID[key]
    if result.analysis.kind!=experiment.analysis.kind:
        messagebox.showinfo('Experiment','Run the experiment’s configured analysis before checking results.',parent=app);return
    try:findings=evaluate(experiment,app.doc,result)
    except (ValueError,KeyError,StopIteration) as e:
        messagebox.showerror('Experiment','Required measurement is missing: '+str(e),parent=app);return
    lines=[experiment.title,'PDF pages: '+experiment.pages,experiment.note,'']
    for c in findings:
        lines.append(f"{'PASS' if c['passed'] else 'FAIL'}  {c['node']} / {c['metric']}: {c['actual']:.7g}; expected {c['min']:.7g} to {c['max']:.7g}")
    lines.append('\nThese are model-specific course checks, not NI Multisim reference measurements.')
    app.write_panel('results','\n'.join(lines));app.report_tabs.select(0)
    app.status('Experiment checks: '+('PASS' if all(c['passed'] for c in findings) else 'FAIL'))

def browser(app):
    win=tk.Toplevel(app);win.title('Electronics II — Experiments');win.geometry('1040x670');win.transient(app)
    top=ttk.Frame(win);top.pack(fill='x',padx=12,pady=10)
    ttk.Label(top,text='Search experiments').pack(side='left');query=tk.StringVar();entry=ttk.Entry(top,textvariable=query);entry.pack(side='left',fill='x',expand=True,padx=12)
    tree=ttk.Treeview(win,columns=('chapter','title','pages','analysis'),show='headings',selectmode='browse')
    for col,text,width in [('chapter','Course section',190),('title','Experiment',430),('pages','PDF pages',120),('analysis','Analysis',100)]:
        tree.heading(col,text=text);tree.column(col,width=width)
    scroll=ttk.Scrollbar(win,command=tree.yview);scroll.pack(side='right',fill='y');tree.configure(yscrollcommand=scroll.set);tree.pack(fill='both',expand=True,padx=12)
    detail=tk.StringVar();ttk.Label(win,textvariable=detail,wraplength=980,justify='left').pack(fill='x',padx=12,pady=12)
    def selected(event=None):
        if tree.selection():
            e=BY_ID[tree.selection()[0]];detail.set(e.note+'\nChecks: '+', '.join(c['node']+' / '+c['metric'] for c in e.checks))
        else:detail.set('No matching experiments')
    def refresh(*args):
        tree.delete(*tree.get_children());needle=query.get().lower().strip()
        for e in EXPERIMENTS:
            if needle not in (e.title+' '+e.chapter+' '+e.id).lower():continue
            tree.insert('','end',iid=e.id,values=(e.chapter.replace(chr(8211),'-'),e.title,e.pages.replace(chr(8211),'-'),e.analysis.kind.upper()))
        if tree.get_children():tree.selection_set(tree.get_children()[0])
        selected()
    def load(run=False):
        if not tree.selection():return
        if load_experiment(app,tree.selection()[0]):
            win.destroy()
            if run:app.run_selected()
    actions=ttk.Frame(win);actions.pack(fill='x',padx=12,pady=12)
    ttk.Label(actions,text='Editable labelled circuits | ngspice required | limits shown per experiment').pack(side='left')
    ttk.Button(actions,text='Load and Run',command=lambda:load(True)).pack(side='right',padx=4)
    ttk.Button(actions,text='Load circuit',command=load).pack(side='right',padx=4)
    tree.bind('<<TreeviewSelect>>',selected);tree.bind('<Double-1>',lambda e:load());query.trace_add('write',refresh);refresh();entry.focus_set()
