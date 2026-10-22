"""Read-only Electronics Workbench container metadata inspector.

Format registry/header/section layout adapted from electronics-workbench-decoder
cb9c13bc6131488bf0c6ac15505d54b4a7e3aa2a, Cameron Tacklind (C) 2021–2026, ISC.
Full notice: data/COPYING.ew-decoder. This does not decode XML or map circuits.
"""
import hashlib,json,stat,os
from pathlib import Path
FORMATS=((b'MSMCompressedElectronicsWorkbenchXML','Multisim compressed XML'),
         (b'CompressedElectronicsWorkbenchXML','Electronics Workbench compressed XML'),
         (b'\x00\x01\x00\x00Standard Jet DB','Jet component database'))

def inspect_container(path):
    path=Path(path)
    with path.open('rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError('Inspector requires a regular file')
        data=stream.read(64*1024*1024+1)
    if len(data)>64*1024*1024:raise ValueError('Inspector limit: 64 MiB')
    report={'filename':path.name,'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                                'format':'Unknown','signature_hex':data[:40].hex(),'circuit_mapping':'Not performed','original_modified':False}
    for header,name in FORMATS:
        if not data.startswith(header):continue
        report['format']=name
        if name=='Jet component database':return report
        pos=len(header)
        if len(data)<pos+8:raise ValueError('Truncated decompressed-length field')
        total=int.from_bytes(data[pos:pos+8],'little');pos+=8;decoded=0;sections=[]
        while decoded<total:
            if len(sections)>=4096:raise ValueError("Inspector limit: 4096 sections")
            if len(data)<pos+8:raise ValueError('Truncated section header')
            length=int.from_bytes(data[pos:pos+4],'little');compressed=int.from_bytes(data[pos+4:pos+8],'little');pos+=8
            if not length or not compressed or length>total-decoded or compressed>len(data)-pos:raise ValueError('Invalid section bounds')
            sections.append({'offset':pos,'compressed_bytes':compressed,'declared_decompressed_bytes':length})
            pos+=compressed;decoded+=length
        report.update(declared_xml_bytes=total,sections=sections,trailing_bytes=len(data)-pos)
        return report
    return report

def save_report(source, target, contents):
    source, target = Path(source), Path(target)
    if source.resolve() == target.resolve() or (target.exists() and source.samefile(target)):
        raise ValueError("Choose a separate report file; the inspected original must be preserved")
    target.write_text(contents+"\n", encoding="utf-8")

def inspect_dialog(app):
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    from . import theme
    path=filedialog.askopenfilename(title='Inspect EW/Multisim container (read only)',parent=app)
    if not path:return
    try:report=inspect_container(path)
    except (OSError,ValueError) as e:messagebox.showerror('Container inspection',str(e),parent=app);return
    win=tk.Toplevel(app);win.title('File Format Inspector — Read Only');win.geometry('820x580');win.transient(app)
    ttk.Label(win,text='Container metadata only. No XML decompression, circuit conversion or NI roundtrip validation.',wraplength=780).pack(fill='x',padx=12,pady=12)
    text=tk.Text(win,font=(theme.MONO,10),bg='white',relief='flat');text.pack(fill='both',expand=True,padx=12,pady=4)
    contents=json.dumps(report,indent=2);text.insert('end',contents);text.configure(state='disabled')
    def save():
        target=filedialog.asksaveasfilename(parent=win,title='Save inspection report',defaultextension='.json')
        if target:
            try:save_report(path,target,contents)
            except (OSError,ValueError) as e:messagebox.showerror('Save report',str(e),parent=win)
    ttk.Button(win,text='Save report...',command=save).pack(anchor='e',padx=12,pady=12)
