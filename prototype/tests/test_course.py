"""Course topology regressions run with the real separately installed ngspice."""
import os,shutil,tempfile,unittest,json
from pathlib import Path
from workbench.core import Document,PINS
from workbench.course import EXPERIMENTS,BY_ID,evaluate
from workbench.spice import Engine,Analysis,compile_deck,source_value
from workbench.devices import MODELS

class CourseDocumentTests(unittest.TestCase):
    def test_named_nets_persist_and_do_not_join_different_names(self):
        d=BY_ID['inverting'].document();nets=d.networks()
        aliases={}
        for p in d.parts:
            if p.kind=='NET':aliases.setdefault(p.value,set()).add(nets[(p.id,0)])
        self.assertTrue(all(len(v)==1 for v in aliases.values()))
        self.assertEqual(len({next(iter(v)) for v in aliases.values()}),len(aliases))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'lab.ocw.json';d.save(p);loaded=Document.load(p)
            self.assertEqual(loaded.to_dict(),d.to_dict());self.assertEqual(loaded.networks(),nets)
    def test_invalid_saved_alias_rejected_before_load(self):
        data=BY_ID['ohms-law'].document().to_dict()
        next(p for p in data['parts'] if p['kind']=='NET')['value']='bad\nname'
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'invalid.ocw.json';path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'Invalid net alias'):Document.load(path)
    def test_unknown_diode_model_does_not_silently_become_generic(self):
        d=BY_ID['zener'].document();diode=next(p for p in d.parts if p.kind=='D')
        diode.value='Course_Zener5V1x'
        with self.assertRaisesRegex(ValueError,'Unknown diode model'):compile_deck(d,Analysis(kind='op'))
    def test_explicit_ac_input_is_not_supply(self):
        e=BY_ID['npn-frequency'];deck,*_=compile_deck(e.document(),e.analysis)
        self.assertIn('VVCC 1 0 DC 15 AC 0',deck)
        self.assertIn('SIN(0 0.005 1000) AC 1',deck)
        with self.assertRaises(ValueError):compile_deck(e.document(),Analysis(kind='ac',ac_source='missing'))
    def test_triangle_has_explicit_nonzero_width(self):
        out=source_value('PULSE(-1 1 0 500u 500u 0 1m)')
        nums=list(map(float,out[out.index('(')+1:out.index(')')].split()))
        self.assertGreater(nums[5],0);self.assertAlmostEqual(sum(nums[3:6]),nums[6])
    def test_course_fixtures_cover_every_chapter_and_required_family(self):
        self.assertEqual(len(EXPERIMENTS),len(BY_ID))
        for kind in ('NPN','PNP','NJF','PJF','NMOS','PMOS','SCR','TRIAC','DIAC','IGBT','POT','I','OPAMP'):
            self.assertTrue(any(kind==part[1] for e in EXPERIMENTS for part in e.components),kind)
        for e in EXPERIMENTS:
            self.assertTrue(e.checks,e.id)
            for _,kind,_,nodes in e.components:self.assertEqual(len(PINS[kind]),len(nodes),e.id)
    def test_potentiometer_and_alias_invalid_values_rejected(self):
        d=BY_ID['pot-divider'].document();pot=next(p for p in d.parts if p.kind=='POT')
        for v in ('10k:2','-1:0.5','1k:nan','oops'):
            pot.value=v
            with self.assertRaises(ValueError):compile_deck(d,Analysis(kind='op'))
        label=next(p for p in d.parts if p.kind=='NET');label.value='bad\nname'
        with self.assertRaises(ValueError):d.networks()

@unittest.skipUnless(shutil.which('ngspice') or os.environ.get('OCW_NGSPICE'),'Requires ngspice')
class CourseSolverTests(unittest.TestCase):
    def test_all_course_experiments(self):
        for e in EXPERIMENTS:
            with self.subTest(experiment=e.id):
                d=e.document();r=Engine().run(d,e.analysis);findings=evaluate(e,d,r)
                self.assertTrue(all(c['passed'] for c in findings),findings)
    def test_new_pinned_models_load_in_solver(self):
        from workbench.course import F,V,R
        from workbench.core import Part
        for name,model in MODELS.items():
            if not (model['source'].endswith(('JFETs.lib','MOSFETs.lib','Diodes.lib'))):continue
            with self.subTest(model=name):
                kind=model['kind'];sign=-1 if kind.startswith('P') else 1
                e=BY_ID['current-source']
                from workbench.course import Experiment
                if kind=='D':parts=[V('V1','in','0',1),R('R1','in','out','1k'),('D1','D',name,('out','0'))]
                else:parts=[F(kind,name),V('VDS','out','0',10*sign),V('VGS','gate','0',3*sign if 'MOS' in kind else 0),R('RS','source','0','1m')]
                d=Experiment('model','Model smoke','','',parts,Analysis(kind='op'),[]).document()
                result=Engine().run(d,Analysis(kind='op'));self.assertTrue(result.voltages)
