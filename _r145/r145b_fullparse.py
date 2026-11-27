#!/usr/bin/env python3
"""R145 B：完整内存操作数解析器重做「装表站点」普查（量化 R144 解析器漏了多少）。

R144 的 RE_STORE 形如 ^dword ptr \[([a-z0-9]+)([+-]0x[0-9a-f]+)?\](?:,(...))?$
它只接受单基址 + 正位移，且依赖 norm() 把 '-' 归一到 '+0x'（实测不归一）。
本脚本用一个完整解析器把 [base] [+index*scale] [+disp] 全部拆开，重扫全 .text：
  ① 所有 mov dword ptr <mem>, <imm> 站点（无论 base/index/scale/符号）
  ② imm ∈ VTS 的站点：总数 / distinct vt / 位移分布（正/零/负）
  ③ 与 R144 口径（RE_STORE 严格）逐项对照：多认出多少站点、多少张虚表
  ④ 残余：VTS − 全覆盖；再与 r144h 的 5 张残余对照
内存纪律：disasm_lite 64 KB 流式，不开 detail=True。

🔴 S-322（本脚本 v1 的两条预期是错的，已按实测改为可失败断言）：
  v1 写「单形态残余 <= 4」与「残余全部落在 R144 的 5 张之内」，实测都是 FALSE（残余 6 张，
  多出 0x7F7A1C / 0x7F7AEC）。原因不是解析器有问题，而是**本脚本只算「mov dword ptr <mem>, imm」一种形态**，
  那两张在 R144 里是被 **F5 寄存器搬运**（mov edx,0x7F7Axx → mov [esi+disp],edx）覆盖的，
  单形态口径当然看不到。结论由 r145c（口径对齐）给出：完整六形态并集 1214、残余 4。
  ⇒ 教训：**「残余」这个词必须带形态口径**，否则同一地址在不同口径下既算「已覆盖」又算「残余」。
"""
import sys, re, json, struct, collections, hashlib, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN = L.GEN
COLof = {}; coloff = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
for c in COL: coloff[c] = B.dw(c + 4)
off_of = lambda vt: coloff.get(COLof.get(vt))
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

MOVMEMIMM = re.compile(r'^dword ptr \[(.+)\],(.+)$')
def parse_mem(s):
    """'eax-0xc' / 'ecx+eax*4+0x1c' / '0x4a8660' -> (base,index,scale,disp,kind)"""
    s = s.replace(' ', '')
    kind = 'abs' if s.startswith('0x') else 'reg'
    toks = re.findall(r'[+-]?[^+-]+', s)
    base = index = None; scale = 0; disp = 0
    for i, t in enumerate(toks):
        sign = -1 if t.startswith('-') else 1
        core = t.lstrip('+-')
        if '*' in core:
            r, k = core.split('*'); index = r; scale = int(k)
        elif re.fullmatch(r'0x[0-9a-f]+|\d+', core):
            disp += sign * (int(core, 16) if core.startswith('0x') else int(core))
        else:
            if base is None: base = core
            elif index is None: index = core; scale = 1
            else: return None
    return base, index, scale, disp, kind

sites = []           # (va, base, index, scale, disp, kind, vt)
strict_sites = []    # RE_STORE 严格口径下能认出的（仅用于对照）
dropped = []
for a, sz, mn, op in B.sweep(md):
    if not op or not mn in ('mov',): continue
    m = MOVMEMIMM.match(op)
    if not m: continue
    src = m.group(2)
    if not L.RE_IMM.match(src): continue
    iv = immv(src)
    p = parse_mem(m.group(1))
    if p is None:
        dropped.append((a, op)); continue
    if iv in VTS:
        sites.append((a, p[0], p[1], p[2], p[3], p[4], iv))
    if L.RE_STORE.match(op) and iv in VTS:
        strict_sites.append((a, iv))

cov = {s[6] for s in sites}
cov_strict = {s[1] for s in strict_sites}
resid = sorted(VTS - cov)
mis4 = set(int(x, 16) for x in json.load(open('_r144/r144h_stack.json'))['resid']) - {0x7E6060}
resid_strict = sorted(VTS - cov_strict)
prev5 = [int(x, 16) for x in json.load(open('_r144/r144h_stack.json'))['resid']]

disp_hist = collections.Counter(s[4] for s in sites)
neg = [s for s in sites if s[4] < 0]
idxform = [s for s in sites if s[1] is not None and s[2] is not None]
agree = sum(1 for s in sites if s[4] == off_of(s[6]))
agree_nonzero = sum(1 for s in sites if s[4] > 0 and s[4] == off_of(s[6]))
n_nonzero = sum(1 for s in sites if s[4] > 0)
neg_agree = sum(1 for s in neg if s[4] == off_of(s[6]))

res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'vt_distinct': len(VTS),
 'sites_all_forms': len(sites), 'distinct_vt_all': len(cov),
 'sites_strict': len(strict_sites), 'distinct_vt_strict': len(cov_strict),
 'extra_sites': len(sites) - len(strict_sites), 'extra_vt': len(cov - cov_strict),
 'unparsed_n': len(dropped), 'unparsed_sample': [[hex(a), o] for a, o in dropped[:8]],
 'resid_n': len(resid), 'resid': [hex(v) for v in resid],
 'resid_strict_n': len(resid_strict),
 'resid_eq_r144_5': [hex(v) for v in resid] == [hex(v) for v in sorted(prev5)],
 'resid_are_prev5': set(resid) <= set(prev5), 'prev5_covered': [hex(v) for v in prev5 if v in cov],
 'neg_sites': len(neg), 'neg_distinct': len({s[6] for s in neg}),
 'idx_sites': len(idxform), 'idx_distinct': len({s[6] for s in idxform}),
 'agree_all': agree, 'agree_rate_all': round(agree / max(1, len(sites)), 4),
 'agree_nonzero': agree_nonzero, 'n_nonzero': n_nonzero,
 'agree_rate_nonzero': round(agree_nonzero / max(1, n_nonzero), 4),
 'neg_agree': neg_agree,
 'disp_hist_top': disp_hist.most_common(10),
 'sample_neg': [[hex(a), b, i, sc, d, hex(v)] for a, b, i, sc, d, k, v in neg[:10]],
 'sample_idx': [[hex(a), b, i, sc, d, hex(v)] for a, b, i, sc, d, k, v in idxform[:10]],
 'elapsed_s': round(time.time() - T0, 1),
}

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('正控：parse_mem 解出 eax-0xc 的 disp=-12', parse_mem('eax-0xc') == ('eax', None, 0, -12, 'reg'), parse_mem('eax-0xc'))
chk('正控：parse_mem 解出 ecx+eax*4+0x1c', parse_mem('ecx+eax*4+0x1c') == ('ecx', 'eax', 4, 28, 'reg'), parse_mem('ecx+eax*4+0x1c'))
chk('反控：parse_mem 对三寄存器式返回 None', parse_mem('esi+ecx+edx') is None, parse_mem('esi+ecx+edx'))
chk('未解析站点占比 < 1%', len(dropped) < max(5, 0.01 * (len(sites) + len(dropped))), [len(dropped), len(sites)])
chk('完整解析器认出 >= 严格口径的站点数', len(sites) >= len(strict_sites), [len(sites), len(strict_sites)])
chk('完整解析器多认出 >= 1 张虚表', len(cov) > len(cov_strict), [len(cov), len(cov_strict)])
chk('0x7E6060 被完整解析器覆盖（R144 判它无装表站点）', 0x7E6060 in cov, 0x7E6060 in cov)
chk('单形态口径残余 == 6（比 R144 的 5 张多 2 张，见 S-322）', len(resid) == 6, len(resid))
chk('残余 ⊇ R144 的 4 张误收，且额外 2 张是 .rdata（F5 覆盖，不属单形态口径）',
    mis4 <= set(resid) and {v for v in resid if B.sec_of(v) == '.rdata'} == set(resid) - mis4,
    [hex(v) for v in sorted(set(resid) - mis4)])
chk('负位移站点数 >= 5', len(neg) >= 5, len(neg))
res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r145/r145b_fullparse.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'POS'}, indent=1, ensure_ascii=False)[:4200])
for p in POS: print(('PASS ' if p[1] else 'FAIL ') + '%-52s %s' % (p[0], p[2]))
print('POS %d/%d FAIL %d elapsed %ss' % (res['pos_pass'], len(POS), res['pos_fail'], res['elapsed_s']))
