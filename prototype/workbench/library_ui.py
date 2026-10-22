"""Native searchable catalog of pinned Qucs-S-derived devices."""
import tkinter as tk
from tkinter import ttk
from .devices import MODELS
from .core import DEFAULTS

def component_browser(app):
    win=tk.Toplevel(app);win.title('Component Database — Qucs-S models');win.geometry('1040x650');win.transient(app)
    win.grab_set();top=ttk.Frame(win);top.pack(fill='x',padx=12,pady=10)
    ttk.Label(top,text=f'Master Database: {len(MODELS)} adapted device models + basic parts').pack(side='left')
    query=tk.StringVar();ttk.Label(top,text='Search').pack(side='left',padx=(20,5));entry=ttk.Entry(top,textvariable=query);entry.pack(side='left',fill='x',expand=True)
    body=ttk.PanedWindow(win,orient='horizontal');body.pack(fill='both',expand=True,padx=12)
    side=ttk.Frame(body);body.add(side,weight=0);ttk.Label(side,text='Group / Family').pack(anchor='w')
    groups=tk.Listbox(side,exportselection=False,width=18);groups.pack(fill='both',expand=True)
    for value in ('All','Basic','Sources','Diodes','Switches','NPN','PNP','OPAMP'):groups.insert('end',value)
    groups.selection_set(0)
    mid=ttk.Frame(body);body.add(mid,weight=1)
    tree=ttk.Treeview(mid,columns=('name','family','pins'),show='headings',selectmode='browse')
    for key,title,width in [('name','Component / model',240),('family','Family',100),('pins','Electrical pin order',200)]:tree.heading(key,text=title);tree.column(key,width=width)
    scroll=ttk.Scrollbar(mid,command=tree.yview);tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');tree.pack(fill='both',expand=True)
    info=tk.StringVar();ttk.Label(win,textvariable=info,wraplength=990,justify='left').pack(fill='x',padx=12,pady=10)
    names={'R':'Resistor','C':'Capacitor','L':'Inductor','V':'DC voltage source','GND':'Ground reference','D':'Diode','LED':'Light emitting diode','SW':'Switch'}
    catalog={k:{'kind':k,'value':DEFAULTS[k][0],'family':family,'description':names[k]+' — built-in primitive'} for k,family in [('R','Basic'),('C','Basic'),('L','Basic'),('V','Sources'),('GND','Sources'),('D','Diodes'),('LED','Diodes'),('SW','Switches')]}
    catalog.update({name:{'kind':data['kind'],'value':name,'family':data['kind'],'description':data['description'],'source':data['source']} for name,data in MODELS.items()})
    pin_order={'NPN':'C / B / E','PNP':'C / B / E','OPAMP':'+ / − / VCC / VEE / OUT','GND':'Reference'}
    def preview(event=None):
        chosen=tree.selection()
        if not chosen:info.set('No matching components');return
        model=catalog[chosen[0]];description=model['description'].replace('\n',' ')[:600]
        info.set(f"{chosen[0]} — {pin_order.get(model['kind'],'Pin 1 / Pin 2')}\n{description}\nSource: {model.get('source','Open Circuit Workbench')}. Electrical symbol order is not physical package numbering.")
    def refresh(*_):
        group=groups.get(groups.curselection()[0]) if groups.curselection() else 'All';needle=query.get().lower().strip()
        tree.delete(*tree.get_children())
        for name,data in catalog.items():
            if group not in ('All',data['family']):continue
            if needle and needle not in (name+' '+data['description']).lower():continue
            tree.insert('','end',iid=name,values=(name,data['family'],pin_order.get(data['kind'],'1 / 2')))
        if tree.get_children():tree.selection_set(tree.get_children()[0])
        preview()
    def choose(event=None):
        if not tree.selection():return
        data=catalog[tree.selection()[0]];app.set_mode(data['kind']);app.placement_value=data['value'];win.destroy()
    tree.bind('<<TreeviewSelect>>',preview);tree.bind('<Double-1>',choose);tree.bind('<Return>',choose)
    groups.bind('<<ListboxSelect>>',refresh);query.trace_add('write',refresh)
    actions=ttk.Frame(win);actions.pack(fill='x',padx=12,pady=(0,12))
    ttk.Button(actions,text='Cancel',command=win.destroy).pack(side='right',padx=5);ttk.Button(actions,text='Place component',command=choose).pack(side='right')
    refresh();entry.focus_set()
