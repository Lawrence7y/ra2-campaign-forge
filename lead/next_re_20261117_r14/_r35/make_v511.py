# -*- coding: utf-8 -*-
"""生成 FACT_INDEX v5.11（改动集 1 + 改动集 2）。
纪律：读 v5.10 → 逐行比对 → 断言只有目标行变化 → wx 独占创建 → 回读校验。
"""
import io, os, hashlib

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SRC  = os.path.join(R14, 'R17_R65_FACTINDEX_V510')
DST  = os.path.join(R14, 'R17_R66_FACTINDEX_V511')
os.makedirs(DST, exist_ok=True)

raw = io.open(os.path.join(SRC, 'FACT_INDEX.tsv'), encoding='utf-8', newline='').read()
assert '\r' not in raw
lines = raw.split('\n')
assert lines[0].split('\t') == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations']
data = [l for l in lines[1:] if l.strip()]
assert len(data) == 54

# ================= 改动集 1：limitations（Check A 两处真缺陷） =================
F15_LIM = ('stats.tsv 现盘为 129/125/5（unresolved 3、需重分类 19），与 R17_R28_R12_REPAIR/REPORT.md 一致；'
           '早期草稿值 108/82/4/33 见 R17_LEDGER_1063 事项4（该目录已 SUPERSEDED、不得引用），'
           '权威值 129/125/5/19 见 R17_LEDGER_1063R；'
           '形态命中数不受 host 修正影响须给 267/70/1/7/9 依据；见 conflicts.md C01')
F15_EV_ADD = r'lead\next_re_20261117_r14\R17_LEDGER_1063\SUPERSEDED.md'

F35_LIM = ('ceil(0.9n)/ceil(0.5n)/proved_strict 均为卡面口径；PANEL M47 给判定式原文，M52 给达标复算，'
           '「严格口径双列表」给 proved_strict 定义（= atlas 内 [已证] 且语义栏不含 [未证]）；'
           'M44 是并表说明、正文无 proved_strict 定义。'
           'F25/F26 只记结果与裁定、未记判据式，故不重复。')

# ================= 改动集 2：statement（跨家族审计 A1/A2/B1 全部成立后落地） =================
F24_STMT = ('证据可解析度：R_OK 863 / 1,654（52.18%）为上限；R_MISSING 0；R_TRACE_ONLY 791 行'
            '（= 116 dump-only + 675 零候选）。675 行已做有界内容级搜索'
            '（primary 口径 = 6 类扩展名 .tsv/.txt/.json/.md/.csv/.log，23,791 文件 / 1.29 GB；'
            '扩展名限制把搜索面缩小 58 倍），真实四环回指 = 0'
            '（检测器对已知 11 行正控召回 11/11，故该 0 有判别力）'
            '⇒ 791 行属「事实层面没有逐 entry 四环证据」，不是「指针没连上」。')
F24_LIM = ('『改指针无解、不再投卡』是 Lead 行动裁决（台账 §1054），不入本条证据、不随数字一并作已证；'
           '数字与负结论；归因见 §16.1；R_OK 863 是「至少一个路径解析到真实文件」，不等于「逐 entry 专属证据」；'
           '引 §16.1 只能引其「判据」，其表内数字是历史快照（旧 478/374/802），数字须取现盘。')

F29_STMT_OLD_TAIL = '（反例：0x7F3D98 slot1/slot2 为转发、0x6C2AC0 是 InterlockedIncrement 真 AddRef）'
F29_STMT_NEW_TAIL = ('（反例：0x7F3D98 slot1/slot2 为转发、0x6C2AC0 是 call [0x7E11C8] 的真 AddRef'
                     '——对 [this+4] 自增；「InterlockedIncrement」系推断措辞、未经字节证实）')

out_rows, changed = [], []
for l in data:
    c = l.split('\t')
    assert len(c) == 5, (c[0], len(c))
    fid = c[0]
    if fid == 'F15':
        changed.append(('F15', 'limitations', c[4], F15_LIM))
        c[3] = c[3] + ';' + F15_EV_ADD
        c[4] = F15_LIM
    elif fid == 'F35':
        changed.append(('F35', 'limitations', c[4], F35_LIM))
        c[4] = F35_LIM
    elif fid == 'F24':
        changed.append(('F24', 'statement', c[1], F24_STMT))
        changed.append(('F24', 'limitations', c[4], F24_LIM))
        c[1] = F24_STMT
        c[4] = F24_LIM
    elif fid == 'F29':
        assert F29_STMT_OLD_TAIL in c[1], 'F29 tail not found'
        new = c[1].replace(F29_STMT_OLD_TAIL, F29_STMT_NEW_TAIL)
        changed.append(('F29', 'statement', c[1], new))
        c[1] = new
    out_rows.append('\t'.join(c))

assert len(changed) == 5, len(changed)  # F15 lim / F35 lim / F24 stmt / F24 lim / F29 stmt

out = '\n'.join([lines[0]] + out_rows) + '\n'
assert '\r' not in out
dst = os.path.join(DST, 'FACT_INDEX.tsv')
if os.path.exists(dst):
    # 只允许覆盖本轮自建、尚无任何标记指向的 v5.11
    assert 'R17_R66_FACTINDEX_V511' in dst
    os.remove(dst)
with open(dst, 'x', encoding='utf-8', newline='') as f:
    f.write(out)

back = io.open(dst, encoding='utf-8', newline='').read()
assert back == out, 'readback mismatch'
assert back.count('\n') == 55
assert back.count('\t') == 55 * 4
backrows = [l for l in back.split('\n')[1:] if l.strip()]
assert len(backrows) == 54
for a, b in zip(data, backrows):
    fa = a.split('\t')[0]
    assert fa == b.split('\t')[0]
    if fa not in ('F15', 'F35', 'F24', 'F29'):
        assert a == b, 'unexpected change in ' + fa

dist = {}
for b in backrows:
    g = b.split('\t')[2]
    dist[g] = dist.get(g, 0) + 1
assert dist.get('[已证]') == 27 and dist.get('[静态推断]') == 1 and dist.get('未取得') == 2 and dist.get('[流程]') == 24, dist

print('OK', dst, 'bytes =', os.path.getsize(dst))
print('sha256 =', hashlib.sha256(back.encode()).hexdigest().upper())
print('grade dist ok =', dist)
print('changed cells =', len(changed))
for fid, col, old, new in changed:
    print()
    print('--- %s.%s ---' % (fid, col))
    print('OLD:', old)
    print('NEW:', new)
