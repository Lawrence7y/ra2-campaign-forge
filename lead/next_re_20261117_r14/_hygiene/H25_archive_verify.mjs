// H25 archive verifier (ESM-native, runs via node script.mjs; also mirrored in H25.md)
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const r14=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const board=path.join(r14,'STATUS_BOARD.md'),arc=path.join(r14,'BOARD_ARCHIVE.md');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex').toUpperCase();
const bc=fs.readFileSync(board);let before=bc.toString('utf8').split(/\r?\n/);if(before[before.length-1]==='')before.pop();
const cut=before.findIndex(l=>l.startsWith('## \u{1F504} R14 \u7eed\u8dd1\u7b2c 6 \u6bb5'));
if(cut<0)throw Error('s6 header not found');
const moved=before.slice(0,cut),kept=before.slice(cut);
const ac=fs.readFileSync(arc),N=ac.length,A0=sha(ac);
fs.appendFileSync(arc,Buffer.concat(moved.map(l=>Buffer.from(l+'\n','utf8'))));
const ac2=fs.readFileSync(arc);const prefixOK=sha(ac2.subarray(0,N))===A0;
let tail=ac2.subarray(N).toString('utf8').split('\n');if(tail[tail.length-1]==='')tail.pop();
let missing=0;for(let i=0;i<Math.max(moved.length,tail.length);i++){if(i>=moved.length||i>=tail.length||moved[i]!==tail[i])missing++;}
const stamp=new Date().toLocaleString('sv-SE',{timeZone:'Asia/Shanghai'}).replace('T',' ').slice(0,16);
const pointer='> \u{1F4E6} \u7b2c 1\u2013'+cut+' \u6bb5\u5df2\u5f52\u6863\u81f3 BOARD_ARCHIVE.md\uff08'+stamp+'\uff0c\u9010\u5b57\u642c\uff0cmissing=0\uff09';
const out=kept.slice();out.splice(1,0,'',pointer);fs.writeFileSync(board,out.join('\n')+'\n','utf8');
const after=fs.readFileSync(board,'utf8').split(/\r?\n/);if(after[after.length-1]==='')after.pop();
const text=after.join('\n');
const req=['# R14 \u8fd0\u884c\u770b\u677f v2','## \u57fa\u7ebf\u4e0e\u5e76\u53d1\u63a7\u5236','## \u5e38\u8bbe\u771f\u673a\u6388\u6743\uff08\u5df2\u751f\u6548\uff09','## Lead \u53e3\u5f84\u88c1\u5b9a\uff08\u6d41\u7a0b\u89c4\u8303\uff0c\u975e\u6280\u672f\u7ed3\u8bba\uff09'];
console.log(JSON.stringify({before_lines:before.length,moved_lines:moved.length,after_lines:after.length,
 archive_before_bytes:N,archive_before_sha:A0,archive_after_bytes:ac2.length,archive_after_sha:sha(ac2),prefix_sha:sha(ac2.subarray(0,N)),prefix_ok:prefixOK,
 missing,compared:moved.length,tail_lines:tail.length,pointer,
 required_headers_missing:req.filter(h=>!text.includes(h)).length,
 has_s6:text.includes('R14 \u7eed\u8dd1\u7b2c 6 \u6bb5'),has_s7:text.includes('R14 \u7eed\u8dd1\u7b2c 7 \u6bb5'),has_r1:text.includes('\u6536\u4ef6 1'),has_r2r3:text.includes('\u6536\u4ef6 2 \u4e0e 3')},null,2));
