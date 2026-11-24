# PATCH-D35 · 字节级补丁报告

卡号 PATCH-D35｜卡目录 `lead\next_re_20261117_r14\PATCH_D35\`｜2026-11-19
目标（只读）：`ra2youli\gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · 4,825,360 B · ImageBase `0x400000`

## 1 洞的复算（独立从 exe 字节，不照抄裁决）

规则依据：R14_COMMON.md §6 纪律 2（capstone `skipdata=True`）、纪律 17（函数区间包含判定，**不用 `entry_at_or_before`**）；§8.1 错源 ⑨（假否定）、⑪（定义级真）。脚本 `work/recalc_cave.py`，原始输出见本节。

### 1.1 VA → 文件偏移（用 PE 节表）
- `VA 0x7DF781` → `RVA = 0x7DF781 − 0x400000 = 0x3DF781`
- `.text` 节：`VirtualAddress=0x1000`，`VirtualSize=0x3DF38D`，`SizeOfRawData=0x3E0000`，`PointerToRawData=0x1000`
- `0x3DF781` 落在 `.text`（`0x1000 ≤ 0x3DF781 < 0x1000+max(0x3DF38D,0x3E0000)=0x3F1000`）
- 文件偏移 `= RawPtr + (RVA − VA) = 0x1000 + (0x3DF781 − 0x1000) = 0x3DF781`（.text 的 VA 与 RawPtr 同为 `0x1000`，故 RVA 恰等于文件偏移）

### 1.2 63 B 实际字节内容
- 63 B（文件 `0x3DF781..0x3DF7BF`，VA `0x7DF781..0x7DF7BF`）：**全部 `0xCC`，63/63，无例外**。
- 最长连续 `int3` 运行：文件 `[0x3DF781, 0x3DF7C0)`，长度恰 63，VA `[0x7DF781, 0x7DF7C0)`。向前一字节 `0x7DF780 = 0xC3 (ret)`，向后 `0x7DF7C0 = 0x55 (push ebp)` 是新函数序言。
- **结论：洞的大小（63 B）与内容（全 int3）与裁决逐字相符。**

### 1.3 函数区间包含判定（不用 entry_at_or_before）
- 用 `function_atlas.tsv`（12,916 函数，`entry`(hex) + `size`(十进制)，判 `[entry, entry+size)`）。
- 洞 VA `0x7DF781`：**CONTAINING = NONE** —— 不落在任何已知 atlas 函数体内。
- 相邻：前函数 `0x7DF640 + 243 → 0x7DF733`（before，距洞起点 `0x4E`）；后函数 `0x7DF7C0 + 242 → 0x7DF8B2`（after，紧邻洞尾）。洞是两函数之间的对齐填充。

## 2 补丁设计（依据 W178_PATCH/_audit/VERDICT.md ★C 反证 1）

VERDICT ★C 给出洞桩方案规格："13B 共享桩（`85 C9/74 05/E9→0x724730 尾跳/83 C4 04/C3`，尾跳复用返回地址与 `ret 4`）+ 19B 块守卫 = 32B/63B，零位移、零重定向"。本卡按此规格在洞内写入 32 B（余 31 B 保留 `0xCC`）。

### 2.1 13 B 共享桩（洞 +0，VA `0x7DF781`，文件 `0x3DF781`）
```
85 C9            test ecx, ecx          ; ecx=this，NULL 时进入 add esp,4 路径
74 05            jz  +5 → 洞+9          ; NULL → add esp,4
E9 A6 4F F4 FF   jmp 0x724730           ; 非 NULL 尾跳原 callee（rel32 = 0xFFF44FA6）
83 C4 04         add esp, 4             ; 补做 callee `ret 4` 的 1 个栈参数清理
C3               ret                    ; 复用站点 call 压入的返回地址返回调用者
```
- **尾跳为何零位移**：站点原 `E8 rel32 call 0x724730`（5 B）若改指向本桩，仍只需 5 B `E8`/`E9`，站点侧长度不变；桩内 `jmp 0x724730` 不压栈、不新建栈帧，直接复用站点压入的返回地址；callee `0x724730` 以 `ret 4` 收尾，弹回该返回地址并清 1 个参数；NULL 路径由桩内 `add esp,4 + ret` 达同一 ESP 汇合点。栈语义与 P1 就地守卫一致，但无需 +9 位移/重链。

### 2.2 19 B 块守卫（洞 +13，VA `0x7DF78E`，文件 `0x3DF78E`）
针对非 call 站点 `0x6CD8CD`（`mov ecx,[eax+0x250]`，eax 来自 `mov eax,[0x8871E0]`）。VERDICT ★C："可行路径是 5B `E9` 覆盖 `0x6CD8C2` 的 `A1 E0 71 88 00` → 洞内 19B 块"。
```
A1 E0 71 88 00   mov eax, [0x8871E0]     ; 重放站点被 5B E9 覆盖的原指令
85 C0            test eax, eax           ; NULL?
74 05            jz  +5 → 洞+27          ; NULL → 跳过整块
E9 2B E1 EE FF   jmp 0x6CD8C7            ; 非 NULL：跳回原块继续
E9 37 E1 EE FF   jmp 0x6CD8D8            ; NULL：跳到汇合点（未 push，ESP 平衡）
```

### 2.3 为何零位移、洞外 0 变化
- 桩与守卫**只写进洞内** `[0x7DF781,0x7DF7A0)`（32 B）。
- **本卡交付的副本未做站点侧接线**：30 处 `call 0x724730` 与 `0x6CD8C2` 的 `E9` 改写均未落地，因为卡面第三步铁规要求"不得改动洞里之外的任何字节 / 洞外 0 字节变化"，且收尾须逐字节比对证明洞外 0 变化。
- 因此副本相对原 exe 的差异**恰为洞内 32 B**，洞外 0 B；这是卡面授权边界内的最大部署。

## 3 逐字节 diff（证明洞外 0 变化）
- 全文件逐字节比对（`work/gen_diff_evidence.py`，输出 `EVIDENCE/byte_diff.tsv`）：差异 32 个偏移，集合为 `0x3DF781..0x3DF7A0`，全部落在洞 `[0x3DF781,0x3DF781+63)` 内。
- **洞外差异 = 0**。
- 原 exe SHA-256 = `73201CC0…F67476`（未变）；补丁副本 SHA-256 = `4EBC5195203140F4CECD0E9BE0DEA74A69A8388A5B2BC0D5651FF4BBA2C593BB`。完整值见 `EVIDENCE/hashes.txt`。

## 4 副本冒烟（见 SMOKE_TABLE.tsv）
副本从 `work\run\` 启动（游戏资源从 `ra2youli\` 复制到卡目录，排除 6 个大 mix；exe 为 `gamemd_patched.exe`），窗口标题 "Yuri's Revenge" 证明确实进入游戏。8 处冒烟均 **未观测到崩溃**：except.txt 未新增/未变化、无崩溃地址、进程 rc=0 或存活。详见 `PROGRESS.md` 与 `SMOKE_TABLE.tsv`。

**重要限定**：因本卡站点侧未接线、且常规 GUI 操作不会把 `[0x887368]`/`[0x8871E0]` 置 NULL，这些"不崩"观测**不构成对 NULL 路径防护的证明**。
