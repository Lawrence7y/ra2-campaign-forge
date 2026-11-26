#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R138 主会话交付：FACT_INDEX v5.32 -> v5.33（四条正文修订的正文层落盘）

为什么本轮改正文（每条都有本轮实测依据，不是口味）
---------------------------------------------------
① F23：补「12 行分解 6+2+3=11，余 1 行无归属」与「计数依赖 coverage.tsv
   （4,147,334 B / 18,498 行 / 8 列）已失，本机不可重数」。
   依据：_r138/r138a 项1/项2（主会话）+ 执行员 #301 + 审计员 #302 三家同得。
   6+2+3=11 与 total=12 差 1，原文三个分项里没有第 12 行的归属。

② F24：撤下「86.19%」这个数（R136 已证实测 99.992% 有字节对应），
   但**保留**与它独立的「单列地址、无可回原址复核的第二列」结构判据。
   两者分开处理：错的是数字，不是方向。同时在 limitation 里补语料值失效期。
   依据：R136 三实现同测 + 本轮 r138a 项3（现盘 64/1/4,352、71,715,975 B）。

③ F29：四处措辞作用域补全 —— 只做**确实存在于 F29 正文**的三处：
   两份拷贝（80 份中的两份）、idx=62（DLL 内口径，另有全局 63/64）、
   40 次桩序列与 63/77 无因果关系。
   注意：「6 个桩体」实测**不在 F29 正文任何一列**（R138 新发现），
   它是 R135 deepseek 审计时自报的数字，不是本项正文，故**不写入**。

④ F35：补「proved_strict 定义缺一手权威：PANEL.md M52 已失，只有二手转述」。

写入纪律：R17_LEAD_BASELINE 下 wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入
-> 回读校验；源版本目录内容一个字节不动（v5.33 落到新目录）。
"""
import os
import io
import sys
import json
import time
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
PRV = os.path.join(R14, 'R17_R104_FACTINDEX_V532', 'FACT_INDEX.tsv')
DSTD = os.path.join(R14, 'R17_R105_FACTINDEX_V533')
DST = os.path.join(DSTD, 'FACT_INDEX.tsv')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
DRY = '--dry' in sys.argv

OLD_SHA = '84863896227062179adc6e437eff3cf89e437fc6a131620a1f50e831b52cf92f'
OLD_BYTES = 61822
OLD_CR = 0

fails = []
buf = []


def W(s=''):
    print(s)
    buf.append(s)


def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


# ---------------- 新文本（逐条实测来源见文件头） ----------------

# ① F23 limitations 追加两句。原句保留，只在句末追加，不改任何既有数字。
F23_ADD_LIM = (u'**【R138 补·分解不闭合】** 上文「该 12 行中 6 行为否定式、2 行为 callers 计数、'
               u'真正非否定的多计仅 3 行」三个分项之和为 6+2+3=**11**，与 total=12 差 **1 行**，'
               u'该行在上述分解里**没有归属**；换读法（把「3 行本已在 W 内」当作另一批）则为 6+2+3+3=14>12 '
               u'出现重计 ⇒ 两种读法都得不到 12，缺口对读法不敏感。'
               u'**【R138 补·计数层不可重数】** 本条的计数（458/291/293/1196/12/2/9 与分母 1654）'
               u'依赖 `coverage.tsv`（记载 4,147,334 B / 18,498 行 / 8 列），该文件**不在现盘**：'
               u'全库按文件名精确命中 **0**、按 4,147,334 B 精确字节反查命中 **0**，'
               u'`COVERAGE/`、`R17_DELIVERY/`、`R17_R41_RECOMPUTE/` 三目录均不存在；'
               u'11-22 快照清单有 4 条记录（主份 + 3 份 _hygiene 备份）⇒ 曾存在、现失。'
               u'故本机能证的只有**算术闭合**，不能重数底层计数。')

# ② F24：把 86.19% 撤下，换成实测值 + 保留结构判据 + 语料值失效期。
F24_OLD_A = (u'（纯指令起始 VA 清单、**86.19% 盘上无任何字节对应**、不满足「可回原址复核」）')
F24_NEW_A = (u'（纯指令起始 VA 清单；**R138 撤下原「86.19% 盘上无任何字节对应」一数** —— '
             u'R136 三种独立实现（主会话 objdump 起始集、主会话 capstone disasm_lite 64KB 分块、'
             u'hy4 自写 objdump 解析）同测实测 **99.992%（1,392,481/1,392,592）有字节对应**、'
             u'未命中仅 111 条且 111/111 落在前一指令起始 +1..8 内，故该数**错的是数字、不是方向**；'
             u'**保留与本数独立的结构判据**：`bounds` 是单列地址、没有可回原址复核的第二列）')

F24_OLD_B = (u'（1,392,592 条纯指令起始 VA，16,711,118 B，**86.19% 无字节对应**）')
F24_NEW_B = (u'（1,392,592 条纯指令起始 VA，16,711,118 B；**此处原写「86.19% 无字节对应」，'
             u'R138 撤销该数**：R136 三实现实测 1,392,481/1,392,592 = **99.992% 有对应**，'
             u'未命中 111 条全在前一指令起始 +1..8 内；剔除依据改按结构判据「单列地址、无第二列」）')

F24_OLD_C = (u'（`a2_sites` 的 `bounds`，86.19% 无字节对应）')
F24_NEW_C = (u'（`a2_sites` 的 `bounds`；原注「86.19% 无字节对应」已由 R138 撤销，'
             u'实测 99.992% 有字节对应；该件仍剔，依据是单列地址结构判据）')

# F24 语料值失效期：追加在 limitations 末尾
F24_ADD_LIM = (u'**【R138 补·语料值失效期】** 本条主引用值 4,417 件 / 737,517,286 B 是 '
               u'**2026-11-22 快照值**，不是现盘可 stat 到的体量。R138 实测（_r138/r138a 项3，'
               u'执行员 #301 独立同得）：按清单 rel 相对 `lead/` 解析，现盘**存在且字节相同 64 件 / '
               u'26,846,620 B（1.45%）**、存在但字节不同 1 件（`a2_sites.json`：清单 913,237 B vs '
               u'盘上 17,624,355 B，差 +16,711,118 B 恰为被剔 bounds 段）、**不存在 4,352 件 / '
               u'709,757,429 B（98.53%）**；三桶合计仍精确等于 4,417 / 737,517,286 B（这是划分恒等式，'
               u'不构成对逐件归类的校验）。⇒ **引用本条语料值必须同时声明其为 11-22 快照值**，'
               u'不带失效期会把它读成现盘体量。')

# ③ F29 四处措辞的作用域补全（三处确在正文，第四处「6 个桩体」不在正文，故不写）
F29_OLD_1 = (u'是**同一份 AddRef 的两份拷贝**，不是「一个转发 + 一个真 AddRef」')
F29_NEW_1 = (u'是**同一份 AddRef 的两份拷贝**（**作用域**：该 17 字节序列在 `.text` 全镜像出现 '
             u'**80 次**，本条指的是其中的**两份**，不可读成「全镜像只有两份」），'
             u'不是「一个转发 + 一个真 AddRef」')

F29_OLD_2 = (u'（Hint=432、FirstThunk idx=62、IBN 原始字节 B0 01 49 6E 74…）')
F29_NEW_2 = (u'（Hint=432、FirstThunk idx=**62（DLL 内 0-based 口径）**、'
             u'IBN 原始字节 B0 01 49 6E 74…；同址另有**全局 0-based 63**、**全局 1-based 64** '
             u'两个合法下标，三口径互不相同，缺口径即不可引）')

F29_ADD_LIM = (u'**【R138 补·两处作用域】** ① 「两份拷贝」的作用域：17 字节序列 '
               u'8B44240483C00450FF15C8117E00C20400 在 `.text` 全镜像实测出现 **80 次**'
               u'（R138 主会话独立纯字节搜索，与 R135 各家一致），正文「两份拷贝」指的是其中两份，'
               u'不可读成「全镜像只有两份」。② 「FirstThunk idx=62」的口径：本镜像 InterlockedIncrement '
               u'的组内 0-based 下标为 **62**、全局 0-based 为 **63**、全局 1-based 为 **64**，'
               u'三口径互不相同（R138 主会话经 pefile 遍历导入描述符实测，Hint=432 同得），'
               u'62 只在「DLL 内」口径为真。③ 「8 字节桩序列全镜像 40 次」与「63/77 双槽皆桩」'
               u'**互不构成因果、也互不构成矛盾**：40 是桩体出现次数、63/77 是表计数，'
               u'77 mod 40=37、77−40=37，两者无可推关系，不得互相印证。'
               u'**另记一处 R138 新发现**：R135 审计中出现过的「6 个不同桩体」**不在本条正文任何一列**，'
               u'它是审计过程中自报的中间数字，本条不采用、也不需为它补作用域。')

# ④ F35 补 proved_strict 定义缺一手权威
F35_ADD_LIM = (u'**【R138 补·定义缺一手权威】** 本条 `proved_strict`（= atlas 内 [已证] 且语义栏不含 '
               u'[未证]）的定义**只有二手转述**：一手来源 `PANEL.md`（M52 / 严格口径双列表）'
               u'**不在现盘** —— 全库按文件名精确命中 **0**，其父目录 `COVERAGE/` 亦不存在。'
               u'本条 evidence_paths 唯一一项即该已失文件，故 F35 是 v5.32 里与 F23 并列的'
               u'**两条整行证据链失联项**之一。可机械复核的只有两个 ceil 式本身'
               u'（named_S ≥ ceil(0.9n) ∧ proved ≥ ceil(0.5n)）：R138 在四件台账里按'
               u'「排除假样本行与自述复述行」口径实测**13 处出现 / 9 个去重三元组 / 0 失配**'
               u'（另有 3 处「假样本 ceil(0.9×100)=91」是反控引用、4 处是对该等式的元复述，'
               u'均不计入）；反控 ceil+1 命中降为 0、floor 与 ceil 在 3/9 样本上不同。'
               u'**但 `n` 的取法（atlas 内分母）仍只在已失文件里，本轮未证。**')


def load_rows(b):
    txt = b.decode('utf-8')
    lines = txt.split('\n')
    assert lines[-1] == '', 'file must end with a single LF'
    return lines[:-1]


def apply_edits(lines):
    """逐行改动，返回 (new_lines, log)。每处都必须恰好命中 1 次。"""
    log = []
    out = list(lines)

    def one_time(fid, col, old, new, tag):
        # 找到 fid 行
        idx = None
        for i, l in enumerate(out):
            if l.split('\t')[0] == fid:
                idx = i
                break
        assert idx is not None, 'fid not found: ' + fid
        cells = out[idx].split('\t')
        assert len(cells) == 5, (fid, len(cells))
        if tag == 'append':
            assert new not in cells[col], ('append target already present', fid, col)
            cells[col] = cells[col] + new
        else:
            hits = cells[col].count(old)
            assert hits == 1, ('must hit exactly once', fid, col, hits, old[:40])
            cells[col] = cells[col].replace(old, new)
        out[idx] = '\t'.join(cells)
        log.append((fid, col, tag, len(cells[col])))

    # ① F23 limitations 追加
    one_time('F23', 4, None, F23_ADD_LIM, 'append')
    # ② F24 三处数字撤换 + limitations 追加
    one_time('F24', 1, F24_OLD_A, F24_NEW_A, 'replace')
    one_time('F24', 4, F24_OLD_B, F24_NEW_B, 'replace')
    one_time('F24', 4, F24_OLD_C, F24_NEW_C, 'replace')
    one_time('F24', 4, None, F24_ADD_LIM, 'append')
    # ③ F29 两处 statement 替换 + limitations 追加
    one_time('F29', 1, F29_OLD_1, F29_NEW_1, 'replace')
    one_time('F29', 1, F29_OLD_2, F29_NEW_2, 'replace')
    one_time('F29', 4, None, F29_ADD_LIM, 'append')
    # ④ F35 limitations 追加
    one_time('F35', 4, None, F35_ADD_LIM, 'append')
    return out, log


def main():
    W('# R138 FACT_INDEX v5.32 -> v5.33')
    W()
    old_b = open(PRV, 'rb').read()
    ck('旧文件字节数 == %d' % OLD_BYTES, len(old_b) == OLD_BYTES, len(old_b))
    ck('旧文件 CR == %d（LF-only）' % OLD_CR, old_b.count(b'\r') == OLD_CR,
       old_b.count(b'\r'))
    osha = hashlib.sha256(old_b).hexdigest()
    ck('旧文件 sha256 与基线一致', osha == OLD_SHA, osha)

    lines = load_rows(old_b)
    ck('旧文件 %d 行（表头 + 54 事实项）' % (55), len(lines) == 55, len(lines))
    fids_old = [l.split('\t')[0] for l in lines]
    ck('表头为 fact_id', fids_old[0] == 'fact_id', fids_old[0])
    ck('事实项 F01..F54 连续', fids_old[1:] == ['F%02d' % i for i in range(1, 55)],
       len(fids_old) - 1)

    new_lines, log = apply_edits(lines)
    W('  改动日志（fid, 列, 动作, 新单元格字符数）：')
    for t in log:
        W('    %s' % (t,))
    ck('改动共 9 处', len(log) == 9, len(log))

    # 未改动行必须逐字节相同
    changed = {t[0] for t in log}
    same = all(new_lines[i] == lines[i] for i, l in enumerate(lines)
               if l.split('\t')[0] not in changed)
    ck('未改动的 %d 行逐字节相同' % (55 - len(changed)), same,
       (55 - len(changed), sorted(changed)))
    ck('grade 列一字未动（第 3 列）',
       all(new_lines[i].split('\t')[2] == lines[i].split('\t')[2]
           for i in range(len(lines))))
    ck('evidence_paths 列一字未动（第 4 列）',
       all(new_lines[i].split('\t')[3] == lines[i].split('\t')[3]
           for i in range(len(lines))))

    new_b = ('\n'.join(new_lines) + '\n').encode('utf-8')
    ck('新文件 CR == 0（全 LF）', new_b.count(b'\r') == 0, new_b.count(b'\r'))
    ck('新文件以单个 LF 结尾', new_b.endswith(b'\n') and not new_b.endswith(b'\n\n'))
    ck('新文件 55 行', new_b.count(b'\n') == 55, new_b.count(b'\n'))

    # 关键内容必须在场
    nb = new_b.decode('utf-8')
    for probe, label in [
            (u'6+2+3=**11**', 'F23 分项和 11 在场'),
            (u'没有归属', 'F23 余 1 行无归属 在场'),
            (u'4,147,334 B', 'F23 coverage.tsv 字节数 在场'),
            (u'不能重数', 'F23 计数层不可重数 在场'),
            (u'R138 撤下原「86.19%', 'F24 86.19% 撤下声明 在场'),
            (u'99.992%', 'F24 实测 99.992% 在场'),
            (u'单列地址、没有可回原址复核的第二列', 'F24 结构判据保留 在场'),
            (u'2026-11-22 快照值', 'F24 语料值失效期 在场'),
            (u'4,352 件', 'F24 现盘不存在 4,352 件 在场'),
            (u'80 次', 'F29 两份拷贝作用域 80 次 在场'),
            (u'DLL 内 0-based 口径', 'F29 idx=62 口径 在场'),
            (u'全局 0-based 63', 'F29 全局 63 在场'),
            (u'互不构成因果', 'F29 40/63/77 非因果 在场'),
            (u'proved_strict', 'F35 proved_strict 在场'),
            (u'缺一手权威', 'F35 定义缺一手权威 在场'),
            (u'PANEL.md', 'F35 一手来源名 在场')]:
        ck(label, probe in nb, probe)

    # 「86.19% 盘上无任何字节对应」这条断言不得再以**活断言**形态存在。
    # 它只在撤下声明里被引用（「R138 撤下原「…」一数」）是允许的 —— 那不是主张，
    # 是撤回记录。故判据是：每次出现都必须紧跟在「撤下原「」之后。
    DEAD = u'86.19% 盘上无任何字节对应'
    occ = []
    st = 0
    while True:
        i = nb.find(DEAD, st)
        if i < 0:
            break
        occ.append(i)
        st = i + 1
    ck(DEAD + u' 仅作为撤回记录出现（每次都在「撤下原「」之后）',
       all(nb[max(0, i - 4):i] == u'撤下原「' for i in occ) and len(occ) >= 1,
       [(i, nb[max(0, i - 4):i]) for i in occ])

    if DRY:
        W()
        W('--dry：不写盘。新文件将 %d B（旧 %d B，差 %+d）'
          % (len(new_b), OLD_BYTES, len(new_b) - OLD_BYTES))
        W('sha256(new) = ' + hashlib.sha256(new_b).hexdigest())
        return 0 if not fails else 1

    # ---- 备份 ----
    if not os.path.isdir(BASE):
        os.makedirs(BASE)
    ts = time.strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BASE, 'FACT_INDEX.tsv.before_R138_v533_%s.bak' % ts)
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, old_b)
    finally:
        os.close(fd)
    ck('备份已 wx 独占创建', os.path.exists(bak))
    ck('备份 sha256 == 旧文件 sha256',
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == OLD_SHA)

    # ---- 写入 ----
    if not os.path.isdir(DSTD):
        os.makedirs(DSTD)
    fd = os.open(DST, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, new_b)
    finally:
        os.close(fd)
    W('  写入 %s' % DST)

    # ---- 回读校验 ----
    rt = open(DST, 'rb').read()
    ck('回读字节数一致', len(rt) == len(new_b), (len(rt), len(new_b)))
    ck('回读 sha256 一致', hashlib.sha256(rt).hexdigest()
       == hashlib.sha256(new_b).hexdigest())
    ck('回读 CR == 0', rt.count(b'\r') == 0)
    rt_lines = rt.decode('utf-8').split('\n')[:-1]
    ck('回读 55 行', len(rt_lines) == 55, len(rt_lines))
    ck('回读未改动行仍逐字节相同',
       all(rt_lines[i] == lines[i] for i in range(len(lines))
           if lines[i].split('\t')[0] not in changed))
    ck('源版本 v5.32 未被修改',
       hashlib.sha256(open(PRV, 'rb').read()).hexdigest() == OLD_SHA)

    W()
    W('== 断言 %d PASS / %d FAIL ==' % (len(buf) - len(fails) - 0, len(fails)))
    W('new sha256 = ' + hashlib.sha256(rt).hexdigest())
    W('new bytes  = %d (old %d, %+d)' % (len(rt), OLD_BYTES, len(rt) - OLD_BYTES))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
