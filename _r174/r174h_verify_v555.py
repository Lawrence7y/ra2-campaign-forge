#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-H · V555 写后独立复核（不回写、只读盘）

r174g 写盘后 H5 断言「F24 只 1 个非 equal 段」FAIL —— 那是我的断言错：
SequenceMatcher 默认 autojunk=True 会把高频短串当垃圾跳掉，报成 1 replace + 1 insert；
关掉 autojunk 后真值是 **3 段纯插入、0 段删除/替换**。本脚本用正确判据复核，并把它钉成
可失败断言（若将来有人真的删了原文，本脚本必须 FAIL）。

判据：
  K1  V555 五项（字节 / sha256 / CR / 行数 / 列）与 r174g 的落盘值一致
  K2  F24 的差异是**纯插入**：所有非 equal opcode 的 tag 均为 insert，且被删字符数 0
  K3  F35 的差异是**纯插入**且插在末尾（old_end == len(old_lim)）
  K4  其余 52 行 x 5 列与 V554 逐字节相同
  K5  两行的 statement / grade / evidence_paths 与 V554 逐字节相同
  K6  V554 母本一字未改（sha 仍 5de4084b…）

反控：
  N1  把 old/new 调换（假装「新→旧」）必须得 delete 型 opcode ⇒ 证明 K2 能区分方向
  N2  人为在 new 里删掉 10 个字符 ⇒ 必须出现 delete/replace ⇒ 证明 K2 不是恒真
  N3  autojunk 开启与否会改变 opcode 计数（实测两值并报），是本轮 S-617 的机制证据
"""
import hashlib
import io
import json
import os
import sys
from difflib import SequenceMatcher

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
MOM = os.path.join(TIER, 'R17_R126_FACTINDEX_V554/FACT_INDEX.tsv')
CUR = os.path.join(TIER, 'R17_R127_FACTINDEX_V555/FACT_INDEX.tsv')
OUT = '/home/t628/projects/ra2-campaign-forge/_r174/r174h_verify_v555.json'
MOM_SHA = '5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0'
CUR_SHA = '5396d2df9f032e1cc6febdd340dd51591c4a52a961591a2babde52ef25f3496c'
CUR_BYTES = 124834

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def rows_of(path):
    raw = io.open(path, 'rb').read()
    lines = raw.decode('utf-8').rstrip('\n').split('\n')
    out = {}
    for l in lines[1:]:
        f = l.split('\t')
        out[f[0]] = f
    return raw, lines, out


raw_m, lines_m, r_m = rows_of(MOM)
raw_c, lines_c, r_c = rows_of(CUR)
sha_c = hashlib.sha256(raw_c).hexdigest()

print('== K1 · 现盘五项 ==')
ck('K1a V555 字节 == 124,834', len(raw_c) == CUR_BYTES, len(raw_c))
ck('K1b V555 sha256 == 5396d2df…', sha_c == CUR_SHA, sha_c[:16])
ck('K1c V555 CR == 0', raw_c.count(b'\r') == 0, raw_c.count(b'\r'))
ck('K1d V555 55 行', len(lines_c) == 55, len(lines_c))
ck('K1e V555 全行 5 列', all(len(l.split('\t')) == 5 for l in lines_c),
   sorted(set(len(l.split('\t')) for l in lines_c)))

print('== K2 · F24 差异是纯插入 ==')
o24, n24 = r_m['F24'][4], r_c['F24'][4]
ops24 = [o for o in SequenceMatcher(None, o24, n24, autojunk=False).get_opcodes() if o[0] != 'equal']
deleted = sum(o[2] - o[1] for o in ops24)
print('  ops=%s  deleted_chars=%d' % (ops24, deleted))
ck('K2a 非 equal opcode 全为 insert', all(o[0] == 'insert' for o in ops24), [o[0] for o in ops24])
ck('K2b 被删字符数 == 0', deleted == 0, deleted)
ck('K2c 插入段数 == 3', len(ops24) == 3, len(ops24))
ck('K2d 字符增量 == 162', len(n24) - len(o24) == 162, len(n24) - len(o24))
sm24 = SequenceMatcher(None, o24, n24, autojunk=False)
rebuilt_old = ''.join(n24[o[3]:o[4]] for o in sm24.get_opcodes() if o[0] == 'equal')
rebuilt_new = ''.join(o24[o[1]:o[2]] if o[0] == 'equal' else n24[o[3]:o[4]] for o in sm24.get_opcodes())
ck('K2e 只取 equal 段拼回 == 原文（即删掉全部插入得回原串）', rebuilt_old == o24,
   (len(rebuilt_old), len(o24)))
ck('K2f equal 段 + 插入段拼回 == 新串', rebuilt_new == n24, (len(rebuilt_new), len(n24)))
ck('K2g 原文 4 个 equal 段（= 插入 3 处把原文切 4 段）',
   len([o for o in sm24.get_opcodes() if o[0] == 'equal']) == 4,
   len([o for o in sm24.get_opcodes() if o[0] == 'equal']))

print('== K3 · F35 差异是末尾纯插入 ==')
o35, n35 = r_m['F35'][4], r_c['F35'][4]
ops35 = [o for o in SequenceMatcher(None, o35, n35, autojunk=False).get_opcodes() if o[0] != 'equal']
print('  ops=%s' % ops35)
ck('K3a 只有 1 个非 equal opcode', len(ops35) == 1, len(ops35))
ck('K3b 该 opcode 是 insert', ops35[0][0] == 'insert', ops35[0][0])
ck('K3c 插在 old 末尾', ops35[0][1] == len(o35), (ops35[0][1], len(o35)))
ck('K3d 原串在新列里仍 1 次（前缀完全保留）', n35.count(o35) == 1, n35.count(o35))

print('== K4/K5 · 未改行与未改列 ==')
bad = [k for k in r_m if k not in ('F24', 'F35') and r_m[k] != r_c[k]]
ck('K4 其余 52 行 x 5 列逐字节相同', not bad, bad)
ck('K5a F24 statement 未变', r_m['F24'][1] == r_c['F24'][1])
ck('K5b F24 grade 未变', r_m['F24'][2] == r_c['F24'][2])
ck('K5c F24 evidence 未变', r_m['F24'][3] == r_c['F24'][3])
ck('K5d F35 statement 未变', r_m['F35'][1] == r_c['F35'][1])
ck('K5e F35 grade 未变', r_m['F35'][2] == r_c['F35'][2])
ck('K5f F35 evidence 未变', r_m['F35'][3] == r_c['F35'][3])
ck('K5g 其余 52 行 statement/grade/evidence 也全未变',
   all(r_m[k][i] == r_c[k][i] for k in r_m if k not in ('F24', 'F35') for i in (1, 2, 3)))

print('== K6 · 母本一字未改 ==')
ck('K6a V554 sha256 仍 5de4084b…', hashlib.sha256(raw_m).hexdigest() == MOM_SHA,
   hashlib.sha256(raw_m).hexdigest()[:16])
ck('K6b V554 字节仍 123,851', len(raw_m) == 123851, len(raw_m))

print('== 反控 ==')
ops_rev = [o for o in SequenceMatcher(None, n24, o24, autojunk=False).get_opcodes() if o[0] != 'equal']
ck('N1 反向（新→旧）必得 delete 型 opcode', any(o[0] == 'delete' for o in ops_rev), [o[0] for o in ops_rev])
cut = n24[:100] + n24[110:]
ops_cut = [o for o in SequenceMatcher(None, o24, cut, autojunk=False).get_opcodes() if o[0] != 'equal']
ck('N2 人为删 10 字符 ⇒ 必出现 delete/replace', any(o[0] in ('delete', 'replace') for o in ops_cut),
   [o[0] for o in ops_cut])
aj = [o for o in SequenceMatcher(None, o24, n24).get_opcodes() if o[0] != 'equal']
ck('N3 autojunk=True 时 opcode 计数与 False 不同（S-617 机制）',
   len(aj) != len(ops24), (len(aj), len(ops24)))
print('  autojunk=True ops=%s' % aj)

res = {
    'script': 'r174h_verify_v555.py',
    'cur_bytes': len(raw_c), 'cur_sha256': sha_c,
    'f24_ops_autojunk_false': ops24, 'f24_deleted_chars': deleted,
    'f35_ops': ops35,
    'autojunk_true_op_count': len(aj), 'autojunk_false_op_count': len(ops24),
    'assertions_total': n, 'fails': fails,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n== RESULT: %d assertions, %d FAIL ==' % (n, len(fails)))
if fails:
    print('FAILS: %s' % fails)
print('wrote ' + OUT)
sys.exit(1 if fails else 0)
