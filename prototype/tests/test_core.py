import math
import tempfile
import unittest
from pathlib import Path
from workbench.core import Document, numeric, simulate


def make_rc():
    d = Document('RC charging')
    v = d.add('V',100,180,'5')
    r = d.add('R',220,140,'1k')
    c = d.add('C',380,220,'1u')
    g = d.add('GND',100,340)
    d.add_wire(v.pins()[0], (100,140)); d.add_wire((100,140),r.pins()[0])
    d.add_wire(r.pins()[1],(380,140)); d.add_wire((380,140),c.pins()[0])
    d.add_wire(c.pins()[1],(380,320)); d.add_wire((380,320),(100,320))
    d.add_wire((100,320),v.pins()[1]); d.add_wire((100,320),g.pins()[0])
    return d,v,r,c,g

class WorkbenchTests(unittest.TestCase):
    def test_units(self):
        self.assertAlmostEqual(numeric('1k'),1000)
        self.assertAlmostEqual(numeric('1u'),1e-6)
        self.assertAlmostEqual(numeric('2.2meg'),2.2e6)
    def test_roundtrip(self):
        doc,*_ = make_rc()
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'workbench.json'; doc.save(path)
            loaded = Document.load(path)
        self.assertEqual(doc.to_dict(),loaded.to_dict())
    def test_network_and_netlist(self):
        d,v,r,c,g = make_rc(); nets=d.networks()
        self.assertEqual(nets[(v.id,1)],'0')
        self.assertEqual(nets[(c.id,1)],'0')
        self.assertEqual(nets[(r.id,1)],nets[(c.id,0)])
        net=d.netlist(); self.assertIn('R1',net); self.assertIn('.tran',net)
    def test_rc_response(self):
        d,v,r,c,g=make_rc()
        times,hist,nets=simulate(d, duration=.005,steps=1000)
        node=nets[(c.id,0)]
        self.assertAlmostEqual(hist[node][0],0.0,delta=.05)
        self.assertAlmostEqual(hist[node][200],5*(1-math.exp(-1)),delta=.02)
        self.assertGreater(hist[node][-1],4.9)
    def test_missing_ground(self):
        d=Document(); d.add('V',100,100)
        with self.assertRaisesRegex(ValueError,'ground'): simulate(d)
    def test_crossing_not_connected(self):
        d=Document(); a=d.add('R',100,100); b=d.add('R',300,100)
        d.add_wire((120,120),(280,120)); d.add_wire((200,60),(200,180))
        self.assertNotEqual(d.networks()[(a.id,0)],d.networks()[(b.id,0)])

if __name__=='__main__': unittest.main()
