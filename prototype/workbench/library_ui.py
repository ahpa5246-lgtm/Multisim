"""Native searchable catalog of pinned Qucs-S-derived devices."""
import tkinter as tk
from . import theme
from tkinter import ttk
from .devices import MODELS
from .core import DEFAULTS, PIN_LABELS

def component_browser(app):
    win=tk.Toplevel(app);win.title('Select a Component');win.geometry('1040x650');win.transient(app)
    win.grab_set();top=ttk.Frame(win);top.pack(fill='x',padx=12,pady=10)
    ttk.Label(top,text='Database:').pack(side='left',padx=(0,8))
    database=ttk.Combobox(top,values=['Master Database'],state='readonly',width=25);database.current(0);database.pack(side='left')
    query=tk.StringVar();ttk.Label(top,text='Search').pack(side='left',padx=(20,5));entry=ttk.Entry(top,textvariable=query);entry.pack(side='left',fill='x',expand=True)
    body=ttk.PanedWindow(win,orient='horizontal');body.pack(fill='both',expand=True,padx=12)
    side=ttk.Frame(body);body.add(side,weight=0);ttk.Label(side,text='Group / Family').pack(anchor='w')
    groups=tk.Listbox(side,exportselection=False,width=18);groups.pack(fill='both',expand=True)
    for value in ('All','Basic','Sources','Diodes','Switches','NPN','PNP','NJF','PJF','NMOS','PMOS','SCR','TRIAC','DIAC','IGBT','OPAMP'):groups.insert('end',value)
    groups.selection_set(0)
    mid=ttk.Frame(body);body.add(mid,weight=1)
    tree=ttk.Treeview(mid,columns=('name','family','pins'),show='headings',selectmode='browse')
    for key,title,width in [('name','Component / model',240),('family','Family',100),('pins','Electrical pin order',200)]:tree.heading(key,text=title);tree.column(key,width=width)
    scroll=ttk.Scrollbar(mid,command=tree.yview);tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');tree.pack(fill='both',expand=True)
    details=ttk.Frame(body,width=245);body.add(details,weight=0)
    symbol_box=ttk.LabelFrame(details,text='Symbol');symbol_box.pack(fill='x',padx=(10,0),pady=(0,8))
    symbol=tk.Canvas(symbol_box,width=230,height=175,bg='white',highlightthickness=0);symbol.pack(fill='x',padx=4,pady=4)
    model_box=ttk.LabelFrame(details,text='Model / pin details');model_box.pack(fill='both',expand=True,padx=(10,0))
    model_text=tk.Text(model_box,width=28,height=10,wrap='word',font=(theme.FAMILY,9),bg='white',relief='flat',padx=8,pady=8,state='disabled');model_text.pack(fill='both',expand=True)
    info=tk.StringVar();ttk.Label(win,textvariable=info,wraplength=990,justify='left').pack(fill='x',padx=12,pady=10)
    names={'R':'Resistor','C':'Capacitor','L':'Inductor','V':'DC voltage source','GND':'Ground reference','D':'Diode','LED':'Light emitting diode','IPROBE':'Series current probe (ideal zero-volt source)','SW':'Switch','POT':'Potentiometer (total resistance:position)','I':'Current source'}
    catalog={k:{'kind':k,'value':DEFAULTS[k][0],'family':family,'description':names[k]+' — built-in primitive'} for k,family in [('IPROBE','Sources'),('I','Sources'),('POT','Basic'),('R','Basic'),('C','Basic'),('L','Basic'),('V','Sources'),('GND','Sources'),('D','Diodes'),('LED','Diodes'),('SW','Switches')]}
    catalog.update({name:{'kind':data['kind'],'value':name,'family':data['kind'],'description':data['description'],'source':data['source']} for name,data in MODELS.items()})
    catalog['Generic diode']={'kind':'D','value':'Generic','family':'Diodes','description':'Original generic diode; not a manufacturer model'}
    pin_order=PIN_LABELS
    def draw_symbol(kind):
        symbol.delete('all');c='#123f96'
        def line(*coords,**kw):symbol.create_line(*coords,fill=c,width=2,**kw)
        def label(x,y,text):symbol.create_text(x,y,text=text,fill='#333',font=(theme.FAMILY,9))
        if kind in ('NPN','PNP'):
            line(35,85,95,85);line(95,55,95,115)
            line(95,65,145,40,145,20);line(95,105,145,130,145,150)
            line(115,115,137,126,arrow='last') if kind=='NPN' else line(135,125,109,112,arrow='last')
            label(25,85,'B');label(165,20,'C');label(165,150,'E')
        elif kind in ('NJF','PJF','NMOS','PMOS','IGBT'):
            line(65,85,90,85);line(90,48,90,122);line(103,55,140,55,140,25);line(103,115,140,115,140,150)
            line(103,55,103,115);line(125,115,138,115,arrow='last' if kind in ('NJF','NMOS','IGBT') else 'first')
            if kind in ('NMOS','PMOS'):line(103,85,190,85);label(195,85,'B')
        elif kind in ('SCR','TRIAC','DIAC'):
            line(115,20,115,55);line(115,115,115,150);line(90,55,140,55,115,95,90,55);line(90,95,140,95)
            if kind!='DIAC':line(65,125,115,95)
            if kind in ('TRIAC','DIAC'):line(145,115,170,75,120,75,145,115)
        elif kind=='OPAMP':
            line(65,35,65,140,175,87,65,35);line(30,60,65,60);line(30,115,65,115);line(175,87,210,87)
            line(110,12,110,56);line(110,125,110,163)
            label(80,60,'+');label(80,115,'−');label(135,13,'VCC');label(135,162,'VEE');label(210,108,'OUT')
        elif kind in ('R','POT'):
            line(25,85,65,85);line(155,85,205,85);symbol.create_rectangle(65,70,155,100,outline=c,width=2)
            if kind=='POT':line(115,150,115,100,arrow='last')
        elif kind=='C':line(25,85,105,85);line(105,50,105,120);line(125,50,125,120);line(125,85,205,85)
        elif kind=='IPROBE':line(25,85,205,85,arrow='last')
        elif kind=='GND':
            line(115,40,115,85)
            for y,w in ((85,70),(98,45),(111,20)):line(115-w/2,y,115+w/2,y)
        elif kind in ('V','I'):
            symbol.create_oval(85,48,145,112,outline=c,width=2);line(115,20,115,48);line(115,112,115,150);label(115,65,'+');label(115,95,'−')
            if kind=='I':line(115,65,115,100,arrow='last')
        elif kind in ('D','LED'):
            line(25,85,80,85);line(150,85,205,85);line(80,60,80,110,150,85,80,60);line(150,55,150,115)
        elif kind=='SW':line(25,100,75,100,150,55);line(155,100,205,100)
        elif kind=='L':
            line(25,100,65,100);line(165,100,205,100)
            for x in (65,90,115,140):symbol.create_arc(x,60,x+25,140,start=0,extent=180,outline=c,width=2,style='arc')
    def preview(event=None):
        chosen=tree.selection()
        if not chosen:
            info.set('No matching components');symbol.delete('all')
            model_text.config(state='normal');model_text.delete('1.0','end');model_text.config(state='disabled')
            return
        model=catalog[chosen[0]];draw_symbol(model['kind']);description=model['description'].replace('\n',' ')[:600]
        text=f"{chosen[0]}\n\nElectrical pin order:\n{pin_order.get(model['kind'],'1 / 2')}\n\n{description}\n\n{model.get('source','Built-in primitive')}"
        model_text.config(state='normal');model_text.delete('1.0','end');model_text.insert('end',text);model_text.config(state='disabled')
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
