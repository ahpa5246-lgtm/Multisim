"""Multisim-inspired offline desktop circuit workbench (original Tkinter UI).

Run: python -m workbench.app
Requires Python 3.10+ and Tcl/Tk, no external packages.
"""
from __future__ import annotations
import math
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from .toolbar import ToolButton
from .core import Document, Part, PINS, DEFAULTS, GRID, numeric, snap, simulate

PAPER = '#ffffff'; INK = '#202020'; BLUE = '#163fa0'; RED = '#bf2028'
GREY = '#606060'; BOARD = '#ededed'; OUTLINE = '#b1b1b1'; PALE = '#f5f5f5'

class Workbench(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Open Circuit Workbench — Design1')
        self.geometry('1360x850'); self.minsize(950,610)
        self.configure(background=BOARD)
        self.doc = Document()
        self.filepath = None
        self.mode = 'select'; self.selected = None
        self.pending = None; self.drag_offset=None; self.drag_start=None
        self.clipboard = None
        self.scale_factor = 1.0
        self.timeline = None; self.last_nets = None
        self._make_style(); self._make_menu(); self._make_layout(); self._keys()
        self.example()

    def _make_style(self):
        style=ttk.Style(self)
        if 'clam' in style.theme_names(): style.theme_use('clam')
        style.configure('.', font=('Segoe UI',9))
        style.configure('TFrame',background=BOARD)
        style.configure('Tool.TFrame',background='#f0f1f2')
        style.configure('TButton',font=('Segoe UI',9),padding=(7,4))
        style.configure('Treeview',font=('Segoe UI',9),rowheight=21,background='white')
        style.configure('Treeview.Heading',font=('Segoe UI',9,'bold'))
        style.configure('TNotebook',background=BOARD)
        style.configure('TNotebook.Tab',padding=(10,3))
        style.configure('TLabel', background=BOARD)

    def _make_menu(self):
        menu=tk.Menu(self)
        items={
            'File':[('New',self.new),('Open...',self.open),('Save',self.save),('Save As...',self.save_as),('Export SPICE Netlist...',self.export_netlist),None,('Exit',self.destroy)],
            'Edit':[('Undo',self.undo),('Redo',self.redo),None,('Delete Selected',self.delete_selected),('Rotate Selected',self.rotate),('Properties',self.properties)],
            'View':[('Zoom In',lambda:self.zoom(1.25)),('Zoom Out',lambda:self.zoom(.8)),('Zoom to Fit',self.fit),('Show Grid',self.toggle_grid)],
            'Place':[('Resistor',lambda:self.set_mode('R')),('Capacitor',lambda:self.set_mode('C')),('Inductor',lambda:self.set_mode('L')),('DC Voltage',lambda:self.set_mode('V')),('Ground',lambda:self.set_mode('GND')),('Diode',lambda:self.set_mode('D')),('LED',lambda:self.set_mode('LED')),('Switch',lambda:self.set_mode('SW')),None,('Wire',lambda:self.set_mode('wire'))],
            'Simulate':[('Run Transient',self.run),('Stop',self.stop),('Oscilloscope',self.scope),None,('Load RC Example',self.example)],
            'Tools':[('Components Browser',self.component_browser),('Project Information',self.project_info)],
            'Reports':[('Netlist Preview',self.preview_netlist)],
            'Options':[('Grid Snap',self.toggle_snap)],
            'Window':[('Reset Workspace',self.reset_workspace)],
            'Help':[('About',self.about),('Keyboard Shortcuts',self.shortcuts)]
        }
        for title,commands in items.items():
            m=tk.Menu(menu,tearoff=False)
            for pair in commands:
                if pair is None: m.add_separator()
                else: m.add_command(label=pair[0],command=pair[1])
            menu.add_cascade(label=title,menu=m)
        self.config(menu=menu)

    def _tool(self, parent, icon, command, label, key=None, disabled=False, vertical=False):
        button=ToolButton(parent,icon,command,label,disabled)
        button.pack(side='top' if vertical else 'left',padx=1,pady=1)
        if key:self.tool_buttons[key]=button
        return button

    def _separator(self,parent):
        tk.Frame(parent,width=1,bg='#b8b8b8').pack(side='left',fill='y',padx=5,pady=4)

    def _make_layout(self):
        self.tool_buttons={}
        head=tk.Frame(self,bg='#f0f0f0',bd=1,relief='raised');head.pack(fill='x')
        for icon,cmd,label in [('new',self.new,'New (Ctrl+N)'),('open',self.open,'Open (Ctrl+O)'),
                               ('save',self.save,'Save (Ctrl+S)')]:self._tool(head,icon,cmd,label)
        self._separator(head)
        for icon,cmd,label in [('undo',self.undo,'Undo (Ctrl+Z)'),('redo',self.redo,'Redo (Ctrl+Y)'),
                               ('delete',self.delete_selected,'Delete selected component')]:self._tool(head,icon,cmd,label)
        self._separator(head)
        for icon,cmd,label in [('zoom_in',lambda:self.zoom(1.25),'Zoom in'),('zoom_out',lambda:self.zoom(.8),'Zoom out'),
                               ('fit',self.fit,'Reset view'),('grid',self.toggle_grid,'Show / hide grid')]:self._tool(head,icon,cmd,label)
        self.zoom_value=tk.StringVar(value='100%')
        zoom=ttk.Combobox(head,textvariable=self.zoom_value,values=['50%','75%','100%','125%','150%','200%'],state='readonly',width=6)
        zoom.pack(side='left',padx=5)
        zoom.bind('<<ComboboxSelected>>',lambda e:self.zoom(float(self.zoom_value.get().strip('%'))/100/self.scale_factor))
        self._separator(head)
        self._tool(head,'run',self.run,'Run transient analysis (F5)')
        self._tool(head,'stop',self.stop,'Stop — solver runs synchronously')
        tk.Label(head,text='Transient analysis',bg='#f0f0f0',fg='#444',font=('Segoe UI',9)).pack(side='left',padx=8)
        self.hint=tk.StringVar(value='Ready')
        second=tk.Frame(self,bg='#f0f0f0',bd=1,relief='raised');second.pack(fill='x')
        self._tool(second,'select',self.cancel,'Select (Esc)',key='select')
        self._tool(second,'wire',lambda:self.set_mode('wire'),'Place wire',key='wire')
        self._separator(second)
        self._tool(second,'catalog',self.component_browser,'Select a component')
        for kind,label in [('V','DC voltage source'),('GND','Ground'),('R','Resistor'),('C','Capacitor'),
                           ('L','Inductor — export only'),('D','Diode — symbol only'),('LED','LED — symbol only'),('SW','Switch — symbol only')]:
            self._tool(second,kind,lambda k=kind:self.set_mode(k),label,key=kind)
        self._separator(second)
        self._tool(second,'rotate',self.rotate,'Rotate selected (Ctrl+R)')
        self._tool(second,'probe',self.probe,'Read simulated node voltages')
        tk.Label(second,text='In use:',bg='#f0f0f0',font=('Segoe UI',9)).pack(side='left',padx=(16,4))
        self.in_use=ttk.Combobox(second,state='readonly',width=22);self.in_use.pack(side='left',padx=4)
        self.in_use.bind('<<ComboboxSelected>>',self.select_in_use)
        body=ttk.PanedWindow(self,orient=tk.HORIZONTAL);body.pack(fill='both',expand=True)
        left=ttk.Frame(body,width=185);body.add(left,weight=0)
        title=tk.Frame(left,bg='#d8dfe8');title.pack(fill='x')
        tk.Label(title,text='Design Toolbox',bg='#d8dfe8',fg='#243449',font=('Segoe UI',9,'bold'),anchor='w').pack(fill='x',padx=6,pady=4)
        tools=ttk.Notebook(left);tools.pack(fill='both',expand=True)
        hierarchy=ttk.Frame(tools);tools.add(hierarchy,text='Hierarchy')
        self.tree=ttk.Treeview(hierarchy,show='tree',selectmode='browse');self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self.on_tree_select)
        components=ttk.Frame(tools);tools.add(components,text='Components')
        self.parts_list=tk.Listbox(components,relief='flat',bg='white',font=('Segoe UI',9),highlightthickness=0)
        self.parts_list.pack(fill='both',expand=True);self.parts_list.bind('<Double-Button-1>',self.list_place)
        for label in ['Resistor  (R)','Capacitor  (C)','Inductor  (L)','DC Voltage  (V)','Ground  (GND)','Diode  (D)','LED','Switch  (SW)']:self.parts_list.insert('end',label)
        middle=ttk.Frame(body);body.add(middle,weight=5)
        docbar=tk.Frame(middle,bg='#d6d6d6',height=27);docbar.pack(fill='x')
        self.doclabel=tk.Label(docbar,text='Design1',bg='white',fg='#222',font=('Segoe UI',9),padx=14,pady=4,relief='ridge',bd=1)
        self.doclabel.pack(side='left',padx=(2,0),pady=(2,0))
        vertical=ttk.PanedWindow(middle,orient=tk.VERTICAL);vertical.pack(fill='both',expand=True)
        workspace=ttk.Frame(vertical);vertical.add(workspace,weight=5)
        self.canvas=tk.Canvas(workspace,bg=PAPER,bd=0,highlightthickness=0,scrollregion=(0,0,2100,1500),cursor='arrow')
        self.scroll_y=ttk.Scrollbar(workspace,orient='vertical',command=self.canvas.yview)
        self.scroll_x=ttk.Scrollbar(workspace,orient='horizontal',command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.scroll_x.set,yscrollcommand=self.scroll_y.set)
        self.canvas.grid(row=0,column=0,sticky='nsew');self.scroll_y.grid(row=0,column=1,sticky='ns');self.scroll_x.grid(row=1,column=0,sticky='ew')
        workspace.columnconfigure(0,weight=1);workspace.rowconfigure(0,weight=1)
        self.grid_visible=True;self.snap_on=True
        for event,fn in [('<Button-1>',self.canvas_down),('<B1-Motion>',self.canvas_drag),('<ButtonRelease-1>',self.canvas_up),
                         ('<Double-Button-1>',self.canvas_double),('<Motion>',self.canvas_move),('<Button-3>',self.right_click),('<MouseWheel>',self.on_mousewheel)]:self.canvas.bind(event,fn)
        self.canvas.bind('<Button-4>',lambda ev:self.zoom(1.1));self.canvas.bind('<Button-5>',lambda ev:self.zoom(.9))
        self.canvas.bind('<ButtonPress-2>',lambda e:self.canvas.scan_mark(e.x,e.y));self.canvas.bind('<B2-Motion>',lambda e:self.canvas.scan_dragto(e.x,e.y,gain=1))
        results_frame=ttk.Frame(vertical,height=165);vertical.add(results_frame,weight=1)
        tk.Label(results_frame,text='Spreadsheet View',anchor='w',bg='#d8dfe8',fg='#243449',font=('Segoe UI',9,'bold'),padx=6,pady=3).pack(fill='x')
        results=ttk.Notebook(results_frame,height=118);results.pack(fill='both',expand=True);self.report_tabs=results
        for label in ['Results','Nets','Components','Simulation']:
            f=ttk.Frame(results);results.add(f,text=label)
            if label=='Components':
                self.component_sheet=ttk.Treeview(f,columns=('ref','value','type','rotation'),show='headings',selectmode='browse',height=4)
                for col,title,width in [('ref','RefDes',100),('value','Value',160),('type','Component',180),('rotation','Rotation',100)]:
                    self.component_sheet.heading(col,text=title);self.component_sheet.column(col,width=width,anchor='w')
                self.component_sheet.pack(fill='both',expand=True)
                self.component_sheet.bind('<<TreeviewSelect>>',self.select_sheet)
                self.component_sheet.bind('<Double-1>',lambda e:self.properties())
            else:
                t=tk.Text(f,height=4,wrap='word',font=('Consolas',9),bg='white',fg=INK,relief='flat',padx=5,pady=4)
                t.pack(fill='both',expand=True);t.config(state='disabled');setattr(self,'panel_'+label.lower(),t)
        right=tk.Frame(body,width=36,bg='#f0f0f0',bd=1,relief='raised');body.add(right,weight=0)
        for icon,cmd,label,disabled in [('meter',self.multimeter,'Multimeter: simulated DC node readings',False),
                ('scope',self.scope,'Oscilloscope: transient node voltages',False),('generator',self.generator,'Function generator — unavailable',True),
                ('bode',self.not_ready,'Bode plotter — unavailable',True),('logic',self.not_ready,'Logic analyzer — unavailable',True),
                ('probe',self.probe,'Read simulated node voltages',False)]:self._tool(right,icon,cmd,label,disabled=disabled,vertical=True)
        bottom=tk.Frame(self,bg='#f0f0f0',bd=1,relief='sunken');bottom.pack(side='bottom',fill='x',before=body)
        tk.Label(bottom,textvariable=self.hint,bg='#f0f0f0',fg='#333',anchor='w',font=('Segoe UI',9)).pack(side='left',padx=6,pady=3)
        self.coordlabel=tk.Label(bottom,text='X: 0  Y: 0',bg='#f0f0f0',font=('Segoe UI',9));self.coordlabel.pack(side='right',padx=8)
        self.history=[];self.future=[];self.tool_buttons['select'].selected(True)
        self.report_tabs.select(2)

    def select_sheet(self,event=None):
        chosen=self.component_sheet.selection()
        if chosen and chosen[0]!=self.selected:
            self.selected=chosen[0];self.render()

    def select_in_use(self,event=None):
        chosen=self.in_use.get().split(' ')[0]
        if any(p.id==chosen for p in self.doc.parts):self.selected=chosen;self.render()

    def _keys(self):
        for event,fn in [('<Control-n>',self.new),('<Control-o>',self.open),('<Control-s>',self.save),
                         ('<Control-z>',self.undo),('<Control-y>',self.redo),('<Delete>',self.delete_selected),
                         ('<F5>',self.run),('<Escape>',self.cancel),('<Control-r>',self.rotate)]:
            self.bind_all(event,lambda e,fn=fn:fn())

    def status(self,msg): self.hint.set(msg)
    def update_labels(self):
        self.title('Open Circuit Workbench — '+self.doc.title)
        self.doclabel.configure(text=self.doc.title)
        self.tree.delete(*self.tree.get_children())
        root=self.tree.insert('', 'end', iid='design', text=self.doc.title,open=True)
        for group in ['Analog','Sources','References','Others']:
            key='group_'+group
            self.tree.insert(root,'end',iid=key,text=group,open=True)
            for p in self.doc.parts:
                if ('Analog' if p.kind in ('R','C','L') else
                    'Sources' if p.kind=='V' else 'References' if p.kind=='GND' else 'Others')==group:
                    self.tree.insert(key,'end',iid=p.id,text=f'  {p.id}  {p.value}')
        current={part.id for part in self.doc.parts}
        for key in self.component_sheet.get_children():
            if key not in current:self.component_sheet.delete(key)
        for part in self.doc.parts:
            values=(part.id,part.value,part.kind,f'{part.rotation}°')
            if self.component_sheet.exists(part.id):self.component_sheet.item(part.id,values=values)
            else:self.component_sheet.insert('', 'end',iid=part.id,values=values)
        if self.selected and self.component_sheet.exists(self.selected):
            if self.component_sheet.selection()!=(self.selected,):self.component_sheet.selection_set(self.selected)
        elif self.component_sheet.selection():self.component_sheet.selection_remove(*self.component_sheet.selection())
        self.in_use['values']=[f'{p.id}  {p.value}' for p in self.doc.parts]
        self.in_use.set(next((f'{p.id}  {p.value}' for p in self.doc.parts if p.id==self.selected),''))
        self.write_panel('nets','\n'.join(f'{k[0]} pin {k[1]+1}: node {v}' for k,v in self.doc.networks().items()))

    def write_panel(self,tab,text):
        widget=getattr(self,'panel_'+tab)
        widget.config(state='normal'); widget.delete('1.0','end'); widget.insert('end',text); widget.config(state='disabled')

    def checkpoint(self):
        self.timeline=None  # prevent stale scope readings after schematic edits
        self.history.append(self.doc.to_dict())
        if len(self.history)>60: self.history.pop(0)
        self.future.clear()

    def restore(self,data):
        from .core import Part,Wire
        self.timeline=None
        self.doc=Document(data['title'], [Part(**p) for p in data['parts']], [Wire(tuple(w['a']),tuple(w['b'])) for w in data['wires']])
        self.selected=None; self.render()

    def undo(self):
        if self.history:
            self.future.append(self.doc.to_dict())
            self.restore(self.history.pop()); self.status('Undo')
    def redo(self):
        if self.future:
            self.history.append(self.doc.to_dict())
            self.restore(self.future.pop()); self.status('Redo')
    def set_mode(self,mode):
        self.mode=mode; self.pending=None;
        for key,button in self.tool_buttons.items():button.selected(key==mode)
        self.status('Click canvas to place '+mode if mode not in ('select','wire') else ('Click a pin to begin wiring; click another pin to finish' if mode=='wire' else 'Select component'))
        self.canvas.configure(cursor='crosshair' if mode!='select' else 'arrow')
        self.render()
    def cancel(self): self.set_mode('select')
    def toggle_grid(self): self.grid_visible=not self.grid_visible; self.render()
    def toggle_snap(self): self.snap_on=not self.snap_on; self.status('Grid snap '+('ON' if self.snap_on else 'OFF'))
    def zoom(self,fac):
        nxt=max(.5,min(2.0,self.scale_factor*fac))
        self.scale_factor=nxt; self.zoom_value.set(f'{nxt*100:g}%'); self.render(); self.status(f'Zoom: {int(nxt*100)}%')
    def fit(self): self.scale_factor=1; self.zoom_value.set('100%'); self.render(); self.canvas.xview_moveto(0);self.canvas.yview_moveto(0)
    def on_mousewheel(self,event):
        if event.state & 0x0004: self.zoom(1.1 if event.delta>0 else .9)
        else: self.canvas.yview_scroll(-1 if event.delta>0 else 1,'units')
    def wp(self,ev): return (snap(self.canvas.canvasx(ev.x)/self.scale_factor),snap(self.canvas.canvasy(ev.y)/self.scale_factor))
    def xp(self,pt): return tuple(v*self.scale_factor for v in pt)
    def box(self,kind,x,y):
        scale=self.scale_factor; return (x-46*scale,y-46*scale,x+46*scale,y+46*scale)
    def find_part(self,pt):
        for part in reversed(self.doc.parts):
            # Ignore pin anchors when selecting component body.
            dx,dy=abs(pt[0]-part.x),abs(pt[1]-part.y)
            if dx<=30 and dy<=30: return part
        return None
    def pin_at(self,pt):
        for p in reversed(self.doc.parts):
            for i,xy in enumerate(p.pins()):
                if math.dist(pt,xy)<=13: return p,i,xy
        return None
    def on_tree_select(self,event):
        ids=self.tree.selection()
        if ids:
            self.selected=next((p.id for p in self.doc.parts if p.id==ids[0]),None);self.render()
    def list_place(self,event):
        idx=self.parts_list.curselection()
        if idx:self.set_mode(list(PINS)[idx[0]])
    def canvas_move(self,ev):
        pt=self.wp(ev); self.coordlabel.configure(text=f'X: {pt[0]}  Y: {pt[1]}  •  Zoom: {int(self.scale_factor*100)}%')
        if self.mode in PINS:
            self.canvas.delete('placement')
            old=set(self.canvas.find_all())
            ghost=Part(self.doc.next_name(self.mode),self.mode,*pt,DEFAULTS[self.mode][0])
            self._shape(ghost)
            for item in set(self.canvas.find_all())-old:self.canvas.addtag_withtag('placement',item)
        if self.mode=='wire' and self.pending:
            self.canvas.delete('rubber')
            a=self.xp(self.pending); b=self.xp(pt)
            self.canvas.create_line(a[0],a[1],b[0],a[1],b[0],b[1],fill=RED,dash=(4,3),width=2,tags='rubber')
    def canvas_down(self,ev):
        pt=self.wp(ev)
        if self.mode=='wire':
            pin=self.pin_at(pt)
            if pin: pt=pin[2]
            if self.pending is None: self.pending=pt; self.status(f'Start wire at {pt}; click endpoint')
            else:
                self.checkpoint();self.doc.add_wire(self.pending,pt)
                self.pending=pt if not pin else None
                self.render();self.status('Wire created')
            return
        if self.mode!='select':
            self.checkpoint();p=self.doc.add(self.mode,*pt)
            self.selected=p.id;self.set_mode('select');self.render();self.status('Placed '+p.id);return
        part=self.find_part(pt)
        self.selected=part.id if part else None
        self.drag_start=pt
        if part:
            self.drag_offset=(pt[0]-part.x,pt[1]-part.y)
        else: self.drag_offset=None
        self.render()
    def canvas_drag(self,ev):
        if self.mode!='select' or not self.selected or self.drag_offset is None:return
        part=next((p for p in self.doc.parts if p.id==self.selected),None)
        if not part:return
        pt=self.wp(ev); x,y=pt[0]-self.drag_offset[0],pt[1]-self.drag_offset[1]
        x,y=snap(x),snap(y)
        if (x,y)==(part.x,part.y): return
        if not getattr(self,'_drag_checkpoint',False):
            self.checkpoint();self._drag_checkpoint=True
        old=part.pins(); part.x=x;part.y=y
        new=part.pins(); self._move_connected(old,new);self.render()
    def canvas_up(self,ev):self.drag_offset=None;self._drag_checkpoint=False;self.drag_start=None
    def _move_connected(self,old,new):
        for wire in self.doc.wires:
            if wire.a in old: wire.a=new[old.index(wire.a)]
            if wire.b in old: wire.b=new[old.index(wire.b)]
    def canvas_double(self,ev):
        p=self.find_part(self.wp(ev));
        if p:self.selected=p.id;self.properties()
    def right_click(self,ev):
        p=self.find_part(self.wp(ev));
        if p:self.selected=p.id
        menu=tk.Menu(self,tearoff=False)
        menu.add_command(label='Properties...',command=self.properties)
        menu.add_command(label='Rotate 90°',command=self.rotate)
        menu.add_separator();menu.add_command(label='Delete',command=self.delete_selected)
        menu.tk_popup(ev.x_root,ev.y_root)
    def rotate(self):
        p=next((p for p in self.doc.parts if p.id==self.selected),None)
        if p:
            self.checkpoint();old=p.pins();p.rotation=(p.rotation+90)%360
            self._move_connected(old,p.pins());self.render()
    def delete_selected(self):
        p=next((p for p in self.doc.parts if p.id==self.selected),None)
        if p:
            self.checkpoint();positions=set(p.pins())
            self.doc.parts.remove(p)
            self.doc.wires=[w for w in self.doc.wires if w.a not in positions and w.b not in positions]
            self.selected=None;self.render()
    def properties(self):
        p=next((p for p in self.doc.parts if p.id==self.selected),None)
        if not p:return
        if p.kind=='GND':return
        value=simpledialog.askstring('Component Properties',f'{p.id} — {p.kind}\nValue (use suffixes: k, m, u, n):',initialvalue=p.value,parent=self)
        if value is None:return
        if p.kind in ('R','C','L','V'):
            try: numeric(value)
            except ValueError as e:messagebox.showerror('Invalid component value',str(e));return
        self.checkpoint();p.value=value;self.render()
    def _line(self,pts,**kw):
        coords=[]
        for p in pts: coords.extend(self.xp(p))
        self.canvas.create_line(*coords,**kw)
    def _shape(self,p):
        """Draw original symbols instead of copying vendor icon artwork."""
        x,y=p.x,p.y; a=(p.rotation//90)%4
        def tf(dx,dy):
            if a==1:dx,dy=-dy,dx
            elif a==2:dx,dy=-dx,-dy
            elif a==3:dx,dy=dy,-dx
            return (x+dx,y+dy)
        def line(pts,**kw):self._line([tf(*z) for z in pts],fill=BLUE,width=max(1.25,1.6*self.scale_factor),**kw)
        kind=p.kind
        if kind=='R':
            line([(-40,0),(-22,0)]); line([(22,0),(40,0)])
            line([(-22,0),(-22,-9),(22,-9),(22,9),(-22,9),(-22,0)])
        elif kind=='C':
            line([(-40,0),(-6,0)]);line([(6,0),(40,0)])
            line([(-6,-16),(-6,16)]);line([(6,-16),(6,16)])
        elif kind=='L':
            line([(-40,0),(-22,0)]);line([(22,0),(40,0)])
            for i in range(4):
                # Four half-circle coils.
                cx=-16+i*11
                px1,py1=self.xp(tf(cx-5,-8));px2,py2=self.xp(tf(cx+5,5))
                self.canvas.create_oval(min(px1,px2),min(py1,py2),max(px1,px2),max(py1,py2),outline=BLUE,width=1.5)
        elif kind=='V':
            line([(0,-40),(0,-18)]);line([(0,18),(0,40)])
            x1,y1=self.xp(tf(-18,-18));x2,y2=self.xp(tf(18,18))
            self.canvas.create_oval(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2),outline=BLUE,width=2,fill='white')
            line([(-7,-6),(7,-6)]);line([(0,-12),(0,0)]);line([(-7,8),(7,8)])
        elif kind=='GND':
            line([(0,-20),(0,0)]);line([(-15,0),(15,0)]);line([(-10,6),(10,6)]);line([(-5,12),(5,12)])
        elif kind in ('D','LED'):
            line([(-40,0),(-14,0)]);line([(14,0),(40,0)])
            line([(-14,-12),(-14,12),(14,0),(-14,-12)])
            line([(14,-13),(14,13)])
            if kind=='LED':line([(0,-19),(13,-32)]);line([(10,-20),(23,-33)])
        elif kind=='SW':
            line([(-40,0),(-22,0)]);line([(22,0),(40,0)])
            line([(-22,0),(12,-17)])
            for xp,yp in [(-22,0),(22,0)]:
                a1,b1=self.xp(tf(xp-2,yp-2));a2,b2=self.xp(tf(xp+2,yp+2))
                self.canvas.create_oval(a1,b1,a2,b2,fill=BLUE,outline=BLUE)
        if kind != 'GND':
            # Symbols are labelled independently from schematic wires.
            labpos=tf(0,-38) if kind!='V' else tf(34,-12)
            textpos=tf(0,26) if kind!='V' else tf(36,6)
            self.canvas.create_text(*self.xp(labpos),text=p.id,anchor='center' if kind!='V' else 'w',fill=INK,font=('Segoe UI',max(8,int(10*self.scale_factor)),'bold'))
            self.canvas.create_text(*self.xp(textpos),text=p.value,anchor='center' if kind!='V' else 'w',fill=GREY,font=('Segoe UI',max(8,int(9*self.scale_factor))))
        for pt in p.pins():
            px,py=self.xp(pt);r=max(2.2,2.7*self.scale_factor)
            self.canvas.create_oval(px-r,py-r,px+r,py+r,fill=BLUE,outline='white',width=1)
        if p.id==self.selected:
            cx,cy=self.xp((x,y));r=49*self.scale_factor
            self.canvas.create_rectangle(cx-r,cy-r,cx+r,cy+r,dash=(4,3),outline='#4298d5')

    def render(self):
        self.canvas.delete('all')
        w=int(2100*self.scale_factor);h=int(1500*self.scale_factor)
        self.canvas.configure(scrollregion=(0,0,w,h))
        if self.grid_visible:
            g=int(GRID*self.scale_factor)
            if g>=8:
                for xx in range(0,w+1,g):
                    for yy in range(0,h+1,g):
                        self.canvas.create_rectangle(xx,yy,xx+0.6,yy+0.6,outline='#d3dce5')
        # NI-like worksheet origin rulers; they are original drawing commands.
        self.canvas.create_line(0,0,w,0,fill=OUTLINE)
        for x in range(0,2101,200):
            xx=x*self.scale_factor;self.canvas.create_text(xx+8,12,text=str(x//200+1),fill='#9ba9b8',font=('Segoe UI',8),anchor='w')
        for y in range(0,1501,200):
            yy=y*self.scale_factor;self.canvas.create_text(7,yy+26,text=chr(65+(y//200)%26),fill='#9ba9b8',font=('Segoe UI',8),anchor='w')
        for wi in self.doc.wires:
            a,b=wi.a,wi.b
            route=[a,(b[0],a[1]),b] if a[0]!=b[0] and a[1]!=b[1] else [a,b]
            self._line(route,fill=RED,width=max(1.4,1.7*self.scale_factor))
        # Show actual connected pin locations as red connection dots.
        points={tuple(pt) for w in self.doc.wires for pt in (w.a,w.b)}
        for p in self.doc.parts:
            for pt in p.pins():
                if pt in points:
                    x,y=self.xp(pt);self.canvas.create_oval(x-3,y-3,x+3,y+3,fill=RED,outline=RED)
        for part in self.doc.parts:self._shape(part)
        self.update_labels()

    def new(self):
        if self.doc.parts and not messagebox.askyesno('New design','Start a new empty design? Unsaved changes will be lost.'):
            return
        self.doc=Document();self.filepath=None;self.selected=None
        self.history.clear();self.future.clear();self.render();self.status('New design')
    def open(self):
        path=filedialog.askopenfilename(title='Open Circuit Workbench project',filetypes=[('Workbench project','*.ocw.json'),('JSON','*.json')])
        if not path:return
        try:self.doc=Document.load(path)
        except (OSError,ValueError,TypeError,KeyError) as e:messagebox.showerror('Cannot open',str(e));return
        self.filepath=path;self.selected=None;self.history.clear();self.future.clear();self.render();self.status('Opened '+path)
    def save(self):
        if not self.filepath:return self.save_as()
        try:self.doc.save(self.filepath);self.status('Saved '+self.filepath)
        except OSError as e:messagebox.showerror('Save failed',str(e))
    def save_as(self):
        path=filedialog.asksaveasfilename(title='Save project',defaultextension='.ocw.json',filetypes=[('Workbench project','*.ocw.json')])
        if path:self.filepath=path;self.save()
    def export_netlist(self):
        try:net=self.doc.netlist()
        except ValueError as e:messagebox.showerror('Netlist error',str(e));return
        path=filedialog.asksaveasfilename(title='Export SPICE',defaultextension='.cir',filetypes=[('SPICE circuit','*.cir')])
        if path:
            Path(path).write_text(net,encoding='utf-8');self.status('Exported '+path)
    def preview_netlist(self):
        try:contents=self.doc.netlist()
        except ValueError as e:contents=str(e)
        self.write_panel('results',contents);self.report_tabs.select(0)
    def example(self):
        self.doc=Document('RC Charging Circuit')
        v=self.doc.add('V',300,320,'5')
        r=self.doc.add('R',480,240,'1k')
        c=self.doc.add('C',660,320,'1u')
        c.rotation=90  # vertical capacitor is standard in this RC layout
        g=self.doc.add('GND',300,500)
        # Circuit drawn in a recognisably traditional schematic layout.
        self.doc.add_wire(v.pins()[0],(300,240))
        self.doc.add_wire((300,240),r.pins()[0])
        self.doc.add_wire(r.pins()[1],(660,240))
        self.doc.add_wire((660,240),c.pins()[0])
        self.doc.add_wire(c.pins()[1],(660,460))
        self.doc.add_wire((660,460),(300,460))
        self.doc.add_wire((300,460),v.pins()[1])
        self.doc.add_wire((300,460),g.pins()[0])
        for part in self.doc.parts:part.y-=80
        for wire in self.doc.wires:
            wire.a=(wire.a[0],wire.a[1]-80);wire.b=(wire.b[0],wire.b[1]-80)
        self.filepath=None;self.history.clear();self.future.clear();self.selected=None;self.timeline=None
        self.render();self.write_panel('results','Example: a 5 V DC source charges a 1 µF capacitor through 1 kΩ.\nClick ▶ Run to solve a real 240-step transient.\nDouble-click a part to change its value.')
        self.status('Ready — sample RC circuit loaded')
    def run(self):
        try:self.timeline=simulate(self.doc);self.last_nets=self.timeline[2]
        except ValueError as e:
            self.timeline=None;messagebox.showerror('Simulation error',str(e));self.write_panel('simulation','Error: '+str(e));return
        times,history,nets=self.timeline
        summary=f'Transient solved: {len(times)} samples, duration={times[-1]*1e3:.1f} ms\n'
        summary+='\n'.join(f'V({key}) = {series[-1]:.5f} V' for key,series in history.items() if key!='0')
        self.write_panel('results',summary);self.write_panel('simulation','Educational MNA / backward-Euler solver — DC voltage sources, resistors and capacitors.\nFor advanced circuits use the existing Qucs-S / ngspice engine.');self.report_tabs.select(0)
        self.status('Simulation completed');self.scope()
    def stop(self):self.status('Simulation stopped (synchronous solver is already idle)')
    def scope(self):
        if self.timeline is None:
            messagebox.showinfo('Oscilloscope','Run a valid circuit first to display measured node voltages.');return
        t,h,nets=self.timeline
        dialog=tk.Toplevel(self);dialog.title('XSC1 — Virtual Oscilloscope  |  Transient Analysis')
        dialog.geometry('920x545');dialog.configure(bg='#ccd1d6')
        toolbar=ttk.Frame(dialog);toolbar.pack(fill='x')
        ttk.Label(toolbar,text='  XSC1   Oscilloscope       Timebase: '+f'{t[-1]*1e3:.1f} ms'+'      Coupling: DC',font=('Segoe UI',10,'bold')).pack(side='left',pady=10)
        area=tk.Canvas(dialog,bg='#12191f',highlightthickness=3,highlightbackground='#81919d',width=880,height=395)
        area.pack(fill='both',expand=True,padx=14,pady=5)
        dialog.update_idletasks(); w=area.winfo_width();hgt=area.winfo_height();margin=45
        for k in range(11):
            x=margin+(w-2*margin)*k/10
            area.create_line(x,22,x,hgt-30,fill='#223943',dash=(2,4))
            area.create_text(x,hgt-15,text=f'{t[-1]*1000*k/10:.1f}',fill='#a1acb7',font=('Consolas',8))
        vals=[v for name,series in h.items() if name!='0' for v in series]
        lo=min(0,min(vals or [0]));hi=max(1,max(vals or [5]));span=hi-lo
        for k in range(7):
            y=22+(hgt-52)*k/6; area.create_line(margin,y,w-margin,y,fill='#223943',dash=(2,4))
            area.create_text(27,y,text=f'{hi-span*k/6:.1f}',fill='#a1acb7',font=('Consolas',8))
        colors=['#ffe45e','#00e4c3','#fa638e','#7fb5ff','#d7e67a']
        for i,(node,series) in enumerate((q for q in h.items() if q[0]!='0')):
            points=[]
            for j,v in enumerate(series):
                points.extend([margin+(w-2*margin)*j/(len(series)-1),22+(hi-v)/span*(hgt-52)])
            area.create_line(*points,fill=colors[i%len(colors)],width=2.2,smooth=False)
            area.create_text(75+i*116,12,text=f'CH{i+1}: V({node})',fill=colors[i%len(colors)],font=('Consolas',10,'bold'))
        ttk.Label(dialog,text='  Time (ms)                       Simulation readings — educational transient engine, not an NI instrument emulator',foreground=GREY).pack(anchor='w',padx=20,pady=8)
    def multimeter(self):
        if not self.timeline:
            messagebox.showinfo('XMM1 — Multimeter','Run a circuit to read DC node voltages.');return
        _,h,_=self.timeline
        text='\n'.join(f'Node {n}:  {values[-1]:.5f} V DC' for n,values in h.items() if n!='0')
        messagebox.showinfo('XMM1 — Virtual Multimeter',text or 'No nodes measured')
    def generator(self):messagebox.showinfo('Function Generator','The function generator is planned, but not implemented. Do not rely on its outputs yet.')
    def probe(self):
        if self.timeline:self.multimeter()
        else:messagebox.showinfo('Voltage Probe','Run the simulation to inspect node voltages.')
    def not_ready(self):messagebox.showinfo('Not implemented','This instrument is not functional in this prototype.')
    def component_browser(self):
        """Actual searchable component-picker window, styled after legacy CAD dialogs."""
        win = tk.Toplevel(self)
        win.title('Select a Component — Open Circuit Workbench')
        win.geometry('790x530')
        win.minsize(650, 430)
        win.transient(self)
        win.configure(background=BOARD)
        win.grab_set()
        top = ttk.Frame(win)
        top.pack(fill='x', padx=12, pady=(13, 7))
        ttk.Label(top, text='Database:').pack(side='left', padx=(0, 9))
        db = ttk.Combobox(top, values=['Master Database (Open Circuit Workbench)'], state='readonly', width=34)
        db.current(0); db.pack(side='left')
        ttk.Label(top, text='Search:').pack(side='left', padx=(22, 8))
        query = tk.StringVar()
        search = ttk.Entry(top, textvariable=query)
        search.pack(side='left', fill='x', expand=True)
        body = ttk.PanedWindow(win, orient=tk.HORIZONTAL)
        body.pack(fill='both', expand=True, padx=12, pady=(0, 8))
        left = ttk.Frame(body); body.add(left, weight=1)
        ttk.Label(left, text='Group / Family', font=('Segoe UI',9,'bold')).pack(anchor='w', pady=5)
        groups = tk.Listbox(left, exportselection=False, height=10, font=('Segoe UI',10),
                            bg='white', relief='groove')
        groups.pack(fill='both', expand=True)
        for name in ('All Components', 'Basic', 'Sources', 'Diodes', 'Switches'):
            groups.insert('end', name)
        groups.selection_set(0)
        mid = ttk.Frame(body); body.add(mid, weight=3)
        ttk.Label(mid, text='Component', font=('Segoe UI',9,'bold')).pack(anchor='w', pady=5)
        tree = ttk.Treeview(mid, columns=('type','default','support'), show='headings', height=10,
                            selectmode='browse')
        tree.heading('type',text='Component');tree.column('type',width=140)
        tree.heading('default',text='Default');tree.column('default',width=85)
        tree.heading('support',text='Simulation');tree.column('support',width=100)
        tree.pack(fill='both',expand=True)
        detail = ttk.Frame(win)
        detail.pack(fill='x', padx=12, pady=(0,5))
        ttk.Label(detail, text='Symbol preview:', font=('Segoe UI',9,'bold')).pack(anchor='w')
        previews = ttk.Frame(detail); previews.pack(fill='x')
        symbol = tk.Canvas(previews, width=125, height=92, bg='white', highlightthickness=1,
                           highlightbackground=OUTLINE)
        symbol.pack(side='left', padx=(0,12))
        description = tk.StringVar(value='Select a component to preview its symbol and properties.')
        ttk.Label(previews, textvariable=description, wraplength=550, justify='left').pack(side='left',fill='x',expand=True)
        catalog = [
            ('R','Resistor','Basic','Linear'), ('C','Capacitor','Basic','Linear'),
            ('L','Inductor','Basic','SPICE export only'), ('V','DC Voltage Source','Sources','Linear'),
            ('GND','Ground','Sources','Reference'), ('D','Diode','Diodes','Symbol only'),
            ('LED','Light-Emitting Diode','Diodes','Symbol only'),('SW','Switch','Switches','Symbol only')]
        by_kind = {item[0]: item for item in catalog}
        def redraw():
            group = groups.get(groups.curselection()[0]) if groups.curselection() else 'All Components'
            needle = query.get().lower().strip()
            old_selection=tree.selection()[0] if tree.selection() else None
            tree.delete(*tree.get_children())
            for kind,label,family,support in catalog:
                if (group in ('All Components',family)) and (not needle or needle in (label+' '+kind).lower()):
                    tree.insert('','end',iid=kind,values=(label,DEFAULTS[kind][0],support))
            if old_selection and tree.exists(old_selection): tree.selection_set(old_selection)
            elif tree.get_children(): tree.selection_set(tree.get_children()[0])
            preview()
        def preview(event=None):
            symbol.delete('all')
            chosen=tree.selection()
            if not chosen:
                description.set('No matching components.')
                return
            kind=chosen[0]
            name,group,support=by_kind[kind][1:]
            description.set(f'{name} ({kind})\nGroup: {group}     Default value: {DEFAULTS[kind][0] or "—"}\nStatus: {support}\nSelect Place, then click on the schematic grid.')
            symbol.create_line(12,46,112,46,fill=BLUE,width=2)
            if kind=='R':symbol.create_rectangle(39,36,85,56,outline=BLUE,fill='white',width=2)
            elif kind=='C':
                symbol.create_rectangle(56,23,59,69,outline=BLUE,fill=BLUE)
                symbol.create_rectangle(66,23,69,69,outline=BLUE,fill=BLUE)
                symbol.create_rectangle(58,35,67,57,fill='white',outline='white')
            elif kind=='V':
                symbol.create_oval(42,18,82,74,outline=BLUE,fill='white',width=2)
                symbol.create_text(62,40,text='+',fill=BLUE,font=('Consolas',14,'bold'))
            elif kind=='GND':
                symbol.delete('all');symbol.create_line(62,14,62,44,fill=BLUE,width=2)
                for y,w in [(46,34),(53,24),(60,12)]:symbol.create_line(62-w//2,y,62+w//2,y,fill=BLUE,width=2)
            elif kind=='L':
                for xx in (44,54,64,74):symbol.create_arc(xx,35,xx+14,59,start=0,extent=180,style='arc',outline=BLUE,width=2)
            elif kind in ('D','LED'):
                symbol.create_polygon(43,29,43,63,80,46,outline=BLUE,fill='white',width=2)
                symbol.create_line(80,28,80,64,fill=BLUE,width=2)
            elif kind=='SW':
                symbol.create_line(43,46,80,29,fill=BLUE,width=2)
        def choose(event=None):
            selected=tree.selection()
            if selected:
                self.set_mode(selected[0]);win.grab_release();win.destroy()
        tree.bind('<<TreeviewSelect>>',preview)
        tree.bind('<Double-1>',choose)
        groups.bind('<<ListboxSelect>>',lambda e:redraw())
        query.trace_add('write',lambda *_:redraw())
        actions=ttk.Frame(win);actions.pack(side='bottom',fill='x',padx=12,pady=(0,10))
        ttk.Button(actions,text='Cancel',command=win.destroy).pack(side='right',padx=(7,0))
        ttk.Button(actions,text='Place',command=choose).pack(side='right')
        redraw();search.focus_set()
    def project_info(self):
        messagebox.showinfo('Project Information',f'{self.doc.title}\nComponents: {len(self.doc.parts)}\nWires: {len(self.doc.wires)}\nSave format: .ocw.json\nNo NI Multisim compatibility is claimed.')
    def reset_workspace(self):self.fit();self.status('Workspace reset')
    def about(self):messagebox.showinfo('Open Circuit Workbench','Original offline schematic editor — layout inspired by publicly documented circuit design software.\nBuilt with Python standard library; not affiliated with NI/Emerson.\nQucs-S remains a separately licensed simulation/editor backend in the parent repository.')
    def shortcuts(self):messagebox.showinfo('Shortcuts','Ctrl+N New | Ctrl+O Open | Ctrl+S Save | Ctrl+Z Undo | Ctrl+Y Redo\nF5 Run | Del Delete | Ctrl+R Rotate | Esc Select\nMiddle mouse: pan | Ctrl + wheel: zoom')

if __name__=='__main__': Workbench().mainloop()