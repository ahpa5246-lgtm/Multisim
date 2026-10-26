"""Multisim-inspired offline desktop circuit workbench (original Tkinter UI).

Run: python -m workbench.app
Requires Python 3.10+ and Tcl/Tk, no external packages.
"""
from __future__ import annotations
import math
import os
import sys
import tkinter as tk
from . import theme
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from .toolbar import ToolButton
from .instruments import Instruments
from .spice import Analysis, source_value, compile_deck
from .core import Document, Part, PINS, DEFAULTS, GRID, numeric, snap, simulate, PIN_LABELS

# Neutral Windows-CAD palette, based on the documented Multisim workspace anatomy.
# Original drawing primitives and existing simulation features are retained.
PAPER = '#ffffff'; INK = '#20252c'; BLUE = '#16449c'; RED = '#c02737'
GREY = '#526071'; BOARD = '#e4e8ed'; OUTLINE = '#b3bdc9'; PALE = '#f4f6f9'
CHROME = '#edf0f4'; BAR = '#e6eaf0'; HEADER = '#d6e0ec'; ACCENT = '#265795'

class Workbench(Instruments, tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Open Circuit Workbench — Design1')
        self.geometry('1460x900'); self.minsize(1050,680)
        self.configure(background=BOARD)
        self.doc = Document()
        self.filepath = None
        self.mode = 'select'; self.selected = None
        self.pending = None; self.drag_offset=None; self.drag_start=None
        self.clipboard = None
        self.scale_factor = 1.0
        self.timeline = None; self.last_nets = None
        self.result=None;self.analysis=Analysis();self._job=None;self.ngspice_path=None
        self.protocol("WM_DELETE_WINDOW",self.close_workbench)
        theme.configure(self)
        self._make_style(); self._make_menu(); self._make_layout(); self._keys()
        self.example()

    def _make_style(self):
        style = ttk.Style(self)
        # Clam gives consistent CAD-like dividers on both Windows and Linux;
        # retaining native ttk widgets keeps menus and assistive access usable.
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        style.configure('.', font=(theme.FAMILY, 9))
        style.configure('TFrame', background=BOARD)
        style.configure('TLabel', background=BOARD, foreground=INK)
        style.configure('TButton', font=(theme.FAMILY, 9), padding=(8, 4),
                        background=CHROME, foreground=INK, relief='raised')
        style.map('TButton', background=[('active', '#dae5f1'), ('pressed', '#c4d7ec')])
        style.configure('TPanedwindow', background=OUTLINE)
        style.configure('Sash', sashthickness=5)
        style.configure('TNotebook', background=BOARD, borderwidth=0)
        style.configure('TNotebook.Tab', padding=(12, 5),
                        background='#e4e9ef', foreground='#475368')
        style.map('TNotebook.Tab',
                  background=[('selected', '#ffffff'), ('active', '#f5f8fd')],
                  foreground=[('selected', '#173e71')])
        style.configure('Treeview', font=(theme.FAMILY, 9), rowheight=24,
                        background='#ffffff', fieldbackground='#ffffff',
                        foreground='#26364b', bordercolor='#c8d1de')
        style.configure('Treeview.Heading', font=(theme.FAMILY, 9, 'bold'),
                        background='#e5ebf2', foreground='#2e405a',
                        padding=(7, 5), relief='flat')
        style.map('Treeview', background=[('selected', '#cce0f7')],
                  foreground=[('selected', '#173554')])
        style.configure('TCombobox', padding=3)
        style.map('TCombobox', fieldbackground=[('readonly', '#ffffff')])

    def _make_menu(self):
        menu=tk.Menu(self)
        items={
            'File':[('New',self.new),('Open...',self.open),('Save',self.save),('Save As...',self.save_as),('Export SPICE Netlist...',self.export_netlist),None,('Exit',self.close_workbench)],
            'Edit':[('Undo',self.undo),('Redo',self.redo),None,('Delete Selected',self.delete_selected),('Rotate Selected',self.rotate),('Properties',self.properties)],
            'View':[('Zoom In',lambda:self.zoom(1.25)),('Zoom Out',lambda:self.zoom(.8)),('Zoom to Fit',self.fit),('Show Grid',self.toggle_grid)],
            'Place':[('Component... (Ctrl+W)',self.component_browser),('Net Alias',lambda:self.set_mode('NET')),('Current Source',lambda:self.set_mode('I')),('Potentiometer',lambda:self.set_mode('POT')),('Resistor',lambda:self.set_mode('R')),('Capacitor',lambda:self.set_mode('C')),('Inductor',lambda:self.set_mode('L')),('DC Voltage',lambda:self.set_mode('V')),('Ground',lambda:self.set_mode('GND')),('Diode',lambda:self.set_mode('D')),('LED',lambda:self.set_mode('LED')),('Switch',lambda:self.set_mode('SW')),None,('Wire',lambda:self.set_mode('wire'))],
            'Simulate':[('Run Transient',self.run),('DC Operating Point',self.dc_analysis),('DC Sweep / I–V...',self.dc_sweep),('AC Sweep / Bode',self.bode),('Analysis Settings...',self.analysis_settings),('Stop',self.stop),None,('Oscilloscope',self.scope),('Multimeter',self.multimeter),('Function Generator',self.generator),('Logic Traces',self.logic),('Voltage Spectrum',self.spectrum_panel),('Export Simulation Data...',self.export_results),None,('Load RC Example',self.example),('Load AM Example 1',lambda:self.load_demo('am-example1.ocw.json')),('Load Op-Amp Example',lambda:self.load_demo('opamp-follower.ocw.json')),('Load Transistor Example',lambda:self.load_demo('bjt-characteristic.ocw.json'))],
            'Tools':[('Course Experiments...',self.course_browser),('Check Experiment Results',self.check_experiment),('Components Browser',self.component_browser),('Inspect EW/Multisim Container...',self.inspect_container),('Project Information',self.project_info),('Electrical Rule Check',lambda:self.report_tabs.select(6))],
            'Reports':[('Netlist Preview',self.preview_netlist)],
            'Options':[('Grid Snap',self.toggle_snap),('Locate ngspice executable...',self.locate_ngspice)],
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
        # On X11 without a window manager the native menu can be omitted from
        # captured client-area screenshots. Provide an accessible in-window
        # menu strip on non-Windows hosts; Windows retains its native menu.
        if sys.platform != 'win32':
            menustrip=tk.Frame(self,bg=CHROME,bd=1,relief='raised')
            menustrip.pack(side='top',fill='x')
            for caption, commands in items.items():
                btn=tk.Menubutton(menustrip,text=caption,bg=CHROME,fg='#243c59',
                                  activebackground='#d4e3f5',activeforeground='#193d67',
                                  relief='flat',bd=0,padx=9,pady=3,
                                  font=(theme.FAMILY,9),direction='below')
                submenu=tk.Menu(btn,tearoff=False)
                for pair in commands:
                    if pair is None:
                        submenu.add_separator()
                    else:
                        submenu.add_command(label=pair[0],command=pair[1])
                btn.configure(menu=submenu)
                btn.pack(side='left')

    def _tool(self, parent, icon, command, label, key=None, disabled=False, vertical=False):
        button=ToolButton(parent,icon,command,label,disabled)
        button.pack(side='top' if vertical else 'left',padx=1,pady=1)
        if key:self.tool_buttons[key]=button
        return button

    def _separator(self,parent):
        tk.Frame(parent,width=1,bg='#b7c3d1').pack(side='left',fill='y',padx=6,pady=5)

    def _quick_component(self, parent, text, kind):
        """Labeled shortcuts complement the original vector component toolbar."""
        button = tk.Button(parent, text=text, command=lambda k=kind:self.set_mode(k),
                           font=(theme.FAMILY, 9), bg=CHROME, fg='#244263',
                           activebackground='#d2e3f7', activeforeground='#173c70',
                           relief='groove', bd=1, padx=9, pady=2, cursor='hand2')
        button.pack(side='left', padx=2, pady=3)
        return button

    def _make_layout(self):
        self.tool_buttons={}
        head=tk.Frame(self,bg=CHROME,bd=1,relief='raised');head.pack(fill='x')
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
        self._tool(head,'run',self.run_selected,'Run selected analysis (F5)')
        self._tool(head,'stop',self.stop,'Stop ngspice simulation')
        self.analysis_mode=tk.StringVar(value='Transient')
        self.analysis_choice=ttk.Combobox(head,textvariable=self.analysis_mode,values=['Transient','DC Operating Point','AC Sweep','DC Sweep'],state='readonly',width=20)
        self.analysis_choice.pack(side='left',padx=8)
        ttk.Button(head,text='Experiments',command=self.course_browser).pack(side='left',padx=4)
        self.hint=tk.StringVar(value='Ready')
        second=tk.Frame(self,bg=CHROME,bd=1,relief='raised');second.pack(fill='x')
        self._tool(second,'select',self.cancel,'Select (Esc)',key='select')
        self._tool(second,'wire',lambda:self.set_mode('wire'),'Place wire',key='wire')
        self._separator(second)
        self._tool(second,'catalog',self.component_browser,'Select a component')
        for kind,label in [('V','DC voltage source'),('GND','Ground'),('R','Resistor'),('C','Capacitor'),
                           ('L','Inductor'),('D','Diode - selected library model'),('LED','LED — generic electrical model'),('SW','Static open/closed switch')]:
            self._tool(second,kind,lambda k=kind:self.set_mode(k),label,key=kind)
        self._separator(second)
        self._tool(second,'rotate',self.rotate,'Rotate selected (Ctrl+R)')
        self._tool(second,'probe',self.probe,'Read simulated node voltages')
        tk.Label(second,text='In Use:',bg=CHROME,fg='#3b4d61',font=(theme.FAMILY,9)).pack(side='left',padx=(16,4))
        self.in_use=ttk.Combobox(second,state='readonly',width=22);self.in_use.pack(side='left',padx=4)
        self.in_use.bind('<<ComboboxSelected>>',self.select_in_use)
        # Multisim's classic component toolbar is separate from the standard
        # and simulation toolbars. Every shortcut below places a real part.
        placebar = tk.Frame(self, bg=BAR, bd=1, relief='groove')
        placebar.pack(fill='x')
        tk.Label(placebar, text='PLACE', bg=BAR, fg='#405673',
                 font=(theme.FAMILY, 8, 'bold')).pack(side='left', padx=(10, 9))
        for label, kind in [('Resistor', 'R'), ('Capacitor', 'C'),
                            ('Inductor', 'L'), ('BJT NPN', 'NPN'),
                            ('BJT PNP', 'PNP'), ('MOSFET', 'NMOS'),
                            ('Op-Amp', 'OPAMP'), ('Current', 'I'),
                            ('Potentiometer', 'POT'), ('Net Alias', 'NET')]:
            self._quick_component(placebar, label, kind)
        ttk.Button(placebar, text='Select Component…',
                   command=self.component_browser).pack(side='right', padx=8, pady=2)
        body=ttk.PanedWindow(self,orient=tk.HORIZONTAL);body.pack(fill='both',expand=True)
        left=ttk.Frame(body,width=224);body.add(left,weight=0)
        title=tk.Frame(left,bg=HEADER,bd=1,relief='groove');title.pack(fill='x')
        tk.Frame(title, bg=ACCENT, width=4).pack(side='left',fill='y')
        tk.Label(title,text='Design Toolbox',bg=HEADER,fg='#213c5c',
                 font=(theme.FAMILY,9,'bold'),anchor='w').pack(fill='x',padx=9,pady=6)
        tools=ttk.Notebook(left);tools.pack(fill='both',expand=True)
        project=ttk.Frame(tools);tools.add(project,text='Project')
        self.project_tree=ttk.Treeview(project,show='tree',selectmode='browse')
        self.project_tree.pack(fill='both',expand=True)
        self.project_tree.bind('<Double-1>', self._project_open)
        hierarchy=ttk.Frame(tools);tools.add(hierarchy,text='Hierarchy')
        self.tree=ttk.Treeview(hierarchy,show='tree',selectmode='browse');self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self.on_tree_select)
        components=ttk.Frame(tools);tools.add(components,text='Components')
        self.parts_list=tk.Listbox(components,relief='flat',bg='white',fg='#233958',selectbackground='#bfd9f7',selectforeground='#173554',font=(theme.FAMILY,9),highlightthickness=0)
        self.parts_list.pack(fill='both',expand=True);self.parts_list.bind('<Double-Button-1>',self.list_place)
        self.palette_kinds=['IPROBE','R','C','L','V','I','GND','D','LED','SW','POT','NPN','PNP','NJF','PJF','NMOS','PMOS','SCR','TRIAC','DIAC','IGBT','OPAMP','NET']
        for kind in self.palette_kinds:self.parts_list.insert('end',kind+'  '+DEFAULTS[kind][0])
        middle=ttk.Frame(body);body.add(middle,weight=5)
        docbar=tk.Frame(middle,bg='#d8e0ea',height=31,bd=1,relief='groove');docbar.pack(fill='x')
        tk.Label(docbar,text='▦',bg='#d8e0ea',fg=ACCENT,font=(theme.FAMILY,11)).pack(side='left',padx=(8,4))
        self.doclabel=tk.Label(docbar,text='Design1',bg='#ffffff',fg='#183a66',
                               font=(theme.FAMILY,9,'bold'),padx=14,pady=4,relief='ridge',bd=1)
        self.doclabel.pack(side='left',padx=(0,0),pady=(3,0))
        tk.Label(docbar,text='Schematic capture',bg='#d8e0ea',fg='#596a80',
                 font=(theme.FAMILY,9)).pack(side='left',padx=14)
        tk.Label(docbar,text=f'Grid: {GRID}  •  Sheet 1 / 1',bg='#d8e0ea',
                 fg='#596a80',font=(theme.FAMILY,8)).pack(side='right',padx=12)
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
        sheet_title=tk.Frame(results_frame,bg=HEADER,bd=1,relief='groove');sheet_title.pack(fill='x')
        tk.Frame(sheet_title,bg=ACCENT,width=4).pack(side='left',fill='y')
        tk.Label(sheet_title,text='Spreadsheet View',anchor='w',bg=HEADER,fg='#213c5c',
                 font=(theme.FAMILY,9,'bold'),padx=10,pady=4).pack(side='left')
        self.sheet_summary=tk.StringVar(value='4 components')
        tk.Label(sheet_title,textvariable=self.sheet_summary,bg=HEADER,fg='#566780',
                 font=(theme.FAMILY,8)).pack(side='right',padx=10)
        results=ttk.Notebook(results_frame,height=118);results.pack(fill='both',expand=True);self.report_tabs=results
        for label in ['Results','Nets','Components','Simulation','Models','BOM','Diagnostics']:
            f=ttk.Frame(results);results.add(f,text=label)
            if label=='Components':
                self.component_sheet=ttk.Treeview(f,columns=('ref','value','type','rotation'),show='headings',selectmode='browse',height=4)
                for col,title,width in [('ref','RefDes',100),('value','Value',160),('type','Component',180),('rotation','Rotation',100)]:
                    self.component_sheet.heading(col,text=title);self.component_sheet.column(col,width=width,anchor='w')
                self.component_sheet.pack(fill='both',expand=True)
                self.component_sheet.bind('<<TreeviewSelect>>',self.select_sheet)
                self.component_sheet.bind('<Double-1>',lambda e:self.properties())
            else:
                t=tk.Text(f,height=4,wrap='word',font=(theme.MONO,9),bg='white',fg=INK,relief='flat',padx=5,pady=4)
                t.pack(fill='both',expand=True);t.config(state='disabled');setattr(self,'panel_'+label.lower(),t)
        right=tk.Frame(body,width=41,bg=CHROME,bd=1,relief='raised');body.add(right,weight=0)
        tk.Label(right,text='INSTR.',bg='#dce5f0',fg='#3f587a',
                 font=(theme.FAMILY,7,'bold'),padx=3,pady=5).pack(side='top',fill='x')
        for icon,cmd,label,disabled in [('meter',self.multimeter,'Multimeter: simulated DC node readings',False),
                ('scope',self.scope,'Oscilloscope: transient node voltages',False),('generator',self.generator,'Function generator: configure voltage source',False),
                ('bode',self.bode,'Bode: AC small-signal analysis',False),('logic',self.logic,'Logic traces: threshold sampled analog voltages',False),('spectrum',self.spectrum_panel,'Sampled voltage spectrum',False),
                ('probe',self.probe,'Read simulated node voltages',False)]:self._tool(right,icon,cmd,label,disabled=disabled,vertical=True)
        bottom=tk.Frame(self,bg='#e7edf3',bd=1,relief='sunken');bottom.pack(side='bottom',fill='x',before=body)
        tk.Label(bottom,textvariable=self.hint,bg='#e7edf3',fg='#33465d',anchor='w',
                 font=(theme.FAMILY,9)).pack(side='left',padx=8,pady=4)
        tk.Label(bottom,text='OCW  |  ngspice',bg='#e7edf3',fg='#536981',
                 font=(theme.FAMILY,8)).pack(side='right',padx=9)
        self.coordlabel=tk.Label(bottom,text='X: 0  Y: 0',bg='#e7edf3',
                                 fg='#2d4768',font=(theme.MONO,9))
        self.coordlabel.pack(side='right',padx=9)
        tk.Frame(bottom,bg='#bac9db',width=1).pack(side='right',fill='y',pady=2)
        self.history=[];self.future=[];self.tool_buttons['select'].selected(True)
        self.report_tabs.select(2)
        tools.select(project)

    def _project_open(self, event=None):
        selected = self.project_tree.selection()
        if not selected:
            return
        if selected[0] == 'project_components':
            self.report_tabs.select(2)
        elif selected[0] == 'project_netlist':
            self.preview_netlist()
        elif selected[0] == 'project_schematic':
            self.canvas.focus_set()
            self.fit()

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
                         ('<F5>',self.run_selected),('<Escape>',self.cancel),('<Control-r>',self.rotate),('<Control-w>',self.component_browser)]:
            self.bind_all(event,lambda e,fn=fn:fn())

    def status(self,msg): self.hint.set(msg)
    def update_labels(self):
        self.title('Open Circuit Workbench — '+self.doc.title)
        self.doclabel.configure(text=self.doc.title)
        self.sheet_summary.set(f'{len(self.doc.parts)} components  •  {len(self.doc.wires)} wires')
        # The project navigator is a real shortcut into existing views.
        self.project_tree.delete(*self.project_tree.get_children())
        pid=self.project_tree.insert('', 'end', iid='project_design',
                                     text='▣  '+self.doc.title, open=True)
        self.project_tree.insert(pid,'end',iid='project_schematic',text='▦  Schematic1')
        self.project_tree.insert(pid,'end',iid='project_components',text='▤  Component list')
        self.project_tree.insert(pid,'end',iid='project_netlist',text='≡  SPICE netlist')
        self.tree.delete(*self.tree.get_children())
        root=self.tree.insert('', 'end', iid='design', text=self.doc.title,open=True)
        for group in ['Analog','Sources','References','Others']:
            key='group_'+group
            self.tree.insert(root,'end',iid=key,text=group,open=True)
            for p in self.doc.parts:
                if ('Analog' if p.kind in ('R','C','L') else
                    'Sources' if p.kind in ('V','I') else 'References' if p.kind in ('GND','NET') else 'Others')==group:
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
        from .devices import MODELS
        from collections import Counter
        self.write_panel('models','\n\n'.join(f'{p.id}: {p.value} — {MODELS[p.value]["source"]}\n{MODELS[p.value]["description"]}' for p in self.doc.parts if p.value in MODELS))
        counts=Counter((p.kind,p.value) for p in self.doc.parts if p.kind not in ('NET','GND'))
        self.write_panel('bom','Quantity  Type  Value / Model\n'+'\n'.join(f'{count:8}  {kind:6}  {value}' for (kind,value),count in sorted(counts.items())))
        nets=self.doc.networks();physical={p.id for p in self.doc.parts if p.kind!='NET'};contacts=Counter(node for (ref,_),node in nets.items() if ref in physical);warnings=[]
        if '0' not in contacts:warnings.append('ERROR: missing ground reference')
        for (part,pin),node in nets.items():
            if part in physical and contacts[node]==1:warnings.append(f'WARNING: {part} pin {pin+1} is the only component terminal on node {node}')
        self.write_panel('diagnostics','\n'.join(warnings) or 'No isolated terminals detected. This connectivity check does not validate models, ratings or circuit function.')


    def write_panel(self,tab,text):
        widget=getattr(self,'panel_'+tab)
        widget.config(state='normal'); widget.delete('1.0','end'); widget.insert('end',text); widget.config(state='disabled')

    def checkpoint(self):
        self.timeline=None;self.result=None
        if self._job is not None:self.stop()  # discard stale results after an edit
        self.history.append(self.doc.to_dict())
        if len(self.history)>60: self.history.pop(0)
        self.future.clear()

    def restore(self,data):
        from .core import Part,Wire
        self.timeline=None;self.result=None
        if self._job is not None:self.stop()
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
        self.mode=mode; self.pending=None;self.placement_value=None;
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
        if idx:self.set_mode(self.palette_kinds[idx[0]])
    def canvas_move(self,ev):
        pt=self.wp(ev); self.coordlabel.configure(text=f'X: {pt[0]}  Y: {pt[1]}  •  Zoom: {int(self.scale_factor*100)}%')
        if self.mode in PINS:
            self.canvas.delete('placement')
            old=set(self.canvas.find_all())
            ghost=Part(self.doc.next_name(self.mode),self.mode,*pt,getattr(self,'placement_value',None) or DEFAULTS[self.mode][0])
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
            self.checkpoint();p=self.doc.add(self.mode,*pt,value=getattr(self,'placement_value',None))
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
        turn=0
        if len(old)>1:
            before=math.atan2(old[1][1]-old[0][1],old[1][0]-old[0][0]);after=math.atan2(new[1][1]-new[0][1],new[1][0]-new[0][0])
            turn=round(math.degrees(after-before)/90)*90
        for alias in self.doc.parts:
            if alias.kind=='NET' and (alias.x,alias.y) in old:
                alias.x,alias.y=new[old.index((alias.x,alias.y))]
                alias.rotation=(alias.rotation+turn)%360
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
        value=simpledialog.askstring('Component Properties',f'{p.id} — {p.kind}\nPins: {PIN_LABELS.get(p.kind, "1 / 2")}\n'+('Total ohms:position (0 to 1)' if p.kind=='POT' else 'Value / exact library model (suffixes k, m, u, n):'),initialvalue=p.value,parent=self)
        if value is None:return
        if p.kind in ('R','C','L','V'):
            try: source_value(value) if p.kind=='V' else numeric(value)
            except ValueError as e:messagebox.showerror('Invalid component value',str(e));return
        from .devices import device_model
        import re
        try:
            if p.kind=='NET' and not re.fullmatch(r'(?:[A-Za-z_][A-Za-z0-9_]*|0)',value):raise ValueError('Use a net name or 0')
            if p.kind in ('NPN','PNP','NJF','PJF','NMOS','PMOS','OPAMP','SCR','TRIAC','DIAC','IGBT'):device_model(p.kind,value)
        except ValueError as e:messagebox.showerror('Component Properties',str(e),parent=self);return
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
        if kind=='NET':
            line([(0,0),(40,0)])
            self.canvas.create_text(*self.xp(tf(46,0)),text=p.value,anchor={0:'w',1:'n',2:'e',3:'s'}[a],fill=BLUE,font=(theme.FAMILY,max(8,int(9*self.scale_factor))))
            return
        if kind in ('R','POT'):
            # Original ANSI zig-zag resistor glyph. Terminals stay at +/-40
            # so changing the visual representation never changes net geometry.
            line([(-40,0),(-22,0)])
            line([(-22,0),(-17,-9),(-11,9),(-5,-9),(1,9),
                  (7,-9),(13,9),(19,-9),(22,0)])
            line([(22,0),(40,0)])
            if kind=='POT':
                line([(0,40),(0,11)],arrow='last')
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
        elif kind in ('V','I'):
            line([(0,-40),(0,-18)]);line([(0,18),(0,40)])
            x1,y1=self.xp(tf(-18,-18));x2,y2=self.xp(tf(18,18))
            self.canvas.create_oval(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2),outline=BLUE,width=2,fill='white')
            if kind=='I':line([(0,-10),(0,10)],arrow='last')
            else:line([(-7,-6),(7,-6)]);line([(0,-12),(0,0)]);line([(-7,8),(7,8)])
        elif kind=='IPROBE':
            line([(-40,0),(40,0)],arrow='last')
        elif kind=='GND':
            line([(0,-20),(0,0)]);line([(-15,0),(15,0)]);line([(-10,6),(10,6)]);line([(-5,12),(5,12)])
        elif kind in ('D','LED'):
            line([(-40,0),(-14,0)]);line([(14,0),(40,0)])
            line([(-14,-12),(-14,12),(14,0),(-14,-12)])
            line([(14,-13),(14,13)])
            if kind=='LED':line([(0,-19),(13,-32)]);line([(10,-20),(23,-33)])
        elif kind in ('NPN','PNP'):
            line([(-40,0),(-12,0)]);line([(-12,-20),(-12,20)])
            line([(-12,-14),(20,-30),(20,-40)])
            line([(-12,14),(20,30),(20,40)])
            line([(5,23),(16,28)] if kind=='NPN' else [(12,26),(-5,17)],arrow='last')
        elif kind in ('NJF','PJF','NMOS','PMOS','IGBT'):
            line([(-40,0),(-16,0)]);line([(-16,-20),(-16,20)])
            line([(-8,-20),(-8,20)]);line([(-8,-18),(20,-18),(20,-40)]);line([(-8,18),(20,18),(20,40)])
            line([(0,18),(15,18)],arrow='last' if kind in ('NJF','NMOS','IGBT') else 'first')
            if kind in ('NMOS','PMOS'):line([(-8,0),(40,0)])
        elif kind in ('SCR','TRIAC','DIAC'):
            if kind=='DIAC':
                line([(-40,0),(-15,0)]);line([(15,0),(40,0)])
                line([(-15,-12),(-15,12),(5,0),(-15,-12)]);line([(15,-12),(15,12),(-5,0),(15,-12)])
            else:
                line([(0,-40),(0,-15)]);line([(0,15),(0,40)]);line([(-40,20),(0,15)])
                line([(-12,-15),(12,-15),(0,15),(-12,-15)]);line([(-12,15),(12,15)])
                if kind=='TRIAC':line([(18,15),(30,-15),(6,-15),(18,15)])
        elif kind=='OPAMP':
            line([(-35,-40),(-35,40),(40,0),(-35,-40)])
            line([(-60,-20),(-35,-20)]);line([(-60,20),(-35,20)]);line([(40,0),(60,0)])
            line([(0,-60),(0,-22)]);line([(0,60),(0,22)])
            line([(-29,-20),(-19,-20)]);line([(-24,-25),(-24,-15)]);line([(-29,20),(-19,20)])
        elif kind=='SW':
            line([(-40,0),(-22,0)]);line([(22,0),(40,0)])
            line([(-22,0),(22,0) if p.value.lower()=='closed' else (12,-17)])
            for xp,yp in [(-22,0),(22,0)]:
                a1,b1=self.xp(tf(xp-2,yp-2));a2,b2=self.xp(tf(xp+2,yp+2))
                self.canvas.create_oval(a1,b1,a2,b2,fill=BLUE,outline=BLUE)
        if kind != 'GND':
            # Symbols are labelled independently from schematic wires.
            labpos=tf(0,-78) if kind=='OPAMP' else tf(0,-38) if kind!='V' else tf(34,-12)
            textpos=tf(0,78) if kind=='OPAMP' else tf(0,64) if kind in PIN_LABELS else tf(0,26) if kind!='V' else tf(36,6)
            self.canvas.create_text(*self.xp(labpos),text=p.id,anchor='center' if kind!='V' else 'w',fill=INK,font=(theme.FAMILY,max(8,int(10*self.scale_factor)),'bold'))
            self.canvas.create_text(*self.xp(textpos),text=p.value,anchor='center' if kind!='V' else 'w',fill=GREY,font=(theme.FAMILY,max(8,int(9*self.scale_factor))))
        for pt in p.pins():
            px,py=self.xp(pt);r=max(2.2,2.7*self.scale_factor)
            self.canvas.create_oval(px-r,py-r,px+r,py+r,fill=PAPER,outline=BLUE,width=1,tags='terminal')
        if p.id==self.selected:
            cx,cy=self.xp((x,y));r=49*self.scale_factor
            self.canvas.create_rectangle(cx-r,cy-r,cx+r,cy+r,dash=(4,3),outline='#4298d5')

    def render(self):
        self.canvas.delete('all')
        docw=max(2100,max((p.x+160 for p in self.doc.parts),default=0));doch=max(1500,max((p.y+160 for p in self.doc.parts),default=0))
        w=int(docw*self.scale_factor);h=int(doch*self.scale_factor)
        self.canvas.configure(scrollregion=(0,0,w,h))
        if self.grid_visible:
            g=int(GRID*self.scale_factor)
            if g>=8:
                for xx in range(0,w+1,g):
                    for yy in range(0,h+1,g):
                        self.canvas.create_rectangle(xx,yy,xx+1,yy+1,outline='#cfd7e2',fill='#cfd7e2',width=0,tags='worksheet_grid')
        # NI-like worksheet origin rulers; they are original drawing commands.
        self.canvas.create_line(0,0,w,0,fill=OUTLINE)
        for x in range(0,int(docw)+1,200):
            xx=x*self.scale_factor;self.canvas.create_text(xx+8,12,text=str(x//200+1),fill='#9ba9b8',font=(theme.FAMILY,8),anchor='w')
        for y in range(0,int(doch)+1,200):
            yy=y*self.scale_factor;self.canvas.create_text(7,yy+26,text=chr(65+(y//200)%26),fill='#9ba9b8',font=(theme.FAMILY,8),anchor='w')
        for wi in self.doc.wires:
            a,b=wi.a,wi.b
            route=[a,(b[0],a[1]),b] if a[0]!=b[0] and a[1]!=b[1] else [a,b]
            self._line(route,fill=RED,width=max(1.4,1.7*self.scale_factor))
        for part in self.doc.parts:self._shape(part)
        # Connection junctions must be painted *after* the symbols so terminal
        # circles cannot obscure the red electrical connection indicators.
        points={tuple(pt) for w in self.doc.wires for pt in (w.a,w.b)}
        for p in self.doc.parts:
            for pt in p.pins():
                if pt in points:
                    px,py=self.xp(pt)
                    self.canvas.create_oval(px-3,py-3,px+3,py+3,fill=RED,outline=RED,
                                            tags='junction')
        self.update_labels()

    def new(self):
        if self.doc.parts and not messagebox.askyesno('New design','Start a new empty design? Unsaved changes will be lost.'):
            return
        self.result=None;self.timeline=None;self.stop()
        self.doc=Document();self.filepath=None;self.selected=None
        self.history.clear();self.future.clear();self.render();self.status('New design')
    def open(self):
        path=filedialog.askopenfilename(title='Open Circuit Workbench project',filetypes=[('Workbench project','*.ocw.json'),('JSON','*.json')])
        if not path:return
        try:self.doc=Document.load(path)
        except (OSError,ValueError,TypeError,KeyError) as e:messagebox.showerror('Cannot open',str(e));return
        self.result=None;self.timeline=None;self.stop()
        self.filepath=path;self.selected=None;self.history.clear();self.future.clear();self.render();self.status('Opened '+path)
    def save(self):
        if not self.filepath:return self.save_as()
        try:self.doc.save(self.filepath);self.status('Saved '+self.filepath)
        except OSError as e:messagebox.showerror('Save failed',str(e))
    def save_as(self):
        path=filedialog.asksaveasfilename(title='Save project',defaultextension='.ocw.json',filetypes=[('Workbench project','*.ocw.json')])
        if path:self.filepath=path;self.save()
    def export_netlist(self):
        try:net=compile_deck(self.doc,self.analysis)[0]
        except ValueError as e:messagebox.showerror('Netlist error',str(e));return
        path=filedialog.asksaveasfilename(title='Export SPICE',defaultextension='.cir',filetypes=[('SPICE circuit','*.cir')])
        if path:
            Path(path).write_text(net,encoding='utf-8');self.status('Exported '+path)
    def preview_netlist(self):
        try:contents=compile_deck(self.doc,self.analysis)[0]
        except ValueError as e:contents=str(e)
        self.write_panel('results',contents);self.report_tabs.select(0)
    def example(self):
        self.analysis=Analysis();self.analysis_mode.set('Transient')
        self.result=None;self.stop()
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
        self.render();self.write_panel('results','Example: a 5 V DC source charges a 1 µF capacitor through 1 kΩ.\nClick Run to solve with ngspice. Use Simulate for DC/AC analysis.\nDouble-click a part to change its value.')
        self.status('Ready — sample RC circuit loaded')
    def load_demo(self,name):
        try:document=Document.load(Path(__file__).resolve().parents[2]/'examples'/name)
        except (OSError,ValueError) as e:messagebox.showerror('Example',str(e),parent=self);return
        self.stop();self.doc=document;self.result=None;self.timeline=None;self.filepath=None;self.selected=None
        self.history.clear();self.future.clear();self.cancel()
        if name=='am-example1.ocw.json':
            self.analysis=Analysis(kind='tran',duration=1,points=5000)
            self.analysis_mode.set('Transient')
        self.render()
        self.status('Loaded '+document.title+' — Run Transient, then Oscilloscope')
    def course_browser(self):
        from .course_ui import browser
        browser(self)
    def check_experiment(self):
        from .course_ui import check_experiment
        check_experiment(self)
    def run_selected(self):
        mode=self.analysis_mode.get()
        if mode=='DC Operating Point':self.dc_analysis()
        elif mode=='AC Sweep':self.bode()
        elif mode=='DC Sweep':
            if self.analysis.kind=='dc':self.start_analysis(self.analysis,self.dc_plot)
            else:self.dc_sweep()
        else:self.run()
    def inspect_container(self):
        from .interop import inspect_dialog
        inspect_dialog(self)
    def component_browser(self):
        from .library_ui import component_browser
        component_browser(self)
    def project_info(self):
        messagebox.showinfo('Project Information',f'{self.doc.title}\nComponents: {len(self.doc.parts)}\nWires: {len(self.doc.wires)}\nSave format: .ocw.json\nNo NI Multisim compatibility is claimed.')
    def reset_workspace(self):self.fit();self.status('Workspace reset')
    def about(self):messagebox.showinfo('Open Circuit Workbench','Original offline schematic editor — layout inspired by publicly documented circuit design software.\nBuilt with Python standard library; not affiliated with NI/Emerson.\nQucs-S remains a separately licensed simulation/editor backend in the parent repository.')
    def shortcuts(self):messagebox.showinfo('Shortcuts','Ctrl+N New | Ctrl+O Open | Ctrl+S Save | Ctrl+Z Undo | Ctrl+Y Redo\nF5 Run | Del Delete | Ctrl+R Rotate | Esc Select\nMiddle mouse: pan | Ctrl + wheel: zoom')

if __name__=='__main__': Workbench().mainloop()