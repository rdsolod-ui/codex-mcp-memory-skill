"""Back up explicitly selected rollout files and verify bytes. Never restores or edits history."""
import argparse,hashlib,json,shutil
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def backup(files,output):
    files=[Path(p) for p in files];output=Path(output)
    if not files:raise ValueError('No rollout files selected')
    for p in files:
        if p.is_symlink() or not p.is_file() or p.suffix.lower()!='.jsonl':raise ValueError('Only explicit regular .jsonl rollout files are supported')
    resolved=[p.resolve() for p in files]
    if len(set(resolved))!=len(resolved):raise ValueError('Duplicate input')
    output.mkdir(parents=False,exist_ok=False)
    receipt=[]
    for i,p in enumerate(resolved):
        stat=p.stat();digest=sha(p);target=output/f'{i:03d}.jsonl'
        with p.open('rb') as source,target.open('xb') as destination:shutil.copyfileobj(source,destination)
        after=p.stat()
        if stat.st_size!=after.st_size or stat.st_mtime_ns!=after.st_mtime_ns or sha(p)!=digest or sha(target)!=digest:
            raise RuntimeError('History changed during backup; no valid receipt was issued. Keep partial evidence and re-evaluate chat activity.')
        receipt.append({'source':str(p),'backup':target.name,'bytes':stat.st_size,'sha256':digest})
    # Recheck the entire set before issuing a receipt.
    for row in receipt:
        if sha(Path(row['source']))!=row['sha256']:raise RuntimeError('History changed before receipt; do not unload')
    doc={'schemaVersion':1,'files':receipt,'note':'Private evidence. Keep metadata/turn/native-state receipt separately. No database snapshot is implied.'}
    with (output/'receipt.json').open('x',encoding='utf-8') as f:json.dump(doc,f,ensure_ascii=False,indent=2)
    return doc

def prefix_sha(path,size):
    h=hashlib.sha256()
    with path.open('rb') as f:
        remaining=size
        while remaining:
            block=f.read(min(1024*1024,remaining))
            if not block:return None
            h.update(block);remaining-=len(block)
    return h.hexdigest()

def verify(receipt,allow_append=False):
    receipt=Path(receipt);doc=json.loads(receipt.read_text(encoding='utf-8-sig'));results=[]
    for row in doc['files']:
        name=row['backup']
        if Path(name).name!=name:raise ValueError('Invalid backup name')
        saved=receipt.parent/name;original=Path(row['source'])
        intact=saved.is_file() and sha(saved)==row['sha256']
        unchanged=original.is_file() and sha(original)==row['sha256']
        result={'source':str(original),'backupIntact':intact,'sourceUnchanged':unchanged}
        if allow_append:
            size=row.get('bytes')
            if type(size) is not int or size<0:raise ValueError('Invalid baseline byte count')
            result['sourcePrefixUnchanged']=bool(intact and saved.stat().st_size==size and original.is_file() and prefix_sha(original,size)==row['sha256'])
        results.append(result)
    answer={'allUnchanged':bool(results) and all(x['backupIntact'] and x['sourceUnchanged'] for x in results),'files':results}
    if allow_append:
        answer['allPreserved']=bool(results) and all(x['sourcePrefixUnchanged'] for x in results)
        answer['note']='Prefix verification preserves legitimate appends; it does not verify a database, explain new content, or authorize an unload.'
    return answer

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    b=s.add_parser('backup');b.add_argument('--output',required=True,type=Path);b.add_argument('files',nargs='+',type=Path)
    v=s.add_parser('verify');v.add_argument('receipt',type=Path);v.add_argument('--allow-append',action='store_true',help='Verify intact original bytes after an independently verified legitimate new turn; no restoration');args=p.parse_args()
    result=backup(args.files,args.output) if args.command=='backup' else verify(args.receipt,args.allow_append)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.command=='verify' and not result['allPreserved' if args.allow_append else 'allUnchanged']:raise SystemExit(2)
if __name__=='__main__':main()
