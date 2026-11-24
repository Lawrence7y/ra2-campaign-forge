// Independent path resolver for R17_R44_FACTINDEX_V32 (borrowed split_top/base_path idea from R43 work.py)
const fs = require('fs');
const path = require('path');
const ROOT = 'D:\\Project\\ra2-campaign-forge';
const OUT = path.join(ROOT,'lead','next_re_20261117_r14','R17_R44_FACTINDEX_V32');
const INDEX = path.join(OUT,'FACT_INDEX.tsv');
const PATHS = path.join(OUT,'paths.tsv');
function splitTop(s){const o=[];let d=0,st=0;for(let i=0;i<s.length;i++){const c=s[i];if(c==='(')d++;else if(c===')')d=Math.max(0,d-1);else if(c===';'&&d===0){o.push(s.slice(st,i).trim());st=i+1;}}o.push(s.slice(st).trim());return o.filter(Boolean);}
function basePath(raw){const i=raw.indexOf('(');return (i>=0?raw.slice(0,i):raw).trim();}
function main(){
  const lines=fs.readFileSync(INDEX,'utf8').replace(/\r/g,'').split('\n').filter(Boolean);
  const out=['fact_id\t路径\t是否存在\t实际绝对路径'];
  let resolved=0,partial=0,broken=0,checks=0;
  for(const ln of lines.slice(1)){
    const c=ln.split('\t');const fid=c[0],ev=c[3];let ok=0;const toks=splitTop(ev);
    for(const raw of toks){
      const p=path.resolve(ROOT,basePath(raw));let mark='NO';
      try{if(fs.existsSync(p)){ok++;mark=fs.statSync(p).isDirectory()?'YES:DIR':'YES:FILE';}}catch(e){}
      checks++;out.push([fid,raw,mark,p].join('\t'));
    }
    if(ok===toks.length)resolved++;else if(ok>0)partial++;else broken++;
  }
  fs.writeFileSync(PATHS,Buffer.from(out.join('\n')+'\n','utf8'));
  console.log('checks='+checks+' RESOLVED='+resolved+' PARTIAL='+partial+' BROKEN='+broken);
  if(broken!==0||partial!==0||resolved!==26) process.exitCode=1;
  // CR self-check
  for(const f of ['FACT_INDEX.tsv','README.md','REPORT.md','paths.tsv','verify.js']){
    if(fs.readFileSync(path.join(OUT,f)).includes(13)){console.log('CR FOUND in '+f);process.exitCode=1;}
  }
}
main();
