// Development writes: isolated test accounts, zero value, full consensus, resumable hashes.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createClient,abi} from 'genlayer-js';
import {studionet} from 'genlayer-js/chains';
import {TransactionHashVariant} from 'genlayer-js/types';
import {generatePrivateKey,privateKeyToAccount} from 'viem/accounts';
const root=path.resolve(import.meta.dirname,'..');
const file=process.env.BANDPACT_STATE||path.join(os.homedir(),'.bandpact-studionet.json');
const stringify=x=>JSON.stringify(x,(_,v)=>typeof v==='bigint'?v.toString():v,2);
let run;
if(fs.existsSync(file))run=JSON.parse(fs.readFileSync(file));
else{
 if(process.env.BANDPACT_NEW!=='1')throw Error('Set BANDPACT_NEW=1 once to start a new zero-value test run.');
 run={keys:[generatePrivateKey(),generatePrivateKey()],transactions:{},checkpoints:{}};
 fs.writeFileSync(file,stringify(run),{mode:0o600});
}
const save=()=>fs.writeFileSync(file,stringify(run),{mode:0o600});
const accounts=run.keys.map(privateKeyToAccount),clients=accounts.map(account=>createClient({chain:studionet,account}));
const owner=accounts[0].address,peer=accounts[1].address,client=clients[0];
assert.equal(Number(await client.getChainId()),61999);
const code=fs.readFileSync(path.join(root,'contracts/band_pact.py'),'utf8');
const sha=crypto.createHash('sha256').update(code).digest('hex');
if(run.sourceSha256)assert.equal(run.sourceSha256,sha,'Changed source must not resume old transactions.');
run.sourceSha256=sha;save();
const normalize=r=>{r.resultName??=r.result_name;r.txExecutionResultName??=r.consensus_data?.leader_receipt?.find(x=>x.mode==='leader')?.execution_result;return r;};
async function send(label,actor,method,args){
 let tx=run.transactions[label];
 if(!tx){
  tx=run.transactions[label]={intent:true,signer:accounts[actor].address,method,args};save();
  // Unknown send outcomes are locked, never automatically resent.
  tx.hash=method==='deploy'?await clients[actor].deployContract({code,args:[],leaderOnly:false}):
   await clients[actor].writeContract({address:run.address,functionName:method,args,value:0n,leaderOnly:false});
  save();console.log(label,'submitted',tx.hash);
 }
 assert.equal(tx.signer,accounts[actor].address);assert.equal(tx.method,method);assert.deepEqual(tx.args,args);
 if(!tx.hash)throw Error('Unresolved submission intent '+label);
 for(let i=0;i<180;i++){
  if(tx.receipt?.statusName==='FINALIZED')break;
  tx.receipt=normalize(await client.getTransaction({hash:tx.hash}));save();
  if(['UNDETERMINED','CANCELED'].includes(tx.receipt.statusName))throw Error(label+' failed: inspect existing receipt, no resend');
  if(tx.receipt.statusName!=='FINALIZED')await new Promise(r=>setTimeout(r,2000));
 }
 const r=normalize(tx.receipt);save();assert.equal(r.statusName,'FINALIZED','Resume the pending hash');
 assert.equal(r.resultName,'MAJORITY_AGREE');assert.equal(r.txExecutionResultName,'SUCCESS');assert.equal(r.leader_only,false);
 assert.equal(r.from_address.toLowerCase(),tx.signer.toLowerCase());
 if(method==='deploy'){run.address=r.to_address;save();assert.equal(Buffer.from(r.data.contract_code,'base64').toString(),code);}
 else{
  assert.equal(r.to_address.toLowerCase(),run.address.toLowerCase());const decoded=abi.calldata.decode(Buffer.from(r.data.calldata.base64,'base64'));
  assert.equal(decoded.get('method'),method);assert.deepEqual(decoded.get('args'),args);
 }
 console.log(label,r.statusName,r.resultName,r.txExecutionResultName);
}
const read=async()=>JSON.parse(await client.readContract({address:run.address,functionName:'get_pact',args:[owner,'archive-demo'],transactionHashVariant:TransactionHashVariant.LATEST_FINAL}));
await send('deploy',0,'deploy',[]);assert.equal(await client.getContractCode(run.address),code);
await send('open',0,'open_pact',['archive-demo',peer,'OBJECT']);
const reports=['a','b'].map(n=>fs.readFileSync(path.join(root,`examples/report-${n}.json`),'utf8'));
await send('report_a',0,'submit_report',[owner,'archive-demo',reports[0]]);
await send('report_b',1,'submit_report',[owner,'archive-demo',reports[1]]);
await send('compare',0,'compare',[owner,'archive-demo']);
let record=await read();
assert.deepEqual(record.intersection,[100,110]);assert.ok(record.alignment.every(f=>f.relation==='SAME'));
if(!run.transactions.approve_a){assert.equal(record.status,'AWAITING_APPROVAL');run.checkpoints.compared=record;save();}
const digest=record.result_digest;
await send('approve_a',0,'approve',[owner,'archive-demo',digest]);
if(!run.transactions.approve_b){record=await read();assert.equal(record.status,'AWAITING_APPROVAL');assert.equal(record.approvals.length,1);run.checkpoints.one_approval=record;save();}
await send('approve_b',1,'approve',[owner,'archive-demo',digest]);
record=await read();assert.equal(record.status,'AGREED');assert.equal(record.approvals.length,2);
function projected(r){return {hash:r.hash,statusName:r.statusName,resultName:r.resultName,txExecutionResultName:r.txExecutionResultName,
 from_address:r.from_address,to_address:r.to_address,leader_only:r.leader_only,data:{...r.data,calldata:{base64:r.data?.calldata?.base64}},
 consensus_data:{votes:r.consensus_data?.votes,leader_receipt:r.consensus_data?.leader_receipt?.map(l=>({mode:l.mode,execution_result:l.execution_result,result:{status:l.result?.status,payload:typeof l.result?.payload==='object'?{readable:l.result.payload?.readable}:l.result?.payload}}))}};}
const evidence={network:{chainId:61999,rpc:'https://studio.genlayer.com/api'},address:run.address,owner,peer,sourceSha256:sha,
 note:'Synthetic archive count reports; both test wallets controlled by one operator. No measured data or real institution is authenticated. Public receipt projections omit node configurations, timing logs and redundant byte arrays.',
 transactions:Object.fromEntries(Object.entries(run.transactions).map(([label,t])=>[label,{hash:t.hash,signer:t.signer,method:t.method,args:t.args,receipt:projected(t.receipt)}])),checkpoints:run.checkpoints,record};
fs.writeFileSync(path.join(root,'evidence/studionet.json'),stringify(evidence)+'\n');console.log('VERIFIED',run.address,record.status);
