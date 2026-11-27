#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-B · 913,237 与 16,711,118 同源：两个数都是同一个偏移的补数

R174-A 已证：清单 bytes=913,237 精确等于 a2_sites.json 里分段标记 '}, "bounds": [' 的起始偏移，
而 calls-only 的合法 JSON 长度是 913,239（差 2）。本脚本把「闭合式是否提供独立信息」这件事测出来。

判据（可失败）：
  Q1  F24 两式在代数上同解：44,470,975 − 16,711,118 = 26,846,620 + 913,237
      ⇒ 第二式不含任何独立于第一式的信息（16,711,118 的定义就是 17,624,355 − 913,237）
  Q2  盘的独立实测对是 (913,239, 16,711,116)：26,846,620 + 913,239 = 44,470,975 − 16,711,116
  Q3  上述两对各自内部的差都恰为 2；且清单总和 737,517,286 只与清单对 (913,237,16,711,118) 相容
  Q4  913,237 不可能同时是「清单里那件文件的字节数」：任何合法 calls-only JSON 都是 913,239

反控：
  N1  把 16,711,118 换成独立实测的 16,711,104（bounds 值跨度）⇒ Q1 的等式必须不成立
  N2  把 913,237 换成 913,238 ⇒ Q1 等式必须不成立（差 1 也抓得住，说明不是宽等）
  N3  小样本：'{"calls": {"1": ["2"]}, "bounds": ["A"]}' 里 偏移与 calls-only 长度差仍为 2，
      且「file − offset」与「file − calls-only」也差 2（同规则在小样本上复现，排除大文件巧合）

只读 a2_sites.json、tier_final_4417.tsv、V554 的 F24 行；只写 _r174/r174b_offset_source.json。
"""
import csv
import hashlib
import io
import json
import os

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
MF = 'lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv'
FI = 'lead/next_re_20261117_r14/R17_R126_FACTINDEX_V554/FACT_INDEX.tsv'
OUT = '_r174/r174b_offset_source.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:600]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:400]) if detail else ''))


print('== Q0 · 输入（全部实测） ==')
d = io.open(A2, 'rb').read()
L = len(d)
V = json.loads(d)['calls']
B = json.loads(d)['bounds']
CK = len(json.dumps({'calls': V}, ensure_ascii=False).encode())
BL = len(json.dumps(B, ensure_ascii=False).encode())
MK = b'}, "bounds": ['
OFF = d.find(MK)
DEL = d.rfind(b']') - (OFF + 1) + 1    # 从 bounds 前那个逗号（OFF+1）起、到结尾 ']' 含，删掉整条成员的长度
SAME, DIFF, GONE = 64, 1, 4352
B_SAME, B_DIFF = 26846620, 913237
B_GONE = 709757429
TOTAL = 737517286
print('L=%d C(calls-only)=%d len(dumps(bounds))=%d OFF=%d DEL=%d' % (L, CK, BL, OFF, DEL))
print('清单三元组: same=%d diff=%d gone=%d total=%d' % (B_SAME, B_DIFF, B_GONE, TOTAL))

print('== Q1 · 第二式对任意 X 都成立 ⇒ 无独立信息 ==')
print('44,470,975 = %d ; 26,846,620 + 17,624,355 = %d' % (B_SAME + L, B_SAME + L))
ck('Q1a 44,470,975 == 26,846,620 + 17,624,355（现盘两桶）', B_SAME + L == 44470975, B_SAME + L)
ck('Q1b 16,711,118 的定义就是 L − 913,237', L - B_DIFF == 16711118, L - B_DIFF)
f = lambda X: (B_SAME + L) - (L - X) + B_GONE
g = lambda X: B_SAME + X + B_GONE
xs = [0, 1, 913237, 913238, 913239, 16711104, L]
hits = [(X, f(X), g(X), f(X) == g(X)) for X in xs]
for X, a, b, ok in hits:
    print('  X=%-10d f(X)=%-12d g(X)=%-12d equal=%s' % (X, a, b, ok))
ck('Q1c 第二式对全部 7 个 X 都与第一式同解（含 X=0 与 X=L 两个非实测值）',
   all(h[3] for h in hits), [h[0] for h in hits])
ck('Q1d 因此第二式不含独立于第一式的信息（X=0 也闭合）', f(0) == g(0), (f(0), g(0)))

print('== Q2 · 用盘上实测值代入，差 +2（这才是可失败的判别） ==')
tot_disk = (B_SAME + L) - DEL + B_GONE
tot_disk2 = B_SAME + CK + B_GONE
print('实测删段跨度 DEL=%d ; L−DEL=%d ; calls-only=%d' % (DEL, L - DEL, CK))
print('用 DEL 代入 ⇒ %d ; 用 calls-only 代入 ⇒ %d ; 目标 %d' % (tot_disk, tot_disk2, TOTAL))
ck('Q2a L − DEL == 913,239', L - DEL == 913239, L - DEL)
ck('Q2b 用实测删段跨度代入得 737,517,288（+2）', tot_disk == TOTAL + 2, tot_disk - TOTAL)
ck('Q2c 清单总和 737,517,286 只能由清单值 913,237 闭合',
   B_SAME + B_DIFF + B_GONE == TOTAL and tot_disk != TOTAL, (B_SAME + B_DIFF + B_GONE, tot_disk))
ck('Q2d 实测对与清单对只差 diff 桶一项 2 B', tot_disk - (B_SAME + B_DIFF + B_GONE) == CK - B_DIFF,
   tot_disk - (B_SAME + B_DIFF + B_GONE))

print('== Q3 · 清单总和只与清单对相容 ==')
t_manifest = B_SAME + B_DIFF + B_GONE
t_disk = B_SAME + CK + B_GONE
t_disk2 = B_SAME + CK + B_GONE
print('清单对总和 = %d ; 实测对总和 = %d' % (t_manifest, t_disk))
ck('Q3a 清单对总和 == 737,517,286', t_manifest == TOTAL, t_manifest)
ck('Q3b 实测对总和 == 737,517,288（差 +2）', t_disk == TOTAL + 2, t_disk)
ck('Q3c 两对只差在 diff 桶一项', t_disk - t_manifest == CK - B_DIFF, t_disk - t_manifest)

print('== Q4 · 913,237 不可能是该件的字节数 ==')
print('calls-only 序列化长度 = %d ; 清单值 = %d' % (CK, B_DIFF))
ck('Q4a 913,237 != calls-only 长度', B_DIFF != CK, (B_DIFF, CK))
ck('Q4b 913,237 恰等于标记偏移', B_DIFF == OFF, (B_DIFF, OFF))
ck('Q4c 913,237 恰等于 CK − 2（末尾右花括号的偏移）', B_DIFF == CK - 2, CK - 2)
ck('Q4d d[913237] 是 dumps(V) 的右花括号', d[913237:913238] == b'}', d[913237:913238])

print('== N1 · 清单总和 737,517,286 把 X 唯一钉在 913,237（这才是判别式） ==')
for nm, X in (('bounds 值跨度', BL), ('calls-only 实测', CK), ('偏移+1', OFF + 1), ('偏移−1', OFF - 1)):
    print('  X=%-8d (%s) ⇒ 总和 %d ; 与目标差 %+d' % (X, nm, g(X), g(X) - TOTAL))
ck('N1a 用 bounds 值跨度 16,711,104 代入 ⇒ 总和 != 737,517,286', g(BL) != TOTAL, g(BL) - TOTAL)
ck('N1b 用实测 calls-only 913,239 代入 ⇒ 差恰 +2', g(CK) - TOTAL == 2, g(CK) - TOTAL)
ck('N1c 用 913,238 代入 ⇒ 差恰 +1', g(OFF + 1) - TOTAL == 1, g(OFF + 1) - TOTAL)
ck('N1d 用 913,236 代入 ⇒ 差恰 −1', g(OFF - 1) - TOTAL == -1, g(OFF - 1) - TOTAL)
ck('N1e 七个候选里只有 913,237 使总和精确等于 737,517,286',
   [X for X in (BL, CK, OFF - 1, OFF, OFF + 1, 0, L) if g(X) == TOTAL] == [OFF],
   [X for X in (BL, CK, OFF - 1, OFF, OFF + 1, 0, L) if g(X) == TOTAL])

print('== N3 · 小样本同规则复现 ==')
smp = b'{"calls": {"1": ["2"]}, "bounds": ["A"]}'
sV = json.loads(smp)['calls']
sCK = len(json.dumps({'calls': sV}, ensure_ascii=False).encode())
sOFF = smp.find(MK)
sDEL = len(smp) - sOFF + 1
print('small: len=%d calls-only=%d off=%d' % (len(smp), sCK, sOFF))
ck('N3a 小样本 calls-only − off == 2', sCK - sOFF == 2, sCK - sOFF)
ck('N3b 小样本 (len − off) − (len − calls-only) == 2', (len(smp) - sOFF) - (len(smp) - sCK) == 2,
   (len(smp) - sOFF) - (len(smp) - sCK))

print('== F24 行里 913,237 的分布（改哪一列要看它落在哪） ==')
rows = {r[0]: r for r in csv.reader(io.open(FI, encoding='utf-8'), delimiter='\t')}
st, lim = rows['F24'][1], rows['F24'][4]
print('statement: 913,237 x%d ; 16,711,118 x%d ; 17,624,355 x%d' %
      (st.count('913,237'), st.count('16,711,118'), st.count('17,624,355')))
print('limitations: 913,237 x%d ; 16,711,118 x%d ; 17,624,355 x%d' %
      (lim.count('913,237'), lim.count('16,711,118'), lim.count('17,624,355')))
ck('F1 statement 含 913,237', '913,237' in st, st.count('913,237'))
ck('F2 全文 913,237 总次数 == statement + limitations',
   st.count('913,237') + lim.count('913,237') == (st + '\t' + lim).count('913,237'),
   st.count('913,237') + lim.count('913,237'))

out = {
    'script': 'r174b_offset_source.py',
    'file_bytes': L,
    'sha256': hashlib.sha256(d).hexdigest(),
    'calls_only_len': CK,
    'dumps_bounds_len': BL,
    'marker_offset': OFF,
    'deleted_member_span': DEL,
    'manifest_diff_bucket': B_DIFF,
    'total_manifest_pair': t_manifest, 'total_disk_pair': t_disk,
    'total_with_measured_del': tot_disk,
    'unique_pin': [X for X in (BL, CK, OFF - 1, OFF, OFF + 1, 0, L) if g(X) == TOTAL],
    'f24_stmt_counts': {'913237': st.count('913,237'), '16711118': st.count('16,711,118'),
                        '17624355': st.count('17,624,355')},
    'f24_lim_counts': {'913237': lim.count('913,237'), '16711118': lim.count('16,711,118'),
                       '17624355': lim.count('17,624,355')},
    'assertions': RES, 'fail': FAIL,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('\n== RESULT: %d assertions, %d FAIL ==' % (len(RES), FAIL))
print('wrote ' + OUT)
raise SystemExit(1 if FAIL else 0)
