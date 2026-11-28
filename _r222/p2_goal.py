# -*- coding: utf-8 -*-
"""R222 p2：GOAL_THREE_TARGETS §1280 追加。"""
import os, hashlib, re

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = ROOT + '/R17_LEAD_BASELINE'
GOAL = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
fails = []


def ck(n, c, d=''):
    if not c:
        fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))


def bak(path, tag):
    b = open(path, 'rb').read()
    base = '%s/%s.before_r222_%s' % (BASE, os.path.basename(path), tag)
    for i in range(10):
        dst = base + (('_%d' % i) if i else '') + '_20261128.bak'
        if os.path.exists(dst):
            if open(dst, 'rb').read() == b:
                return b, dst
            continue
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as f:
            f.write(b)
        return b, dst
    raise SystemExit('bak exhausted')


b = open(GOAL, 'rb').read()
ck('G0 GOAL CR=337 bytes=5485245', b.count(b'\r') == 337 and len(b) == 5485245, (b.count(b'\r'), len(b)))
s = b.decode('utf-8')
ck('G1 GOAL 末节 §1279', [l for l in s.split('\n') if l.startswith('## §')][-1].startswith('## §1279'))

APP = """
## §1280 · R222（2026-11-28）· ADPCM 解包器 0x7c62ac 定性（内联 delta + 双声道两遍）+ 16 项索引表 + 两个分派器接受集差异；FACT_INDEX V604

**一句话**：`0x7c62ac` 不是编码器，是**内联 delta 解包器**：吃 packed nibble 吐 PCM 样本，delta 用
`test eax,4/2/1 + shr 3 + test eax,8` 现算（与差分表 `0x879b30` 同一个律 D 定义，m6 已证 1424/1424），
三份展开副本按**声道**而非位宽划分，双声道时 copy2→copy3 各解一个声道并隔字交错写出。

**1. 方向判据（关闭 R221 待办①）.**
- 读入 `mov al, byte ptr [esi]`（1 B 含 2 nibble），写出 `mov word ptr [edi], ax`（16 位）或
  `xor ah,0x80` + `mov byte ptr [edi], ah`（8 位）；反控成立：全函数**既无** `mov [esi],..` **也无**把 `[edi]` 读进累加器
  （`_r222/m8_inline_dec.py` R1）。
- 全函数 **0 条** `0x879b30` 引用。delta 定义 = `(s>>3) + [n&4]s + [n&2](s>>1) + [n&1](s>>2)`，`n&8` 取负；
  与表版解码器 `0x7c6808` / `0x7c7428` 的律 D 完全一致（`_r222/m6_final.py` C1 **1424/1424**）。
- nibble 选择用 `test dword ptr [ebx+0x10], 1` 的 bit0：置位时 `mov ax, word[ebx+0x1c]` + `shr eax,4`（复用缓存字的高 4 位），
  清零时读新字节取低 4 位；每条路径末 `and eax,0xf` 截到 0..15。
- 样本计数 16 位模式先 `shr eax,1`（`0x7c62ce cmp word[ebx+0x38],0x10` / `0x7c62d5 shr eax,1`），8 位不除。

**2. 声道拓扑（修正「按位宽划分」的初判）.** 字段实测（`_r222/m11_channel_layout.py`，14 断言 / 0 FAIL）：
copy1（`0x7c62ea..0x7c63e8`，78 条）与 copy2（`0x7c63ea..0x7c6509`，88 条）只用 **ch1** 状态；
copy3（`0x7c6509..0x7c6609`，75 条）只用 **ch2** 状态；六对字段基址差恒为 **0x14**
（`+0x10↔+0x24`、`+0x14↔+0x28`、`+0x1c↔+0x30`、`+0x1e↔+0x32`、`+0x20↔+0x34`、`+0x22↔+0x36`，delta 累加器 `+0x18↔+0x2c`），
两套状态**互不相交**，只共享 `+0x38`（位宽）与 `+0x3a`（声道数）两个格式字段。
入口 `0x7c62df cmp word[ebx+0x3a],2` / `0x7c62e4 je 0x7c63ea`（6 B）：**声道 1 顺序落入 copy1 单遍；
声道 2 跳 copy2**；copy2 尾部 `0x7c64f0..0x7c6506` 重建 `esi=[ebx]+1`、`edi=[ebx+4]+1`（16 位再 `inc edi`）后
`jmp 0x7c6509` 进 copy3。输出步进 copy1 `edi+=2`/`inc`，copy2/copy3 `edi+=4`/`+=2` ⇒ 双声道**隔字交错**。
三条尾部都收在 `0x7c6609` 共享返回块（`mov eax,[ebp-4]` + 5 pop + leave + ret）。

**3. 0x8758d4「0 条字面引用」≠ 死数据.** 解包器 `mov ax, word[ecx + 0x8758c4]`（`0x7c639b`/`0x7c649f`/`0x7c65be`）
里 `ecx = 2*nibble`（`0x7c6399 shl ecx,1`），nibble 15 时读 `0x8758e2..0x8758e3`，落在 `0x8758d4..0x8758e3` 内。
实测 16 项有符号字 = `(-1,-1,-1,-1,2,4,6,8)` 重复两遍，两处 16 B 逐字节相同 ⇒ 这是**一张 16 项表**
（低 3 位选幅度调整、bit3 是负号），`0x8758d4` 是它的第二个 8 项。R221 记的「未被引用的重复常量」据此订正。

**4. 两个分派器接受集不同.** `0x7c6752`（块1）与 `0x7c7371`（块2）都读 `word[+0x38]`/`word[+0x3a]` 做同一套 2x2 比较，
但落点不同：`0x7c6752` 的三条非 `(16,1)` 组合全部跳 `0x7c69ad`（实测为尾声 `pop/leave/ret`），
只有 `(0x10,1)` 顺序落入 `0x7c67a4` 主体；`0x7c7371` 把 `(0x10,2)` 送到 `0x7c7788`（stereo 入口）、
`(0x10,1)` 顺序落入 `0x7c73c3`（mono 入口），`cx∈{8}` 与其他组合都跳 `0x7c75cc` 尾声（且该路径 `eax` 未被置值，
返回值是调用方残留 —— 审计 #582 口径② 成立）。另：`0x7c7371` 直接跳尾声时不做任何解码，实测其字节
`5a 59 5b 5f 5e c9 c3`（纯 pop/leave/ret）。

**5. 0x7c7371 只有 2 个调用点（R221 待办写「4 个」）.**
全 `.text` `e8 rel32` 扫唯一命中 `0x7c24a2` 与 `0x7c2557`；该地址作为 dword 字面量在全文件出现 **0** 次。
两个调用点都压 6 个实参并 `add esp,0x18`，按 stdcall 逆序：
`[ebp+8]=esi`（源）、`[ebp+0xc]=[ebx+0x78c]` 或 `[ebx+0x7a8]`（目标）、`[ebp+0x10]=byte[ebx+0x3f]`、
`[ebp+0x14]=byte[ebx+0x3e]`、`[ebp+0x18]=ebp`（寄存器值，静态不能证明其语义）、`[ebp+0x1c]=&[ebx+0x7d0]`（状态块）。
`byte[ebx+0x3e]` / `byte[ebx+0x3f]` 的写点 `0x7c2a0d` / `0x7c2a29` / `0x7c2a32`，取自
`word[ebx+0x104]` / `byte[ebx+0x106]` / `byte[ebx+0x107]`（或 `+0x100/+0x102/+0x103` 另一分支），即 ACM 流格式块字段。

**6. 两个初始化函数不对称且与声道布局自洽.** `0x7c6270` 清 8 个字段（两套完整状态）并置两声道 step=7；
`0x7c6730` 只清 4 个（两套的 index + 预测器），不碰 step/count。块1 路径的 step 初值来自主循环首次读
`0x8758e4` 表首项 7，块2 路径由 init 直接置 —— 两条路径终值相同、处置方式不同。

**7. 判据与反控.** `_r222/m6_final.py` **42 断言 / 0 FAIL**、`m7_newfacts.py` 23 / 0、`m8_inline_dec.py` 11 / 0、
`m9_interleave.py` 11 / 0、`m10_audit_recheck.py` 8 / 0、`m11_channel_layout.py` 14 / 0、`m12_topology.py` 14 / 0。
反控：step 表基址 +2 ⇒ **64/1424**；错表 `0x87b170` 当 dword ⇒ **2/1424**；nibble 反序 `n^7` ⇒ **0/1424**；
step 右移 1 ⇒ **2/1424**；stereo 去掉 `+2 B` 偏置 ⇒ 并集只剩 8 word（覆盖半帧）；`ch2` 专属字段在 copy1/copy2 出现 0 次。
`gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`。

**8. 跨家族.** card A `#581`（hy4 exec **35 回合 / 6.87′**，无超时）10 组与主会话一致，其中 T4（三段同构）口径偏离已如实记录；
审计 `#582`（deepseek audit **23 回合 / 21.9′**，`[OVERTIME: 21.9' vs 12.0']`）给 4 条口径修正，主会话逐条复算：
①`0x7c6000..0x7c7000` 内 `mov ax,word[esi]` 与 `lodsw` 皆 **0** 条（成立，卡面 T12 描述作废）；
②`0x7c62f5`/`0x7c63f5`/`0x7c6514` 复用 `word[ebx+0x1c]`/`[ebx+0x30]` 的高 4 位（成立）；
③`0x7c75cc` 7 字节 = `5a595b5f5ec9c3`（成立）；④直达尾声中 `eax` 未被置值（成立）；
⑤卡面 T3 终止地址 `0x7c635d` 切在 `0x7c635b mov eax,[ebx+0x14]`（3 B）中间（成立，主会话卡面笔误）。
自错 2 条 **0 条进结论**：E1 `m9` 把 `0x7c7b4c` 段截到 `0x7c7b58` 导致漏读 `mov edx,[ebp+0x18]`；
E2 `p1_r14.py` 的 W2 断言「原文无 CRLF」与实际（CR=1081 本就是 CRLF 计数）矛盾，属断言口径错，不影响写入结果。

**9. 仍未取得.** ①`0x7c6620` 是 ACM 帧内 8 B 记录的条件更新器（`imul dword[0x8759a4]` + `lea esi,[esi+eax*8]`），
记录字段 `[esi]`/`[esi+4]` bit0/bit1 语义未定；②`0x7c7371` 的 `[ebp+0x1c]`（`&[ebx+0x7d0]`）内部布局；
③块1 的 `0x7c6b58` 4 项对齐表（`0x7c67c3/0x7c67d8/0x7c67e8/0x7c67f8`）与块2 三张 4 项表是否同构；
④F23/F35 grade；⑤C7 三死分支、C11 十二 ID 接入方案。
"""
APP = APP.replace('\r\n', '\n')
b2, dst = bak(GOAL, 'GOAL')
ck('G2 GOAL 备份已独占创建', os.path.exists(dst), dst)
ck('G3 追加段无 CR', '\r' not in APP)
ck('G4 追加段无 tab', '\t' not in APP)
new = s + APP
nb = new.encode('utf-8')
ck('G5 GOAL 新 CR == 337', nb.count(b'\r') == 337, nb.count(b'\r'))
ck('G6 GOAL 字节净增 == 追加段长度', len(nb) - len(b2) == len(APP.encode('utf-8')),
   (len(b2), len(nb), len(APP.encode('utf-8'))))
ck('G7 GOAL 新末节 §1280', [l for l in new.split('\n') if l.startswith('## §')][-1].startswith('## §1280'))
if fails:
    print('[ABORT]', fails)
    raise SystemExit(1)
open(GOAL, 'wb').write(nb)
chk = open(GOAL, 'rb').read()
ck('G8 GOAL 回读一致', chk == nb, hashlib.sha256(chk).hexdigest()[:16])
print('[GOAL] %d -> %d B, CR=%d' % (len(b2), len(nb), chk.count(b'\r')))
