# -*- coding: utf-8 -*-
"""追加 §361/§362/§363 到主账本（纯追加，零删除）。"""
import hashlib
import io
from pathlib import Path

LEDGER = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

SEC = r"""
## §361　★ RC-4 崩溃入口定案：`0x654413`（现场栈直接取证）

**日期**：2026-10-22　**性质**：只读离线，零真机
**二进制**：`ra2youli/gamemd.exe` sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
**现场**：`ra2youli/except.txt` sha256 `584069adfe5b4a5b7587a383620f716edbe79c52cf899b43038d599d4ed52cfa`（27631 B）

### 一、方法：不靠序言算术，直接遍历栈值反查调用点

对栈转储的**每个 4 字节值 V**，若 `V-5` 处是一条 `E8 rel32` 且目标等于已知函数，
则 V 就是那个函数帧的返回地址。该方法对整个转储通用，且**可被反证**（找不到即失败）。

### 二、结果：五帧逐帧成立

| 被调函数 | 调用点 | 返回地址 | 栈槽 | 判定 |
|:--|:--|:--|:--|:--|
| `0x724730` | `0x654413` | `0x00654418` | `0x00F9A358` | CONFIRMED |
| `0x654320` | `0x6403A3` | `0x006403A8` | `0x00F9A388` | CONFIRMED |
| `0x6403A0` | `0x6ABD39` | `0x006ABD3E` | `0x00F9A3AC` | CONFIRMED |
| `0x6ABD30` | `0x4A8B13` | `0x004A8B18` | `0x00F9A3E4` | CONFIRMED |
| `0x4A8850` | `0x652D4C` | `0x00652D51` | `0x00F9A43C` | CONFIRMED |

⇒ **崩溃入口 = `0x654413`**，不是 L3 自己的 `0x4A8B75`。

### 三、三条独立交叉判据（全部指向同一结论）

1. **返回地址唯一命中**：栈上 `0x724730` 的返回地址只出现 1 次（`0x00F9A358`）。
2. **参数值判据**：`[ESP+0x18] = 0xF2`；`0x654413` 前的 `push 0xF2` 在 `0x6543FC`。
   竞争点 `0x4A8B75` 前压的是 `push 0x1F4` ⇒ **参数本身即可区分**。
3. **`0x4A8B7A` 不在栈上任何位置**（且无任何 V 使 `V-5 == 0x4A8B75`）。

### 四、一个真实误判陷阱（核验员提出）

栈槽 `0x00F9A354 = 0x006543B1` 是个漂亮的代码地址，但它只是 `0x6543AC` 那次
**已完成调用遗留在本地变量区的返回值残留**。
⇒ **任何「从栈底往上找第一个像代码地址的值」的朴素做法都会先命中它**，
从而把调用点误判到 `0x6543AC`。必须用帧算术 `Esp+0x14` 才能定位真返回地址。

### 五、`L3 是否在链上` 的精确表述（更正旧账本）

旧账本写「本次崩溃**不经 L3**」——**过强**。

事实：`0x4A8B18`（= L3 内 `0x4A8B13` 调 `0x6ABD30` 的返回地址）**在栈上**（槽 `0x00F9A3E4`）。
且 `0x4A8960..0x4A8B75` 之间**无 ret** ⇒ `0x4A8B13` 与 `0x4A8B75` 同属 L3 一个函数体。

⇒ 正确表述：**L3 在崩溃路径上（祖先帧），但本帧的直接调用者是 `0x654413`，
不是 L3 自己在 `0x4A8B75` 的直接调用。**

这条更正很重要，因为它直接决定了「在 `0x4A8B35` 加守卫」是否有用：
那条守卫在 `0x4A8B75` 之前生效，但崩溃分支在 `0x4A8B13` 就转出去了 ⇒ **守不到**。

### 六、交付件

| 文件 | EXIT | 断言 |
|:--|:--:|:--:|
| `goal2_rc4_frameproof_20261022/_crash_frame_census.py` / `lead/go2_frame.txt` | 0 | **28/28** |
| `goal2_rc4_frameproof_20261022/VERIFY_FRAME.py` / `.txt` | 0 | **13/13**（异族子代理独立实现） |
| `goal2_rc4_frameproof_20261022/VERIFY_RC4_FRAME.py` / `.txt` | 0 | **71/71**（异族子代理全量复核） |

---

## §362　★★ 修复草案 v1 的两处硬伤（本轮推翻）

**性质**：离线复核，零真机。**裁决 11 仍有效：只离线，不部署。**

### 硬伤 1：只守 `0x724730` 不充分 —— 兄弟函数 `0x724580` 会立刻以同一 Access 崩溃

`0x654320` 内有 **4 处**以 `[0x887368]` 为 this 的 deref 调用，**全部无守卫**：

| load | call | 目标 | 守卫 |
|:--|:--|:--|:--|
| `0x654405` | `0x654413` | `0x724730` | ★无 |
| `0x654418` | `0x654423` | `0x724580` | ★无 |
| `0x654446` | `0x654469` | `0x724730` | ★无 |
| `0x654473` | `0x654479` | `0x724580` | ★无 |

守卫判据用 **flags 级**（`mov` 不改 flags）：四段的 mov→call 之间改 flags 指令数 **0**，jcc 数 **0**。

`0x724580` 在 `ecx=0` 时：

```asm
00724588  8bd9           mov  ebx, ecx          ; ebx = 0
0072458C  8db34c020000   lea  esi, [ebx+0x24c]  ; esi = 0x24C
00724596  8b4604         mov  eax, [esi+4]      ; ★ 读 0x250 ⇒ AV
```

**`0x24C + 4 = 0x250`，与 except.txt 的 `Access address:00000250` 完全相同。**

⇒ 若只守 `0x724730`：它会安全返回 → `0x654418` 再读一次仍为 0 →
`0x654423 call 0x724580` → `0x724596` 读 `0x250` → **同样的 AV、同样的 Access**。
症状一模一样，看起来像「补丁没生效」。

**核验员措辞更正**：`0x724580` 的**首个**解引用是 `0x72458A` 的 `[edi]`（读调用方压入的
栈地址，`ecx=0` 时仍合法）；首个**随 ecx 变化**的解引用才是 `0x724596` 的 `[esi+4]`。
结论不变，但「首次解引用」措辞不精确。

### 硬伤 2：`.detour` 段**没有执行位**，且「2304 字节空闲」不成立

| 项 | 实测值 |
|:--|:--|
| `.detour` Characteristics | **`0xC0000040`** |
| `MEM_EXECUTE` (0x20000000) | **CLEAR** ← v1 写「R/W/**X**」是错的 |
| `MEM_READ` (0x40000000) / `MEM_WRITE` (0x80000000) | SET / SET |
| `CNT_CODE` (0x20) / `CNT_INITIALIZED_DATA` (0x40) | CLEAR / SET |
| VirtualSize | `0x2718`（段末 VA `0xB95718`） |
| SizeOfRawData | `0x3000`（raw 末 `0xB96000`） |
| 段内末个非零字节 | **`0xB956FE`** |
| `0xB95700` 之后 VirtualSize 内剩余 | **仅 24 字节** |
| 段首 | `40 00 00 00`（长度字段）+ **`Dtr\0`**（Detours 签名，在 **+4** 处） |
| 段内 +0x40 | `4D 5A`（内嵌 MZ 映像） |
| VirtualSize 内 >=64B 全零空洞 | **恰 1 处：`0xB9375C`，1548 字节** |

⇒ 该段是 **Detours 载荷区**（签名 + 内嵌映像），不是空白代码区。
⇒ 「2304 字节空闲」只在 **raw padding** 意义上成立（`0xB95700..0xB96000`），
   按 VirtualSize 只有 24 字节。v1 的 21 字节 cave 恰好塞得下 ⇒
   **v1 的硬伤不是越界，而是该段没有执行位 + 该区实为载荷尾部。**

### 三、交付件

| 文件 | EXIT | 断言 |
|:--|:--:|:--:|
| `goal2_rc4_frameproof_20261022/_next_crash_proof.py` | 0 | 42/44 → 见 §363 |
| `goal2_rc4_frameproof_20261022/_rc4_fix_v2_proof.py` / `lead/go2_v2.txt` | 0 | **50/50** |

---

## §363　RC-4 修复草案 v2：双守卫 + DLL 内 trampoline

**性质**：离线草案，**未部署、未编译、未真机**。裁决 11 有效。

### 一、照搬项目既有范式（`ra2render/blitter_hooks.cpp:1384`）

```
gamemd 侧：只改函数头 5/8 字节 → E9 rel32 跳到 DLL 自己的静态数组
DLL 侧  ：静态数组 VirtualProtect(PAGE_EXECUTE_READWRITE) 后填充
          守卫 + 重放原序言 + E9 rel32 跳回 gamemd
```

好处：cave 在 DLL 里，段属性由 DLL 自己控制；**不动 gamemd 的节表**。

### 二、两个函数头（不是 v1 的一个）

| 函数 | 原前 N 字节 | N | 重放后跳回 |
|:--|:--|:--:|:--|
| `0x724730` | `83 ec 0c 55 8b e9` = `sub esp,0xc; push ebp; mov ebp,ecx` | **6** | `0x724737` |
| `0x724580` | `53 55 56 57 8b 7c 24 14` = `push ebx/ebp/esi/edi; mov edi,[esp+0x14]` | **8** | `0x724588` |

★ `0x724730` 的 `push esi`（`0x724736`）**不在** 6 字节 hook 内，必须在 cave 里重放。

### 三、cave 逻辑布局

```
caveA (21B) : 85 c9 | 74 0c | 83 ec 0c 55 8b e9 | 56 | e9 <rel32→0x724737> | 31 c0 c2 04 00
caveB (22B) : 85 c9 | 74 0d | 53 55 56 57 8b 7c 24 14 | e9 <rel32→0x724588> | 31 c0 c2 04 00
```

`.null` 分支：`xor eax,eax` + `ret 4`。

### 四、栈平衡（六条路径全部回到基线）

| 路径 | esp 净变化 | 结果 |
|:--|:--|:--|
| `0x724730` 原 | `-4 -4 -0xc -4 -4 +4 +4 +0xc +8` | 0 ✅ |
| `0x724730` 非零 | 同上（cave 重放等价） | 0 ✅ |
| `0x724730` 零值 | `-4 -4 +8` | 0 ✅ |
| `0x724580` 原 | `-4 -4 -4×4 +4×4 +8` | 0 ✅ |
| `0x724580` 非零 | 同上（cave 重放等价） | 0 ✅ |
| `0x724580` 零值 | `-4 -4 +8` | 0 ✅ |

★ 零值路径**未执行** `sub`/`push`，故**不需要** `pop`/`add`，直接 `ret 4` 正确。
★ caveB 的 `mov edi,[esp+0x14]` 在 4 个 push 之后执行 ⇒ 与原函数取同一槽（`E-0x10`）。

### 五、返回值语义（决定 `.null` 分支的 `eax=0` 是否安全）

| 函数 | 直接 E8 调用者 | 覆盖 eax | 读 eax | 不碰 |
|:--|:--:|:--:|:--:|:--:|
| `0x724730` | 30 | 2 | **0** | 28 |
| `0x724580` | 18 | 7 | **0** | 11 |

⇒ 两函数的调用者**全不读返回值** ⇒ `.null` 返回 `eax=0` 安全。

### 六、交付件

| 文件 | EXIT | 断言 |
|:--|:--:|:--:|
| `goal2_rc4_frameproof_20261022/_rc4_fix_v2_proof.py` | 0 | **50/50** |
| `goal2_rc4_frameproof_20261022/VERIFY_RC4_FRAME.py` / `.txt` | 0 | **71/71**（异族独立复核三项推翻） |

### 七、诚实边界

- 本草案的**核心事实**已字节级 + 现场栈双重证实。
- 但**仍未**：写入任何二进制、编译、真机验证。
- `0x724580` 的 18 个调用者中，是否有**间接**调用（`call [mem]`）会读返回值：未查。
- DLL 侧 trampoline 的**实际代码**未写（本轮只给逻辑布局与字节）。
- 新增风险：DLL 卸载/hook 移除时必须恢复原 6/8 字节，否则 gamemd 跳向已释放内存。
"""

raw = LEDGER.read_bytes()
print("before:", len(raw), "bytes; CRLF count:", raw.count(b"\r\n"))
add = SEC.replace("\r\n", "\n").encode("utf-8")
with open(LEDGER, "ab") as f:
    f.write(add)
new = LEDGER.read_bytes()
print("after :", len(new), "bytes; CRLF count:", new.count(b"\r\n"))
assert new.startswith(raw), "prefix changed!"
assert new == raw + add, "not pure append!"
assert new.count(b"\r\n") == raw.count(b"\r\n"), "CRLF introduced!"
print("OK: pure append, zero deletions, zero CRLF")
print("sha256:", hashlib.sha256(new).hexdigest())
