// Read only: source, exact transactions, arithmetic, digests and final state.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createClient,abi} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';
import {TransactionHashVariant} from 'genlayer-js/types';
const root=path.resolve(import.meta.dirname,'..');
const e=JSON.parse(fs.readFileSync(path.join(root,'evidence/studionet.json')));
const client=createClient({chain:studionet});assert.equal(Number(await client.getChainId()),61999);
const source=fs.readFileSync(path.join(root,'contracts/band_pact.py'),'utf8');
assert.equal(crypto.createHash('sha256').update(source).digest('hex'),e.sourceSha256);
assert.equal(await client.getContractCode(e.address),source);
const r=JSON.parse(await client.readContract({address:e.address,functionName:'get_pact',args:[e.owner,'archive-demo'],transactionHashVariant:TransactionHashVariant.LATEST_FINAL}));
assert.deepEqual(r,e.record);assert.equal(r.status,'AGREED');assert.equal(r.approvals.length,2);
assert.deepEqual([...r.approvals].sort(),[...r.parties].sort());assert.ok(r.alignment.every(x=>x.relation==='SAME'));
const reports=r.parties.map(p=>r.reports[p]);
assert.deepEqual(r.intersection,[Math.max(...reports.map(x=>x.lower)),Math.min(...reports.map(x=>x.upper))]);
assert.deepEqual(r.intersection,[100,110]);
function canonical(x){
 if(x===null||typeof x!=='object')return JSON.stringify(x).replace(/[\u007f-\uffff]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));
 if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';
 return '{'+Object.keys(x).sort().map(k=>canonical(k)+':'+canonical(x[k])).join(',')+'}';
}
const digest=crypto.createHash('sha256').update(canonical({protocol:r.protocol,owner:r.owner,id:r.id,parties:r.parties,unit:r.unit,
 reports:r.reports,alignment:r.alignment,resolution:{status:'AWAITING_APPROVAL',intersection:r.intersection}})).digest('hex');
assert.equal(r.result_digest,digest);
for(const [name,t] of Object.entries(e.transactions)){
 const receipt=await client.getTransaction({hash:t.hash});
 assert.equal(receipt.statusName,'FINALIZED');assert.equal(receipt.resultName||receipt.result_name,'MAJORITY_AGREE');
 assert.equal(receipt.txExecutionResultName||receipt.consensus_data?.leader_receipt?.find(x=>x.mode==='leader')?.execution_result,'SUCCESS');
 assert.equal(receipt.leader_only,false);assert.equal(receipt.from_address.toLowerCase(),t.signer.toLowerCase());
 assert.equal(receipt.to_address.toLowerCase(),e.address.toLowerCase());
 if(t.method==='deploy')assert.equal(Buffer.from(receipt.data.contract_code,'base64').toString(),source);
 else{
  const data=abi.calldata.decode(Buffer.from(receipt.data.calldata.base64,'base64'));
  assert.equal(data.get('method'),t.method);assert.deepEqual(data.get('args'),t.args);
 }
 console.log(name,t.hash,'FINALIZED');
}
assert.equal(e.checkpoints.one_approval.status,'AWAITING_APPROVAL');assert.equal(e.checkpoints.one_approval.approvals.length,1);
console.log('VERIFIED: source, receipt binding, semantic agreement, exact interval/digest, bilateral approval and finalized state.');
