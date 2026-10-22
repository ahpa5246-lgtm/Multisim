"""Run all editable course fixtures with ngspice; optionally retain full raw evidence.

python scripts/verify_course.py --output reports/course --raw
The default compact evidence preserves model-specific checks, decks and logs.
"""
import argparse,gzip,json,sys,platform
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'prototype'))
from workbench.course import EXPERIMENTS,evaluate
from workbench.spice import Engine

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('reports/course'));parser.add_argument('--raw',action='store_true');args=parser.parse_args()
    root=args.output;root.mkdir(parents=True,exist_ok=True);records=[];decks={};logs={}
    for e in EXPERIMENTS:
        d=e.document();record={'id':e.id,'title':e.title,'pages':e.pages,'analysis':e.analysis.kind,'note':e.note}
        try:
            r=Engine().run(d,e.analysis);findings=evaluate(e,d,r);record.update(checks=findings,passed=all(c['passed'] for c in findings))
            decks[e.id]=r.deck;logs[e.id]=r.log
            if args.raw:r.export(root/e.id)
        except (ValueError,OSError) as error:record.update(passed=False,error=str(error))
        records.append(record);print(('PASS ' if record['passed'] else 'FAIL ')+e.id,flush=True)
    summary={'python':platform.python_version(),'platform':platform.platform(),'engine':'Separately installed ngspice; exact solver version is in logs','passed':sum(r['passed'] for r in records),'total':len(records),'NI_reference_comparison':False,'experiments':records}
    (root/'report.json').write_text(json.dumps(summary,indent=2)+'\n')
    for name,data in [('decks',decks),('solver-logs',logs)]:
        (root/(name+'.json.gz')).write_bytes(gzip.compress((json.dumps(data,indent=2)+'\n').encode(),mtime=0))
    return 0 if all(r['passed'] for r in records) else 1
if __name__=='__main__':raise SystemExit(main())
