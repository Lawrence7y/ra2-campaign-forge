#!/usr/bin/env python3
"""R145 A：负位移装表站点被 RE_STORE 整类丢弃（R144 残余 5 张的根因）。

线索：残余表 0x7E6060 在 .text 里唯一的 4 字节出现是 0x4A8660 处的
      mov dword ptr [eax - 8],0x7e6060  —— 这明明就是装表站点。
为什么 R144 判它「没找到装表站点」？
  capstone 对负位移打印成 '[eax - 8]'（减号两侧有空格），
  r143lib.norm() 只压 '+' ',' '*' 两侧空白，**不压 '-'**；
  于是十进制→十六进制归一的正则 ([+-])(\d+) 因 '-' 后跟空格而失配，
  RE_STORE 的 ^dword ptr \[([a-z0-9]+)([+-]0x[0-9a-f]+)?\] 也要求符号紧跟基址 ⇒ 整条丢弃。

本脚本：同一遍 disasm_lite 流式里用**宽容解析器**重新解析所有 dword 立即数写，
分三路计数：被 RE_STORE 接受 / 被拒且位移为负 / 被拒的其他形态，
再判定负位移站点对虚表覆盖的增量、以及 5 张残余是否被覆盖。
"""
import sys, re, json, struct, hashlib, collections, time
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN, STK = L.GEN, L.STK
IMM = L.RE_IMM

# 宽容解析器：允许符号两侧空格、允许负位移
TOL = re.compile(r'^dword ptr \[([a-z0-9]+)(?:\s*([+-])\s*(0x[0-9a-f]+|\d+))?\](?:,(.+))?$')
def immv(t):
    return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

def tol_parse(op):
    m = TOL.match(op)
    if not m: return None
    base, sign, num, tgt = m.group(1), m.group(2), m.group(3), m.group(4)
    if num is None: disp = 0
    else:
        v = int(num, 16) if num.startswith('0x') else int(num)
        disp = -v if sign == '-' else v
    return base, disp, tgt

acc, rej_neg, rej_other = [], [], []
neg_imm_vts = []      # (va, base, disp, vt)
acc_imm_vts = []
raw_neg_shapes = collections.Counter()

for a, sz, mn, op in B.sweep(md):
    if not op or not op.startswith('dword ptr ['): continue
    m = L.RE_STORE.match(op)
    t = tol_parse(op)
    if m:
        tgt = m.group(3)
        if tgt is not None and IMM.match(tgt):
            acc.append((a, m.group(1), L.disp_of(m.group(2))))
            iv = immv(tgt)
            if iv in VTS: acc_imm_vts.append((a, m.group(1), L.disp_of(m.group(2)), iv))
        continue
    if t is None:
        rej_other.append((a, op)); continue
    base, disp, tgt = t
    if disp < 0:
        tgt_l = tgt.split(',')[-1].strip() if tgt else None
        if tgt_l is not None and IMM.match(tgt_l):
            rej_neg.append((a, base, disp))
            iv = immv(tgt_l)
            raw_neg_shapes[(mn, 'imm', iv in VTS)] += 1
            if iv in VTS: neg_imm_vts.append((a, base, disp, iv))
    else:
        rej_other.append((a, op))

cov_acc = {s[3] for s in acc_imm_vts}
cov_neg = {s[3] for s in neg_imm_vts}
resid = [int(x, 16) for x in json.load(open('_r144/r144h_stack.json'))['resid']]
# 统一：直接用宽容解析器的 disp 是否 0 分桶
acc_disp0 = {s[3] for s in acc_imm_vts if s[2] == 0}
neg_covered_resid = [hex(v) for v in resid if v in cov_neg]
resid_left = [hex(v) for v in resid if v not in cov_neg and v not in cov_acc]

coloff = {}
COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
for c in COL:
    coloff[c] = B.dw(c + 4)
off_of = lambda vt: coloff.get(COLof.get(vt))
neg_agree = sum(1 for s in neg_imm_vts if off_of(s[3]) == s[2])
neg_absagree = sum(1 for s in neg_imm_vts if off_of(s[3]) == -s[2])

# 结构线索：负位移站点是否都伴随「同一函数里前面有 [same_base+...] 的行走」
res = {
 'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
 'vt_distinct': len(VTS),
 'RE_STORE_accepted_sites': len(acc),
 'RE_STORE_accepted_imm_vts_sites': len(acc_imm_vts),
 'RE_STORE_distinct_vt': len(cov_acc),
 'rejected_neg_imm_sites': len(rej_neg),
 'neg_imm_vts_sites': len(neg_imm_vts),
 'neg_distinct_vt': len(cov_neg),
 'neg_new_vs_accepted': len(cov_neg - cov_acc),
 'neg_new_list': [hex(v) for v in sorted(cov_neg - cov_acc)],
 'rej_other_n': len(rej_other),
 'rej_other_sample': [ [hex(a), o] for a, o in rej_other[:12] ],
 'neg_disp_hist': collections.Counter(s[2] for s in neg_imm_vts).most_common(12),
 'neg_base_hist': collections.Counter(s[1] for s in neg_imm_vts).most_common(8),
 'neg_agree_with_coloff': neg_agree,
 'neg_abs_agree': neg_absagree,
 'resid_in': resid and [hex(v) for v in resid],
 'resid_covered_by_neg': neg_covered_resid,
 'resid_left': resid_left,
 'samples_neg': [[hex(a), b, d, hex(v)] for a, b, d, v in neg_imm_vts[:14]],
 'elapsed_s': round(time.time() - T0, 1),
}

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
# 正控：复现解析漏洞
lit = 'dword ptr [eax - 8],0x7e6060'
chk('正控：RE_STORE 不接受负位移写法（复现漏洞）', L.RE_STORE.match(lit) is None, str(L.RE_STORE.match(lit)))
chk('正控：同一操作改成正则写法后被接受', L.RE_STORE.match('dword ptr [eax-0x8],0x7e6060') is not None, 'ok')
chk('正控：norm 只压 + 两侧空白、不压 -', L.norm('dword ptr [eax - 8],0x1') == 'dword ptr [eax - 8],0x1' and L.norm('dword ptr [eax + 8],0x1') == 'dword ptr [eax+0x8],0x1', [L.norm('dword ptr [eax - 8],0x1'), L.norm('dword ptr [eax + 8],0x1')])
chk('正控：宽容解析器把 [eax - 8] 解成 disp=-8', tol_parse(lit)[1] == -8, tol_parse(lit))
# 反控：宽容解析器不得吞 byte ptr
chk('反控：宽容解析器不匹配 byte ptr', tol_parse('byte ptr [eax - 8],0x1') is None, tol_parse('byte ptr [eax - 8],0x1'))
chk('反控：宽容解析器不匹配索引式 [reg+idx*4]', tol_parse('dword ptr [eax+ecx*4+0x8],0x1') is None, tol_parse('dword ptr [eax+ecx*4+0x8],0x1'))
# 事实断言
chk('存在被 RE_STORE 拒绝的负位移立即数写', len(rej_neg) > 0, len(rej_neg))
chk('其中 imm∈VTS 的站点 > 0', len(neg_imm_vts) > 0, len(neg_imm_vts))
chk('负位移站点覆盖到 F1/RE_STORE 之外的虚表', len(cov_neg - cov_acc) >= 1, len(cov_neg - cov_acc))
chk('残余 5 张里至少 1 张被负位移站点覆盖', len(neg_covered_resid) >= 1, neg_covered_resid)
chk('0x7E6060 在负位移覆盖名单里', '0x7e6060' in [x.lower() for x in neg_covered_resid], neg_covered_resid)

res['POS'] = POS
res['pos_pass'] = sum(1 for x in POS if x[1]); res['pos_fail'] = sum(1 for x in POS if not x[1])
json.dump(res, open('_r145/r145a_negdisp.json', 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'POS'}, indent=1, ensure_ascii=False)[:4000])
for p in POS: print(('PASS ' if p[1] else 'FAIL ') + '%-56s %s' % (p[0], p[2]))
print('POS %d/%d FAIL %d elapsed %ss' % (res['pos_pass'], len(POS), res['pos_fail'], res['elapsed_s']))
