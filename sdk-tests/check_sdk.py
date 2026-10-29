"""Real pinned SDK storage/calldata with mocked LLM, not live consensus."""
import json
from pathlib import Path
from gltest.direct import VMContext, deploy_contract
root=Path(__file__).resolve().parents[1];owner='0x'+'1'*40;peer='0x'+'2'*40
reports=[json.loads((root/f'examples/report-{x}.json').read_text()) for x in ['a','b']]
facets=['metric','population','window','basis']
response={'alignment':[{'facet':f,'relation':'SAME','reason':'Both report definitions describe the same quantity and scope.'} for f in facets]}
vm=VMContext();vm.sender=owner;vm.mock_llm('^Compare the semantic',json.dumps(response))
with vm.activate():
    pact=deploy_contract(root/'contracts/band_pact.py',vm,sdk_version='v0.3.0-rc7')
    pact.open_pact('sdk',peer,'OBJECT');pact.submit_report(owner,'sdk',json.dumps(reports[0]))
    with vm.prank(peer):pact.submit_report(owner,'sdk',json.dumps(reports[1]))
    record=json.loads(pact.compare(owner,'sdk'));assert record['intersection']==[100,110]
    assert vm.run_validator() is True
    vm.clear_mocks();response['alignment'][0]['relation']='DIFFERENT';vm.mock_llm('^Compare the semantic',json.dumps(response))
    assert vm.run_validator() is False
    pact.approve(owner,'sdk',record['result_digest']);assert json.loads(pact.get_pact(owner,'sdk'))['status']=='AWAITING_APPROVAL'
    with vm.prank(peer):pact.approve(owner,'sdk',record['result_digest'])
    assert json.loads(pact.get_pact(owner,'sdk'))['status']=='AGREED'
print('PASS: real SDK storage/calldata, independent validator acceptance/rejection, intersection and dual approval (mocked LLM).')
