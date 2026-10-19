import test from 'node:test';
import assert from 'node:assert/strict';
import { runInNewContext } from 'node:vm';
import { DesktopHarnessService } from '../desktop/service.mjs';
import { DesktopConnection } from '../desktop/cdp.mjs';

function fixture(overrides = {}) {
  const calls = []; let closed = 0;
  const c = { targetId: 'gui', close() { closed++; }, async call(method, args) {
    calls.push({method,args});
    if (overrides[method]) return await overrides[method](args);
    if (method === 'watchChatSessionControl') return {state:{sessionId:args[0],runtimeState:'idle',activeTurn:null,queuedTurns:[],pendingInteractions:[]}};
    if (method === 'openChatSession') return {summary:{agentId:'real-agent'},messages:[{role:'assistant',content:'desktop output'}]};
    if (method === 'setChatSessionModel') return {model:args[1]};
    if (method === 'sendChatMessage') return {status:'accepted',inputId:args[0].inputId};
    if (method === 'queryData') return {data:[{id:'real-agent',name:'Agent',secret:'never return',instructions:'private'}],error:null};
    if (method === 'listChatSessions') return [{sessionId:'existing'}];
    if (method === 'getDesktopSessionActivity') return {runningAgentSessionCount:2};
    return undefined;
  }};
  const service = new DesktopHarnessService({harnesses:{'qoder-cn':{endpoint:'http://127.0.0.1:9344'},zcode:{endpoint:'http://127.0.0.1:9333'},codex:{kind:'pending'}}}, async () => c);
  return {service,calls,get closed(){return closed;}};
}
test('desktop probe does not send a prompt', async () => {
 const f=fixture(); const r=await f.service.run({action:'probe',harness:'qoder-cn'});
 assert.equal(r.transport,'existing-desktop-ipc');assert.equal(r.modelTasksInvoked,0);assert.deepEqual(f.calls.map(c=>c.method),['listChatSessions']);assert.equal(f.closed,1);
});
test('desktop dispatch creates a real GUI session with safe modes and acceptance not completion', async()=>{
 const f=fixture();const r=await f.service.run({action:'dispatch',harness:'qoder-cn',agentId:'real-agent',prompt:'hello'});
 const i=f.calls[0].args[0];assert.equal(i.sessionId,r.sessionId);assert.equal(i.inputId,r.inputId);assert.equal(i.planMode,true);assert.equal(i.permissionMode,'default');assert.equal(r.completed,false);assert.equal(f.closed,1);
});
test('desktop continuation uses persisted agent identity and no permission escalation',async()=>{
 const f=fixture();await f.service.run({action:'prompt',harness:'qoder-cn',sessionId:'existing',prompt:'next',agentId:'wrong'});
 const i=f.calls.find(c=>c.method==='sendChatMessage').args[0];assert.equal(i.agentId,'real-agent');assert.equal(i.permissionMode,undefined);assert.equal(i.planMode,undefined);assert.ok(f.calls.some(c=>c.method==='unwatchChatSessionControl'));
});
test('busy desktop session is not interrupted for prompt or model change',async()=>{
 for(const action of ['prompt','model']){
  const f=fixture({watchChatSessionControl:args=>({state:{sessionId:args[0],runtimeState:'running',activeTurn:{turnId:'human-task'}}})});
  await assert.rejects(f.service.run({action,harness:'qoder-cn',sessionId:'existing',prompt:'next',modelId:'m'}),/正在运行/);
  assert.equal(f.calls.some(c=>['sendChatMessage','setChatSessionModel','interruptChatSession'].includes(c.method)),false);assert.equal(f.closed,1);
 }
});
test('model readback is reported honestly, not simulated',async()=>{
 const f=fixture({setChatSessionModel:()=>({model:'unchanged'})});const r=await f.service.run({action:'model',harness:'qoder-cn',sessionId:'existing',modelId:'new'});assert.equal(r.verified,false);
});
test('missing control state fails closed and releases observer',async()=>{
 const f=fixture({watchChatSessionControl:()=>({state:null})});await assert.rejects(f.service.run({action:'model',harness:'qoder-cn',sessionId:'existing',modelId:'m'}),/控制状态无效/);assert.ok(f.calls.some(c=>c.method==='unwatchChatSessionControl'));assert.equal(f.closed,1);
});
test('pending desktop adapters and ZCode unsupported actions never fall back to CLI',async()=>{
 const f=fixture();await assert.rejects(f.service.run({action:'dispatch',harness:'zcode'}),/不会改用 CLI/);await assert.rejects(f.service.run({action:'probe',harness:'codex'}),/不会改用 CLI/);assert.equal(f.closed,0);assert.equal(f.calls.length,0);
});
test('desktop thinking cannot overwrite global model preferences',async()=>{
 const f=fixture();await assert.rejects(f.service.run({action:'model',harness:'qoder-cn',thinking:'high'}),/全局模型偏好/);assert.equal(f.calls.length,0);
});
test('write timeout includes reconciliation IDs and never retries',async()=>{
 const f=fixture({sendChatMessage:()=>{throw new Error('timeout');}});await assert.rejects(f.service.run({action:'dispatch',harness:'qoder-cn',agentId:'real-agent',prompt:'p'}),/sessionId=.*inputId=.*不自动重发/);assert.equal(f.calls.filter(c=>c.method==='sendChatMessage').length,1);assert.equal(f.closed,1);
});
test('agent catalog filters config and instructions',async()=>{
 const f=fixture();const r=await f.service.run({action:'agents',harness:'qoder-cn'});assert.equal(r.agents[0].id,'real-agent');assert.equal(JSON.stringify(r).includes('private'),false);assert.equal(JSON.stringify(r).includes('secret'),false);
});
test('history pagination calls the native history API',async()=>{
 const f=fixture();await f.service.run({action:'read',harness:'qoder-cn',sessionId:'existing',agentId:'real-agent',beforeMessageId:'anchor',limit:10});assert.deepEqual(f.calls[0],{method:'loadChatHistoryBefore',args:['existing','real-agent','anchor',10]});
});
test('desktop endpoints reject remote hosts and credentials',()=>{
 for(const endpoint of ['https://127.0.0.1:9344','http://remote:9344','http://user:pass@localhost:9344','http://localhost:9344/path'])assert.throws(()=>new DesktopConnection({endpoint}));
});
test('IPC arguments are JSON values, not renderer code',async()=>{
 const c=new DesktopConnection({endpoint:'http://127.0.0.1:9344',api:'qoderDesktop'});
 const dangerous='\");globalThis.pwned=true;//';let received;const context={window:{qoderDesktop:{sendChatMessage:x=>{received=x;return {ok:true};}}}};
 c.evaluate=async expr=>await runInNewContext(expr,context);const r=await c.call('sendChatMessage',[{prompt:dangerous}]);assert.equal(r.ok,true);assert.equal(received.prompt,dangerous);assert.equal(context.pwned,undefined);
});
