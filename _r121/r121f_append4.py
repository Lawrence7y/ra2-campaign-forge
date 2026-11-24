#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r121f_append4.py -- R121 四件套写入（严格按写入纪律）。

纪律：
  R0 写盘前先断言新段不含反引号（本轮上一版把这条断言放在了写之后，属于自错，已修）。
  R1 在 R17_LEAD_BASELINE/ 用 'x'（wx）排他创建唯一备份；文件已存在即失败。
  R2 备份前断言旧 sha256 与旧 CR 与预期相等；不等即中止。
  R3 一次性写入（每文件一次 write）。
  R4 回读校验：新 CR、新 sha256、LF 增量、行数上限。

反控：
  N4 幂等反控：再建同名备份必须 FileExistsError（证明 wx 语义成立）。
"""
import hashlib
import json
import os
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASELINE = os.path.join(BASE, 'R17_LEAD_BASELINE')
FILES = {
    'R14_COMMON': os.path.join(BASE, 'R14_COMMON.md'),
    'STATUS_BOARD': os.path.join(BASE, 'STATUS_BOARD.md'),
    'LEDGER': os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md'),
    'LEAD_LOCK': os.path.join(ROOT, 'lead/LEAD_LOCK'),
}
EXPECT_CR = {'R14_COMMON': 1081, 'STATUS_BOARD': 0, 'LEDGER': 337, 'LEAD_LOCK': 137}
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name +
          ((' | ' + json.dumps(detail, ensure_ascii=False)) if detail != '' else ''), flush=True)
    return bool(cond)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def backup(key, path, tag):
    raw = open(path, 'rb').read()
    old_sha, old_cr = sha(raw), raw.count(b'\r')
    ck('%s 备份前断言旧 CR = %d（预期 %d）' % (key, old_cr, EXPECT_CR[key]),
       old_cr == EXPECT_CR[key], {'old_cr': old_cr, 'old_sha': old_sha[:16]})
    stamp = time.strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(BASELINE, 'SUPERSEDED.before_r121b_%s_%s.bak' % (tag, stamp))
    with open(dst, 'xb') as f:
        f.write(raw)
    ck('%s 备份已 wx 排他创建' % key, os.path.isfile(dst),
       {'backup': os.path.basename(dst), 'bytes': len(raw), 'sha': old_sha[:16]})
    return dst, old_sha, raw


SEC_2125 = '''

## 2.125 R121 —— 崩溃轮遗留的两处判据缺陷被定位并修掉；QI 出参去向从「36 个」修正为 60/60；并给出「通用包装器」的第一条强证据

### 2.125.1 本轮先修的是上一轮的半成品，不是新找一条链

R121 前两次主会话（#225/#226）被 harness 重启打断，_r121/r121a_qiconsume.py 落盘时 10/11 PASS，唯一 FAIL 是反控 N3。本轮没有绕过它，而是查它为什么翻不动，结果查出两处判据本身的缺陷。

### 2.125.2 缺陷 D1：ppv 槽 K 从未参与判定（反控 N3 结构性恒 FAIL）

r121a 的 analyze() 解出 P = mov P,[esp+K] 之后，只把 P 写进 out 的 P 字段与 arg_index；consume 的写入点在源码第 178 行，P 的唯一使用点在第 180 行，且全文件不存在 P is None 门槛（复算 r121d 的 A1/A1b 成立）。所以 K 平移任意值，consume 桶都不变。

实测（r121d 与 r121b 双向验证）：K 平移 -0x10 / -0xc / -8 / -4 / +4 / +8 / +0x10 / +0x14 共 8 个值，OleSaveToStream 恒为 36。加 P 门槛后同一反控立刻翻动：36 变成 0（r121d 的 A4 实跑，审计员先前只给推断的「预测 0」被实测确认）。

### 2.125.3 缺陷 D2：寄存器回溯的后向窗口只有 0x40 字节

调用是 win(s, 0x40, 0x100)（第 135 行，复算 A5 成立）。24 个站点写成 call ebp（字节 ff d5，24/24 全中，复算 B1 成立），而 ebp 的初值在 0x67d351 的 mov ebp, dword ptr [0x7e15f4]。站点到该写的距离：最小 0x9d = 157 字节，最大 2938 字节（复算 B4/B4b），全部落在 0x40 窗口外，因此被误报 REG:ebp<-UNRESOLVED。

这一步还抓出我自己的第三个缺陷：把后向窗口改宽后，线性回溯给出的「最近一次写 ebp」是 0x67d44f 的 pop ebp，而该指令位于错误返回路径（0x67d44b 的 jge 0x67d457 跳过它）。所以线性回溯在该函数上结构性失效，必须换 CFG。那一版脚本当时跑出 11/11 PASS 而结论是错的 —— 断言全绿不等于结论对。

### 2.125.4 改用 CFG 到达定义后：60 个站点横跨 36 个函数体

r121c（reaching definitions，disasm_lite 与函数体级单步，未整段 .text 开 detail）实测：

- 60 个站点覆盖 36 个函数体：1 个主函数 0x67d300（25 站）加 35 个 0x80 字节孪生函数（各 1 站，地址 0x67fdf0 + 0x80*k）。
- 主函数 25 站：ebp 的到达定义集合恰为单元素 0x67d351（即 mov ebp,[0x7e15f4]），因此 call ebp 的目标可机械确定为 ole32 的 OleSaveToStream。反控 N2（入口改 0x67d357 跳过序言）使该结论归 0，证明判据真的在用这个定义。
- 35 个孪生函数：不用 ebp（写 ebp 0 个、call ebp 0 个，复算 T2），直接 call dword ptr [0x7e15f4]。

### 2.125.5 合并口径：60/60，且 ppv 恒为第 1 实参

唯一允许写进台账的口径（r121e）：合格 = Ⅰ 直接 IAT 调 [0x7e15f4]（35 个）加 Ⅱ call REG 且该处 REG 的 CFG 到达定义为唯一的 mov REG,[0x7e15f4]（25 个）= 60/60。ppv 的实参位置分布是 {0: 60}（全是 OleSaveToStream 的第 1 实参 pPStm）。

对照与反控：只用规则 Ⅰ 得 35（规则 Ⅱ 贡献 25，非冗余）；放宽为「到达定义含该定义」得 60（本盘「唯一」未剔除任何站，但它是规则的一部分，不是装饰）；0x7f7c90 的 56 站里 IAT 直调 OleSaveToStream 为 0 个。

### 2.125.6 「通用包装器」第一条强证据（L3 从「未排除」降级为「已有反证，覆盖 35/60」）

35 个孪生函数字节完全相同：体长 127 字节、不同哈希数为 1（复算 T1）。但它们被 35 个不同调用点以 35 个不同的 edx 立即数调用（35 个不同地址，实测无重复）。

所以若这 35 处是「35 个手写函数各自专门使用该接口」，字节不该完全相同；字节相同而只差一个参数，这是代码生成器按元素类型展开模板的形态，不是手写专用代码。这是 R120 判「统计量排不掉」之后，第一条不依赖统计量的方向性反证。

但仍不外推：它证明的是这 35 处是模板展开，不证明主函数的 25 处也是；主函数那 25 处只有「到达定义唯一」这一条支撑。L3 的诚实表述是：35/60 已有模板展开的强证据，25/60 仍未排除。

### 2.125.7 跨家族审计（hy4 task 229，27 回合，2.3 分钟，无 OVERTIME）全部成立，r121d 20/20 PASS 逐条复算

审计员报的每一条我都用完全独立的实现重算，全部成立，连它自标「未复算」的两项也补上了：N6 的 176（我复算 176）与「ebp 收到 OleSaveToStream 的写点 2 个」（我复算 0x5be84f 与 0x67d351）。

审计给出我自己没发现的第三条缺陷 C2：after 的循环上界是 range(i+1, i+10) 即 9 条内，而断言文案写「<=8 条内」，差 1 条。我复算：真 9 条内命中 60、真 8 条内命中 60，本样本上不改变结论，但文案是错的，已就此更正。审计还指出 C3：after 的键恒为 [ecx + 8]，断言却写成任意 reg，是特化。两条都成立。

### 2.125.8 执行员（deepseek task 228）OVERTIME 且 failed，但其落盘原始数字可用

wait_subagents 回报：failed，61 回合，实测 17.03 分钟 vs 预算 8.0 分钟 [OVERTIME]，错误 error_max_turns，只落 q1/q2，report 未写。

按规则 D 我不采信其结论，只取它的原始数字并与我独立复算比对：站点集 60/60 逐地址相同；反控 0x7f7c81 得 0；对照 0x7f7c90 得 56；K 分布 {16:1, 20:24, 12:35}；ppv 槽装回寄存器 eax 60/60；逐站点桶归属 0 处分歧（iat 35 / reg 25）。所以两个家族在 60 个站点的桶归属上完全一致，分歧只在它没做完 Q3/Q4。

### 2.125.9 未取得（不粉饰）

① 35 个孪生函数的 35 个 edx 参数指向什么结构（只测到 35 个不同地址）；② 主函数那 25 站的模板展开证据（与 35 站不同源）；③ 0x7f7c70 的接口名（本机仍无 IID 到名映射表，全盘 grep 无 IPersistStream 头）；④ IPersistStream 方法数；⑤ 门禁 C11 的其余 4 处「永远通过」子项；⑥ 五条不可能行未裁定；⑦ 窗口表未扩。

### 2.125.10 自错登记 S-85..S-94

- S-85 首版 r121b 的 ppv_slot 要求 lea 与 push 相邻，而真实形态中间隔一条 mov eax,[eax+ebx*4]，导致只有 23/60 解出槽（把合法形态判成非法）。
- S-86 last_write_before 用 ops.endswith 逗号加 reg 与 ops 等于 reg 去捕获「写」，把 call ebp 与 push ebp 这类读当成了写，算出 23 个 REG-OTHER-WRITE。
- S-87 上面那个 bug 修好后脚本 11/11 PASS，但结论仍错（线性回溯被错误返回路径的 pop ebp 截断）—— 断言全绿不等于结论对。
- S-88 全局变量 OUT 被 reaching_defs 的返回值覆盖，导致 TypeError 且掩盖了真实结果。
- S-89 首版 CFG 只建 0x67d300 一个函数，把 60 站里 35 站报成 OUT-OF-CFG，我一度以为是解码错。
- S-90 把 0x67fdf0 与 0x67fe70 当成两个独立函数，实际是 35 个孪生函数里的前两个（漏了 33 个）。
- S-91 r121d 里 re.fullmatch(...).group(1) 在匹配失败时抛 AttributeError（先调用再判空）。
- S-92 审计卡里塞了审计员根本不看的占位预设数值。
- S-93 我一度准备把「23 个 REG-OTHER-WRITE」写进台账，若没查 pop ebp 的路径可达性，本轮就会把错数写成交付。
- S-94 四件套写入脚本把「新段不含反引号」这条断言放在了写盘之后，第一次跑就真把带反引号的段落写进了四个文件；靠 wx 备份全量回滚才恢复（四个文件旧 sha 已逐一核对复原）。

另外用 grep 自查发现 9 条断言写成 ck(..., True, ...) 恒定通过，已全部改成真实条件（改后仍全 PASS）。

收口：r121b 11 / r121c 11 / r121d 20 / r121e 7 = 49 项断言全 PASS；全程 disasm_lite 与函数体级单步，未对整段 .text 开 detail；脚本均带 timeout，收口确认无孤儿进程；五项 CR 全绿 1081/137/337/0/2952。
'''

SEC_1175 = '''

## §1175 R121 · 崩溃轮半成品里的两处判据缺陷；QI 出参从 36 修正为 60/60；并给出通用包装器的第一条强证据

- 先修半成品，不绕过 FAIL：#225/#226 打断留下的 _r121/r121a_qiconsume.py 是 10/11 PASS，唯一 FAIL 是反控 N3。查因查出判据缺陷而非数据问题。
- D1 ppv 槽 K 从未参与判定：consume 写入点（第 178 行）早于 P 的唯一使用点（第 180 行），全文件无 P is None 门槛，所以 K 平移 8 个值（-0x10 到 +0x14），OleSaveToStream 恒为 36。加门槛后反控立即翻动 36 到 0（实跑）。
- D2 后向窗口只有 0x40 字节：24 站写 call ebp（字节 ff d5，24/24），ebp 初值在 0x67d351 的 mov ebp,[0x7e15f4]，距离 157 到 2938 字节，全在窗口外，因此误报 UNRESOLVED。
- 第三个缺陷是我自己的：窗口改宽后线性回溯抓到 0x67d44f 的 pop ebp，而它在错误返回路径（0x67d44b 的 jge 跳过），所以线性回溯结构性失效，必须换 CFG。该版脚本当时 11/11 PASS 而结论错。
- CFG 到达定义：60 站横跨 36 个函数体（主函数 0x67d300 的 25 站加 35 个 0x80 字节孪生函数各 1 站）。主函数 25 站的 ebp 到达定义恰为单元素 0x67d351；反控（入口改 0x67d357 跳过序言）使其归 0。
- 合并口径 60/60：Ⅰ IAT 直调 [0x7e15f4] 共 35 加 Ⅱ CFG 唯一到达定义 25，合计 60/60，ppv 实参位置 {0: 60}。只用 Ⅰ 得 35（Ⅱ 贡献 25，非冗余）；0x7f7c90 侧 OLE 直调 0。
- L3 降级为「已有反证（覆盖 35/60）」：35 个孪生函数体长 127、不同哈希数为 1（字节完全相同），却被 35 个不同调用点以 35 个不同 edx 立即数调用，手写专用代码不该字节全同，所以这 35/60 是模板展开。但主函数 25/60 仍未排除，不整体宣称排除。
- 跨家族审计（hy4 task 229，27 回合 2.3 分钟，无 OVERTIME）全部成立，r121d 20/20 PASS 复算，含它自标未复算的 176 与「2 个写点」。审计另给出我漏的 C2：after 循环上界是 i+10 即 9 条内而断言文案写 <=8 条，差 1 条（本样本不改变结论，但文案错）；C3：after 键恒 [ecx+8]，断言写成任意 reg 是特化。
- 执行员 deepseek task 228：failed 加 [OVERTIME]，61 回合，17.03 分钟 vs 预算 8.0 分钟，error_max_turns，只落 q1/q2，report 未写。按规则 D 不采信结论，只取原始数字：站点集 60/60 逐地址相同、反控一致、K 分布 {16:1, 20:24, 12:35} 相同、逐站点桶归属 0 处分歧。
- 未取得：35 个 edx 参数指向的结构；主函数 25 站的模板证据；0x7f7c70 接口名；IPersistStream 方法数；C11 其余 4 处「永远通过」；五条不可能行未裁定；窗口表未扩。
- 自错 S-85 到 S-94 共 10 条（ppv_slot 要求相邻、把读当写、断言全绿结论仍错、全局名被覆盖、只建一个函数、漏 33 个孪生、先 group 再判空、卡面塞无用预设、差点把 23 这个错数写进台账、反引号断言放在写盘之后导致真写进文件后靠备份回滚）。另自查发现 9 条 ck 写成恒真，已改成真实条件。
'''

SEC_LOCK_EP = '''

## EP · R17 第 121 轮（2026-11-24 21:2x 至 22:0x）· 崩溃轮的两处判据缺陷被定位；QI 出参由 36 修正为 60/60；通用包装器第一次拿到不依赖统计量的反证（覆盖 35/60）

EP1. 接手的是半成品，不是新链。#225/#226 被 harness 重启打断，_r121/r121a_qiconsume.py 落盘时 10/11 PASS，唯一 FAIL 是反控 N3。我没有绕开它，而是把它当线索。

EP2. D1（判据缺陷，不是数据问题）：consume 的写入点在源码第 178 行，P 的唯一使用点在第 180 行，且全文件无 P is None 门槛，所以 K 从未参与判定。实测 K 平移 8 个值（-0x10/-0xc/-8/-4/+4/+8/+0x10/+0x14），OleSaveToStream 恒为 36。加门槛后反控立刻翻动 36 到 0。所以崩溃轮那个 FAIL 是必然而不是异常，且它原先的 36 这个数是被污染的。

EP3. D2（窗口缺陷）：win(s, 0x40, 0x100) 的后向只有 0x40 字节。24 个站点写 call ebp（ff d5，24/24 逐字节核对），ebp 的初值在 0x67d351 的 mov ebp, dword ptr [0x7e15f4]。距离实测 157 到 2938 字节，全部在窗口外，因此误报 REG:ebp<-UNRESOLVED。

EP4. 第三个缺陷是我自己的，也是最危险的一个。把窗口改宽后，线性回溯给出「最近一次写 ebp 是 0x67d44f 的 pop ebp」，而该指令在错误返回路径上（0x67d44b 的 jge 0x67d457 跳过它）。那一版脚本 11/11 全 PASS，结论却是错的。所以断言全绿不等于结论对；线性回溯在有错误返回路径的函数上结构性失效。

EP5. 换 CFG 到达定义。60 个站点横跨 36 个函数体：主函数 0x67d300 的 25 站加 35 个 0x80 字节孪生函数各 1 站（0x67fdf0 + 0x80*k）。主函数 25 站处 ebp 的到达定义集合恰为单元素 0x67d351。反控 N2：入口改 0x67d357 跳过序言使其归 0（证明判据真在用这个定义）。N3 用合成带分支字节串做正控：分析不是恒返回全集或恒返回单值。

EP6. 合并口径 60/60。Ⅰ 直接 IAT 调 [0x7e15f4] 共 35；Ⅱ call REG 且该处 REG 的 CFG 到达定义唯一为 mov REG,[0x7e15f4] 共 25；合计 60/60，ppv 的实参位置分布是 {0: 60}（全是 OleSaveToStream 第 1 实参）。反控：只用 Ⅰ 得 35（Ⅱ 非冗余）；放宽「唯一」得 60（本盘未剔除，但规则保留）；0x7f7c90 侧 OLE 直调 0。

EP7. 通用包装器的第一条强证据（L3 降级）。35 个孪生函数体长 127 字节、不同哈希数为 1（字节完全相同），却被 35 个不同调用点以 35 个不同 edx 立即数调用（35 个不同地址，无重复）。所以手写的 35 个专门使用该接口的函数不该字节全同、只差一个参数；这是代码生成器按元素类型展开模板的形态。R120 判统计量排不掉，本轮给出的是不依赖统计量的反证。但只覆盖 35/60：主函数那 25 站仍未排除，不整体宣称排除。

EP8. 跨家族审计（hy4 task 229，27 回合 / 2.3 分钟 / 无 OVERTIME）全部成立，r121d 20/20 PASS 复算。连它自标「未复算」的两项也补上了：N6 的 176（我复算 176）与 ebp 收到 OleSaveToStream 的写点 2 个（我复算 0x5be84f 与 0x67d351）。审计给出我漏的第三条缺陷 C2：after 的循环上界 range(i+1, i+10) 是 9 条内，断言文案却写 <=8 条（差 1 条；本样本两值都 60，不改变结论，但文案错，已更正）。C3：after 的键恒为 [ecx + 8]，断言写成任意 reg 是特化。两条都成立。

EP9. 规则 D：执行员 deepseek task 228 是 failed 加 [OVERTIME]。61 回合，实测 17.03 分钟 vs 预算 8.0 分钟，error_max_turns，只落 q1/q2，report 未写。其任何结论不采信；只用落盘原始数字与我的独立复算比对：站点集 60/60 逐地址相同、反控 0x7f7c81 得 0 与 0x7f7c90 得 56 相同、K 分布 {16:1, 20:24, 12:35} 相同、ppv 装回寄存器 eax 60/60、逐站点桶归属 0 处分歧（iat 35 / reg 25）。所以两家族在桶归属上完全一致。

EP10. 自错 S-85 到 S-94（10 条）：S-85 ppv_slot 要求 lea 与 push 相邻而真实形态隔一条 mov，导致只有 23/60（把合法形态判非法）；S-86 用 ops.endswith 与 ops 等于 reg 去捕获「写」，把 call ebp 与 push ebp 这类读当成了写；S-87 上 bug 修好后脚本 11/11 PASS 而结论仍错（线性回溯被错误返回路径的 pop ebp 截断）；S-88 全局 OUT 被 reaching_defs 返回值覆盖；S-89 首版 CFG 只建一个函数，35 站报 OUT-OF-CFG；S-90 把 0x67fdf0 与 0x67fe70 当独立函数，漏了 33 个孪生；S-91 re.fullmatch(...).group(1) 先调用再判空抛 AttributeError；S-92 审计卡里塞了审计员根本不看的占位预设；S-93 我一度准备把「23 个 REG-OTHER-WRITE」写进台账，若没查 pop ebp 的路径可达性，本轮会把错数当交付；S-94 四件套写入脚本把「新段不含反引号」的断言放在写盘之后，第一次跑就真把带反引号的段落写进了四个文件，靠 wx 备份全量回滚复原（四个文件旧 sha 已逐一核对）。

EP11. 另用 grep 自查发现 9 条断言写成 ck 的真值参恒为 True（恒定通过），已全部改成真实条件，改后仍全 PASS。这是本轮把「永远通过子项」这条纪律用在自己脚本上的结果。

EP12. 收口：r121b 11 / r121c 11 / r121d 20 / r121e 7 = 49 项断言全 PASS。全程 disasm_lite 与函数体级单步，未对整段 .text 开 detail=True；脚本均带 timeout；收口前确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；check_disc.py exit 0。

EP13. 未取得（不粉饰）：① 35 个 edx 参数各指向什么结构（只测到 35 个不同地址，内容未解）；② 主函数那 25 站的模板展开证据（与 35 站不同源，不能外推）；③ 0x7f7c70 的接口名（本机全盘 grep IPersistStream 无头文件，仍无 IID 到名映射表）；④ IPersistStream 方法数；⑤ 门禁 C11 其余 4 处「永远通过」子项未动；⑥ 五条不可能行未裁定；⑦ 窗口表未扩（缺 55 份真实快照）。
'''

BOARD_ROW = '''- **R121**（2026-11-24）· **崩溃轮半成品里的两处判据缺陷被定位；QI 出参由 36 修正为 60/60；通用包装器首次拿到不依赖统计量的反证（覆盖 35/60）**
  - D1：consume 写入点（源码 178）早于 P 唯一使用点（180），全文件无 P is None 门槛，所以 **ppv 槽 K 从未参与判定**；K 平移 8 个值 OleSaveToStream 恒为 36，加门槛后反控 36 变 0。崩溃轮那个 FAIL 是**必然**，且 36 这个数被污染。
  - D2：后向窗口仅 **0x40** 字节；24 站写 call ebp（ff d5 24/24），ebp 初值在 0x67d351 的 mov ebp,[0x7e15f4]，距离 **157 到 2938 字节**，因此误报 UNRESOLVED。
  - 我自己最危险的错：窗口放宽后线性回溯抓到错误返回路径上的 0x67d44f pop ebp，那版 **11/11 PASS 而结论错**，所以断言全绿不等于结论对。
  - CFG 到达定义：60 站横跨 **36 个函数体**（主函数 0x67d300 的 25 站加 35 个 0x80 孪生各 1 站）；主函数 25 站 ebp 到达定义**唯一** 0x67d351；反控（跳过序言）使其归 0。
  - 合并口径 **60/60**（IAT 35 加 CFG 25），ppv 实参位置 **{0: 60}**；0x7f7c90 侧 OLE 直调 **0**。
  - L3：35 个孪生函数**体长 127、哈希数 1**（字节全同）却接 **35 个不同 edx**，所以是**模板展开**，手写专用说不成立；但只覆盖 35/60，主函数 25 站仍未排除。
  - 审计 hy4 task 229（27 回合 / 2.3 分钟 / 无 OVERTIME）全成立，r121d **20/20 PASS** 复算（含 176 与「2 个写点」）；审计补我漏的 C2（after 是 **9 条内**而文案写 8 条）、C3（键恒 [ecx+8]，写成任意 reg 是特化）。
  - 执行员 deepseek task 228 **failed 加 [OVERTIME]**（61 回合 / **17.03 分钟 vs 预算 8.0** / error_max_turns），只落 q1/q2；按规则 D 只取原始数字：站点 60/60 相同、K 分布相同、**逐站桶归属 0 分歧**。
  - 自错 S-85 到 S-94 共 10 条（含反引号断言放在写盘之后，靠备份回滚）；另自查 9 条恒真断言已改真实条件；r121b/c/d/e 断言 **49 项全 PASS**；五项 CR 全绿；check_disc.py exit 0。
  - 未取得：35 个 edx 指向的结构、主函数 25 站的模板证据、0x7f7c70 接口名、IPersistStream 方法数、C11 其余 4 处、五条不可能行、窗口表未扩。
'''

targets = [
    ('R14_COMMON', SEC_2125, 'R14_COMMON.md'),
    ('LEDGER', SEC_1175, 'GOAL_THREE_TARGETS_20261018.md'),
    ('LEAD_LOCK', SEC_LOCK_EP, 'LEAD_LOCK'),
    ('STATUS_BOARD', '\n' + BOARD_ROW, 'STATUS_BOARD.md'),
]

results = {}
for key, seg, tag in targets:
    path = FILES[key]
    exp_cr = EXPECT_CR[key]
    # R0 写盘前断言
    ck('%s 【写盘前】新段不含反引号' % key, '`' not in seg, {'len': len(seg)})
    if '`' in seg:
        raise SystemExit('refusing to write %s: backtick in segment' % key)
    bdst, old_sha, raw = backup(key, path, tag)
    new = raw + seg.encode('utf-8')
    with open(path, 'wb') as f:
        f.write(new)
    back = open(path, 'rb').read()
    ck('%s 回读 sha256 与写入内容一致' % key, sha(back) == sha(new),
       {'new_sha': sha(back)[:16], 'bytes': len(back)})
    ck('%s 回读 CR 保持 %d' % (key, exp_cr), back.count(b'\r') == exp_cr,
       {'cr': back.count(b'\r'), 'expected': exp_cr})
    ck('%s 回读 LF 增量 = 新段 LF 数' % key,
       back.count(b'\n') - raw.count(b'\n') == seg.encode('utf-8').count(b'\n'),
       {'lf_delta': back.count(b'\n') - raw.count(b'\n')})
    results[key] = dict(backup=os.path.basename(bdst), old_sha=old_sha,
                        new_sha=sha(back), bytes=len(back),
                        cr=back.count(b'\r'), lf=back.count(b'\n'))

for key in EXPECT_CR:
    raw = open(FILES[key], 'rb').read()
    ck('%s 最终 CR = %d' % (key, EXPECT_CR[key]), raw.count(b'\r') == EXPECT_CR[key],
       {'cr': raw.count(b'\r')})

board_lines = open(FILES['STATUS_BOARD'], 'rb').read().count(b'\n')
ck('STATUS_BOARD 行数 = %d（上限 300）' % board_lines, board_lines <= 300, {'lines': board_lines})

for key in EXPECT_CR:
    ck('%s 备份文件存在' % key,
       os.path.isfile(os.path.join(BASELINE, results[key]['backup'])),
       {'file': results[key]['backup']})

again = os.path.join(BASELINE, results['R14_COMMON']['backup'])
try:
    with open(again, 'xb') as f:
        f.write(b'x')
    ck('N4 反控 同名备份不可覆盖', False, {'file': again})
except FileExistsError:
    ck('N4 反控 同名备份不可覆盖（wx 语义成立）', True, {'file': os.path.basename(again)})

outp = os.path.join(ROOT, '_r121', 'r121f_append4.json')
open(outp, 'w', encoding='utf-8').write(json.dumps(
    dict(checks=checks, files=results, board_lines=board_lines), ensure_ascii=False, indent=1))
npass = sum(1 for c in checks if c['ok'])
print('\n%d/%d PASS -> %s' % (npass, len(checks), outp))
sys.exit(0 if npass == len(checks) else 1)
