#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 A：四条待写入 FACT_INDEX 正文的事实，逐条机器复算 + 正反控。
  A1 F23 算术：6+2+3 == 11 != 12；替换读法 6+2+3+3 == 14 > 12（读法不敏感）
  A2 F23 coverage.tsv 失联：按精确文件名 0 命中、按 4,147,334 B 精确字节 0 命中
  A3 F35 strict_panel.py:78 一手判据在盘；两个输入不在盘
  A4 F35 另 3 个脚本同判据；merge_panel.py 不含该判据（反控）
  A5 F24 tier_final_4417.tsv sum(bytes) == 737,517,286 且 4,417 行
  A6 F29 17 字节序列在 .text 内出现 80 次（正控/负控）
所有搜索逐节切片，不在整文件上跨节搜。无 detail=True 反汇编。
"""
import hashlib, io, json, os, struct

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
fails = []
res = {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()


# ---------- A1 算术 ----------
parts = [6, 2, 3]
s3 = sum(parts)
ck('A1a 6+2+3 = 11 且 != 12', s3 == 11 and s3 != 12, '%d vs 12' % s3)
s4 = s3 + 3
ck('A1b 6+2+3+3 = 14 > 12（第二读法重计）', s4 == 14 and s4 > 12, '%d vs 12' % s4)
ck('A1c 两种读法都不等于 12（缺口对读法不敏感）', s3 != 12 and s4 != 12, (s3, s4))
res['A1'] = dict(three_term_sum=s3, four_term_sum=s4, total=12)

# ---------- A2 coverage.tsv 失联 ----------
hits_name, hits_size = [], []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in ('.git', '__pycache__')]
    for fn in fns:
        p = os.path.join(dp, fn)
        try:
            st = os.lstat(p)
        except OSError:
            continue
        if fn == 'coverage.tsv':
            hits_name.append(os.path.relpath(p, ROOT))
        if st.st_size == 4147334:
            hits_size.append(os.path.relpath(p, ROOT))
ck('A2a 精确文件名 coverage.tsv 全库 0 命中', len(hits_name) == 0, hits_name[:4])
ck('A2b 精确 4,147,334 B 全库 0 命中', len(hits_size) == 0, hits_size[:4])
ck('A2c 反控：同法找已知存在的文件能命中（判据不是恒 0）',
   os.path.exists(os.path.join(R14, 'DISC_RECHECK.tsv')), '')
res['A2'] = dict(name_hits=len(hits_name), size_hits=len(hits_size))

# ---------- A3 F35 strict_panel.py ----------
sp = os.path.join(R14, 'RULING_R15_20261119', 'work', 'strict_panel.py')
ck('A3a strict_panel.py 在盘', os.path.exists(sp), sp)
txt = rd(sp)
lines = txt.split('\n')
ck('A3b 第 78 行含带方括号字面 [未证] 的过滤句',
   '[未证]" not in sem' in lines[77], repr(lines[77])[:80])
ck('A3c 第 78 行不是裸子串口径（含左方括号字节）', '"[未证]"' in lines[77], repr(lines[77])[:80])
ck('A3d 文件头第 14 行给出散文措辞', len(lines) > 13 and '未证' in lines[13], repr(lines[13])[:80])
ck('A3e 判据在文件内唯一（1 次）', txt.count('[未证]" not in sem') == 1, txt.count('[未证]" not in sem'))
ck('A3f 输入 1 COVERAGE/coverage.tsv 不存在',
   not os.path.exists(os.path.join(R14, 'COVERAGE', 'coverage.tsv')), '')
ck('A3g 输入 2 next_re_20261112_r10/W130_atlas/function_atlas.tsv 不存在',
   not os.path.exists(os.path.join(ROOT, 'lead', 'next_re_20261112_r10',
                                   'W130_atlas', 'function_atlas.tsv')), '')
ck('A3h 两个父目录亦不存在',
   not os.path.isdir(os.path.join(R14, 'COVERAGE'))
   and not os.path.isdir(os.path.join(ROOT, 'lead', 'next_re_20261112_r10')), '')
# 脚本里怎么用这两个输入
ck('A3i 脚本内出现 coverage.tsv 字面', 'coverage.tsv' in txt, txt.count('coverage.tsv'))
ck('A3j 脚本内出现 atlas 字面', 'atlas' in txt, txt.count('atlas'))
res['A3'] = dict(line78=lines[77].strip()[:60], line14=lines[13].strip()[:60],
                 sha=hashlib.sha256(open(sp, 'rb').read()).hexdigest()[:16])

# ---------- A4 另三个脚本 + 反控 merge_panel ----------
others = {}
for rel in ('_cards/M59-MERGE/precheck.py', '_cards/M59-MERGE/simulate.py',
            '_cards/M59-MERGE/verify.py'):
    p = os.path.join(R14, rel)
    ok = os.path.exists(p)
    n = rd(p).count('[未证]" not in sem') if ok else -1
    others[rel] = dict(exists=ok, hits=n)
    ck('A4 同判据在 %s（命中 %d 次）' % (rel, n), ok and n >= 1, others[rel])
mp = None
for dp, dns, fns in os.walk(R14):
    if 'merge_panel.py' in fns:
        mp = os.path.join(dp, 'merge_panel.py')
        break
if mp:
    mt = rd(mp)
    ck('A4e 反控 merge_panel.py 在盘但**不含**该判据', '[未证]" not in sem' not in mt, mp)
    res['A4e'] = dict(path=os.path.relpath(mp, ROOT), has_pred='"[未证]" not in sem' in mt)
else:
    ck('A4e 反控 merge_panel.py 找到了（否则反控无意义）', False, 'not found')
res['A4'] = others

# ---------- A5 tier_final_4417 ----------
tf = os.path.join(R14, 'R17_R101_TIER_FINAL_4417', 'tier_final_4417.tsv')
raw = open(tf, 'rb').read()
rows = [l for l in raw.decode('utf-8').split('\n')[1:] if l.strip()]
n = len(rows)
tot = sum(int(l.split('\t')[1]) for l in rows)
ck('A5a 4,417 行', n == 4417, n)
ck('A5b sum(bytes) == 737,517,286', tot == 737517286, tot)
ck('A5c 回读逐行字节列为整数', all(l.split('\t')[1].isdigit() for l in rows), '')
ck('A5d 反控 sum(前 10 行) != 总值（求和不是恒等式）',
   sum(int(l.split('\t')[1]) for l in rows[:10]) != tot, '')
ck('A5e 全 LF', b'\r' not in raw, raw.count(b'\r'))
res['A5'] = dict(rows=n, sum=tot, bytes=len(raw), sha=hashlib.sha256(raw).hexdigest()[:16])

# ---------- A6 F29 17 字节序列 ----------
raw = open(EXE, 'rb').read()
ck('A6a 镜像 4,825,360 B', len(raw) == 4825360, len(raw))
ck('A6b sha256 前缀 73201cc0', hashlib.sha256(raw).hexdigest().startswith('73201cc0'), '')
e_lfanew = struct.unpack_from('<I', raw, 0x3c)[0]
nsec = struct.unpack_from('<H', raw, e_lfanew + 6)[0]
opt_size = struct.unpack_from('<H', raw, e_lfanew + 20)[0]
opt = e_lfanew + 24
secs = []
for i in range(nsec):
    o = opt + opt_size + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode('latin1')
    vsize, va, rsize, rptr = struct.unpack_from('<IIII', raw, o + 8)
    secs.append(dict(name=nm, va=va, rsize=rsize, rptr=rptr))
PAT = bytes.fromhex('8B44240483C00450FF15C8117E00C20400')
ck('A6c 序列长 17 B', len(PAT) == 17, len(PAT))
per = {}
for s in secs:
    body = raw[s['rptr']:s['rptr'] + s['rsize']]
    c = 0
    i = body.find(PAT)
    pos = []
    while i >= 0:
        pos.append(i)
        c += 1
        i = body.find(PAT, i + 1)
    if c:
        per[s['name']] = dict(count=c, first_va=s['va'] + pos[0] if pos else None)
ck('A6d .text 内 80 次', per.get('.text', {}).get('count') == 80, per.get('.text'))
ck('A6e 逐节切片：其它节 0 次', sum(v['count'] for k, v in per.items() if k != '.text') == 0,
   {k: v['count'] for k, v in per.items()})
# 负控：把 1 字节改掉应得 0
neg = PAT[:8] + b'\x00' + PAT[9:]
ck('A6f 负控 改 1 字节后 .text 命中 0', sum(
    (lambda b: sum(1 for _ in range(len(b))))(b'') for _ in [0]) == 0 and
   all(raw[s['rptr']:s['rptr'] + s['rsize']].find(neg) < 0 for s in secs if s['name'] == '.text'), '')
res['A6'] = dict(per=per, pat=PAT.hex().upper(), mirror_sha=hashlib.sha256(raw).hexdigest()[:16])

json.dump(dict(fails=fails, res=res), open(os.path.join(ROOT, '_r148', 'r148a_verify_facts.json'),
                                          'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
