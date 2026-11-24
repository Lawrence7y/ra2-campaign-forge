# -*- coding: utf-8 -*-
"""生成 FACT_INDEX v5.13：
 1) F24 statement/limitations：修单位（GiB≠GB）、限定 58 倍是体积比、标明快照与漂移；加锚 mev675.py
 2) F29 statement：0x7E11C8 经导入表证实（KERNEL32!InterlockedIncrement），并记非标准 .detour 节；加锚 T1 产物
 3) F14 evidence_paths：加三个数据锚（reconcile.tsv / reconcile_final.tsv / reverse_map.tsv）
纪律：读 v5.12 → 逐行断言只有目标行变化 → wx 独占创建 → 回读校验。
"""
import io, os, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R67_FACTINDEX_V512')
DST  = os.path.join(R14, 'R17_R69_FACTINDEX_V513')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
assert lines[0].split('\t') == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations']
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54

# ---------------- 新值 ----------------
F24_STMT = ('证据可解析度：R_OK 863 / 1,654（52.18%）为上限；R_MISSING 0；R_TRACE_ONLY 791 行'
            '（= 116 dump-only + 675 零候选）。675 行已做有界内容级搜索'
            '（primary 口径 = 6 类扩展名 .tsv/.txt/.json/.md/.csv/.log；当时量 23,791 文件 / '
            '1,383,739,755 B = 1.29 GiB（不是 GB；同一字节数按十进制为 1.38 GB）；'
            '扩展名限制缩小的是体积比约 58 倍，文件数比仅 2.86 倍（68,038→23,791）；'
            '该规模是快照，2026-11-22 重跑同一阶段得 24,623 文件 / 1.40 GiB），真实四环回指 = 0'
            '（检测器对已知 11 行正控召回 11/11，故该 0 有判别力）'
            '⇒ 791 行属「事实层面没有逐 entry 四环证据」，不是「指针没连上」。')
F24_EV_ADD = r'lead\next_re_20261117_r14\R16_MEASURE_EVID675\mev675.py'
F24_LIM = ('『改指针无解、不再投卡』是 Lead 行动裁决（台账 §1054），不入本条证据、不随数字一并作已证；'
           '数字与负结论；归因见 §16.1；R_OK 863 是「至少一个路径解析到真实文件」，不等于「逐 entry 专属证据」；'
           '引 §16.1 只能引其「判据」，其表内数字是历史快照（旧 478/374/802），数字须取现盘；'
           '规模数（23,791 / 1.29 / 58 倍）是**快照且无数值产物落盘**（`stage_scale` 返回值未接），'
           '引用须标日期与重跑口径；其中「1.29」按 `mev675.py` 的 `/1024³` 实为 **GiB**，'
           '「58 倍」只对体积成立（文件数比 2.86 倍）。')

F29_OLD_TAIL = ('0x6C2AC0 是 call [0x7E11C8] 的真 AddRef'
                '——对 [this+4] 自增；「InterlockedIncrement」系推断措辞、未经字节证实）')
F29_NEW_TAIL = ('0x6C2AC0 是 call [0x7E11C8] 的真 AddRef——对 [this+4] 自增；'
                '0x7E11C8 已经导入表证实为 KERNEL32.dll 的 `InterlockedIncrement`'
                '（Hint=432、FirstThunk idx=62、IBN 原始字节 B0 01 49 6E 74…），**不再是推断措辞**；'
                '但本镜像多出一个非标准 `.detour` 节（VA=0x793000/raw=0x497000），导入布局非原版，'
                '引用时须同时声明这一点）')
F29_EV_ADD = r'lead\next_re_20261117_r14\R17_R68_T1_IAT\REPORT.md'
# F29 的 limitations 必须与「已证实」的正文同步（v5.13 第一稿漏改，被 checkC2 的 C1 反控抓到）
F29_LIM_OLD_TAIL = ('0x6C2AC0 的「InterlockedIncrement」是 §13.3 的推断措辞'
                    '（字节只给 call [0x7E11C8]），本条引用时须写明该词未经字节证实')
F29_LIM_NEW_TAIL = ('0x6C2AC0 的「InterlockedIncrement」原先只是 §13.3 的推断措辞（字节只给 call [0x7E11C8]），'
                    '现已由导入表证实（KERNEL32.dll、Hint=432、FirstThunk idx=62，见 R17_R68_T1_IAT），'
                    '引用时不必再写「未经字节证实」，但须同时声明本镜像多出非标准 `.detour` 节、导入布局非原版')

F14_EV_ADD = (r'lead\next_re_20261117_r14\R17_R19_RTTI_XCHECK\reconcile.tsv;'
              r'lead\next_re_20261117_r14\R17_R24_RECON_FINAL\reconcile_final.tsv;'
              r'lead\next_re_20261117_r14\R17_R17_SLOT73_MAP\reverse_map.tsv')

out_rows, changed = [], []
for l in data:
    c = l.split('\t')
    assert len(c) == 5, (c[0], len(c))
    fid = c[0]
    if fid == 'F24':
        changed.append(('F24', 'statement', c[1], F24_STMT))
        changed.append(('F24', 'limitations', c[4], F24_LIM))
        c[1] = F24_STMT
        c[4] = F24_LIM
        assert 'mev675.py' not in c[3]
        c[3] = c[3] + ';' + F24_EV_ADD
    elif fid == 'F29':
        assert F29_OLD_TAIL in c[1], 'F29 tail mismatch:\n' + c[1][-300:]
        new = c[1].replace(F29_OLD_TAIL, F29_NEW_TAIL)
        assert new != c[1]
        changed.append(('F29', 'statement', c[1], new))
        c[1] = new
        assert F29_LIM_OLD_TAIL in c[4], 'F29 limitations tail mismatch:\n' + c[4][-300:]
        newlim = c[4].replace(F29_LIM_OLD_TAIL, F29_LIM_NEW_TAIL)
        assert newlim != c[4]
        changed.append(('F29', 'limitations', c[4], newlim))
        c[4] = newlim
        assert 'R17_R68_T1_IAT' not in c[3]
        c[3] = c[3] + ';' + F29_EV_ADD
    elif fid == 'F14':
        assert 'reconcile_final.tsv' not in c[3]
        c[3] = c[3] + ';' + F14_EV_ADD
        changed.append(('F14', 'evidence_paths', '(before)', c[3]))
    out_rows.append('\t'.join(c))

assert len(changed) == 5, len(changed)   # F24 stmt + F24 lim + F29 stmt + F29 lim + F14 evid

out = '\n'.join([lines[0]] + out_rows) + '\n'
assert '\r' not in out
# 禁用零宽/不可见字符（先前手写时混入过 U+200B）
BAD = {'\u200b', '\u200c', '\u200d', '\ufeff', '\u2060', '\u00a0'}
for ch in BAD:
    assert ch not in out, 'forbidden invisible char U+%04X in output' % ord(ch)
dst = os.path.join(DST, 'FACT_INDEX.tsv')
assert not os.path.exists(dst)
with open(dst, 'x', encoding='utf-8', newline='') as f:
    f.write(out)

back = io.open(dst, encoding='utf-8', newline='').read()
assert back == out
assert back.count('\n') == 55
assert back.count('\t') == 55 * 4
backrows = [l for l in back.split('\n')[1:] if l.strip()]
assert len(backrows) == 54
for a, b in zip(data, backrows):
    fa = a.split('\t')[0]
    assert fa == b.split('\t')[0]
    if fa not in ('F24', 'F29', 'F14'):
        assert a == b, 'unexpected change in ' + fa
dist = {}
for b in backrows:
    g = b.split('\t')[2]
    dist[g] = dist.get(g, 0) + 1
assert dist.get('[已证]') == 27 and dist.get('[静态推断]') == 1 and dist.get('未取得') == 2 and dist.get('[流程]') == 24, dist

print('OK', dst, 'bytes =', os.path.getsize(dst))
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
print('grade dist =', dist)
print('changed cells =', len(changed))
