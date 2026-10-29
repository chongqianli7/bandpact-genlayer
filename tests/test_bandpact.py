"""Actual deployable file with mocked host/model; no network consensus."""
import importlib.util
import itertools
import json
import sys
import types
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A='0x'+'1'*40;B='0x'+'2'*40;C='0x'+'3'*40
class Return:
    def __init__(self,value):self.calldata=value
class Public:
    write=staticmethod(lambda f:f)
    view=staticmethod(lambda f:f)
host=types.SimpleNamespace(Contract=object,public=Public(),message=types.SimpleNamespace(sender_address=A),
     vm=types.SimpleNamespace(UserError=ValueError,Return=Return),nondet=types.SimpleNamespace())
sys.modules['genlayer']=types.SimpleNamespace(gl=host,TreeMap=dict)
spec=importlib.util.spec_from_file_location('band',ROOT/'contracts/band_pact.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
REPORTS=[json.loads((ROOT/f'examples/report-{n}.json').read_text()) for n in ['a','b']]
def alignment(labels=('SAME',)*4):
    return {'alignment':[{'facet':f,'relation':v,'reason':'The supplied definitions explicitly describe equivalent scope.'} for f,v in zip(c.FACETS,labels)]}
class Tests(unittest.TestCase):
    def setUp(self):
        host.message.sender_address=A;self.contract=c.BandPact();self.prompts=[];self.labels=['SAME']*4;self.other_labels=None
        def llm(prompt,**kwargs):
            self.prompts.append(prompt)
            return alignment(self.other_labels if len(self.prompts)>1 and self.other_labels is not None else self.labels)
        host.nondet.exec_prompt=llm
        def run(leader,validator):
            raw=leader()
            if not validator(Return(raw)):raise ValueError('DISAGREEMENT')
            return raw
        host.vm.run_nondet_unsafe=run
    def collect(self,reports=None):
        reports=reports or REPORTS
        self.contract.open_pact('archive',B,'OBJECT')
        self.contract.submit_report(A,'archive',json.dumps(reports[0]))
        host.message.sender_address=B;self.contract.submit_report(A,'archive',json.dumps(reports[1]));host.message.sender_address=A
    def compare(self):return json.loads(self.contract.compare(A,'archive'))
    def read(self):return json.loads(self.contract.get_pact(A,'archive'))
    def approve(self,digest=None):return json.loads(self.contract.approve(A,'archive',digest or self.read()['result_digest']))
    def test_full_bilateral_lifecycle(self):
        self.collect();r=self.compare();self.assertEqual(r['intersection'],[100,110]);self.assertEqual(r['status'],'AWAITING_APPROVAL')
        self.assertEqual(self.approve()['status'],'AWAITING_APPROVAL');host.message.sender_address=B
        self.assertEqual(self.approve()['status'],'AGREED');self.assertEqual(len(self.read()['approvals']),2)
    def test_single_party_cannot_approve_twice(self):
        self.collect();self.compare();self.approve()
        with self.assertRaisesRegex(ValueError,'ALREADY_APPROVED'):self.approve()
    def test_no_report_impersonation(self):
        self.contract.open_pact('archive',B,'OBJECT');host.message.sender_address=C
        with self.assertRaisesRegex(ValueError,'NOT_PARTY'):self.contract.submit_report(A,'archive',json.dumps(REPORTS[1]))
    def test_reports_immutable(self):
        self.collect()
        with self.assertRaisesRegex(ValueError,'REPORT_LOCKED'):self.contract.submit_report(A,'archive',json.dumps(REPORTS[0]))
    def test_incomplete_reports_block_compare(self):
        self.contract.open_pact('archive',B,'OBJECT')
        with self.assertRaisesRegex(ValueError,'NOT_READY'):self.compare()
    def test_bands_withheld_from_both_prompts(self):
        self.collect();self.compare();self.assertEqual(len(self.prompts),2)
        for p in self.prompts:
            self.assertNotIn('"lower"',p);self.assertNotIn('"upper"',p);self.assertNotIn('"approvals"',p)
    def test_independent_disagreement_atomic(self):
        self.collect();self.other_labels=['SAME','DIFFERENT','SAME','SAME']
        with self.assertRaisesRegex(ValueError,'DISAGREEMENT'):self.compare()
        self.assertEqual(self.read()['status'],'READY');self.assertEqual(self.read()['alignment'],[])
    def test_incomparable_blocks_even_when_numbers_overlap(self):
        self.collect();self.labels=['SAME','SAME','SAME','DIFFERENT'];r=self.compare()
        self.assertEqual(r['status'],'INCOMPARABLE');self.assertEqual(r['intersection'],[])
        with self.assertRaisesRegex(ValueError,'NOT_APPROVABLE'):self.approve()
    def test_unclear_blocks(self):
        self.collect();self.labels=['SAME','UNCLEAR','SAME','SAME'];self.assertEqual(self.compare()['status'],'REVIEW')
    def test_disjoint(self):
        reports=[REPORTS[0],dict(REPORTS[1],lower=111)]
        self.collect(reports);self.assertEqual(self.compare()['status'],'DISJOINT')
        with self.assertRaisesRegex(ValueError,'NOT_APPROVABLE'):self.approve()
    def test_touching_boundary_included(self):
        self.collect([REPORTS[0],dict(REPORTS[1],lower=110)]);self.assertEqual(self.compare()['intersection'],[110,110])
    def test_digest_rejected(self):
        self.collect();self.compare()
        with self.assertRaisesRegex(ValueError,'DIGEST_MISMATCH'):self.approve('0'*64)
    def test_comparison_locked(self):
        self.collect();self.compare()
        with self.assertRaisesRegex(ValueError,'NOT_READY'):self.compare()
    def test_stranger_compare_and_approve(self):
        self.collect();host.message.sender_address=C
        with self.assertRaisesRegex(ValueError,'NOT_PARTY'):self.compare()
        host.message.sender_address=A;self.compare();host.message.sender_address=C
        with self.assertRaisesRegex(ValueError,'NOT_PARTY'):self.approve()
    def test_same_address_and_bad_peer(self):
        for peer in [A,'0x'+'0'*40,'0xwrong']:
            with self.assertRaises(ValueError):self.contract.open_pact('archive',peer,'OBJECT')
    def test_owner_namespaces(self):
        self.contract.open_pact('archive',B,'OBJECT');host.message.sender_address=B;self.contract.open_pact('archive',C,'OBJECT')
        self.assertEqual(len(self.contract.pacts),2)
    def test_interval_bounds_and_types(self):
        for lo,hi in [(-1,2),(3,2),(True,2),(0,1.5),(0,10**12+1)]:
            with self.assertRaisesRegex(ValueError,'INVALID_INTERVAL'):c.decode_report(json.dumps(dict(REPORTS[0],lower=lo,upper=hi)))
    def test_evidence_is_exact_complete_metadata(self):
        clean=c.parse_alignment(alignment(),REPORTS)
        self.assertEqual(clean[0]['evidence'],[r['metric'] for r in REPORTS])
        raw=alignment();raw['alignment'][0]['evidence']=['Invented quoted evidence.','Other invented evidence.']
        with self.assertRaisesRegex(ValueError,'ALTERED_EVIDENCE'):c.parse_alignment(raw,REPORTS)
    def test_alignment_order_and_completeness(self):
        for raw in [{'alignment':[]},{'alignment':list(reversed(alignment()['alignment']))}]:
            with self.assertRaises(ValueError):c.parse_alignment(raw,REPORTS)
    def test_all_label_vectors(self):
        for labels in itertools.product(['SAME','DIFFERENT','UNCLEAR'],repeat=4):
            r=c.resolve(REPORTS,c.parse_alignment(alignment(labels),REPORTS))
            expected='INCOMPARABLE' if 'DIFFERENT' in labels else 'REVIEW' if 'UNCLEAR' in labels else 'AWAITING_APPROVAL'
            self.assertEqual(r['status'],expected)
    def test_exhaustive_integer_intersections(self):
        intervals=[(a,b) for a in range(6) for b in range(a,6)]
        labels=c.parse_alignment(alignment(),REPORTS)
        for left,right in itertools.product(intervals,repeat=2):
            reports=[dict(REPORTS[0],lower=left[0],upper=left[1]),dict(REPORTS[1],lower=right[0],upper=right[1])]
            shared=set(range(left[0],left[1]+1))&set(range(right[0],right[1]+1))
            result=c.resolve(reports,labels)
            self.assertEqual(result['intersection'],[min(shared),max(shared)] if shared else [])
            self.assertEqual(result['status'],'AWAITING_APPROVAL' if shared else 'DISJOINT')
if __name__=='__main__':unittest.main()
