# -*- coding: utf-8 -*-
"""FACT_INDEX v5.24：F24 的「1,242 件单列」已过时——其中 976 件早有逐件裁决。
加法式修正：不改区间数（避免在缺「多数派方向」时抢定新区间，且并轨会改 C′ 的语义定义），
只把裁决分布写进限定⑤，并把区间标为「待按新事实重算」。
复算：732+244+266=1,242；10,251,220+31,468,350+4,965,209=46,684,779；254/266=95.5%；1,995,960+2,969,249=4,965,209。
"""
import io, os, re, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R85_FACTINDEX_V523')
DST  = os.path.join(R14, 'R17_R86_FACTINDEX_V524')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54
rows = [l.split('\t') for l in data]
for r in rows:
    assert len(r) == 5, (r[0], len(r))
f24 = {r[0]: r for r in rows}['F24']

# ① statement：把「1,242 件…既不计入也不算已排除」改为带裁决分布的表述
OLD_ST = '若要「干净上限」只能是 **18,712~19,954 文件 / 1,363,708,720~1,410,393,499 B**'
NEW_ST = ('该桶**已部分裁决**：**732 件 / 10,251,220 B 判为对象抄本、244 件 / 31,468,350 B 判为过程输出、'
          '266 件 / 4,965,209 B 仍无法判定**（三者合计 1,242 件 / 46,684,779 B）；'
          '266 件里真正的名-内容冲突仅 12 件，254 件（95.5%）是内容信号弱；'
          '用「同目录多数派」还可再裁 114 件 / 1,995,960 B（留一法 96.4%），余 152 件 / 2,969,249 B。'
          '**上述 18,712~19,954 的区间是在「1,242 件整桶未裁」时给的，已过时**：'
          '若把 732 件对象并入 C′ 则得 19,444 件 / 1,373,959,940 B，再加余 152 件得上界 19,596 件 / 1,376,929,189 B——'
          '**但这等于把 C′ 从「未被排除集合」改成「对象 ∪ 残差」，是改定义不是修数，故本版不给新区间，标为待按新事实重算**')
assert OLD_ST in f24[1], 'statement range fragment not found'
new_stmt = f24[1].replace(OLD_ST, NEW_ST)
assert new_stmt != f24[1]

# ② limitations：限定⑤ 末尾补裁决分布与 _audit 结论
ADD = ('【限定⑤附·1,242 件桶的最新状态（v5.24 补）】**732 件 / 10,251,220 B 判对象抄本、244 件 / 31,468,350 B 判过程输出、'
       '266 / 4,965,209 B 仍无法判定**（合计 1,242 / 46,684,779 B，我复算一致）；266 里真冲突仅 12 件、'
       '254 件（95.5%）为内容信号弱（前 8 KiB 行首 VA 多为 0%）；同目录多数派（同父目录已裁件 ≥3 且同向 ≥75%，留一法 96.4%）'
       '可再裁 114 件 / 1,995,960 B，余 152 件 / 2,969,249 B。'
       '另：C′ 内 `_audit` 段共 540 件 / 67,129,511 B，其中 P1a 对象抄本 527 件 / 66,864,593 B（97.6% 件、99.6% 字节）'
       '⇒ 该段**不可整体归为过程区**，须逐件判；而同目录段的排除集里另有 1,111 件属过程/元记录。')
assert '\n' not in ADD
new_lim = f24[4].rstrip() + ADD
assert '1,242 件桶的最新状态' in new_lim

f24[1] = new_stmt
f24[4] = new_lim
ADDS = [r'lead\next_re_20261117_r14\R17_R84_T2_EVID2\REPORT.md']
for a in ADDS:
    assert a not in f24[3]
    assert os.path.isfile(os.path.join(ROOT, a.replace('\\', '/'))), a
    f24[3] = f24[3] + ';' + a

out = '\n'.join([lines[0]] + ['\t'.join(r) for r in rows]) + '\n'
assert '\r' not in out
for ch in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'):
    assert ch not in out, 'invisible U+%04X' % ord(ch)
assert new_stmt.count('（') == new_stmt.count('）'), (new_stmt.count('（'), new_stmt.count('）'))
# 数字断言
assert 732 + 244 + 266 == 1242
assert 10251220 + 31468350 + 4965209 == 46684779
assert 1995960 + 2969249 == 4965209
assert 18712 + 732 == 19444 and 1363708720 + 10251220 == 1373959940
assert 19444 + 152 == 19596 and 1373959940 + 2969249 == 1376929189
assert len(re.findall(r'【限定[①②③④⑤⑥⑦]·', new_lim)) == 7, len(re.findall(r'【限定[①②③④⑤⑥⑦]·', new_lim))

dst = os.path.join(DST, 'FACT_INDEX.tsv')
assert not os.path.exists(dst)
with open(dst, 'x', encoding='utf-8', newline='') as f:
    f.write(out)

back = io.open(dst, encoding='utf-8', newline='').read()
assert back == out
assert back.count('\n') == 55 and back.count('\t') == 55 * 4
brows = [l.split('\t') for l in back.split('\n')[1:] if l.strip()]
assert len(brows) == 54
for a, b in zip(rows, brows):
    assert a[0] == b[0] and len(b) == 5
    if a[0] != 'F24':
        assert a == b, 'unexpected change ' + a[0]
dist = {}
for b in brows:
    dist[b[2]] = dist.get(b[2], 0) + 1
assert dist.get('[已证]') == 27 and dist.get('[静态推断]') == 1 and dist.get('未取得') == 2 and dist.get('[流程]') == 24

print('OK', dst, os.path.getsize(dst), 'bytes')
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
print('grade dist =', dist, '; F24 evidence items =', len(f24[3].split(';')))
