"""Compare read-only snapshots by PID AND creation time; never terminates processes."""
import argparse,json
from pathlib import Path

def identity(row):return row['pid'],row['createdUtc']
def compare(before,after,cohort=None):
    if (before['rootPid'],before['rootCreatedUtc'])!=(after['rootPid'],after['rootCreatedUtc']):
        raise ValueError('Root changed: snapshots are not comparable')
    b={identity(p):p for p in before['rows']};a={identity(p):p for p in after['rows']}
    selected=set(b) if cohort is None else {identity(p) for p in cohort}
    if not selected<=b.keys():raise ValueError('Cohort contains an identity absent from the before snapshot')
    retired=[b[k] for k in sorted(selected-a.keys())]
    return {'schemaVersion':1,'atBefore':before['at'],'atAfter':after['at'],
            'cohortWasExplicit':cohort is not None,'exitedCount':len(retired),
            'exitedBaselinePrivateMiB':round(sum(p['privateBytes'] for p in retired)/1048576,3),
            'beforePrivateMiB':round(sum(p['privateBytes'] for p in b.values())/1048576,3),
            'afterPrivateMiB':round(sum(p['privateBytes'] for p in a.values())/1048576,3),
            'newIdentityCount':len(a.keys()-b.keys()),'retired':retired,
            'interpretation':'Observed private committed memory of exited identities. Not unique physical RAM. Not causal savings without independent ownership and action evidence. Missing rows may reflect sampling races; confirm each exit separately.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('--cohort',type=Path);p.add_argument('--output',type=Path);args=p.parse_args()
    read=lambda f:json.loads(f.read_text(encoding='utf-8-sig'))
    result=compare(read(args.before),read(args.after),read(args.cohort) if args.cohort else None)
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        with args.output.open('x',encoding='utf-8') as f:f.write(text+'\n')
    else:print(text)
if __name__=='__main__':main()
