// H28 board archive verifier: byte-exact append, line-exact tail compare, gates
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const NL=String.fromCharCode(10), CR=String.fromCharCode(13);
const r14=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const hyg=path.join(r14,'_hygiene');
const board=path.join(r14,'STATUS_BOARD.md');
const arc=path.join(r14,'BOARD_ARCHIVE.md');
const root=path.resolve(r14,'..','..');
const resultPath=path.join(hyg,'H28_archive_result.json');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex').toUpperCase();
function readLines(buf){
  const a=buf.toString('utf8').split(NL);
  if(a.length && a[a.length-1]==='')a.pop();
  for(let i=0;i<a.length;i++)if(a[i].endsWith(CR))a[i]=a[i].slice(0,-1);
  return a;
}
function lineStarts(buf){const s=[0];for(let i=0;i<buf.length;i++)if(buf[i]===10)s.push(i+1);if(s[s.length-1]===buf.length)s.pop();return s;}
function writeResult(r){fs.writeFileSync(resultPath,JSON.stringify(r,null,2)+NL);}
function fail(msg,extra){const r={error:String(msg),...(extra||{})};writeResult(r);throw new Error(msg);}
const boardBuf=fs.readFileSync(board);
const boardHash0=sha(boardBuf);
if(sha(fs.readFileSync(board))!==boardHash0)fail('board changed before snapshot');
fs.writeFileSync(path.join(hyg,'STATUS_BOARD.before_H28.bak'),boardBuf);
const before=readLines(boardBuf);
const starts=lineStarts(boardBuf);
if(starts.length!==before.length)fail('line offset mismatch',{starts:starts.length,lines:before.length});
const required=['# R14 运行看板 v2','## 基线与并发控制','## 常设真机授权（已生效）','## Lead 口径裁定'];
const reqMissing=required.filter(h=>!before.some(l=>l.startsWith(h)));
if(reqMissing.length)fail('required headers missing',{required_missing:reqMissing});
const pointer0=before.findIndex(l=>l.includes('第 74–354 段已归档至 BOARD_ARCHIVE.md'));
if(pointer0!==74)fail('H27 pointer not at protected boundary',{pointer_line_1based:pointer0+1});
const protectedLen=75;
const protectedLines=before.slice(0,protectedLen);
const cut=before.findIndex((l,i)=>i>=protectedLen&&l.startsWith('## ')&&l.includes('17:4x')&&l.includes('COMMON-R11'));
if(cut<protectedLen+1)fail('COMMON-R11 recent boundary not found',{cut});
const moved=before.slice(protectedLen,cut);
const kept=before.slice(cut);
if(!moved.length||!kept.length)fail('empty move or keep',{cut});
const movedBlock=boardBuf.subarray(starts[protectedLen],starts[cut]);
const payload=Buffer.concat(moved.map(l=>Buffer.from(l+NL,'utf8')));
const movedBlockExact=payload.equals(movedBlock);
if(!movedBlockExact)fail('moved block not byte-exact against board slice');
const acBuf=fs.readFileSync(arc);
if(acBuf.length&&acBuf[acBuf.length-1]!==10)fail('archive does not end with newline');
const N=acBuf.length,A0=sha(acBuf);
if(sha(fs.readFileSync(board))!==boardHash0)fail('board changed before archive append');
let appended=false,boardWritten=false;
let ac2,prefixOK=false,tail=[],missing=-1,mismatch=0,afterBuf,after=[],afterLines=0,pointer='';
try{
  fs.appendFileSync(arc,payload);appended=true;
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
  pointer='> 📦 第 '+(protectedLen+1)+'–'+cut+' 段已归档至 BOARD_ARCHIVE.md（'+stamp+'，逐字搬，missing=0）';
  const out=[...protectedLines,NL===String.fromCharCode(10)?'':null,pointer,...kept].filter(x=>x!==null);
  if(sha(fs.readFileSync(board))!==boardHash0)fail('board changed before board write');
  fs.writeFileSync(board,out.join(NL)+NL,'utf8');boardWritten=true;
  afterBuf=fs.readFileSync(board);
  after=readLines(afterBuf);
  afterLines=after.length;
  const protectedMissing=protectedLines.filter((l,i)=>after[i]!==l).length;
  const keptMissing=kept.filter((l,i)=>after[i+protectedLines.length+2]!==l).length;
  const afterText=after.join(NL);
  const reqAfterMissing=required.filter(h=>!afterText.includes(h)).length;
  const recentChecks={
    common_r11:afterText.includes('COMMON-R11')&&afterText.includes('17:4x'),
    m34:afterText.includes('M34')&&afterText.includes('1,366'),
    audit_sem_self:afterText.includes('AUDIT-SEM-SELF')&&afterText.includes('44/59'),
    closing_18xx:afterText.includes('18:0x')&&afterText.includes('STATUS_BOARD.md')
  };
  const recentMissing=Object.values(recentChecks).filter(v=>!v).length;
  const firstMovedAbsent=!afterText.includes(moved[0]);
  const firstKeptPresent=afterText.includes(kept[0]);
  const pointerOK=after[protectedLen+1]===pointer;
  if(afterLines>300||protectedMissing||keptMissing||recentMissing||reqAfterMissing||!firstMovedAbsent||!firstKeptPresent||!pointerOK)
    fail('final board verification failed',{after_lines:afterLines,protected_missing:protectedMissing,kept_missing:keptMissing,recent_missing:recentMissing,recent_checks:recentChecks,required_after_missing:reqAfterMissing,first_moved_absent:firstMovedAbsent,first_kept_present:firstKeptPresent,pointer_ok:pointerOK});
  const g={};
  const gm=path.join(root,'ra2youli','gamemd.exe');const gst=fs.statSync(gm);const gh=sha(fs.readFileSync(gm));
  g.B1={status:(gst.size===4825360&&gh.startsWith('73201CC0')&&gh.endsWith('F67476'))?'OK':'FAIL',size:gst.size,sha:gh};
  const dd=path.join(root,'ra2youli','ddraw.dll');const dh=sha(fs.readFileSync(dd));
  const ex=path.join(root,'ra2youli','except.txt');const es=fs.statSync(ex);const em=es.mtime.toLocaleString('sv-SE',{timeZone:'Asia/Shanghai',hour12:false}).replace('T',' ').slice(0,19);
  g.B2={status:(dh.startsWith('85E0F7D5')&&dh.endsWith('3B03A9')&&es.size===26272&&em==='2026-11-13 06:29:17')?'OK':'FAIL',ddraw_sha:dh,except_size:es.size,except_mtime:em};
  let proc='ERR';try{proc=execFileSync('powershell',['-NoProfile','-NonInteractive','-Command','@(Get-Process gamemd -ErrorAction SilentlyContinue).Count'],{encoding:'utf8'}).trim();}catch(e){proc='ERR';}
  const lock=fs.readFileSync(path.join(r14,'LIVE_LOCK'),'utf8').trim();
  g.B3={status:(proc==='0'&&lock==='RELEASED by W177-J (aborted)')?'OK':'FAIL',gamemd_process_count:proc,lock:lock};
  const ledgerPath=path.join(root,'lead','GOAL_THREE_TARGETS_20261018.md');const lbuf=fs.readFileSync(ledgerPath);
  const baseline=JSON.parse(fs.readFileSync(path.join(hyg,'H25_baseline.json'),'utf8'));
  const expected=baseline.ledger.prefix_sha256.toUpperCase();
  const lp=sha(lbuf.subarray(0,3348343));
  g.B4={status:(lbuf.length>=3459443&&lp===expected)?'OK':'FAIL',size:lbuf.length,prefix_bytes:3348343,prefix_sha:lp,baseline_sha:expected,matches_baseline:lp===expected};
  const cb=fs.readFileSync(path.join(r14,'COVERAGE','coverage.tsv'));const cl=readLines(cb);const hist={};
  for(const l of cl.slice(1)){const c=l.split('\t')[4];hist[c]=(hist[c]||0)+1;}
  const expectedHist={'[已证]':1366,'[静态推断]':6041,'[未证]':11024};
  const histOK=Object.entries(expectedHist).every(([k,v])=>hist[k]===v)&&Object.keys(hist).length===3;
  const confLines=readLines(fs.readFileSync(path.join(r14,'COVERAGE','CONFLICTS.tsv')));
  g.B5={status:(cl.length-1===18431&&histOK&&confLines.length===472)?'OK':'FAIL',data_lines:cl.length-1,histogram:hist,sha:sha(cb),conflicts_lines:confLines.length};
  const commonPath=path.join(r14,'R14_COMMON.md');const cst=fs.statSync(commonPath);
  g.B6={status:(cst.size===127465)?'OK':'FAIL',size:cst.size,sha:sha(fs.readFileSync(commonPath))};
  const fails=Object.entries(g).filter(([k,v])=>v.status!=='OK').map(([k])=>k);
  const result={
    task:'H28',
    before_lines:before.length,
    moved_start_line:protectedLen+1,
    moved_end_line:cut,
    moved_lines:moved.length,
    moved_block_byte_exact:movedBlockExact,
    after_lines:afterLines,
    pointer:pointer,
    pointer_line_1based:protectedLen+2,
    protected_lines:protectedLen,
    protected_missing:protectedLines.filter((l,i)=>after[i]!==l).length,
    kept_lines:kept.length,
    kept_missing:kept.filter((l,i)=>after[i+protectedLen+2]!==l).length,
    recent_segments:recentChecks,
    recent_missing:recentMissing,
    required_headers_missing:reqAfterMissing,
    archive_before_bytes:N,
    archive_before_sha:A0,
    archive_after_bytes:ac2.length,
    archive_after_sha:sha(ac2),
    archive_prefix_sha:sha(ac2.subarray(0,N)),
    archive_prefix_ok:prefixOK,
    archive_tail_lines:tail.length,
    compared:moved.length,
    missing:missing,
    mismatch:mismatch,
    gates:g,
    FAIL:fails,
    ok:fails.length===0
  };
  writeResult(result);
  console.log(JSON.stringify(result,null,2));
}catch(e){
  if(appended&&!boardWritten){try{fs.writeFileSync(arc,acBuf);}catch(_){ }}
  if(!fs.existsSync(resultPath)||!fs.readFileSync(resultPath,'utf8').includes('"task": "H28"'))writeResult({error:String(e&&e.message||e)});
  throw e;
}
