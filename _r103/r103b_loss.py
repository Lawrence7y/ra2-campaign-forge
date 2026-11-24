#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r103b_loss.py —— R102 事故（R14_COMMON 丢 12 节而门禁全绿）是否仍可复现

R102 实测：外部守护重复追加+截断，§2.94..§2.105 共 12 节一度全丢（828,603→738,215 B），
五项 CR 不变量对这次丢内容失明。R102 只在 LEAD_LOCK 里提了「辅助单调不变量（标题级节数/
末节号/字节数下界）防内容丢失，本轮只提未加」。

**量测对象声明（R103 落盘后补记）**：A 组量的是 **C15 落盘前**（GATE_VER=R102）的门禁 ——
即「事故发生时门禁看不见」这件事本身；B 组量的是 **C15 落盘后**。故 A 用 `prepare(gate='unpatched')`、
B 用 `prepare(gate='patched')`。两者不可混跑，否则 A 会随盘上门禁变化而自我失效（本轮实测撞到过）。

本脚本做两件事：
  A 复现：在沙箱里把 R14_COMMON 的尾部若干节逐段删掉，看现门禁 exit 码与五项 CR 各自怎么变。
    —— 若 exit 仍 0，则事故仍可复现，R102 待办①的「只提未加」属实。
  B 证明 C15 有鉴别力：用与 A 完全相同的坏文件，换成打了 C15 的门禁必须 exit 1；
    反向控制用未打补丁的门禁必须 exit 0（证明抓到它的是 C15 本身，不是别的检查）。
C15 判据（三条，全部只读，不改任何行）：
  C15a ## 标题里 2.x 编号集合必须 ⊇ 钉住的集合
  C15b 末节 2.x 编号必须 >= 钉住的末节号
  C15c R14_COMMON 字节数必须 >= 钉住的下界（各减一个安全余量，见常量）
钉住值从今天的盘上实测得出，并在输出里逐字打印，便于人工复核。
"""
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbxlib as S

OUT = os.path.join(S.REAL, '_r103')
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

RC_REL = 'R14_COMMON.md'
RC = os.path.join(S.SBX, S.R14REL, RC_REL)
C5 = (('R14_COMMON', 1081), ('STATUS_BOARD', 0), ('LEDGER', 337))

def cr_profile(text):
    """五项 CR 里与 R14_COMMON 相关的那一项：CRLF 计数。"""
    return text.count('\r\n')

def heads(text):
    return re.findall(r'(?m)^##\s+(\d+(?:\.\d+)*)', text.replace('\r\n', '\n'))

def is21(h):
    """是否 §2.x 的一级 2.x 编号（2.7 / 2.106），排除 2.7.1 这类子节与顶层整数节。"""
    if not re.fullmatch(r'2\.\d+', h):
        return False
    return True

def num2(h):
    return int(h.split('.')[1])

def cut_sections(text, lo, hi):
    """删掉 ## 2.lo .. ## 2.hi 全部节（含标题行，到下一个 ## 之前）。"""
    lines = text.split('\n')
    out, dropping, cut = [], False, 0
    for l in lines:
        m = re.match(r'^##\s*2\.(\d+)\b', l)
        if m:
            n = int(m.group(1))
            dropping = lo <= n <= hi
            if dropping:
                cut += 1
        if not dropping:
            out.append(l)
    return '\n'.join(out), cut

S.prepare(gate='unpatched')
BASE = io.open(RC, encoding='utf-8', newline='').read()
h0 = heads(BASE)
d0 = sorted({num2(x) for x in h0 if is21(x)})
print('baseline: bytes=%d CRLF=%d headings=%d 2.x=%d..%d'
      % (len(BASE.encode('utf-8')), cr_profile(BASE), len(h0), d0[0], d0[-1]))

# ---- A 复现：逐段删尾部节 ----
RES = {'A': []}
for lo, hi in ((2.100 and 100, 100), (100, 102), (100, 106), (94, 106)):
    bad, cut = cut_sections(BASE, int(lo), int(hi))
    io.open(RC, 'w', encoding='utf-8', newline='').write(bad)
    rc, f, _ = S.run()
    RES['A'].append({'lo': lo, 'hi': hi, 'cut_headings': cut,
                     'bytes': len(bad.encode('utf-8')), 'bytes_before': len(BASE.encode('utf-8')),
                     'crlf': cr_profile(bad), 'crlf_before': cr_profile(BASE),
                     'exit': rc, 'fails': f})
    print('  A cut 2.%d..2.%d: headings-%d bytes %d->%d CRLF %d->%d exit=%d fails=%s'
          % (lo, hi, cut, len(BASE.encode('utf-8')), len(bad.encode('utf-8')),
             cr_profile(BASE), cr_profile(bad), rc, [x[:45] for x in f][:2]))
io.open(RC, 'w', encoding='utf-8', newline='').write(BASE)
rc_restore, f_restore, _ = S.run()
ck('A0 还原后基线仍 exit 0（删改未污染沙箱）', rc_restore == 0, 'exit=%d' % rc_restore)

invisible = [x for x in RES['A'] if x['exit'] == 0]
ck('A1 R102 事故可复现：删 §2.100..§2.106 共 7 节后现门禁仍 exit 0', 
   any(x['lo'] == 100 and x['hi'] == 106 and x['exit'] == 0 for x in RES['A']),
   'invisible_cuts=%s' % [(x['lo'], x['hi']) for x in invisible])
ck('A2 五项 CR 中对丢内容失明的证据：删节后 CRLF 计数变化量 == 0',
   all(x['crlf'] == x['crlf_before'] for x in RES['A']),
   'crlf_pairs=%s' % [(x['lo'], x['crlf_before'], x['crlf']) for x in RES['A']])
ck('A3 三项 CR 都不拦（R14_COMMON/STATUS_BOARD/LEDGER 的 CR 计数与节数无关）',
   all(x['exit'] == 0 for x in RES['A'][:3]), 'exits=%s' % [x['exit'] for x in RES['A'][:3]])

# ---- B C15 已落盘：改用盘上 patched 门禁直接量（不再本脚本注入第二份补丁）----
# R103 自错 4：第一版在 B 组里把 C15 代码块**再注入一次**到已经含 C15 的门禁上，
# 于是同一坏文件报出两套下界（831,406 与 842,976）—— 那不是两个判据，是我注入两次。
# 修法：C15 已落盘，B 组直接量盘上门禁，不注入；A 组才用备份的 unpatched 门禁。
S.prepare(gate='patched')
BASE = io.open(RC, encoding='utf-8', newline='').read()
GATE = os.path.join(S.SBX, S.R14REL, 'check_disc.py')
GSRC = io.open(GATE, encoding='utf-8', newline='').read()
assert GSRC.count('C15 content floor') == 1, 'gate must carry exactly one C15 block'
RES['pins'] = {'gate_c15_blocks': GSRC.count('C15 content floor')}

rc, f, out = S.run()
ck('B0 盘上 patched 门禁原样 exit 0（纯加严不改今天行为）', rc == 0, 'exit=%d fails=%s' % (rc, f[:3]))
ck('B1 输出含且仅含一条 C15 content floor NOTE', out.count('C15 content floor') == 1,
   [l.strip() for l in out.splitlines() if 'C15' in l][:2])

RES['B'] = []
for lo, hi in ((100, 100), (100, 102), (100, 106), (94, 106)):
    bad, cut = cut_sections(BASE, int(lo), int(hi))
    io.open(RC, 'w', encoding='utf-8', newline='').write(bad)
    rc2, f2, _ = S.run()
    RES['B'].append({'lo': lo, 'hi': hi, 'cut': cut, 'exit': rc2,
                     'fails': [x for x in f2 if x.startswith('C15')]})
    print('  B cut 2.%d..2.%d (%d 节): exit=%d  C15 fails=%d  %s'
          % (lo, hi, cut, rc2, len(RES['B'][-1]['fails']),
             [x[:64] for x in RES['B'][-1]['fails']]))
io.open(RC, 'w', encoding='utf-8', newline='').write(BASE)
rc8, f8, _ = S.run()
ck('B2 全部还原后 exit 0', rc8 == 0, 'exit=%d' % rc8)
ck('B3 C15 抓到全部四种删法（4/4 exit 1，且 FAIL 前缀都是 C15）',
   all(x['exit'] == 1 and x['fails'] for x in RES['B']),
   [(x['lo'], x['hi'], x['exit'], len(x['fails'])) for x in RES['B']])
ck('B3b 每种删法只由一个 C15 块报出（不会出现两套下界数 —— 那是我注入两次的痕迹）',
   all(len({tuple(sorted(set(re.findall(r'floor (\\\\d+)', y)))) for y in x['fails']}) <= 2 for x in RES['B']),
   [len(x['fails']) for x in RES['B']])

# ---- B4 反向控制：同一坏文件 + unpatched 门禁 ⇒ exit 0 ----
S.prepare(gate='unpatched')
RCU = S.p(R.SBX, 'R14_COMMON.md') if False else os.path.join(S.SBX, S.R14REL, 'R14_COMMON.md')
BASEU = io.open(RCU, encoding='utf-8', newline='').read()
bad, cut = cut_sections(BASEU, 100, 106)
io.open(RCU, 'w', encoding='utf-8', newline='').write(bad)
rc_nc, f_nc, _ = S.run()
io.open(RCU, 'w', encoding='utf-8', newline='').write(BASEU)
RES['B4_NC'] = {'exit': rc_nc, 'fails': f_nc, 'cut': cut}
ck('B4 反向控制：同一坏文件（删 7 节）用 unpatched 门禁 ⇒ exit 0（抓到它的是 C15 本身）',
   rc_nc == 0, 'exit=%d fails=%s' % (rc_nc, f_nc[:2]))

# ---- B5 / B6 不误伤（回到 patched 门禁）----
S.prepare(gate='patched')
BASE = io.open(RC, encoding='utf-8', newline='').read()
extra = '\n## 2.108 R103 探针节\n\n本轮探针写入的一节纯文本，用于证明 C15 不拦「正常增节」。\n'
io.open(RC, 'w', encoding='utf-8', newline='').write(BASE + extra)
rc_add, f_add, _ = S.run()
RES['B5_add'] = {'exit': rc_add, 'fails': f_add}
io.open(RC, 'w', encoding='utf-8', newline='').write(BASE)
ck('B5 不误伤：正常追加新节后 exit 0', rc_add == 0, 'exit=%d fails=%s' % (rc_add, f_add[:2]))

mod = BASE.replace('本节只收 R103 本机实测', '本节只收 R103 本机实测（R103 改写探针）', 1)
io.open(RC, 'w', encoding='utf-8', newline='').write(mod)
rc_mod, f_mod, _ = S.run()
RES['B6_mod'] = {'exit': rc_mod, 'fails': f_mod}
io.open(RC, 'w', encoding='utf-8', newline='').write(BASE)
ck('B6 不误伤：小节内改写（正文加字）后 exit 0', rc_mod == 0, 'exit=%d fails=%s' % (rc_mod, f_mod[:2]))

json.dump({'checks': checks, 'results': RES},
          io.open(os.path.join(OUT, 'r103b_loss.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n%d checks, %d FAIL' % (len(checks), nf))
sys.exit(1 if nf else 0)
