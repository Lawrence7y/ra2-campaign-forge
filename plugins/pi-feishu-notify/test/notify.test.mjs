import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { FeishuSender, NotifyLifecycle, validateConfig, redact } from '../core.mjs';
function fixture(options = {}) {
 const cwd=mkdtempSync(join(tmpdir(),'pi-feishu-'));const calls=[];
 const config={enabled:true,command:'mock-cli',expectedAppId:'cli_test',recipient:{type:'user',id:'ou_self'},approvedRecipient:'user:ou_self',includeQuestions:true,...options};
 const run=async(_cmd,args)=>{calls.push(args);return args[0]==='auth'?{code:0,stdout:JSON.stringify({appId:'cli_test',identities:{bot:{available:true,appName:'Bot'}}})}:{code:0,stdout:JSON.stringify({ok:true,identity:'bot',data:{message_id:'om_test'}})};};
 const s=new FeishuSender(config,cwd,run);return {s,calls,cleanup:()=>rmSync(cwd,{recursive:true,force:true}),cwd};
}
test('disabled pending consent never invokes CLI',async()=>{
 const f=fixture({enabled:false,approvedRecipient:null});try{assert.deepEqual(await f.s.send('completed'),{disabled:true});assert.equal(f.calls.length,0);}finally{f.cleanup();}
});
test('recipient change requires renewed confirmation',()=>{
 assert.throws(()=>validateConfig({enabled:true,command:'cli',expectedAppId:'cli_test',recipient:{type:'user',id:'ou_new'},approvedRecipient:'user:ou_old'}),/尚未确认/);
});
test('fixed bot sender, recipient, idempotency and private metadata only',async()=>{
 const f=fixture();try{
  const r=await f.s.send('waiting',{question:'待回答的问题'},'notification-key');assert.equal(r.sent,true);
  const args=f.calls[1];assert.equal(args[args.indexOf('--as')+1],'bot');assert.equal(args[args.indexOf('--user-id')+1],'ou_self');assert.equal(args[args.indexOf('--idempotency-key')+1],'notification-key');assert.ok(args[args.indexOf('--text')+1].includes('待回答的问题'));
  await f.s.send('waiting',{question:'待回答的问题'},'notification-key');assert.equal(f.calls.length,2);
  const log=readFileSync(join(f.cwd,'.pi/feishu-notify/notifications.jsonl'),'utf8');assert.equal(log.includes('待回答的问题'),false);assert.equal(log.includes('om_test'),true);
 }finally{f.cleanup();}
});
test('app identity drift fails closed, never falls back to user',async()=>{
 const f=fixture();try{f.s.run=async()=>({code:0,stdout:JSON.stringify({appId:'cli_other',identities:{bot:{available:true}}})});await assert.rejects(f.s.send('completed'),/身份不可用或 appId 已变化/);}finally{f.cleanup();}
});
test('nonzero or ok:false never becomes successful delivery and is not retried',async()=>{
 const f=fixture();try{const original=f.s.run;let sends=0;f.s.run=async(c,a)=>a[0]==='auth'?original(c,a):(++sends,{code:1,stderr:JSON.stringify({ok:false,identity:'bot',error:{code:99991679}})});
 await assert.rejects(f.s.send('completed',{},'fail-key'),/不自动切身份或重试/);await f.s.send('completed',{},'fail-key');assert.equal(sends,1);
 }finally{f.cleanup();}
});
test('dry-run previews with explicit bot and never records delivery',async()=>{
 const f=fixture({enabled:false,approvedRecipient:null});try{const r=await f.s.send('waiting',{question:'测试'},undefined,{dryRun:true});assert.equal(r.sent,false);assert.equal(r.dryRun,true);assert.ok(f.calls[1].includes('--dry-run'));}finally{f.cleanup();}
});
test('completion summaries are off by default, failure/abort have honest labels',async()=>{
 const f=fixture();try{
  await f.s.send('completed',{outcome:'error',summary:'private full reply'});const text=f.calls[1][f.calls[1].indexOf('--text')+1];assert.equal(text.includes('private'),false);assert.ok(text.includes('失败'));
  await f.s.send('completed',{outcome:'aborted'});assert.ok(f.calls[3][f.calls[3].indexOf('--text')+1].includes('取消'));
 }finally{f.cleanup();}
});
test('settled (not agent end) notifies once after retries',async()=>{
 const events=[];const l=new NotifyLifecycle(async(...e)=>events.push(e));l.start();l.start();assert.equal(events.length,0);l.outcome='error';await l.settled();await l.settled();assert.equal(events.length,1);assert.equal(events[0][1].outcome,'error');
});
test('explicit question sends waiting, suppresses contradictory completion, next run works',async()=>{
 const events=[];const l=new NotifyLifecycle(async(...e)=>events.push(e));l.start();await l.waiting('请选择',true);await l.settled();assert.deepEqual(events.map(e=>e[0]),['waiting']);l.start();await l.settled();assert.deepEqual(events.map(e=>e[0]),['waiting','completed']);
});
test('UI prompt reminder does not mark a later answered run as still waiting',async()=>{
 const events=[];const l=new NotifyLifecycle(async(...e)=>events.push(e));l.start();await l.waiting('确认弹窗',false);await l.settled();assert.deepEqual(events.map(e=>e[0]),['waiting','completed']);assert.notEqual(events[0][2],events[1][2]);
});
test('known credential patterns are redacted and payload bounded',()=>{
 const s=redact('api_key=secret password=pass Bearer abcdef sk-abcdefghijklmnopqrstuvwxyz');assert.equal(s.includes('secret'),false);assert.equal(s.includes('abcdef'),false);assert.equal(redact('长'.repeat(4000)).length,1400);
});
test('disable skips queued jobs before any identity or send calls',async()=>{
 const f=fixture();try{const task=f.s.send('waiting',{question:'queued'});f.s.config.enabled=false;assert.deepEqual(await task,{disabled:true});assert.equal(f.calls.length,0);}finally{f.cleanup();}
});
