# -*- coding: utf-8 -*-
"""R222 p4：STATUS_BOARD 第 222 轮记录（全 LF，CR 保持 0，总行数 <= 300）。"""
import os, hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = ROOT + '/R17_LEAD_BASELINE'
BOARD = ROOT + '/lead/next_re_20261117_r14/STATUS_BOARD.md'
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


b = open(BOARD, 'rb').read()
ck('B0 BOARD CR=0 bytes=89920', b.count(b'\r') == 0 and len(b) == 89920, (b.count(b'\r'), len(b)))
lines = b.count(b'\n')
ck('B1 BOARD 行数 < 260（不触发归档）', lines < 260, lines)
s = b.decode('utf-8')
ck('B2 末轮 = 第 221 轮', [l for l in s.split('\n') if l.startswith('## 第 ')][-1].startswith('## 第 221 轮'))

APP = """
## 第 222 轮（2026-11-28）0x7c62ac 定性为内联 delta 解包器 + 三份副本按声道划分（ch1/ch2 基址差 0x14）+ 16 项索引表 + 两个分派器接受集差异

- **0x7c62ac = 内联 delta 解包器，不是编码器（R221 待办① 关闭）**：读入 `mov al, byte ptr [esi]`（1 B = 2 nibble），写出 `mov word ptr [edi], ax`（16 位）或 `xor ah,0x80` + `mov byte ptr [edi], ah`（8 位）。反控两条成立：全函数**无** `mov [esi],..`、**无**把 `[edi]` 读进累加器。全函数 **0 条** `0x879b30` 引用，delta 现算 `(s>>3) + [n&4]s + [n&2](s>>1) + [n&1](s>>2)` / `n&8` 取负，与表版解码器 `0x7c6808`、`0x7c7428` 的律 D 同一定义（**1424/1424**）。nibble 选择 `test dword ptr [ebx+0x10], 1` 的 bit0：置位复用 `mov ax,word[ebx+0x1c]` + `shr eax,4`（缓存高 4 位），清零读新字节取低 4 位；16 位模式样本数先 `shr eax,1`（`0x7c62ce cmp word[ebx+0x38],0x10`）。
- **三份展开副本按「声道」划分，不是按位宽**：`copy1 0x7c62ea..0x7c63e8`（78 条）、`copy2 0x7c63ea..0x7c6509`（88 条）、`copy3 0x7c6509..0x7c6609`（75 条）。copy1/copy2 只用 **ch1**（`+0x10/+0x14/+0x18/+0x1c/+0x1e/+0x20/+0x22`），copy3 只用 **ch2**（`+0x24/+0x28/+0x2c/+0x30/+0x32/+0x34/+0x36`），六对字段基址差恒 **0x14**，两套**互不相交**，只共享 `+0x38`（位宽）/`+0x3a`（声道数）。入口 `0x7c62df cmp word[ebx+0x3a],2` / `0x7c62e4 je 0x7c63ea`（6 B）：**声道 1 顺序落入 copy1 单遍、声道 2 跳 copy2**；copy2 尾部 `0x7c64f0 mov esi,[ebx]` / `0x7c64f2 mov edi,[ebx+4]` / `inc esi` / `inc edi`（16 位再 `0x7c6505 inc edi`）/ `jmp 0x7c6509` 重建指针进 copy3。输出步进 copy1 `edi+=2`/`inc`、copy2/copy3 `edi+=4`/`+=2` ⇒ 双声道隔字交错；三尾共收 `0x7c6609`（`mov eax,[ebp-4]` + 5 pop + leave + ret）。
- **0x8758d4「0 条字面引用」≠ 死数据**：解包器 `mov ax,word[ecx+0x8758c4]`（`0x7c639b`/`0x7c649f`/`0x7c65be`）里 `ecx = 2*nibble`（`0x7c6399 shl ecx,1`），nibble 15 读 `0x8758e2..0x8758e3`，落在 `0x8758d4..0x8758e3` 内。16 项有符号字实测 = `(-1,-1,-1,-1,2,4,6,8)` 重复两遍（`T16 == T8 + T8`），两处 16 B 逐字节相同 ⇒ **一张 16 项表**（低 3 位选幅度、bit3 取负），`0x8758d4` 是其第二个 8 项。R221 QX7「未被引用的重复常量」订正。
- **两个分派器接受集不同**：`0x7c6752`（块1）三条非 `(16,1)` 组合全跳 `0x7c69ad`（实测尾声 `pop/leave/ret`），只有 `(0x10,1)` 顺序落入 `0x7c67a4`；`0x7c7371`（块2）把 `(0x10,2)` 送 `0x7c7788`（stereo）、`(0x10,1)` 落 `0x7c73c3`（mono），`cx∈{8}` 与其他组合跳 `0x7c75cc` 且该路径 **`eax` 未被置值**（返回值为调用方残留）。`0x7c75cc` 7 字节 = `5a 59 5b 5f 5e c9 c3` 纯尾声。
- **0x7c7371 只有 2 个调用点（R221 待办「4 个」为误）**：`e8 rel32` 全 `.text` 扫唯一命中 `0x7c24a2` / `0x7c2557`，该地址作 dword 字面量全文件出现 **0** 次。两处都压 6 实参 + `add esp,0x18`；stdcall 逆序 `[+8]=esi`（源）、`[+0xc]=[ebx+0x78c]`/`[ebx+0x7a8]`（目标）、`[+0x10]=byte[ebx+0x3f]`、`[+0x14]=byte[ebx+0x3e]`、`[+0x18]=ebp`（静态不能证明语义）、`[+0x1c]=&[ebx+0x7d0]`。`byte[ebx+0x3e]`/`[ebx+0x3f]` 写点 `0x7c2a0d`/`0x7c2a29`/`0x7c2a32`。
- **stereo 两遍 word 下标互补（严格证明）**：两遍 store 字节偏移都是 `0,4,8,..,0x1c`，但遍二入口多 `add edi,2`（`0x7c7b54`；遍一与 mono 入口都无 edi 偏置）。word 下标：遍一 **0,2,..,14**、遍二 **1,3,..,15**，**并集恰 16 word = 32 B = 每块 16 个 16 位立体声样本，交集空**；反控去掉 +2 B 偏置后并集只剩 8 word。遍二另把源指针挪 `[ebp+0x18] >> 3`（`0x7c7b5a shr edx,3`）。
- **状态记录 6 B / stereo 12 B；两个初始化函数不对称**：mono `0x7c73c3` 与 stereo 遍一 `0x7c7788` 读 `dword[ebx]` + `word[ebx+4]`；遍二 `0x7c7b4c` 读 `dword[ebx+6]` + `word[ebx+0xa]`；回写 `0x7c75c1` / `0x7c7d59`。`0x7c6270` 清 8 字段（两套完整状态）并置两声道 step=7（`+0x20`/`+0x34`）；`0x7c6730` 只清 4 字段（两套 index + 预测器），不碰 step/count。
- **反控 6 条 / 断言 123 条**：step 表基址 +2 ⇒ **64/1424**；错表 `0x87b170` 当 dword ⇒ **2/1424**；nibble 反序 `n^7` ⇒ **0/1424**；step 右移 1 ⇒ **2/1424**；stereo 去 `+2 B` 偏置 ⇒ 并集 8 word；ch2 专属五字段在 copy1/copy2 出现 **0** 次。断言合计 **123 / 0 FAIL**（`m6_final` 42、`m7_newfacts` 23、`m8_inline_dec` 11、`m9_interleave` 11、`m10_audit_recheck` 8、`m11_channel_layout` 14、`m12_topology` 14）。
- **跨家族**：card A `#581`（hy4 exec **35 回合 / 6.87′**，无超时）10 组与主会话一致；审计 `#582`（deepseek audit **23 回合 / 21.9′**，`[OVERTIME: 21.9' vs 12.0']`）4 条口径由主会话逐条复算成立：`0x7c6000..0x7c7000` 内 `mov ax,word[esi]` 与 `lodsw` 皆 **0** 条（卡面 T12 描述作废）、`0x7c62f5`/`0x7c63f5`/`0x7c6514` 复用高 4 位、`0x7c75cc` 7 字节 `5a595b5f5ec9c3`、直达尾声 `eax` 未置值；另指卡面 T3 终止地址 `0x7c635d` 切在 `0x7c635b mov eax,[ebx+0x14]`（3 B）中间，属实。
- **自错 2 条（0 条进结论）**：E1 `m9_interleave.py` 把 `0x7c7b4c` 段截到 `0x7c7b58` 导致漏读 `mov edx,[ebp+0x18]`；E2 `p1_r14.py` 的 W2 断言「原文无 CRLF」与 CR=1081 口径矛盾，不影响写入结果。
- **收口**：R14 §2.230 CR **1081**（1957889→1965287 B）、GOAL §1280 CR **337**（5485245→5492231 B）、本段 QY CR **137**（1527799→1534826 B）、本段 CR **0**（258→{nlines} 行，**< 260 不触发归档**）。`gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`。
"""
APP = APP.replace('\r\n', '\n')
b2, dst = bak(BOARD, 'BOARD')
ck('B3 BOARD 备份已独占创建', os.path.exists(dst), dst)
ck('B4 追加段无 CR', '\r' not in APP)
newlines = 14
APP = APP.replace('{nlines}', str(lines + newlines))
new = s + APP
nb = new.encode('utf-8')
ck('B5 BOARD 新 CR == 0', nb.count(b'\r') == 0, nb.count(b'\r'))
ck('B6 BOARD 行数 <= 300', nb.count(b'\n') <= 300, nb.count(b'\n'))
ck('B7 末轮 = 第 222 轮', [l for l in new.split('\n') if l.startswith('## 第 ')][-1].startswith('## 第 222 轮'),
   [l for l in new.split('\n') if l.startswith('## 第 ')][-1][:30])
ck('B8 字节净增 == 追加段长度', len(nb) - len(b2) == len(APP.encode('utf-8')),
   (len(b2), len(nb), len(APP.encode('utf-8'))))
if fails:
    print('[ABORT]', fails)
    raise SystemExit(1)
open(BOARD, 'wb').write(nb)
chk = open(BOARD, 'rb').read()
ck('B9 BOARD 回读一致', chk == nb, hashlib.sha256(chk).hexdigest()[:16])
print('[BOARD] %d -> %d B, %d -> %d 行, CR=%d' % (len(b2), len(nb), lines, chk.count(b'\n'), chk.count(b'\r')))
