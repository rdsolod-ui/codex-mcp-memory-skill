import importlib.util,tempfile,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'skills/codex-mcp-memory/scripts'
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
compare=load('compare').compare;history=load('history_guard')
def snap(rows,root='root-start'):
    return {'rootPid':1,'rootCreatedUtc':root,'at':'test','rows':rows}
def row(pid,created='a',size=1048576):return {'pid':pid,'createdUtc':created,'privateBytes':size}
class CompareTests(unittest.TestCase):
    def test_pid_reuse_is_exit_plus_new_identity(self):
        result=compare(snap([row(2)]),snap([row(2,'b')]),[row(2)])
        self.assertEqual(result['exitedCount'],1);self.assertEqual(result['newIdentityCount'],1)
    def test_live_cohort_not_counted_as_freed(self):
        result=compare(snap([row(2),row(3)]),snap([row(2)]),[row(2)])
        self.assertEqual(result['exitedBaselinePrivateMiB'],0)
    def test_unrelated_exit_excluded(self):
        result=compare(snap([row(2),row(3,size=50000000)]),snap([]),[row(2)])
        self.assertEqual(result['exitedBaselinePrivateMiB'],1)
    def test_root_restart_refused(self):
        with self.assertRaises(ValueError):compare(snap([]),snap([],root='new'))
    def test_unknown_cohort_refused(self):
        with self.assertRaises(ValueError):compare(snap([]),snap([]),[row(3)])
class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.source=self.root/'history.jsonl';self.source.write_text('{"message":"Пример"}\n',encoding='utf-8')
    def tearDown(self):self.tmp.cleanup()
    def test_backup_verify_and_detect_append_without_restore(self):
        output=self.root/'backup';history.backup([self.source],output)
        self.assertTrue(history.verify(output/'receipt.json')['allUnchanged'])
        with self.source.open('a',encoding='utf-8') as f:f.write('{"new":true}\n')
        self.assertFalse(history.verify(output/'receipt.json')['allUnchanged']);self.assertIn('new',self.source.read_text())
    def test_backup_tamper_detected(self):
        output=self.root/'backup';history.backup([self.source],output);(output/'000.jsonl').write_text('changed')
        self.assertFalse(history.verify(output/'receipt.json')['allUnchanged'])
    def test_existing_output_refused(self):
        output=self.root/'backup';output.mkdir()
        with self.assertRaises(FileExistsError):history.backup([self.source],output)
    def test_duplicate_input_refused(self):
        with self.assertRaises(ValueError):history.backup([self.source,self.source],self.root/'backup')
    def test_database_input_refused(self):
        db=self.root/'live.sqlite';db.write_bytes(b'data')
        with self.assertRaises(ValueError):history.backup([db],self.root/'backup')
    def test_path_traversal_receipt_refused(self):
        receipt=self.root/'receipt.json';receipt.write_text(json.dumps({'files':[{'backup':'../secret','source':str(self.source),'sha256':'bad'}]}))
        with self.assertRaises(ValueError):history.verify(receipt)
    def test_explicit_append_verification_preserves_original_utf8_bytes(self):
        output=self.root/'backup';history.backup([self.source],output)
        with self.source.open('ab') as f:f.write('{"new":"Продолжение"}\n'.encode('utf-8'))
        result=history.verify(output/'receipt.json',allow_append=True)
        self.assertTrue(result['allPreserved']);self.assertFalse(result['allUnchanged'])
        self.assertFalse(history.verify(output/'receipt.json')['allUnchanged'])
    def test_append_mode_rejects_changed_prefix_and_truncation(self):
        output=self.root/'backup';history.backup([self.source],output)
        baseline=self.source.read_bytes()
        self.source.write_bytes(b'!'+baseline[1:]+b'new turn')
        self.assertFalse(history.verify(output/'receipt.json',True)['allPreserved'])
        self.source.write_bytes(baseline[:-1])
        self.assertFalse(history.verify(output/'receipt.json',True)['allPreserved'])
    def test_append_mode_requires_intact_backup_and_valid_size(self):
        output=self.root/'backup';history.backup([self.source],output)
        receipt=output/'receipt.json';doc=json.loads(receipt.read_text())
        doc['files'][0]['bytes']=-1;receipt.write_text(json.dumps(doc))
        with self.assertRaises(ValueError):history.verify(receipt,True)
        doc['files'][0]['bytes']=self.source.stat().st_size;receipt.write_text(json.dumps(doc))
        (output/'000.jsonl').write_bytes(b'changed')
        self.assertFalse(history.verify(receipt,True)['allPreserved'])
if __name__=='__main__':unittest.main()
