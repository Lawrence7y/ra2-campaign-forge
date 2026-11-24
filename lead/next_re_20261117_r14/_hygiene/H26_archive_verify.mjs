// H26 board archive verifier: byte-exact append, line-exact tail compare, gates
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const r14=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const hyg=path.join(r14,'_hygiene');
const board=path.join(r14,'STATUS_BOARD.md');
const arc=path.join(r14,'BOARD_ARCHIVE.md');
const root=path.resolve(r14,'..','..');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex').toUpperCase();
function readLines(buf){const a=buf.toString('utf8').split(/\r?\n/); if(a[a.length-1]==='')a.pop(); return a;}
function fail(msg,extra){const r={error:String(msg),...(extra||{})}; fs.writeFileSync(path.join(hyg,'H26_archive_result.json'),JSON.stringify(r,null,2)); throw new Error(msg);}
const boardBuf=fs.readFileSync(board);
const boardHash0=sha(boardBuf);
if(sha(fs.readFileSync(board))!==boardHash0)fail('board changed before snapshot');
fs.writeFileSync(path.join(hyg,'STATUS_BOARD.before_H26.bak'),boardBuf);
const before=readLines(boardBuf);
const required=['# R14 运行看板 v2','## 基线与并发控制','## 常设真机授权（已生效）','## Lead 口径裁定（流程规范，非技术结论）'];
const reqMissing=required.filter(h=>!before.some(l=>l.startsWith(h)));
if(reqMissing.length)fail('required headers missing',{required_missing:reqMissing});
const pointer0=before.findIndex(l=>l.includes('第 71–477 段已归档至 BOARD_ARCHIVE.md'));
if(pointer0!==70)fail('H25 pointer not at protected boundary',{pointer_line_1based:pointer0+1});
const protectedLines=before.slice(0,71);
const headings=[];
for(let i=71;i<before.length;i++)if(before[i].startsWith('## '))headings.push(i);
if(headings.length<3)fail('fewer than 3 recent top-level segments',{headings});
const cut=headings[headings.length-3];
const recent3=headings.slice(-3).map(i=>before[i]);
const moved=before.slice(71,cut);
const kept=before.slice(cut);
if(!moved.length||!kept.length)fail('empty move or keep',{cut});
const acBuf=fs.readFileSync(arc);
const N=acBuf.length,A0=sha(acBuf);
const payload=Buffer.concat(moved.map(l=>Buffer.from(l+'\n','utf8')));
if(sha(fs.readFileSync(board))!==boardHash0)fail('board changed before archive append');
let appended=false,boardWritten=false;
let ac2,prefixOK=false,tail=[],missing=-1,mismatch=0;
try{
  fs.appendFileSync(arc,payload); appended=true;
  ac2=fs.readFileSync(arc);
  prefixOK=sha(ac2.subarray(0,N))===A0;
  tail=readLines(ac2.subarray(N));
  missing=0;
  for(let i=0;i<Math.max(moved.length,tail.length);i++){
    if(i>=moved.length||i>=tail.length){missing++;continue;}
    if(moved[i]!==tail[i]){missing++;mismatch++;}
  }
  if(!prefixOK||missing!==0)fail('archive append verification failed',{prefix_ok:prefixOK,missing,mismatch});
  if(sha(fs.readFileSync(board))!==boardHash0)fail('board changed after archive append');
  const stamp=new Date().toLocaleString('sv-SE',{timeZone:'Asia/Shanghai',hour12:false}).replace('T',' ').slice(0,16);
  const pointer='> 📦 第 72–'+cut+' 段已归档至 BOARD_ARCHIVE.md（'+stamp+'，逐字搬，missing=0）';
  const out=[...protectedLines,'',pointer,...kept];
  fs.writeFileSync(board,out.join('\n')+'\n','utf8'); boardWritten=true;
  const afterBuf=fs.readFileSync(board);
  const after=readLines(afterBuf);
  const afterLines=after.length;
  const protectedMissing=protectedLines.filter((l,i)=>after[i]!==l).length;
  const keptMissing=kept.filter((l,i)=>after[i+protectedLines.length+2]!==l).length;
  const afterText=after.join('\n');
  const recentMissing=recent3.filter(h=>!afterText.includes(h)).length;
  const reqAfterMissing=required.filter(h=>!afterText.includes(h)).length;
  if(afterLines>300||protectedMissing||keptMissing||recentMissing||reqAfterMissing)fail('final board verification failed',{after_lines:afterLines,protected_missing:protectedMissing,kept_missing:keptMissing,recent_missing:recentMissing,required_after_missing:reqAfterMissing});
  // gates
  const g={};
  const gm=path.join(root,'ra2youli','gamemd.exe'); const gst=fs.statSync(gm); const gh=sha(fs.readFileSync(gm));
  g.B1={status:(gst.size===4825360&&gh.startsWith('73201CC0')&&gh.endsWith('F67476'))?'OK':'FAIL',size:gst.size,sha:gh};
  const dd=path.join(root,'ra2youli','ddraw.dll'); const dh=sha(fs.readFileSync(dd));
  g.B2={status:(dh.startsWith('85E0F7D5')&&dh.endsWith('3B03A9'))?'OK':'FAIL',sha:dh};
  const ex=path.join(root,'ra2youli','except.txt'); const es=fs.statSync(ex); const em=es.mtime.toLocaleString('sv-SE',{timeZone:'Asia/Shanghai',hour12:false});
  g.B3={status:(es.size===26272&&em==='2026-11-13 06:29:17')?'OK':'FAIL',size:es.size,mtime:em};
  let proc='ERR';
  try{proc=execFileSync('powershell',['-NoProfile','-NonInteractive','-Command','@(Get-Process gamemd -ErrorAction SilentlyContinue).Count'],{encoding:'utf8'}).trim();}catch(e){proc='ERR';}
  g.B4={status:(proc==='0')?'OK':'FAIL',gamemd_process_count:proc};
  const lock=fs.readFileSync(path.join(r14,'LIVE_LOCK'),'utf8').replace(/\r?\n$/,'');
  g.B5={status:(lock==='RELEASED by W177-J (aborted)')?'OK':'FAIL',value:lock};
  const ledger=path.join(root,'lead','GOAL_THREE_TARGETS_20261018.md'); const lbuf=fs.readFileSync(ledger); const baseline=JSON.parse(fs.readFileSync(path.join(hyg,'H25_baseline.json'),'utf8'));
  const expected=baseline.ledger.prefix_sha256.toUpperCase(); const lp=sha(lbuf.subarray(0,3348343));
  g.B6={status:(lbuf.length>=3370848&&lp===expected)?'OK':'FAIL',size:lbuf.length,prefix_bytes:3348343,prefix_sha:lp,baseline_sha:expected,matches_baseline:lp===expected};
  const cov=path.join(r14,'COVERAGE','coverage.tsv'); const clines=readLines(fs.readFileSync(cov)); const ch=sha(fs.readFileSync(cov));
  g.B7={status:(clines.length-1===18431)?'OK':'FAIL',data_lines:clines.length-1,sha:ch};
  const fails=Object.entries(g).filter(([k,v])=>v.status!=='OK').map(([k])=>k);
  const result={
    task:'H26',before_lines:before.length,moved_start_line:72,moved_end_line:cut,moved_lines:moved.length,
    after_lines:afterLines,pointer,pointer_line_1based:protectedLines.length+2,protected_lines:protectedLines.length,protected_missing:protectedMissing,
    kept_lines:kept.length,kept_missing:keptMissing,recent_segments:recent3,recent_missing:recentMissing,required_headers_missing:reqAfterMissing,
    archive_before_bytes:N,archive_before_sha:A0,archive_after_bytes:ac2.length,archive_after_sha:sha(ac2),archive_prefix_sha:sha(ac2.subarray(0,N)),archive_prefix_ok:prefixOK,
    compared:moved.length,archive_tail_lines:tail.length,missing,mismatch,
    gates:g,FAIL:fails,ok:fails.length===0
  };
  fs.writeFileSync(path.join(hyg,'H26_archive_result.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
}catch(e){
  if(appended&&!boardWritten){try{fs.writeFileSync(arc,acBuf);}catch(_){}}
  if(!fs.existsSync(path.join(hyg,'H26_archive_result.json')))fs.writeFileSync(path.join(hyg,'H26_archive_result.json'),JSON.stringify({error:String(e&&e.message||e)},null,2));
  throw e;
}
