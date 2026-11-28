# -*- coding: utf-8 -*-
"""R222 四件套写入：R14_COMMON §2.230 / GOAL §1280 / LEAD_LOCK QY / STATUS_BOARD 第 222 轮。

写入纪律：
  备份先独占创建（wx），断言旧 sha256 与 CR 不变量，一次性写入，回读校验。
  R14_COMMON / GOAL / LEAD_LOCK / STATUS_BOARD 四份各自独立备份。
"""
import os, hashlib, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = ROOT + '/R17_LEAD_BASELINE'
TIER = ROOT + '/lead/next_re_20261117_r14'
RC = TIER + '/R14_COMMON.md'
GOAL = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'
LOCK = ROOT + '/lead/LEAD_LOCK'
BOARD = TIER + '/STATUS_BOARD.md'
ARCH = TIER + '/BOARD_ARCHIVE.md'

EXPECT = {
    RC:    (1081, 1957889),
    GOAL:  (337, 5485245),
    LOCK:  (137, 1527799),
    BOARD: (0, 89920),
    ARCH:  (2952, 1535894),
}
fails = []


def ck(n, c, d=''):
    if not c:
        fails.append(n)
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''))


def bak(path, tag):
    b = open(path, 'rb').read()
    stem = os.path.basename(path)
    base = '%s/%s.before_r222_%s' % (BASE, stem, tag)
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
    raise SystemExit('bak exhausted: ' + path)


print('=== 0 写前不变量 ===')
pre = {}
for p, (cr, nbytes) in EXPECT.items():
    b = open(p, 'rb').read()
    pre[p] = (hashlib.sha256(b).hexdigest(), len(b), b.count(b'\r'))
    ck('I0 %s CR=%d bytes=%d' % (os.path.basename(p), cr, nbytes),
       b.count(b'\r') == cr and len(b) == nbytes, pre[p])

rc_sections = [l for l in open(RC, encoding='utf-8').read().split('\n') if l.startswith('## 2.')]
goal_sections = [l for l in open(GOAL, encoding='utf-8').read().split('\n') if l.startswith('## §')]
lock_codes = __import__('re').findall(r'^\*\*([A-Z]{2})\d*\.', open(LOCK, encoding='utf-8').read(), __import__('re').M)
board_lines = open(BOARD, 'rb').read().count(b'\n')
ck('I1 R14 末节 = 2.229', rc_sections[-1].startswith('## 2.229'), rc_sections[-1][:40])
ck('I2 GOAL 末节 = §1279', goal_sections[-1].startswith('## §1279'), goal_sections[-1][:40])
ck('I3 LEAD_LOCK 末段 = QX', lock_codes[-1] == 'QX', lock_codes[-3:])
ck('I4 STATUS_BOARD 行数 < 260（不触发归档）', board_lines < 260, board_lines)

if fails:
    print('[ABORT 写前]', fails)
    raise SystemExit(1)

# ---------------------------------------------------------------- R14_COMMON
R14_APP = """
## 2.230 R222（2026-11-28）· ADPCM 内联式解码器定性 + 索引表 16 项显式复制 + 两个分派器接受集差异 + 三份展开副本指针步进

**1. 0x7c62ac 是内联 delta 解码器，不是编码器（R221 遗留待办① 关闭）.** 判据五条全部实测（`_r222/m8_inline_dec.py`，11 断言 / 0 FAIL）：
读入是 `mov al, byte ptr [esi]`（1 B 含 2 nibble），写出是 `mov word ptr [edi], ax`（16 位路径）或
`xor ah,0x80 / mov byte ptr [edi], ah`（8 位路径）；方向是「解包 → 样本」，反控成立（全函数既无 `mov [esi],..`
也无把 `[edi]` 读进累加器）。全函数 **0 条** `0x879b30` 引用，delta 由 `test eax,4` / `test eax,2` / `test eax,1`
+ `shr edx,3` + `test eax,8` 内联算出，其定义与表版解码器 `0x7c6808` / `0x7c7428` 的律 D 完全一致
（m6 C1 已证 1424/1424）。样本计数在 16 位模式下先 `shr eax,1`（`0x7c62ce cmp word[ebx+0x38],0x10` /
`0x7c62d5 shr eax,1`），8 位不除。nibble 由 `test dword ptr [ebx+0x10], 1` 的 bit0 在
「取已缓存字的**高**半字节」与「读新字节、取**低**半字节」之间切换，每次处理完再 `and eax,0xf` 截到 0..15。

**2. 0x8758d4「0 条字面引用」≠ 死数据：它是 16 项索引表的第二半（R221 QX7 补正）.** 编码/解码共用的
`mov ax, word ptr [ecx + 0x8758c4]` 里 `ecx = 2 * nibble`（`0x7c6399 shl ecx,1`），nibble 上界 15 时
地址 = `0x8758c4 + 30 = 0x8758e2`，后半段落进 `0x8758d4..0x8758e3`。实测 16 项有符号字 =
`(-1,-1,-1,-1,2,4,6,8)` 重复两遍（`T16 == T8 + T8`），且两处 16 B 逐字节相同。⇒ 这是一张 **16 项显式复制表**，
按 `n&7` 语义等价（反控：`T16[n] == T8[n&7]` 全 16 真），R221 记的「重复常量」应改为「16 项表的第二半，
被 nibble 8..15 读到」。

**3. 0x7c6752 与 0x7c7371 是两个接受集不同的分派器.** 两者都读 `word[+0x38]`（位宽）/`word[+0x3a]`（声道数）
并做同一套 2x2 比较，但落点不同：`0x7c6752` 的三条非 `(16,1)` 组合全部跳 `0x7c69ad`（尾声，
`pop/leave/ret`，实测该地址不是解码分支），只有 `(0x10,1)` 顺序落入 `0x7c67a4` 主体；
`0x7c7371` 则把 `(0x10,2)` 送到 `0x7c7788`（stereo 入口）。⇒ 块1 侧只支持 16 位单声道（块1 解码器
`0x7c6808` 只 1 份展开、`add edi,0x10`），块2 侧支持单声道 3 份展开 + 双声道 2 份展开。R221 记的
「0x7c7371 是唯一分派器」不成立。

**4. 0x7c7371 只有 2 个调用点（R221 待办写「4 个调用点」，实测 2）.** 全 `.text` 用 `e8 rel32` 扫，
唯一命中 `0x7c24a2` 与 `0x7c2557`；`0x7c7371` 作为 dword 字面量在全文件出现 **0** 次（无函数指针表引用）。
两个调用点都 `push` 6 个实参并 `add esp,0x18`；按 stdcall 逆序：
`[ebp+8]=esi`（源缓冲）、`[ebp+0xc]=[ebx+0x78c]` 或 `[ebx+0x7a8]`（目标缓冲）、`[ebp+0x10]=byte[ebx+0x3f]`、
`[ebp+0x14]=byte[ebx+0x3e]`、`[ebp+0x18]=ebp`（帧字节数）、`[ebp+0x1c]=&[ebx+0x7d0]`（状态块）。
`byte[ebx+0x3e]` / `byte[ebx+0x3f]` 的写点在 `0x7c2a0d/0x7c2a29/0x7c2a32`，取自
`word[ebx+0x104]/byte[ebx+0x106]/byte[ebx+0x107]`（或 `+0x100/+0x102/+0x103` 另一分支），
即 ACM 流格式块的声道/位宽字段。

**5. 解包器 0x7c62ac 的三份展开副本按「声道」划分，不是按位宽.** `copy1 0x7c62ea..0x7c63e8`（78 条）、
`copy2 0x7c63ea..0x7c6509`（88 条）、`copy3 0x7c6509..0x7c6609`（75 条）。字段实测（`_r222/m11_channel_layout.py`，14 断言 / 0 FAIL）：
copy1/copy2 只用 **ch1** 状态（`+0x10` 计数 / `+0x14` 预测器 / `+0x18` delta / `+0x1c` nibble 缓存 / `+0x1e` 当前 nibble /
`+0x20` step / `+0x22` index），copy3 只用 **ch2** 状态（`+0x24/+0x28/+0x2c/+0x30/+0x32/+0x34/+0x36`），
六对字段基址差恒为 **0x14**，两套状态**互不相交**（只共享 `+0x38` 位宽格式字段）。入口分派：
`0x7c62df cmp word[ebx+0x3a],2` / `0x7c62e4 je 0x7c63ea`（6 B，不成立顺序落入 copy1 `0x7c62ea`）⇒
**声道数 1 走 copy1 单遍、声道数 2 走 copy2→copy3 两遍**。copy2 尾部 `0x7c64f0 mov esi,[ebx]` / `0x7c64f2 mov edi,[ebx+4]` /
`0x7c64f5 inc esi` / `0x7c64f6 inc edi`（16 位再 `0x7c6505 inc edi`）/ `0x7c6501 jmp 0x7c6509` 重建指针进 copy3，
故 **ch2 右移 1 个样本单元**（8 位偏 1 B、16 位偏 2 B）。输出步进：copy1 `edi += 2`（16 位）/ `inc edi`（8 位）；
copy2/copy3 `edi += 4`（16 位）/ `+= 2`（8 位）⇒ 双声道写入**隔字交错**，单声道连续。三条尾部都收在 `0x7c6609`
（`mov eax,[ebp-4]` + 五个 `pop` + `leave` + `ret`）共享返回块。

**6. 两个初始化函数的不对称与声道布局自洽.** `0x7c6270` 清 8 个字段（`+0x22/+0x20/+0x14/+0x10/+0x36/+0x34/+0x28/+0x24`）
并置两声道 step=7（`+0x20`、`+0x34`），即**两套完整状态**；`0x7c6730` 只清 4 个（`+0x22/+0x14` 与 `+0x36/+0x28`），
即**两套的 index + 预测器**，不碰 step/count。⇒ 块1 路径（单声道）的 step 初值由主循环首次读 `0x8758e4` 表首项 7 得到，
块2 路径由 init 直接置；两者对 step 的处置方式不同但终值一致（都是 7）。

**7. 状态记录是 6 B（int32 predictor + uint16 step），stereo 12 B.** mono 入口 `0x7c73c3` 读
`eax = dword[ebx]`、`dx = word[ebx+4]`；stereo 遍一 `0x7c7788` 读同一对；stereo 遍二 `0x7c7b4c` 读
`dword[ebx+6]`、`word[ebx+0xa]`（第二声道在 +6）；回写分别在 `0x7c75c1`（`[ebx]`/`[ebx+4]`）与
`0x7c7d59`（`[ebx+6]`/`[ebx+0xa]`）。两遍各处理一个声道，输出 2 B 交错：两遍的 store **字节偏移都是**
`0,4,8,..,0x1c`，但遍二入口多一条 `add edi,2`（`0x7c7b54`；遍一入口 `0x7c7788..0x7c7795` 与 mono 入口
`0x7c73c3..0x7c73d0` 都没有 edi 偏置），换算成 word 下标后遍一占 **0,2,..,14**、遍二占 **1,3,..,15**，
**并集恰为 16 个 word = 32 B = 每块 16 个 16 位立体声样本，交集为空**（`_r222/m9_interleave.py` 11 断言 / 0 FAIL，
反控：去掉 +2 B 偏置后并集只剩 8 word、覆盖半帧）。遍二另把源指针挪 `[ebp+0x18] >> 3`
（`0x7c7b57 mov edx,[ebp+0x18]` / `0x7c7b5a shr edx,3` / `0x7c7b5d add esi,edx`）。

**8. 判据与反控.** `_r222/m6_final.py` **42 断言 / 0 FAIL**（`_r222/m6_out.txt`），`_r222/m7_newfacts.py` 23 断言 / 0 FAIL，
`_r222/m8_inline_dec.py` 11 断言 / 0 FAIL、`_r222/m9_interleave.py` 11 断言 / 0 FAIL、`_r222/m11_channel_layout.py` 14 断言 / 0 FAIL、`_r222/m12_topology.py` 14 断言 / 0 FAIL、`_r222/m10_audit_recheck.py` 8 断言 / 0 FAIL。反控四条：step 表基址 +2 ⇒ 命中 **64/1424**；错表 `0x87b170` 当 dword ⇒ **2/1424**；
nibble 反序（`n^7`）⇒ **0/1424**；step 右移 1 ⇒ **2/1424**。`gamemd.exe` sha256 `73201cc0…f3fcf67476`。

### 十一 · 仍未取得

①`0x7c6620` 是 ACM 帧内 8 B 记录的条件更新器（`imul [0x8759a4]` + `lea esi,[esi+eax*8]`），其记录字段
（`[esi]`/`[esi+4]` bit0/bit1）语义未定；②`0x7c7371` 的 `[ebp+0x1c]`（`&[ebx+0x7d0]`）内部布局未解；
③块1 的 `0x7c6b58` 4 项对齐表（`0x7c67c3/0x7c67d8/0x7c67e8/0x7c67f8`）与块2 的 3 张 4 项表是否同构未验；
④F23/F35 grade 裁定；⑤C7 三死分支自然真实行、C11 十二 ID 真判据接入方案。
"""
R14_APP = R14_APP.replace('\r\n', '\n')
b, dst = bak(RC, 'R14')
ck('W1 R14 备份已独占创建', os.path.exists(dst), dst)
s = b.decode('utf-8')
ck('W2 R14 原文无 \\r\\n', '\r\n' not in s)
ck('W3 R14 追加段无 CR', '\r' not in R14_APP)
ck('W4 R14 追加段无 tab', '\t' not in R14_APP)
new = s + R14_APP
nb = new.encode('utf-8')
ck('W5 R14 新 CR == 1081', nb.count(b'\r') == 1081, nb.count(b'\r'))
ck('W6 R14 字节净增 == 追加段长度', len(nb) - len(b) == len(R14_APP.encode('utf-8')),
   (len(b), len(nb), len(R14_APP.encode('utf-8'))))
ck('W7 R14 新末节 = 2.230', [l for l in new.split('\n') if l.startswith('## 2.')][-1].startswith('## 2.230'))
open(RC, 'wb').write(nb)
back = open(RC, 'rb').read()
ck('W8 R14 回读一致', back == nb, hashlib.sha256(back).hexdigest()[:16])
print('[R14] %d -> %d B, CR=%d' % (len(b), len(nb), back.count(b'\r')))
