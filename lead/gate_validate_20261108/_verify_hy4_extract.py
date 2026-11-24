# -*- coding: utf-8 -*-
# _verify_hy4_extract.py —— 独立复核员·hy4 自写提取器（不复用被核方的 _gv_extract_gates.py）
import json, re, hashlib, pathlib, datetime, sys

REPO = pathlib.Path('D:/Project/ra2-campaign-forge')
RUNS = REPO / '.zcode' / 'workflow-runs'
OUT = REPO / 'lead' / 'gate_validate_20261108'

def js_unescape(s):
    out=[]; i=0
    mp={'n':'\n','t':'\t','r':'\r','b':'\b','f':'\f','v':'\v','0':'\0'}
    while i < len(s):
        c=s[i]
        if c=='\\' and i+1<len(s):
            n=s[i+1]
            if n=='x': out.append(chr(int(s[i+2:i+4],16))); i+=4; continue
            if n=='u':
                if i+2<len(s) and s[i+2]=='{':
                    j=s.index('}',i+3); out.append(chr(int(s[i+3:j],16))); i=j+1; continue
                out.append(chr(int(s[i+2:i+6],16))); i+=6; continue
            if n in mp: out.append(mp[n]); i+=2; continue
            if n=='\n': i+=2; continue
            out.append(n); i+=2; continue
        out.append(c); i+=1
    return ''.join(out)

def split_array(src,start):
    assert src[start]=='['
    i=start+1; elems=[]; cur=[]; depth=0; in_str=False; ch=''
    while i<len(src):
        c=src[i]
        if in_str:
            cur.append(c)
            if c=='\\': cur.append(src[i+1]); i+=2; continue
            if c==ch: in_str=False
            i+=1; continue
        if c in ('"',"'",'`'): in_str=True; ch=c; cur.append(c); i+=1; continue
        if c=='[': depth+=1
        elif c==']':
            if depth==0: elems.append(''.join(cur).strip()); return elems,i
            depth-=1
        if depth==0 and c==',': elems.append(''.join(cur).strip()); cur=[]; i+=1; continue
        cur.append(c); i+=1
    raise ValueError('unterminated')

def parse_lit(tok):
    tok=tok.strip()
    if tok.startswith('"') and tok.endswith('"'): return js_unescape(tok[1:-1])
    if tok.startswith("'") and tok.endswith("'"): return js_unescape(tok[1:-1])
    raise ValueError('non-literal: %r' % tok[:70])

files=sorted(RUNS.glob('dwfrun-*.mjs'))
print('A. .zcode/workflow-runs/dwfrun-*.mjs 总数 =',len(files),flush=True)

rows=[]
for m in files:
    t=m.read_text(encoding='utf-8',errors='replace')
    key='export const payload = '
    p0=t.find(key)
    if p0<0:
        rows.append(dict(file=m.name,payload=False)); continue
    payload,_=json.JSONDecoder().raw_decode(t,p0+len(key))
    low=payload.get('lowered','')
    gd=re.search(r'const\s+GATE_CODE\s*=\s*\[',low)
    mention_only=('GATE_CODE' in low and not gd)
    if not gd:
        rows.append(dict(file=m.name,payload=True,gate=False,mention_only=mention_only,
                         has_gateOk='gateOk' in low))
        continue
    start=gd.end()-1
    elems,endidx=split_array(low,start)
    elems=[e for e in elems if e.strip()!='']
    lines=[]; bad=[]
    for idx,e in enumerate(elems):
        try: lines.append(parse_lit(e))
        except ValueError as ex: bad.append((idx,str(ex)))
    # join 分隔符：只看数组结束后的前 60 字符（线性，无 .* 大回溯）
    tail=low[endidx:endidx+60]
    jm=re.match(r'\]\s*\.\s*join\(\s*(["\'`])([^\1]*?)\1\s*\)',tail)
    if jm:
        sep=js_unescape(jm.group(2))
    else:
        sep='\n'
        print('   WARN join 未识别, tail=%r' % tail[:30],flush=True)
    code=sep.join(lines)
    mt=datetime.datetime.fromtimestamp(m.stat().st_mtime)
    rows.append(dict(file=m.name,payload=True,gate=True,decoded=not bad,bad=bad,
                     code=code,lines=len(lines),bytes=len(code.encode('utf-8')),
                     sha=hashlib.sha256(code.encode('utf-8')).hexdigest(),
                     mtime=mt.strftime('%Y-%m-%d %H:%M:%S'),
                     has_gateOk='gateOk' in low,
                     executed=bool(re.search(r'-c",\s*GATE_CODE',low))))

gates=[r for r in rows if r.get('gate')]
dec=[r for r in gates if r.get('decoded')]
print('B. 定义 const GATE_CODE 的 mjs =',len(gates),'；成功解码 =',len(dec),flush=True)
print('C. 仅提及 GATE_CODE 字样但无定义 =',sum(1 for r in rows if r.get('mention_only')),flush=True)
print('D. 解码失败 =',sum(1 for r in gates if not r.get('decoded')),flush=True)
print('E. 全部有 gateOk 字段 =',all(r.get('has_gateOk') for r in gates),
      '；全部 -c GATE_CODE 执行 =',all(r.get('executed') for r in gates),flush=True)
hex_total=sum(r['code'].count('hexdigest') for r in dec)
print('F. %d 个门禁码中 "hexdigest" 出现总次数 = %d' % (len(dec),hex_total),flush=True)
seal='2026-11-08 16:28:00'
before=[r for r in dec if r['mtime']<seal]; after=[r for r in dec if r['mtime']>=seal]
print('G. 门禁 mtime < 16:28 =',len(before),'；>= 16:28 =',len(after),flush=True)
print('   16:28 之后新增:',[(r['file'][:20],r['mtime']) for r in after],flush=True)
print('H. 门禁清单（file前24 / mtime / lines / bytes / sha12）',flush=True)
for r in sorted(dec,key=lambda x:x['file']):
    print('   %-24s %s lines=%2d bytes=%5d sha=%s' % (r['file'][:24],r['mtime'],r['lines'],r['bytes'],r['sha'][:12]),flush=True)

outdir=OUT/'_verify_gates'; outdir.mkdir(parents=True,exist_ok=True)
manifest=[]
for r in dec:
    short=r['file'].replace('dwfrun-','')[0:8]
    gp=outdir/(short+'.py')
    gp.write_bytes(r['code'].encode('utf-8'))
    manifest.append(dict(short=short,file=r['file'],mtime=r['mtime'],lines=r['lines'],
                         bytes=r['bytes'],sha=r['sha'],gate_py=str(gp)))
(OUT/'_verify_hy4_gates_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=1),encoding='utf-8')
print('I. manifest -> _verify_hy4_gates_manifest.json 共 %d 条' % len(manifest),flush=True)
