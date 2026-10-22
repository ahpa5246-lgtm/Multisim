import os,shutil,tempfile,unittest
from pathlib import Path
from workbench.core import Document
from workbench.spice import Engine,Analysis

def transistor(kind='NPN',model='BC547B'):
    d=Document('BJT bias');q=d.add(kind,500,300,model)
    sign=1 if kind=='NPN' else -1
    vc=d.add('V',700,220,str(sign*5));vb=d.add('V',300,260,str(sign*.65));g=d.add('GND',800,520)
    def wire(*points):
        for a,b in zip(points,points[1:]):d.add_wire(a,b)
    wire(q.pins()[0],(520,180),vc.pins()[0]);wire(vc.pins()[1],(800,260),g.pins()[0])
    wire(vb.pins()[0],(460,220),q.pins()[1]);wire(vb.pins()[1],(200,300),(200,500),g.pins()[0])
    wire(q.pins()[2],(520,500),g.pins()[0])
    return d,q,vc

def follower(model='LM358'):
    d=Document('Op-amp follower');q=d.add('OPAMP',500,300,model)
    vi=d.add('V',200,260,'.2');vp=d.add('V',700,200,'15');vn=d.add('V',900,260,'-15');g=d.add('GND',800,520)
    def wire(*pts):
        for a,b in zip(pts,pts[1:]):d.add_wire(a,b)
    wire(vi.pins()[0],(400,220),(400,280),q.pins()[0]);wire(vi.pins()[1],(200,500),g.pins()[0])
    wire(vp.pins()[0],(500,160),q.pins()[2]);wire(vp.pins()[1],(800,240),g.pins()[0])
    wire(vn.pins()[0],(1000,220),(1000,400),(500,400),q.pins()[3]);wire(vn.pins()[1],(900,500),g.pins()[0])
    wire(q.pins()[4],(600,300),(600,440),(400,440),(400,320),q.pins()[1])
    return d,q

@unittest.skipUnless(os.environ.get('OCW_NGSPICE') or shutil.which('ngspice'),'Requires ngspice')
class DeviceTests(unittest.TestCase):
    def test_npn_pnp_bias(self):
        for kind,model in [('NPN','BC547B'),('PNP','BC557B')]:
            d,q,vc=transistor(kind,model);r=Engine().run(d,Analysis(kind='op'))
            self.assertGreater(abs(r.currents[vc.id][0]),1e-6)
            self.assertLess(abs(r.currents[vc.id][0]),1)
    def test_opamp_follower(self):
        for model in ('LM358','LM324','NE5532'):
            d,q=follower(model);r=Engine().run(d,Analysis(kind='op'))
            self.assertAlmostEqual(r.voltages[r.nets[(q.id,4)]][0],.2,delta=.02)
    def test_dc_sweep(self):
        d,q,vc=transistor();r=Engine().run(d,Analysis(kind='dc',sweep_source=vc.id,sweep_start=0,sweep_stop=5,sweep_step=.1))
        self.assertAlmostEqual(r.axis[-1],5,places=5)
        self.assertEqual(len(r.axis),51)
    def test_every_adapted_bjt_has_solver_smoke_check(self):
        from workbench.devices import MODELS
        count=0
        for name,model in MODELS.items():
            if model['kind'] not in ('NPN','PNP'):continue
            with self.subTest(model=name):
                d,q,v=transistor(model['kind'],name);r=Engine().run(d,Analysis(kind='op'))
                self.assertEqual(len(r.axis),1)
                count+=1
        self.assertGreater(count,450)

class PersistenceTests(unittest.TestCase):
    def test_multiterminal_save_and_rotate(self):
        d,q=follower();old=q.pins();q.rotation=90
        self.assertEqual(len(q.pins()),5);self.assertNotEqual(old,q.pins())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'circuit.json';d.save(p);restored=Document.load(p)
        self.assertEqual(d.to_dict(),restored.to_dict())
    def test_library_femto_conversion(self):
        from workbench.devices import MODELS
        self.assertAlmostEqual(MODELS['2DA1774R']['parameters']['Is'],15.2e-15,delta=1e-25)

@unittest.skipUnless(os.environ.get('OCW_NGSPICE') or shutil.which('ngspice'),'Requires ngspice')
class DiodeConnectionTests(unittest.TestCase):
    def test_collector_base_tie_is_valid(self):
        for kind,model in [('NPN','BC547B'),('PNP','BC557B')]:
            d,q,vc=transistor(kind,model);d.parts.remove(vc)
            d.add_wire(q.pins()[0],q.pins()[1])
            out=Engine().run(d,Analysis(kind='op'))
            self.assertEqual(out.nets[(q.id,0)],out.nets[(q.id,1)])
