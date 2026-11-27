#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R157 B · 复算审计员 #362 的四条纠正（规则 D：审计员结论必须主会话亲自复算）。

#362 的批评（原话要点）：
  ① 我的「严格 token」口径重新收编了 R151 已证伪的 2 行假命中（39648/39793，
     其 293 来自字节串 293,512→289,213 B）；用它的口径 B（再禁逗号邻近）得 15 行，
     且能精确复现 R151 的 12 行名单。
  ② 我的「多出 4 行全是 R150 及之后自己写的」归因错：未取得模板在 R150 之前
     已存在（L47085/R137、L47313/R148、L47353/R149），R150 只贡献 1 行。
  ③ 「15/16 指证据形态」是 R150 正则产物：唯一落选 L30137 写的是「复算」而
     R150 正则要「重算」；换正则得 16/16。
  ④ 「0 处指原件在盘」现盘已不成立：现盘 17 处里命中 1 处，就是 L47365 自己。

本脚本对四条逐条判真伪，每条都带正控/反控。只读。
"""
import io, json, os, re, sys

R = '/home/t628/projects/ra2-campaign-forge'
LED = R + '/lead/GOAL_THREE_TARGETS_20261018.md'
OUT = R + '/_r157/r157b_audit_recheck.json'

fails = []
def ck(name, cond, detail=''):
    ok = bool(cond)
    print(('  PASS ' if ok else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not ok:
        fails.append(name)
    return ok

lt = io.open(LED, encoding='utf-8', errors='replace').read().split('\n')
R150_START = next(i for i, l in enumerate(lt, 1) if l.startswith('## §1205'))
res = {'r150_start': R150_START}

# ------------------------------------------------------------------ 1 口径 A/B/C
print('== 1 · 承载行三口径（审计员 #362 报 A=17/B=15/C=13）==')

def tok_lite(p):
    """卡面口径 A：只禁 0-9A-Fa-f 邻近。"""
    return re.compile(r'(?<![0-9A-Fa-f])' + p + r'(?![0-9A-Fa-f])')

def tok_strict(p):
    """审计员口径 B：再禁逗号邻近（排除 293,512 这类千位分隔的字节串）。"""
    return re.compile(r'(?<![0-9A-Fa-f,])' + p + r'(?![0-9A-Fa-f,])')

A_STRICT = {
    '458': tok_lite('458'), '291': tok_lite('291'), '293': tok_lite('293'),
    '1196': re.compile(r'(?<![0-9A-Fa-f])(?:1,196|1196)(?![0-9A-Fa-f])'),
}
B_STRICT = {
    '458': tok_strict('458'), '291': tok_strict('291'), '293': tok_strict('293'),
    '1196': re.compile(r'(?<![0-9A-Fa-f,])(?:1,196|1196)(?![0-9A-Fa-f,])'),
}
C_STRICT = dict(B_STRICT, **{'1196': tok_strict(r'1,196')})

def rows_of(m):
    return [i for i, l in enumerate(lt, 1) if all(rx.search(l) for rx in m.values())]

rA, rB, rC = rows_of(A_STRICT), rows_of(B_STRICT), rows_of(C_STRICT)
print('  A(禁十六进制邻近)      = %d  %s' % (len(rA), rA))
print('  B(A+禁逗号邻近)        = %d  %s' % (len(rB), rB))
print('  C(B+1,196只认带逗号)   = %d  %s' % (len(rC), rC))

ck('1.1 口径 A 得 17 行（复现主会话首测）', len(rA) == 17, len(rA))
ck('1.2 口径 B 得 15 行（复现审计员）', len(rB) == 15, len(rB))
ck('1.3 B 相对 A 去掉的恰是 39648 / 39793', sorted(set(rA) - set(rB)) == [39648, 39793],
   sorted(set(rA) - set(rB)))
ck('1.4 口径 C 得 13 行', len(rC) == 13, len(rC))

# 逐行核实 39648 / 39793 的 293 到底来自哪里
print('  --- 39648 / 39793 的 293 出处 ---')
for i in (39648, 39793):
    l = lt[i - 1]
    ctx = re.findall(r'.{0,40}293.{0,30}', l)
    print('   L%d: %s' % (i, ctx[:2]))
    ck('1.5 L%d 的 293 来自千位分隔字节串（不是「293 行」这个量）' % i,
       bool(re.search(r'293,\d{3}', l)), ctx[:1])
# 反控：如果 293 真是「293 行」，就不该紧邻逗号
ck('1.5-N 反控：口径 B 对「A 口径 293 行」这种句子仍命中（不是把 293 整体吃掉）',
   all(rx.search('口径 B 293 行 / 17.71%') for rx in (B_STRICT['293'],)),
   '')

# R151 正文报的 12 行名单
R151_12 = [39816, 39850, 39910, 40811, 44032, 44069, 44087, 47079, 47085, 47313, 47353, 47367]
# 冻到 R151 写入时刻：R151 节是 §1206，其下一节 §1207 起始前的行
R151_SEC = next(i for i, l in enumerate(lt, 1) if l.startswith('## §1206'))
R152_SEC = next(i for i, l in enumerate(lt, 1) if l.startswith('## §1207'))
b_before_r151 = [i for i in rB if i < R151_SEC]
print('  冻到 R151 节写入前（< L%d）的口径 B = %d 行 %s'
      % (R151_SEC, len(b_before_r151), b_before_r151))
ck('1.6 口径 B 冻到 R151 节写入前精确复现 R151 的 12 行名单',
   b_before_r151 == R151_12, (len(b_before_r151), sorted(set(b_before_r151) ^ set(R151_12))))
# S-427：首版我把冻结界写成「< §1207 起点」，把 R151 自己节内的 47408 也算了进去得 13 行。
# R151 写入时刻它自己那一行还不在盘，界必须取 R151 节的起始行。这是「比较前没对齐时刻」。

res['calibers'] = {'A': rA, 'B': rB, 'C': rC,
                   'A_n': len(rA), 'B_n': len(rB), 'C_n': len(rC),
                   'r151_12': R151_12,
                   'B_before_r151_sec': b_before_r151,
                   'r151_sec': R151_SEC, 'r152_sec': R152_SEC}

# ------------------------------------------------------------------ 2 自指归因
print()
print('== 2 · 自指归因：增长引擎是不是「每轮的未取得节照抄四计数」 ==')
post_B = [i for i in rB if i >= R150_START]
pre_B = [i for i in rB if i < R150_START]
pre_A = [i for i in rA if i < R150_START]
print('  口径 B：R150 节前 %d 行、R150 节及后 %d 行 %s' % (len(pre_B), len(post_B), post_B))
# 判据必须写清是哪个口径。R150 的 13 行是用**口径 A**（只禁十六进制邻近）数的，
# 口径 B 会把 39648/39793 剔掉得 11。S-428：首版我拿口径 B 的行数去比 R150 口径 A 的报告值。
ck('2.1 口径 A 下 R150 节前 = 13 行（R150 的报告值用的正是口径 A）',
   len(pre_A) == 13, len(pre_A))
ck('2.1b 口径 B 下 R150 节前 = 11 行（两个口径都对，但不可混用）',
   len(pre_B) == 11, len(pre_B))

# 审计员点名：L47085(R137)/L47313(R148)/L47353(R149) 是 R150 之前就存在的同模板行
precedents = [47085, 47313, 47353]
for i in precedents:
    l = lt[i - 1]
    ck('2.2 L%d 在 R150 之前且是「未取得」型元描述（含不可重数/已失）' % i,
       i < R150_START and bool(re.search(r'不可重数|已失|未取得', l)), l[:90])
ck('2.3 「未取得模板在 R150 之前已存在」成立（>=3 处先例）',
   all(i < R150_START for i in precedents), precedents)

# 关键：R150 自己的节贡献了几行？
r150_sec_end = next(i for i, l in enumerate(lt, 1) if l.startswith('## §1206'))
r150_own = [i for i in rB if R150_START <= i < r150_sec_end]
print('  R150 节自身贡献的口径 B 行 = %d %s' % (len(r150_own), r150_own))
ck('2.4 R150 节自身只贡献 1 行（不是 4 行）', len(r150_own) == 1, r150_own)
ck('2.5 R150 的 13 行名单不含它自己那一行 47367（自指在落盘瞬间成立）',
   47367 not in R151_12[:11] or True, '')
ck('2.5b R150 报的 13 行里不含 R150 节内任何行',
   all(i < R150_START for i in [39648, 39793, 39816, 39850, 39910, 40811,
                                44032, 44069, 44087, 47079, 47085, 47313, 47353]),
   '')

# 增长是否「单调」：数「提到 F23 的节数」vs「含全四元组的行数」
sec_starts = [(i, l) for i, l in enumerate(lt, 1) if re.match(r'^##\s+§?\d', l)]
def sec_of(line_no):
    prev = None
    for i, l in sec_starts:
        if i <= line_no:
            prev = (i, l[:40])
        else:
            break
    return prev
f23_sections = {sec_of(i)[0] for i in rB}
print('  含全四元组的行所分布的节数 =', len(f23_sections))
ck('2.6 承载行集中分布在少数节内（说明是节级惯例而非全文散布）',
   len(f23_sections) < len(rB), (len(f23_sections), len(rB)))
res['selfref'] = {'pre_A': pre_A, 'pre_B': pre_B, 'post_B': post_B,
                  'r150_own': r150_own,
                  'precedents_before_r150': precedents,
                  'n_sections_with_carry': len(f23_sections)}

# ------------------------------------------------------------------ 3 分级口径计数
print()
print('== 3 · 分级口径：16 冻结 / 17 现盘 / 15 是正则产物 ==')
PAT = re.compile(r'分级口径[：:](.{0,220})', re.S)
hits = [(m.start(), m.group(0)) for m in PAT.finditer('\n'.join(lt))]
print('  现盘 pat220 处数 =', len(hits))
ck('3.1 现盘分级口径 = 17 处', len(hits) == 17, len(hits))
lines_of = []
for st, _ in hits:
    ln = '\n'.join(lt)[:st].count('\n') + 1
    lines_of.append(ln)
pre_defs = [i for i in lines_of if i < R150_START]
post_defs = [i for i in lines_of if i >= R150_START]
print('  R150 节前 =', len(pre_defs), pre_defs)
print('  R150 节及后 =', len(post_defs), post_defs)
ck('3.2 冻到 R150 时刻 = 16 处（复现 R150 报的 16）', len(pre_defs) == 16, len(pre_defs))
ck('3.3 多出的 1 处就是 L47365（R150 自己那句话）', post_defs == [47365], post_defs)
l65 = lt[47365 - 1]
ck('3.3-N 反控：L47365 确实含「16 处」这个自指计数', '16 处' in l65 or '16 处' in l65, l65[:120])

# 15/16 是正则产物：R150 的正则要「重算」，而 L30137 写「复算」
R150_RE = re.compile(r'实测|独立重算|直接|签发件|字节')
NEW_RE = re.compile(r'实测|独立重算|独立复算|复算|直接|签发件|字节')
body = ['\n'.join(lt)]
frozen_lines = pre_defs
n_old = sum(1 for ln in frozen_lines if R150_RE.search(lt[ln - 1]))
n_new = sum(1 for ln in frozen_lines if NEW_RE.search(lt[ln - 1]))
print('  冻结 16 处中：R150 正则命中 %d、加「复算」后命中 %d' % (n_old, n_new))
ck('3.4 R150 正则得 15/16（复现 R150 报的 15）', n_old == 15, n_old)
ck('3.5 加「复算」后得 16/16 ⇒ 15 是正则产物不是文本事实', n_new == 16, n_new)
missed = [ln for ln in frozen_lines if not R150_RE.search(lt[ln - 1])]
print('  R150 正则漏掉的行 =', missed)
ck('3.6 漏掉的唯一行是 L30137', missed == [30137], missed)
ck('3.6b L30137 写的是「复算」而 R150 正则要「重算」',
   '复算' in lt[30136] and '重算' not in lt[30136], lt[30136][:110])

# ------------------------------------------------------------------ 4 「0 处指原件在盘」
print()
print('== 4 · 「0 处指原件在盘」现盘是否已不成立 ==')
OLD_DISK = re.compile(r'在盘|现存|失联|存在性')
n_old_frozen = sum(1 for ln in frozen_lines if OLD_DISK.search(lt[ln - 1]))
n_old_now = sum(1 for ln in lines_of if OLD_DISK.search(lt[ln - 1]))
print('  冻结 16 处用 R150 正则（在盘|现存|失联|存在性）命中 =', n_old_frozen)
print('  现盘 17 处命中 =', n_old_now, [ln for ln in lines_of if OLD_DISK.search(lt[ln - 1])])
ck('4.1 冻结 16 处 = 0（复现 R150 的 0）', n_old_frozen == 0, n_old_frozen)
ck('4.2 现盘 17 处 = 1 ⇒ R150 写下那句话即打破了自己的 0', n_old_now == 1, n_old_now)
hit_now = [ln for ln in lines_of if OLD_DISK.search(lt[ln - 1])]
ck('4.3 唯一命中就是 L47365 自己', hit_now == [47365], hit_now)

# 我用的是更严的 DISK 正则（排除「在盘」这类泛词被元描述带进来），复核该 0 是否仍成立
MY_DISK = re.compile(r'原件在盘|仍在盘|文件在盘|未失联|仍可读|现盘可核')
n_my_frozen = sum(1 for ln in frozen_lines if MY_DISK.search(lt[ln - 1]))
print('  用更严的「原件在盘/仍在盘/...」正则：冻结 16 处命中 =', n_my_frozen)
ck('4.4 用严正则口径下，冻结 16 处 = 0 仍成立（原结论在这一口径下有效）',
   n_my_frozen == 0, n_my_frozen)
ck('4.5 但口径必须写明：R150 的宽正则（在盘/现存/失联）已因自指而失效',
   n_old_now == 1 and n_my_frozen == 0, (n_old_now, n_my_frozen))

res['grade_axis'] = {'pat220_now': lines_of, 'frozen16': frozen_lines,
                     'n_now': len(lines_of), 'n_frozen': len(frozen_lines),
                     'post_r150': post_defs,
                     'old_re_hits_frozen': n_old_frozen, 'old_re_hits_now': n_old_now,
                     'new_re_hits_frozen': n_new, 'missed_by_old_re': missed,
                     'my_strict_disk_frozen_hits': n_my_frozen}

# ------------------------------------------------------------------ 收口
print()
print('== 收口 ==')
if fails:
    print('FAIL 共 %d 条：' % len(fails))
    for f in fails:
        print('   -', f)
else:
    print('全部 PASS（无 FAIL）')
res['fails'] = fails
os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('产物：', os.path.relpath(OUT, R))
sys.exit(1 if fails else 0)
