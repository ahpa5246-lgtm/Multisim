"""Consistent native desktop type and neutral CAD controls across platforms."""
import tkinter.font as font
FAMILY='Segoe UI'
MONO='Consolas'

def configure(root):
    global FAMILY,MONO
    available={name.lower():name for name in font.families(root)}
    FAMILY=next((available[n.lower()] for n in ('Segoe UI','Tahoma','Arial','Liberation Sans','DejaVu Sans') if n.lower() in available),font.nametofont('TkDefaultFont').actual('family'))
    MONO=next((available[n.lower()] for n in ('Consolas','Liberation Mono','DejaVu Sans Mono') if n.lower() in available),FAMILY)
    for name in ('TkDefaultFont','TkTextFont','TkMenuFont','TkHeadingFont','TkCaptionFont','TkSmallCaptionFont','TkIconFont','TkTooltipFont'):
        font.nametofont(name).configure(family=FAMILY,size=9)
    font.nametofont('TkFixedFont').configure(family=MONO,size=9)
    root.option_add('*Font',(FAMILY,9))
