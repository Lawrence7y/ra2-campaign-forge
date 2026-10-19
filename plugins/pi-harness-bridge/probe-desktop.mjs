import { DesktopConnection } from './desktop/cdp.mjs';
for (const [name, port, api] of [['zcode',9333,'zcode'], ['qoder-cn',9344,'qoderDesktop']]) {
 const c = new DesktopConnection({ endpoint: `http://127.0.0.1:${port}`, api });
 try {
  await c.connect();
  const keys = await c.evaluate(`Object.keys(window[${JSON.stringify(api)}])`);
  const r = { name, connected: true, transport: 'existing-desktop-ipc', targetId: c.targetId };
  if(name==='qoder-cn') {
   r.apiNames = keys.filter(k => /create|send|agent|profile|history|model|session|collaboration|snapshot|runtime|stop/i.test(k));
   const sessions = await c.call('listChatSessions',[1,0,false]);
   r.sessionResultKeys = Object.keys(sessions || {});
   r.sessionItemKeys = Object.keys((Array.isArray(sessions)?sessions:sessions?.sessions || sessions?.items || [])[0] || {});
   r.sessionCount = Array.isArray(sessions)?sessions.length:undefined;
   const models = await c.call('listChatModels',[{ workspaceDirectories: [], forceRefresh: false }]);
   r.modelKeys = Object.keys(models || {});r.modelCount = Array.isArray(models)?models.length:undefined;
   r.modelItemKeys = Object.keys((Array.isArray(models)?models:models?.models || [])[0]||{});
  } else {
   const activity=await c.call('getDesktopSessionActivity');r.activityKeys=Object.keys(activity||{});
   r.otherGlobals = await c.evaluate(`Reflect.ownKeys(window).filter(k=>typeof k==='string'&&/zcode|store|client|protocol|task/i.test(k))`);
  }
  console.log(JSON.stringify(r));
 } catch(e){console.log(JSON.stringify({name, connected:false,error:e.message}));}
 finally {c.close();}
}
