"""m10: bounds + misc evidence tables.

Three nested numbers per subsystem:
  three_ring   = ②∧④∧③b           (measured, all three proven from bytes)
  ub_livevt    = ②∧③b             (upper bound if EVERY missing ④ were really an
                                    undetected livevt dispatch — my ④ scanner only sees
                                    absolute-global installs, so heap/this-ctor installs escape it)
  A            = ②∧④              (upper bound if ③b were under-detected)
This makes the "no subsystem can cross" conclusion independent of the weakest detector.
"""
import sys, json, collections
from pathlib import Path
OUT = Path(__file__).parent.parent
SUBS = ['S%02d' % i for i in range(1, 22)]
def jload(p): return json.loads(Path(p).read_text(encoding='utf-8'))
R = {r['entry']: r for r in jload(OUT/'work'/'rings.json') if 'err' not in r}
pool = jload(OUT/'work'/'pool.json')
met = jload(OUT/'work'/'metrics.json')['metrics']
def h2(r): return r['has2_rtti'] or r['has2_yrpp']
def h4(r): return r['n_direct_out'] > 0 or r['n_livevt_live'] > 0
def h3(r): return bool(r['cats'])

print('%-5s %5s %6s %6s %7s %8s %9s %9s %9s' % (
    'SUB', 'pool', 'A', 'three', 'ub2^3b', 'proved', 'thr', 'up_three', 'up_ub'))
any_up = []
rows = []
T = collections.Counter()
for s in SUBS:
    rs = [R[p['entry']] for p in pool if p['sub'] == s]
    A = sum(h2(x) and h4(x) for x in rs)
    tr = sum(h2(x) and h4(x) and h3(x) for x in rs)
    ub = sum(h2(x) and h3(x) for x in rs)
    pr, thr = met[s]['proved'], met[s]['threshold']
    ok_tr = pr + tr >= thr
    ok_ub = pr + ub >= thr
    if ok_ub: any_up.append(s)
    print('%-5s %5d %6d %6d %7d %8d %9d %9d %9d  %s' % (
        s, len(rs), A, tr, ub, pr, thr, pr+tr, pr+ub,
        ('UB-CROSS' if (ok_ub and not ok_tr) else ('ok' if ok_tr else ''))))
    T['n'] += len(rs); T['A'] += A; T['tr'] += tr; T['ub'] += ub
    T['pr'] += pr; T['thr'] += thr
    rows.append(dict(sub=s, n=len(rs), A=A, three=tr, ub233b=ub, proved=pr, threshold=thr,
                     up_three=pr+tr, up_ub=pr+ub, ok_three=ok_tr, ok_ub=ok_ub))
print('%-5s %5d %6d %6d %7d %8d %9d %9d %9d' % (
    'TOTAL', T['n'], T['A'], T['tr'], T['ub'], T['pr'], T['thr'], T['pr']+T['tr'], T['pr']+T['ub']))
print()
print('subsystems that would cross even at the ②∧③b upper bound =', any_up)

# ---------- EVIDENCE\controls.tsv ----------
CT = jload(OUT/'work'/'controls.json')
CQ = {c['entry']: c for c in CT}
def row(entry, role, expect, got, verdict, note):
    return '\t'.join([entry, role, expect, got, verdict, note])

NOTES = {
 '0053AF40': 'RTTI 通道物理缺失（该 VA 全 .text 0 次引用），② 由 YRpp PsyDom 通道成立：4 个候选绝对成员地址命中 3 个（00A9FA48/00A9FAC0/00A9FAC4）；④ direct 0053A742（E8, 0053A742+5+rel32==0053AF40, 体外）；③b① 跳表 @0053B064 实读 6 目标、5 臂作用两两相异',
 '0045A640': '② 成立（vt 007E44F4 slot1, .?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@）；③b 四档全不成立：唯一循环 0045A65D..0045A66C 为 读+比较+推进+有界(jl) 而**零非栈写** ⇒ 不达 ③b④；无 call ⇒ 无 ③b②；单 cmp/jne 两路 ⇒ 无 ③b①；n_ctor=0 ⇒ 无 ③b③。④ livevt 为 0 见证（堆 ctor / this 指针装表在本卡绝对全局扫描之外）。与 S08_KPROVED2/UNKNOWNS.md:11 独立同判；S08_KPROVED3 的「四环齐全」主张与本卡不符，该行台账处置仍为待裁',
 '0069DEB0': '五模式 ebx=0..4 汇入同一 call 4AED70，各臂独占作用集空 ⇒ ③b① 不达；无回边、无错误码、无形状断言 ⇒ ③a',
 '00704350': '三闸同型（同读 +0x2B5、同一全局、同 scale），仅源寄存器不同 ⇒ 臂签名相同；扫描循环 00704907 无**非栈写**（只有 test [esi+0x140]）⇒ ③b④ 不达 ⇒ ③a',
 '004DDDE0': '闸 +0x95/+0x99/+0xC3 汇入同一返回桩 mov eax,ebx;ret 0xC，+0xAD/+0xBE 汇入另一桩 ⇒ 无 ≥3 道动作不同闸；无回边 ⇒ ③a',
 '004F4240': '④ livevt 不成立，但**理由与原设想不同**：.text 内对绝对全局 0x87F7E8 的写点只有 1 处 0040D1B2 `mov [0x87f7e8],0x7e1964`，而该点位于 atexit 注册的析构器 0040D1B0 体内（308 个 push<dtor>;call 0x7C978A 之一）⇒ 按 §8.6 条1/㉓ 不算活 vptr。ctor 0x5BDA40 的装表是 this 指针形 `mov [esi],0x7e1964`（@005BDA4A），同一单例在 +0x5518 另装 0x7E195C（slot0=006D1770≠entry）⇒ 对象级「该 slot 在所有已装表一致」亦字面不满足。故「同 global 另装表」的措辞在 4 字节全局层面并不成立，真正的否证是 ㉓ + 对象级槽不一致',
}
out = ['entry\trole\texpect\tgot\tverdict\tnote']
VERD = {
 '0053AF40': ('PASS', 'three (②YRpp∧④direct∧③b①)'),
 '0045A640': ('NOT-REPRODUCED', '② only; ③b=③a, ④ livevt=0'),
 '0069DEB0': ('PASS', '③a'),
 '00704350': ('PASS', '③a'),
 '004DDDE0': ('PASS', '③a'),
 '004F4240': ('PASS(with corrected reason)', '④ livevt 不成立'),
}
for e, role, exp in [('0053AF40', 'POS', '②∧④∧③b'), ('0045A640', 'POS', '②∧③b, ④=livevt'),
                     ('0069DEB0', 'NEG', '③b 不成立'), ('00704350', 'NEG', '③b 不成立'),
                     ('004DDDE0', 'NEG', '③b 不成立'), ('004F4240', 'NEG', '④ livevt 不成立')]:
    v, got = VERD[e]
    out.append(row(e, role, exp, got, v, NOTES[e]))
(OUT/'EVIDENCE'/'controls.tsv').write_text('\n'.join(out) + '\n', encoding='utf-8')

# ---------- EVIDENCE\caliber_recon.tsv ----------
MX = jload(OUT/'work'/'matrix.json')
o = ['item\tmine\tprior_card\tdelta\tnote']
o.append('pool_rows\t4350\tTHIRDB 4350\t0\t同截面；RING24 为 4,444（早一截面的 [静态推断]，差 94 行系 M43-M46 并表）')
o.append('ring2_RTTI_only\t4084\tRING24 4084 (91.90%%)\t0\t逐行 0 差异')
o.append('ring3b_main\t472\tTHIRDB 472\t0\t逐行 0 差异（4/4 对照判对）')
o.append('ring3b_sensA\t509\tTHIRDB 509\t0\t② 加回 cmp eax,-1 哨兵')
o.append('A_ring2RTTI_and_4\t338\tRING24 338\t0\t**总数一致但组成差 2 行**，见下两行')
o.append('A_row_004325A0\tin A (④ site 00473C48)\tRING24 not in A\t+1\t本卡 extent=[004325A0,004325B7) span=23 与 atlas 23 精确一致；RING24 的 extent 无尾跳桩护栏，跟随 tail jmp 吞入邻近体，把 00473C48 判成「体内」')
o.append('A_row_004F4240\tnot in A (㉓ 排除)\tRING24 in A\t-1\tRING24 引用的装点 0040D1B2 在 atexit 析构器 0040D1B0 内（project _audit/VERDICT.md:37 亦判「见证点错」）；合法见证应为 ctor 005BDA40 的 mov [esi],0x7E1964，但该 global 的 slot0 在对象级另装表 0x7E195C 下不一致 ⇒ 字面仍不成立')
o.append('A_ring2any_and_4\t341\tRING24 341\t0\t② 含 YRpp 通道后与他们的 341 一致')
o.append('three_ring\t22\t—\t—\t两卡均未测交集；本卡新增')
o.append('proved_sum\t1400\tRING24 1306\t+94\t恰等于两卡池差 94（1,306+94=1,400），非口径差')
(OUT/'EVIDENCE'/'caliber_recon.tsv').write_text('\n'.join(o) + '\n', encoding='utf-8')
print('\nwrote EVIDENCE\\controls.tsv + EVIDENCE\\caliber_recon.tsv')
json.dump(dict(rows=rows, ub_cross=any_up, tot=dict(T)),
          open(OUT/'work'/'bounds.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
