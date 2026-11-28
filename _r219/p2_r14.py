# -*- coding: utf-8 -*-
"""R219 p2：四件套追加（wx 独占备份 -> 断言旧 sha/CR -> 一次性写 -> 回读校验）。

R14_COMMON §2.227 / GOAL §1277 / LEAD_LOCK QM / STATUS_BOARD 第 219 轮。
注意：STATUS_BOARD 当前 220 行 (<260)，本轮不触发归档。
"""
import os, hashlib, json
ROOT = '/home/t628/projects/ra2-campaign-forge'
T = ROOT + '/lead/next_re_20261117_r14'
BASE = ROOT + '/R17_LEAD_BASELINE'
SPEC = {
    'R14_COMMON': dict(path=T + '/R14_COMMON.md', cr=1081),
    'GOAL': dict(path=ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md', cr=337),
    'LOCK': dict(path=ROOT + '/lead/LEAD_LOCK', cr=137),
    'BOARD': dict(path=T + '/STATUS_BOARD.md', cr=0),
    'ARCH': dict(path=T + '/BOARD_ARCHIVE.md', cr=2952),
}

def bak(path, tag):
    b = open(path, 'rb').read()
    base = '%s/%s.before_r219_%s' % (BASE, os.path.basename(path), tag)
    for i in range(10):
        dst = base + (('_%d' % i) if i else '') + '_20261128.bak'
        if os.path.exists(dst):
            if open(dst, 'rb').read() == b: return b
            continue
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted ' + tag)

pre = {}
for k, v in SPEC.items():
    b = open(v['path'], 'rb').read()
    assert b.count(b'\r') == v['cr'], '%s CR %d != %d' % (k, b.count(b'\r'), v['cr'])
    pre[k] = dict(cr=v['cr'], bytes=len(b), sha=hashlib.sha256(b).hexdigest())
    print('[前置OK] %-10s cr=%-5d bytes=%-8d sha=%s' % (k, v['cr'], len(b), hashlib.sha256(b).hexdigest()[:16]))
print('[前置] STATUS_BOARD 行数 = %d' % pre['BOARD']['bytes'])

R14 = """
## 2.227 R219（2026-11-28）· 6 处超域位点定性（函数指针字段 / 12 B 派发表）+ 槽号口径 914/931 复证 + 4 个「幻影」= 162 记录常量表撞 COL + 0x4a1ca0 是 CRC-32

### 一 · 🔴 R218 遗留的 6 处「超 344 槽域」位点全部定性，且都不是虚表槽
| 位点 | 指令 | 定性 |
|---|---|---|
| `0x7bea07` | `call dword ptr [esi + 0x784]` | 对象内函数指针字段 |
| `0x7bea0f` | `call dword ptr [esi + 0x788]` | 同上 |
| `0x7c2f17` / `0x7c301c` | `call dword ptr [esi + 0x77c]` | 同上 |
| `0x7c37c7` | `call dword ptr [esi + 0x780]` | 同上 |
| `0x7cde2b` | `call dword ptr [esi + 0x87c488]` | 12 B 步长静态派发表 |

- 全 `.text` 对 `+0x77c` / `+0x780` / `+0x784` 三个 offset 的引用共 **31** 条；
  其中「`mov dword ptr [reg+off], imm32` 且 imm32 落 `.text`」的**写入端 12** 条，12/12 目标均在 `.text`。
- 同一 offset 还被 `fmul qword ptr [reg+0x780]` **2** 次（`0x4b3da6` / `0x6a33f5`）与 `fstp qword ptr [reg+0x780]` **1** 次（`0x66f2a9`）当 double 使用
  ⇒ 该 offset 是数据字段，`call [reg+off]` 是**读字段里的函数指针**，与虚表槽无关。
- 第 6 处：`esi` 由 `0x7cddac lea esi,[edi+edi*2]` + `0x7cddb6 shl esi,2` 得 **esi = edi*12**；
  `0x87c488` 起是步长 12 B 的派发表（首项 `0x87c488: 007ce046 007f97d0 0087c370`，`dw(0x87c488)=0x7ce046` 落 `.text` 且 `0x7ce046` 是 `xor eax,eax / ret` 桩）；
  上界由 `0x7cdd08 cmp edi, 0x87c4c0` 给出（`(0x87c4c0−0x87c488)/12 = 4` 项余 8 B）。
- **反控**：全库 1218 张虚表**无任何一张槽数 ≥480**（最大 344，`0x7f5c70`）⇒ `s=479/480/481/482` 在语义上不可能对应任何虚表槽。

### 二 · 🔴 「disp//4 = 虚表槽序号」这一口径本身成立（不需要订正 R218 的 931/91/925）
对 931 个 `s≥256` 位点做前驱数据流分类（回看窗口 24 条指令，判据：`mov <base>, dword ptr [<gpr>+0]` = 读 vftable）：
- 窗口 24：**A_vtable 914 / C_neither 17**（98.2% 为 vftable 消费）；
- 余 17 处用 200 条窗口溯源：`from_vtable_load 6 / from_indirect_ld 2 / from_mem_other 1 / from_pop 2` + 上述 6 处字段/派发表，
  **没有一处**落在「虚表槽但前驱缺失」的情形。
- 正控 `0x414471`（`call dword ptr [edx+0x544]`，前驱 `0x414466 mov edx, dword ptr [esi]`）稳定判为 A 类。
- **逐数复现**：逐字节 resync sweep **1,394,186** 条（末 `0x7e0fff`）；接受集 **18,935**（esp 基址 **9**、负 disp **2**、带索引排除 **391**）；
  `s≥256` **931** / distinct **91**；UnitClass 域（`256≤s<344`）**925**；top s `288:309 / 289:85 / 337:73 / 342:58 / 258:44`。
  ⇒ 与 R218 逐数一致；R218 记的 1,394,120 / 0x7e0ffd 与本次 1,394,186 / 0x7e0fff 的差 66 来自是否把「非法跳字节」计为 `.byte` 指令。

### 三 · 🔴 「4 个幻影虚表」的真实载体：162 记录 × 16 B 常量表的**双份逐字节副本**
- `0x876ff4..0x877a03`（2576 B）与 `0x87b170..0x87bb7f`（2576 B）**逐字节相同**，sha256 同为 `7b724b01…`。
- 记录形态 `f0 f1 f2 f3`，**恒有 `f3 − f2 = 0x00800080`**（162/162 记录成立）。
  反控：把记录起点移位 4 / 8 / 12 B ⇒ 命中 **0 / 0 / 0**；改用 delta `0x00800000` / `0x00800100` ⇒ 在整段 `.data` 窗口命中 **0 / 0**。
- 表内是 16 位字递增序列：`0x876ff4 row = 0000 0000 0000 0000 0040 0080 00c0 0100`。
  **`0x00800040` 只是相邻 16 位字 `0x0040` / `0x0080` 被读成 dword 的结果**，数值上恰等于 `DropPodLocomotionClass` 的 COL 地址 `0x800040`。
  这是**数值常量与 COL 地址撞车**，不是虚表记录。
- 反控：表区间被 `.text` 以 dword 引用 **24** 次，**全部指向表首 `0x87b170`**（形如 `0x7c742f mov dx, word ptr [edx+0x87b170]`），即代码按**字**访问；
  无任何 `[reg+off]` 形式的槽消费。
- **最终计数不变**：`dw(V-4) in COL` 且 `dw(V)` 不落 `.text` 的全库候选仍恰 **4** 个（`0x877000`/`0x877010`/`0x87b17c`/`0x87b18c`，全在 `.data`，`dw(V)=0x010000c0`）；
  把整段 `.data 0x870000..0x880000` 排除后真表计数仍 **1214**（delta 0）。
  ⇒ 「1214 真表」结论保持，但**成因描述**由「16 B 形如 `c0000001 …` 的幻影记录」订正为「162 记录常量表的 f2 字段撞 COL 地址」。

### 四 · 🔴 `0x4a1ca0` 不是「环缓冲容量 4」，是 **CRC-32 累加器**
- `cmp eax,4` / `cmp eax,edi` 判的是**已缓冲字节数凑满 4 字节**，不是队列容量。
- 凑满后：`not eax` → 逐字节 `xor idx`（`0x4a1d06`）→ `mov ebx, dword ptr [ebp*4 + 0x81f7b4]`（`0x4a1d0b`）→ `xor eax,ebx` → `not eax`（`0x4a1d18`）→ 存回 `[ecx]` 并把 `[ecx+4]` 清零。
- `0x81f7b4` 处 256 项 dword 表与 CRC-32 反射多项式 `0xEDB88320` 现场生成表**逐项 256/256 相同**
  （反控：CRC-32C `0x82F63B78` 仅 **1/256**、Koopman `0xEB31D82E` 仅 1/256）。
- 字段语义：`+0 = crc`、`+4 = 已缓冲字节数(0..3)`、`+8..+0xb = 4 字节缓冲`、`+0xc = 计数影子`。
- **行为等价性**：按该语义实现 `flush4(prev, buf4)` 与 `zlib.crc32(buf, prev)`，在 3 组 prev × 5 组 buf4 上 **15/15 完全一致**；12 B 链式输入亦一致。

### 五 · 🟡 跨家族与自错
- card A（#569 hy4 exec，9 回合 / 1.88′ vs 8，无 OVERTIME）：succeeded，67 个 diff 目标归类 **other 61 / push_ebp 2 / jmp_rel 4**，
  反查命中：引用 1 次 **53**、4 次 **14**（宿主恒为 Aircraft/Foot/Infantry/Unit 四表）；与 R218 粗分布（other 58 / mov_eax_arg 4 / push_ebp 1）**不一致**，
  差异源于 R218 未留粗判据代码，**无法复现即不采用**（本段采用 card A 的逐字节实测值，并注明 R218 粗分布作废）。
- card B（#570 hy4 exec，14 回合 / 7.22′ vs 8，无 OVERTIME）：succeeded。**其首次运行口径错误**（未设 `skipdata`，只解 1,150,117 条 ⇒ 报 15472 / 744 / 739），
  经主会话指出后自我更正为 **18,935 / 931 / 91 / 925 / 函数 311 / unresolved 528**，与主会话 m6 独立复算逐数一致。
- 主会话自错 2 条：E1 `m5` 忘设 `md.skipdata=True`（只解 155,215 条）；E2 `m4` 的 `trace()` 在两条分支返回标量导致解包崩溃。两条均 0 条进结论。
- 跨家族审计（#571 deepseek，`--max-turns 50`）**超出 12 分钟预算仍在运行，结果未取回**，如实记为 OVERTIME；本轮所有结论均由主会话脚本自带正反控取得。
"""

p = SPEC['R14_COMMON']['path']; b0 = bak(p, 'R14COMMON')
assert b0.endswith(b'\n') and b0.count(b'\r') == 1081
new = b0 + R14.encode('utf-8')
assert new.count(b'\r') == 1081, 'R14 CR %d' % new.count(b'\r')
open(p, 'wb').write(new); chk = open(p, 'rb').read()
assert chk.startswith(b0) and chk.count(b'\r') == 1081
print('[写入] R14_COMMON bytes %d -> %d  CR %d  sha %s -> %s'
      % (len(b0), len(chk), chk.count(b'\r'), hashlib.sha256(b0).hexdigest()[:16], hashlib.sha256(chk).hexdigest()[:16]))
json.dump({'pre': pre, 'r14': dict(bytes=len(chk), sha=hashlib.sha256(chk).hexdigest())},
          open(ROOT + '/_r219/p2.json', 'w'), indent=1)
