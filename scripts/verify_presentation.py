"""Re-run existing tests and enumerate their distinct parameterized cases.

No repetition to inflate totals. Requires a real DISPLAY and ngspice; skipped
cases fail presentation acceptance. Does not certify Windows or NI parity.
"""
import argparse
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'prototype'), str(ROOT/'prototype/tests')]
from workbench.spice import Engine


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
        self.parameterized = set()

    def record(self, case, status, detail=''):
        self.records.append(dict(case=case.id(), status=status, detail=detail))

    def addSubTest(self, test, subtest, error):
        self.parameterized.add(test.id())
        self.record(subtest, 'passed' if error is None else 'failed',
                    '' if error is None else self._exc_info_to_string(error, test))
        super().addSubTest(test, subtest, error)

    def addSuccess(self, test):
        if test.id() not in self.parameterized:
            self.record(test, 'passed')
        super().addSuccess(test)

    def addFailure(self, test, error):
        self.record(test, 'failed', self._exc_info_to_string(error, test))
        super().addFailure(test, error)

    def addError(self, test, error):
        self.record(test, 'error', self._exc_info_to_string(error, test))
        super().addError(test, error)

    def addSkip(self, test, reason):
        self.record(test, 'skipped', reason)
        super().addSkip(test, reason)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'reports/presentation')
    args = parser.parse_args()
    if not os.environ.get('DISPLAY'):
        parser.error('A real DISPLAY / Xvfb is required; GUI skips are not acceptance')
    engine = Engine()
    if not engine.executable:
        parser.error('Install ngspice before the presentation audit')
    version = subprocess.check_output([str(engine.executable), '--version'], text=True)
    suite = unittest.TestSuite()
    for folder in (ROOT/'prototype/tests', ROOT/'tests'):
        suite.addTests(unittest.TestLoader().discover(str(folder), top_level_dir=str(folder)))
    result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
    report = dict(python=platform.python_version(), platform=platform.platform(),
                  source_base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  solver_version=version, test_methods=result.testsRun,
                  count_rule='Leaf cases: subtests replace their containing method; no repeated runs counted.',
                  distinct_cases=len(result.records),
                  passed=sum(r['status']=='passed' for r in result.records),
                  skipped=sum(r['status']=='skipped' for r in result.records),
                  NI_reference_comparison=False, Windows_verified=False,
                  records=result.records)
    accepted=result.wasSuccessful() and report['skipped']==0 and report['passed']>=200
    report['accepted']=accepted
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"{report['passed']}/{report['distinct_cases']} distinct cases passed; {report['skipped']} skipped")
    return 0 if accepted else 1


if __name__=='__main__':
    raise SystemExit(main())
