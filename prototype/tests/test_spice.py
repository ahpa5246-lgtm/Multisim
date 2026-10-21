import math, os, shutil, tempfile, unittest
from pathlib import Path
from test_core import make_rc
try:
    from workbench.spice import Analysis, Engine, compile_deck, source_value
except ImportError:
    Analysis=Engine=compile_deck=source_value=None

class CompilerTests(unittest.TestCase):
    def test_directives_rejected(self):
        self.assertIsNotNone(source_value,'ngspice adapter is missing')
        for value in ('5\n.control\nquit','SIN(0 1 1k) .include foo','nan','inf','PULSE(0 1 0 0 0 1 0)'):
            with self.assertRaises(ValueError):source_value(value)
    def test_missing_solver_is_error(self):
        self.assertIsNotNone(Engine,'ngspice adapter is missing')
        with self.assertRaisesRegex(ValueError,'ngspice'):
            Engine('/nonexistent/ngspice').run(make_rc()[0],Analysis())
    def test_invalid_range(self):
        self.assertIsNotNone(Analysis,'analysis settings are missing')
        for a in (Analysis(duration=0),Analysis(points=0),Analysis(start=1e3,stop=10),Analysis(duration=float('nan'))):
            with self.assertRaises(ValueError):compile_deck(make_rc()[0],a)

@unittest.skipUnless(shutil.which('ngspice') or os.environ.get('OCW_NGSPICE'),'ngspice integration requires executable')
class NgspiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Engine,'ngspice adapter is missing')
        self.engine=Engine(os.environ.get('OCW_NGSPICE'))
    def test_rc_and_evidence(self):
        d,v,r,c,g=make_rc();out=self.engine.run(d,Analysis(duration=.005,points=500))
        node=out.nets[(c.id,0)];i=min(range(len(out.axis)),key=lambda i:abs(out.axis[i]-.001))
        self.assertAlmostEqual(out.voltages[node][i],5*(1-math.exp(-1)),delta=.025)
        with tempfile.TemporaryDirectory() as tmp:
            out.export(Path(tmp))
            self.assertTrue((Path(tmp)/'circuit.cir').is_file())
            self.assertTrue((Path(tmp)/'samples.csv').is_file())
    def test_dc_divider(self):
        d,v,r,c,g=make_rc();c.kind='R';c.id='R2';c.value='1k'
        out=self.engine.run(d,Analysis(kind='op'))
        self.assertAlmostEqual(out.voltages[out.nets[('R2',0)]][0],2.5,places=5)
    def test_rl(self):
        d,v,r,c,g=make_rc();c.kind='L';c.id='L1';c.value='1';r.value='1k'
        out=self.engine.run(d,Analysis(duration=.005,points=500))
        vals=out.voltages[out.nets[('L1',0)]]
        i=min(range(len(out.axis)),key=lambda i:abs(out.axis[i]-.001))
        self.assertAlmostEqual(vals[i],5*math.exp(-1),delta=.03)
    def test_diode_is_nonlinear(self):
        d,v,r,c,g=make_rc();c.kind='D';c.id='D1';c.value='1N4148'
        out=self.engine.run(d,Analysis(kind='op'))
        voltage=out.voltages[out.nets[('D1',0)]][0]
        self.assertGreater(voltage,.5);self.assertLess(voltage,.9)
    def test_switch_states(self):
        d,v,r,c,g=make_rc();c.kind='SW';c.id='S1';c.value='Open'
        a=self.engine.run(d,Analysis(kind='op'));c.value='Closed';b=self.engine.run(d,Analysis(kind='op'))
        self.assertGreater(a.voltages[a.nets[('S1',0)]][0],4.99)
        self.assertLess(b.voltages[b.nets[('S1',0)]][0],.001)
    def test_ac_cutoff(self):
        d,v,r,c,g=make_rc();f=1/(2*math.pi*1000*1e-6)
        out=self.engine.run(d,Analysis(kind='ac',start=f,stop=f*10,points=10))
        vin=out.voltages[out.nets[(v.id,0)]][0];vout=out.voltages[out.nets[(c.id,0)]][0]
        self.assertAlmostEqual(abs(vout/vin),1/math.sqrt(2),places=5)
        self.assertAlmostEqual(math.degrees(__import__('cmath').phase(vout/vin)),-45,places=4)
    def test_sine_source(self):
        d,v,r,c,g=make_rc();v.value='SIN(0 2 1000)'
        out=self.engine.run(d,Analysis(duration=.003,points=600))
        series=out.voltages[out.nets[(v.id,0)]]
        self.assertGreater(max(series),1.99);self.assertLess(min(series),-1.99)

class ResultValidationTests(unittest.TestCase):
    def test_malformed_or_nonfinite_table(self):
        from workbench.spice import parse_table
        for table in ('time v1\n0 nan\n','time v1\n0 1 2\n','time v1\n1 2\n0 3\n','time v1\n'):
            with self.assertRaises(ValueError):parse_table(table,1)
    @unittest.skipIf(os.name=='nt','POSIX executable fixture')
    def test_running_process_can_be_cancelled(self):
        import sys,threading,time
        self.assertIsNotNone(Engine)
        with tempfile.TemporaryDirectory() as tmp:
            executable=Path(tmp)/'slow-engine'
            executable.write_text(f'#!{sys.executable}\nimport time\ntime.sleep(10)\n')
            executable.chmod(0o700);engine=Engine(str(executable));errors=[]
            def run():
                try:engine.run(make_rc()[0],Analysis())
                except ValueError as e:errors.append(str(e))
            thread=threading.Thread(target=run);thread.start()
            until=time.monotonic()+2
            while engine._process is None and time.monotonic()<until:time.sleep(.005)
            engine.cancel();thread.join(2)
            self.assertFalse(thread.is_alive());self.assertTrue(any('cancelled' in e for e in errors))
