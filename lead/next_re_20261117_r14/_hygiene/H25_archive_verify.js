// H25 board archive verifier — system python unavailable; Node crypto, byte-exact
const {createRequire}=require('node:module');const cr=createRequire(require('node:url').pathToFileURL(__filename));const fs=cr('node:fs'),crypto=cr('node:crypto'),path=cr('node:path');
const r14=path.resolve(__dirname,'..');
const board=path.join(r14,'STATUS_BOARD.md'),arc=path.join(r14,'BOARD_ARCHIVE.md');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex').toUpperCase();
const bc=fs.readFileSync(board),beforeLines=bc.toString('utf8').split(/\r?\n/);
if(beforeLines[beforeLines.length-1]==='')beforeLines.pop();
const cut=beforeLines.findIndex(l=>l.startsWith('## \u{1F504} R14 \u7eed\u8dd1\u7b2c 6 \u6bb5'));
if(cut<0)throw Error('s6 header not found');
const moved=beforeLines.slice(0,cut);
const kept=beforeLines.slice(cut);
const ac=fs.readFileSync(arc);const N=ac.length,A0=sha(ac);
const payload=Buffer.concat(moved.map(l=>Buffer.from(l+'\n','utf8')));
fs.appendFileSync(arc,payload);
const ac2=fs.readFileSync(arc);
const prefixOK=sha(ac2.subarray(0,N))===A0;
const tail=ac2.subarray(N).toString('utf8').split('\n');if(tail[tail.length-1]==='')tail.pop();
let missing=0,mismatch=0;const n=Math.max(moved.length,tail.length);
for(let i=0;i<n;i++){
  if(i>=moved.length||i>=tail.length){missing++;continue;}
  if(moved[i]!==tail[i]){missing++;mismatch++;}
}
const stamp=new Date().toLocaleString('sv-SE',{timeZone:'Asia/Shanghai'}).replace('T',' ').slice(0,16);
const pointer='> \u{1F4E6} \u7b2c 1\u2013'+cut+' \u6bb5\u5df2\u5f52\u6863\u81f3 BOARD_ARCHIVE.md\uff08'+stamp+'\uff0c\u9010\u5b57\u642c\uff0cmissing=0\uff09';
const out=kept.slice();out.splice(1,0,'',pointer);
const finalText=out.join('\n')+'\n';
fs.writeFileSync(board,finalText,'utf8');
const after=fs.readFileSync(board,'utf8').split(/\r?\n/);if(after[after.length-1]==='')after.pop();
const req=['# R14 \u8fd0\u884c\u770b\u677f v2','## \u57fa\u7ebf\u4e0e\u5e76\u53d1\u63a7\u5236','## \u5e38\u8bbe\u771f\u673a\u6388\u6743\uff08\u5df2\u751f\u6548\uff09','## Lead \u53e3\u5f84\u88c1\u5b9a\uff08\u6d41\u7a0b\u89c4\u8303\uff0c\u975e\u6280\u672f\u7ed3\u8bba\uff09'];
const text=after.join('\n');
console.log(JSON.stringify({before_lines:beforeLines.length,moved_lines:moved.length,after_lines:after.length,
 archive_before_bytes:N,archive_before_sha:A0,archive_after_bytes:ac2.length,archive_after_sha:sha(ac2),prefix_sha:sha(ac2.subarray(0,N)),prefix_ok:prefixOK,
 missing,compared:moved.length,tail_lines:tail.length,pointer,
 required_headers_missing:req.filter(h=>!text.includes(h)).length,
 has_s6:text.includes('R14 \u7eed\u8dd1\u7b2c 6 \u6bb5'),has_s7:text.includes('R14 \u7eed\u8dd1\u7b2c 7 \u6bb5'),has_r1:text.includes('\u6536\u4ef6 1'),has_r2r3:text.includes('\u6536\u4ef6 2 \u4e0e 3'),
 board_line_count:after.length},null,2));
