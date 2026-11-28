# -*- coding: utf-8 -*-
"""R222 p6：FACT_INDEX V603 -> V604，只在 F29.limitations 追加 R222 实测段。"""
import hashlib, os, json, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = ROOT + '/lead/next_re_20261117_r14'
OLD = TIER + '/R17_R131_FACTINDEX_V603/FACT_INDEX.tsv'
NEWD = TIER + '/R17_R131_FACTINDEX_V604'
NEW = NEWD + '/FACT_INDEX.tsv'
fails = []


def ck(n, c, d=''):
    if not c:
        fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))


raw = open(OLD, 'rb').read()
h = hashlib.sha256(raw).hexdigest()
ck('W1 旧 V603 296444 B / sha b8c12028', len(raw) == 296444 and h.startswith('b8c12028'), (len(raw), h[:16]))
ck('W2 旧 CR == 0', raw.count(b'\r') == 0)
txt = raw.decode('utf-8')
lines = txt.split('\n')
ck('W3 57 行 + 末段空', len(lines) == 58 and lines[-1] == '', len(lines))
rows = [l.split('\t') for l in lines[:57]]
ck('W4 每行 5 列', all(len(r) == 5 for r in rows))
f29 = [r for r in rows if r[0] == 'F29'][0]
L0 = len(f29[4].encode())
ck('W5 F29 lim > 66000 B', L0 > 66000, L0)

APP = ('**【R222 实测·ADPCM 解包器 0x7c62ac 定性（内联 delta + 双声道两遍）+ 16 项索引表 + 两个分派器接受集差异；statement 与 grade 均不改】** '
'R222 用 `_r222/m6_final.py`（**42 断言 / 0 FAIL**）、`m7_newfacts.py`（23/0）、`m8_inline_dec.py`（11/0）、'
'`m9_interleave.py`（11/0）、`m10_audit_recheck.py`（8/0）、`m11_channel_layout.py`（14/0）、`m12_topology.py`（14/0），'
'合计 **123 断言 / 0 FAIL**，在现盘 `ra2bench/gamemd.exe`（sha256 `73201cc0…f3fcf67476`）上重算：'
'① **`0x7c62ac` 是内联 delta 解包器，不是编码器**（R221 待办① 关闭）：读入 `mov al, byte ptr [esi]`（1 B = 2 nibble），'
'写出 `mov word ptr [edi], ax`（16 位）或 `xor ah,0x80` + `mov byte ptr [edi], ah`（8 位）；反控两条成立 —— 全函数**既无** `mov [esi],..` '
'**也无**把 `[edi]` 读进累加器；全函数 **0 条** `0x879b30` 引用，delta 现算 = `(s>>3) + [n&4]s + [n&2](s>>1) + [n&1](s>>2)`、`n&8` 取负，'
'与表版解码器 `0x7c6808` / `0x7c7428` 的律 D **同一定义**（C1 **1424/1424**，且 `n&8` 与 `n>=8` 在 n∈0..15 上等价）；'
'nibble 由 `test dword ptr [ebx+0x10], 1` 的 bit0 选择：置位复用 `mov ax,word[ebx+0x1c]` + `shr eax,4`（缓存字高 4 位），清零读新字节取低 4 位，'
'两路末 `and eax,0xf` 截到 0..15；16 位模式样本数先 `shr eax,1`（`0x7c62ce cmp word[ebx+0x38],0x10` / `0x7c62d5 shr eax,1`）。'
'② **三份展开副本按「声道」划分，不是按位宽**：`copy1 0x7c62ea..0x7c63e8`（78 条）、`copy2 0x7c63ea..0x7c6509`（88 条）、'
'`copy3 0x7c6509..0x7c6609`（75 条）；copy1/copy2 只用 **ch1**（`+0x10/+0x14/+0x18/+0x1c/+0x1e/+0x20/+0x22`），'
'copy3 只用 **ch2**（`+0x24/+0x28/+0x2c/+0x30/+0x32/+0x34/+0x36`），六对字段基址差恒 **0x14**，两套**互不相交**，'
'只共享 `+0x38`（位宽）与 `+0x3a`（声道数）。入口 `0x7c62df cmp word[ebx+0x3a],2` / `0x7c62e4 je 0x7c63ea`（6 B，不成立顺序落入 copy1）：'
'**声道 1 走 copy1 单遍、声道 2 跳 copy2**；copy2 尾部 `0x7c64f0 mov esi,[ebx]` / `0x7c64f2 mov edi,[ebx+4]` / `inc esi` / `inc edi`'
'（16 位再 `0x7c6505 inc edi`）/ `jmp 0x7c6509` 重建指针进 copy3。输出步进 copy1 `edi+=2`/`inc`、copy2/copy3 `edi+=4`/`+=2` ⇒ 双声道**隔字交错**；'
'三条尾部共收 `0x7c6609`（`mov eax,[ebp-4]` + 5 pop + leave + ret）。'
'③ **`0x8758d4` 的「0 条字面引用」≠ 死数据**：解包器 `mov ax, word[ecx + 0x8758c4]`（`0x7c639b`/`0x7c649f`/`0x7c65be`）里 '
'`ecx = 2*nibble`（`0x7c6399 shl ecx,1`），nibble 15 读 `0x8758e2..0x8758e3`，落在 `0x8758d4..0x8758e3` 内；'
'16 项有符号字实测 = `(-1,-1,-1,-1,2,4,6,8)` 重复两遍（`T16 == T8 + T8`），两处 16 B 逐字节相同 ⇒ 这是**一张 16 项表**'
'（低 3 位选幅度调整、bit3 是负号），`0x8758d4` 是它的第二个 8 项。R221 QX7 记的「未被引用的重复常量」据此订正。'
'④ **两个分派器接受集不同**：`0x7c6752`（块1）与 `0x7c7371`（块2）都做 `word[+0x38]`/`word[+0x3a]` 的 2x2 比较，'
'但 `0x7c6752` 的三条非 `(16,1)` 组合全部跳 `0x7c69ad`（实测 `pop/leave/ret` 尾声），只有 `(0x10,1)` 顺序落入 `0x7c67a4`；'
'`0x7c7371` 把 `(0x10,2)` 送 `0x7c7788`（stereo 入口）、`(0x10,1)` 落 `0x7c73c3`（mono 入口），`cx∈{8}` 与其他组合跳 `0x7c75cc` '
'且该路径 **`eax` 未被置值**（返回值是调用方残留）。`0x7c75cc` 7 字节 = `5a595b5f5ec9c3` 纯尾声。'
'⑤ **`0x7c7371` 只有 2 个调用点**（R221 待办写「4 个」为误）：全 `.text` `e8 rel32` 扫唯一命中 `0x7c24a2` 与 `0x7c2557`；'
'该地址作 dword 字面量在全文件出现 **0** 次。两处都压 6 实参 + `add esp,0x18`，stdcall 逆序：'
'`[+8]=esi`（源）、`[+0xc]=[ebx+0x78c]` 或 `[ebx+0x7a8]`（目标）、`[+0x10]=byte[ebx+0x3f]`、`[+0x14]=byte[ebx+0x3e]`、'
'`[+0x18]=ebp`（寄存器值，静态不能证明语义）、`[+0x1c]=&[ebx+0x7d0]`（状态块）；`byte[ebx+0x3e]`/`byte[ebx+0x3f]` 写点 '
'`0x7c2a0d`/`0x7c2a29`/`0x7c2a32`，源为 `word[ebx+0x104]`/`byte[ebx+0x106]`/`byte[ebx+0x107]`（或 `+0x100/+0x102/+0x103` 另一分支），'
'即 ACM 流格式块字段。'
'⑥ **stereo 两遍 word 下标互补（严格证明）**：两遍 store **字节偏移都是** `0,4,8,..,0x1c`，但遍二入口多 `add edi,2`（`0x7c7b54`；'
'遍一 `0x7c7788..0x7c7795` 与 mono `0x7c73c3..0x7c73d0` 都无 edi 偏置）；换算成 word 下标后遍一占 **0,2,..,14**、遍二占 **1,3,..,15**，'
'**并集恰 16 word = 32 B = 每块 16 个 16 位立体声样本，交集为空**；反控去掉 `+2 B` 偏置后并集只剩 8 word（覆盖半帧）。'
'遍二另把源指针挪 `[ebp+0x18] >> 3`（`0x7c7b57 mov edx,[ebp+0x18]` / `0x7c7b5a shr edx,3` / `0x7c7b5d add esi,edx`）。'
'⑦ **状态记录 6 B（int32 predictor + uint16 step）/ stereo 12 B**：mono `0x7c73c3` 与 stereo 遍一 `0x7c7788` 读 '
'`dword[ebx]` + `word[ebx+4]`；遍二 `0x7c7b4c` 读 `dword[ebx+6]` + `word[ebx+0xa]`；回写 `0x7c75c1`（`[ebx]`/`[ebx+4]`）与 '
'`0x7c7d59`（`[ebx+6]`/`[ebx+0xa]`）。两个初始化函数不对称：`0x7c6270` 清 8 字段（两套完整状态）并置两声道 step=7'
'（`+0x20`/`+0x34`）；`0x7c6730` 只清 4 字段（两套 index + 预测器），不碰 step/count —— 两条路径 step 终值都是 7、处置方式不同。'
'⑧ **反控 6 条**：step 表基址 +2 ⇒ **64/1424**；错表 `0x87b170` 当 dword ⇒ **2/1424**；nibble 反序 `n^7` ⇒ **0/1424**；'
'step 右移 1 ⇒ **2/1424**；stereo 去 `+2 B` 偏置 ⇒ 并集只剩 8 word；ch2 专属五字段在 copy1/copy2 出现 **0** 次。'
'⑨ **跨家族 / 自错**：card A `#581`（hy4 exec **35 回合 / 6.87′**，无超时）10 组与主会话数值一致，T4「三段同构」口径偏离已如实记录；'
'审计 `#582`（deepseek audit **23 回合 / 21.9′**，`[OVERTIME: 21.9\' vs 12.0\']`）4 条口径由主会话逐条复算**全部成立并采纳**：'
'P1 `0x7c6000..0x7c7000` 内 `mov ax,word[esi]` 与 `lodsw` 皆 **0** 条（卡面 T12 描述作废）；'
'P2 `0x7c62f5`/`0x7c63f5`/`0x7c6514` 复用 `word[ebx+0x1c]`/`[ebx+0x30]` 的高 4 位（4-bit 打包，不是 16 位样本）；'
'P3 `0x7c75cc` 7 字节 `5a595b5f5ec9c3`；P4 直达尾声中 `eax` 未被置值；另指卡面 T3 终止地址 `0x7c635d` 切在 '
'`0x7c635b mov eax,[ebx+0x14]`（3 B）中间，属实（主会话卡面笔误）。'
'自错 2 条 **0 条进结论**：E1 `m9_interleave.py` 把 `0x7c7b4c` 段截到 `0x7c7b58` 导致漏读 `mov edx,[ebp+0x18]`；'
'E2 `p1_r14.py` 的 W2 断言「原文无 CRLF」与 CR=1081 口径矛盾（不影响写入结果）。'
'**边界**：本条不改 F29 的 statement 与 grade；`coverage.tsv` / `function_atlas.tsv` 仍不可读；'
'`0x7c6620`（ACM 帧内 8 B 记录条件更新器）、`0x7c7371` 的 `[ebp+0x1c]` 状态块内部布局、块1 `0x7c6b58` 4 项对齐表与块2 三张 4 项表是否同构仍未取得。')

ck('W6 无 tab', '\t' not in APP)
ck('W7 无 CR/换行', '\r' not in APP and '\n' not in APP)
ck('W8 无双引号', '"' not in APP)
ck('W9 以句号结尾且 >4000 B', APP.endswith('。') and len(APP.encode()) > 4000, len(APP.encode()))
newlim = f29[4] + APP
ck('W10 lim 只增不减', len(newlim.encode()) > L0, len(newlim.encode()))
f29[4] = newlim
newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode('utf-8')
ck('W11 新字节 = 旧 + 追加段', len(nb) == len(raw) + len(APP.encode()), (len(nb), len(raw) + len(APP.encode())))
ck('W12 新 CR == 0', nb.count(b'\r') == 0)
ck('W13 除 F29 外 56 行逐字节不变',
   all(lines[i] == '\t'.join(rows[i]) for i in range(57) if rows[i][0] != 'F29'))
if fails:
    print('[ABORT]', fails)
    raise SystemExit(1)
os.makedirs(NEWD, exist_ok=True)
assert not os.path.exists(NEW)
open(NEW, 'wb').write(nb)
chk = open(NEW, 'rb').read()
assert chk == nb
print('[写入] %s bytes %d -> %d sha %s -> %s' %
      (NEW, len(raw), len(chk), h[:16], hashlib.sha256(chk).hexdigest()[:16]))
json.dump(dict(old_sha=h, new_sha=hashlib.sha256(chk).hexdigest(), old_bytes=len(raw), new_bytes=len(chk)),
          open(ROOT + '/_r222/p6.json', 'w'), indent=1)
