"""Small keyboard-accessible CAD controls; original vector artwork, no font icons."""
import tkinter as tk
from . import theme

CHROME = '#edf0f4'
ACTIVE = '#d3e3f7'
BORDER = '#a6b9cf'

class ToolButton(tk.Canvas):
    def __init__(self, parent, icon, command, label, disabled=False):
        super().__init__(parent,width=30,height=28,background=CHROME,
                         bd=0,highlightthickness=1,highlightbackground=CHROME,
                         takefocus=not disabled, cursor='arrow' if disabled else 'hand2')
        self.command=command; self.disabled=disabled; self.tip=None; self.timer=None
        self.label=label; self.active=False
        self.draw(icon, '#9da3aa' if disabled else '#234e83')
        self.bind('<Enter>',self.enter); self.bind('<Leave>',self.leave)
        self.bind('<Button-1>',lambda e:self.invoke())
        self.bind('<Return>',lambda e:self.invoke());self.bind('<space>',lambda e:self.invoke())
        self.bind('<FocusIn>',lambda e:self.configure(highlightbackground='#7ca4cb'))
        self.bind('<FocusOut>',lambda e:self.configure(highlightbackground=CHROME))
    def invoke(self):
        if not self.disabled:return self.command()
    def selected(self,value):
        self.active=value
        self.configure(bg=ACTIVE if value else CHROME,
                       highlightbackground=BORDER if value else CHROME)
    def enter(self,event):
        if self.disabled:
            return
        self.configure(bg='#dfe9f6',highlightbackground=BORDER)
        if self.timer:
            self.after_cancel(self.timer)
        self.timer=self.after(600,self.show_tip)
    def show_tip(self):
        self.timer=None
        if self.tip or not self.winfo_exists():
            return
        self.tip=tk.Toplevel(self);self.tip.overrideredirect(True)
        self.tip.geometry(f'+{self.winfo_rootx()+12}+{self.winfo_rooty()+29}')
        tk.Label(self.tip,text=self.label,bg='#ffffe1',fg='#222',relief='solid',bd=1,
                 font=(theme.FAMILY,9),padx=5,pady=3).pack()
    def leave(self,event):
        if self.timer:self.after_cancel(self.timer);self.timer=None
        if self.tip:self.tip.destroy();self.tip=None
        self.selected(self.active)
    def draw(self,kind,c):
        def line(*p,**kw):self.create_line(*p,fill=c,width=1.5,**kw)
        def rect(*p,**kw):self.create_rectangle(*p,outline=c,**kw)
        if kind=='new':
            self.create_polygon(7,3,17,3,21,7,21,22,7,22,fill='white',outline=c)
            line(17,3,17,8,21,8)
        elif kind=='open':
            self.create_polygon(3,8,11,8,13,5,23,5,23,21,3,21,fill='#ffdf85',outline=c)
            self.create_polygon(3,12,25,12,21,21,3,21,fill='#ffedb3',outline=c)
        elif kind=='save':
            rect(5,3,23,22,fill='#6f9cca');rect(9,3,19,10,fill='white');rect(9,15,19,22,fill='white')
        elif kind in ('undo','redo'):
            self.create_arc(7,6,23,23,start=0 if kind=='undo' else 0,extent=250,style='arc',outline=c,width=2)
            line(*( (5,10,7,5,12,7) if kind=='undo' else (18,7,23,5,25,10)))
        elif kind=='run':self.create_polygon(9,4,22,13,9,22,fill='#219241',outline='#176f2e')
        elif kind=='stop':rect(7,6,21,20,fill='#b44340')
        elif kind=='wire':line(4,21,12,21,12,6,24,6);rect(2,19,6,23);rect(22,4,26,8)
        elif kind=='select':self.create_polygon(8,3,8,21,13,16,17,23,20,21,16,14,23,13,fill='#333',outline='white')
        elif kind=='R':line(3,13,7,13,9,8,12,18,15,8,18,18,21,13,26,13)
        elif kind=='C':line(3,13,11,13);line(11,5,11,21);line(17,5,17,21);line(17,13,25,13)
        elif kind=='L':
            line(2,15,6,15);line(23,15,27,15)
            for x in (6,12,18):self.create_arc(x,7,x+7,22,start=0,extent=180,style='arc',outline=c,width=1.5)
        elif kind in ('D','LED'):
            line(2,13,25,13);self.create_polygon(9,6,9,20,18,13,fill='#f0f0f0',outline=c);line(19,5,19,21)
            if kind=='LED':line(18,5,23,1,arrow='last')
        elif kind=='SW':line(2,17,8,17,21,6);line(21,17,27,17)
        elif kind=='GND':
            line(14,3,14,12)
            for y,w in ((13,18),(17,12),(21,6)):line(14-w/2,y,14+w/2,y)
        elif kind=='V':
            self.create_oval(6,5,22,21,outline=c,width=1.5);line(14,1,14,5);line(14,21,14,25);line(11,10,17,10);line(14,7,14,13);line(11,17,17,17)
        elif kind in ('scope','bode','logic','meter','generator','probe','spectrum'):
            # Distinct ORIGINAL instrument pictograms; these all open actual
            # working instrument panels, never decorative placeholders.
            if kind=='meter':
                rect(4,3,25,24,fill='#f9fcff')
                self.create_text(14.5,11,text='V',font=(theme.FAMILY,10,'bold'),fill=c)
                line(8,17,21,17)
                self.create_oval(9,19,11,21,fill='#c22b34',outline='#c22b34')
                self.create_oval(19,19,21,21,fill='#202b40',outline='#202b40')
            elif kind=='generator':
                self.create_oval(4,3,24,23,fill='#fbfdff',outline=c,width=1.5)
                line(6,14,9,14,11,8,14,8,17,19,20,19,22,13)
                line(24,13,29,13)
            elif kind=='probe':
                line(6,22,20,7)
                self.create_oval(17,4,24,11,outline=c,width=1.5)
                self.create_oval(2,21,7,26,fill='#b52c39',outline=c)
            else:
                rect(3,4,26,23,fill='#f9fcff')
                line(6,19,23,19);line(6,7,6,19)
                if kind=='scope':
                    line(7,14,10,14,12,9,15,10,18,17,21,15,23,12)
                elif kind=='bode':
                    line(7,17,10,16,13,13,16,11,19,9,23,8)
                elif kind=='logic':
                    line(7,17,10,17,10,9,15,9,15,17,20,17,20,10,23,10)
                elif kind=='spectrum':
                    for xx, top in ((9,15),(13,10),(17,7),(21,13)):
                        line(xx,19,xx,top)
        elif kind in ('zoom_in','zoom_out','fit'):
            self.create_oval(4,3,18,17,outline=c,width=1.5);line(17,16,24,23);line(7,10,15,10)
            if kind=='zoom_in':line(11,6,11,14)
            if kind=='fit':rect(1,1,25,24)
        elif kind=='rotate':
            self.create_arc(5,4,23,22,start=10,extent=290,style='arc',outline=c,width=1.5);line(18,3,24,5,23,11)
        elif kind=='grid':
            for x in (6,14,22):
                for y in (5,13,21):rect(x,y,x+1,y+1,fill=c)
        elif kind=='delete':
            rect(8,7,21,22);line(5,5,24,5);line(11,2,18,2);line(12,10,12,19);line(17,10,17,19)
        else:
            rect(5,4,23,22)
            for y in (8,13,18):line(8,y,20,y)
