# W178-PATCH 候选补丁件（静态设计，不落地）

> 卡号 W178-PATCH｜目标 `ra2youli\gamemd.exe` SHA-256 全值一致｜**只写本卡目录**；未改游戏目录、未注入、未写进程内存、未跑真机。
> 授权依据：`lead\PENDING_DECISIONS.md` D-13（写候选件 + 离线单测获授权）与 D-34（真机常设授权，但禁区仍含写进程内存/注入/改 `ra2youli\`）。本卡为静态卡，不调用任何真机授权。

## 0 关键发现：调用约定决定补丁形状

`0x724730` 序言 `mov ebp,ecx`（thiscall），首访 `0x724737 mov eax,[ebp+0x250]`；若 `ecx=0` ⇒ fault `0x250`。
**callee 唯一 ret = `0x7248AE ret 4`**（`EVIDENCE/core.json:callee`）——它清掉调用者压入的 1 个栈 dword 参数。
⇒ 任何只跳过 `call` 而不清栈的守卫会**泄漏 4 字节/次**（`BASELINE.txt` B2: 30/30 证明朴素 4 字节设计失败）。

## P1（首选，A 级，可离线验证）：调用点内守卫式调用

把 5 字节 `E8 rel32` **就地替换为 14 字节**：
```asm
C+0  85 C9            test ecx, ecx        ; ecx=this，最后一次写入为 [0x887368]
C+2  74 07            jz  C+11
C+4  E8 <rel32-4>     call 0x724730        ; 原调用，rel32 减 4 补偿前插 4 字节
C+9  EB 03            jmp C+14             ; 非 NULL 汇合
C+11 83 C4 04         add esp, 4           ; NULL 路径补做 ret 4 的清栈
C+14 <原 C+5 指令>                          ; 两条路径同 ESP 汇合
```

- **适用场景**：`ecx` 在调用点即 this（`EVIDENCE/DESIGN_FACTS.txt` 30/30 `this=mem [0x887368]`），NULL 可达但希望只把"崩溃"降级为"跳过该次调用"。
- **插入字节/位置/跳转目标**：逐处见 `PATCH_MAP.tsv`；`jz→C+11`（add esp,4），`jmp→C+14`（汇合点）。
- **对指令长度/相对跳转的影响**：在原 5 字节位置就地改写，**原 C 之前的指令不动**；原 C+5 起全部后移 **+9 字节**（14−5），函数内所有跨越 C 的相对跳转须重定位。
- **空间核查（T3）**：`space_ok=N`（30/30）。目标位置现有 5 字节就是 `call` 本身，**无 ≥2 字节可覆盖 nop/int3** ⇒ 无就地填充空间；必须整函数重链（re-link）。
- **跳转冲突**：5/30 处原本有相对跳转指向 C+5（落在 14 字节体内），须从 `C+5` 重定向到 `C+14`（+9 增量）；`BASELINE.txt` RETARGET 11/11 全部在 rel8/rel32 范围内。逐处清单见 `EVIDENCE/UNIT_TEST.txt`（`retarget` 字段）。
- **候选件之间的字节区间争用**：**0**。31 个 P1 的 `insert_at` 两两不同（30 个 `call` 地址 + `0x6CD8C7`），无两个候选件覆盖同一字节区间。唯一"相邻"via 同宿主多站点（如 `0x6ABD30` 6 处）不构成字节重叠，只影响重链顺序（见 `RISKS.md` G1）。
- **离线验证**：`work/unit_test.py` 对 30 处各跑 8 项检查，**31/31 PASS**（`EVIDENCE/UNIT_TEST.txt`）；基线 `work/baseline.py`（`EVIDENCE/BASELINE.txt`）显示 BNUL 0/200、B2 30/30、F1 30/30，判据有鉴别力、非 N/N 自证。

### P1 逐处清单（26 处可达 + 4 处零静态引用；后者先按同形状给出，是否生效取决于真机入边）

| call_site | host | 路径长 | 宿主级 | 变体 | P1 字节 | jz 目标 | 冲突跳转数 | 等级 |
|---|---|---|---|---|---|---|---|---|
| 004A8B75 | 004A8960 | 50 | static-ref | PASS | 85 c9 74 07 e8 b2 bb 27 00 eb 03 83 c4 04 | 0x4a8b80 | 0 | A |
| 00640427 | 006403A0 | 31 | static-ref | PASS | 85 c9 74 07 e8 00 43 0e 00 eb 03 83 c4 04 | 0x640432 | 0 | A |
| 00654413 | 00654320 | 60 | static-ref | PASS | 85 c9 74 07 e8 14 03 0d 00 eb 03 83 c4 04 | 0x65441e | 0 | A |
| 00654469 | 00654320 | 77 | static-ref | PASS | 85 c9 74 07 e8 be 02 0d 00 eb 03 83 c4 04 | 0x654474 | 0 | A |
| 006AC00B | 006ABD30 | 160 | static-ref | PASS | 85 c9 74 07 e8 1c 87 07 00 eb 03 83 c4 04 | 0x6ac016 | 0 | A |
| 006AC03E | 006ABD30 | 174 | static-ref | PASS | 85 c9 74 07 e8 e9 86 07 00 eb 03 83 c4 04 | 0x6ac049 | 0 | A |
| 006AC0ED | 006ABD30 | 195 | static-ref | PASS | 85 c9 74 07 e8 3a 86 07 00 eb 03 83 c4 04 | 0x6ac0f8 | 0 | A |
| 006AC140 | 006ABD30 | 212 | static-ref | PASS | 85 c9 74 07 e8 e7 85 07 00 eb 03 83 c4 04 | 0x6ac14b | 0 | A |
| 006AC193 | 006ABD30 | 229 | static-ref | PASS | 85 c9 74 07 e8 94 85 07 00 eb 03 83 c4 04 | 0x6ac19e | 0 | A |
| 006AC1E6 | 006ABD30 | 246 | static-ref | PASS | 85 c9 74 07 e8 41 85 07 00 eb 03 83 c4 04 | 0x6ac1f1 | 0 | A |
| 006D059B | 006D04F0 | 38 | static-ref | PASS | 85 c9 74 07 e8 8c 41 05 00 eb 03 83 c4 04 | 0x6d05a6 | 0 | A |
| 006D0619 | 006D04F0 | 44 | static-ref | PASS | 85 c9 74 07 e8 0e 41 05 00 eb 03 83 c4 04 | 0x6d0624 | 3 | A |
| 006D0634 | 006D04F0 | 39 | static-ref | PASS | 85 c9 74 07 e8 f3 40 05 00 eb 03 83 c4 04 | 0x6d063f | 0 | A |
| 006D0664 | 006D04F0 | 23 | static-ref | PASS | 85 c9 74 07 e8 c3 40 05 00 eb 03 83 c4 04 | 0x6d066f | 1 | A |
| 006D089D | 006D0680 | 50 | static-ref | PASS | 85 c9 74 07 e8 8a 3e 05 00 eb 03 83 c4 04 | 0x6d08a8 | 1 | A |
| 006D08B3 | 006D0680 | 52 | static-ref | PASS | 85 c9 74 07 e8 74 3e 05 00 eb 03 83 c4 04 | 0x6d08be | 0 | A |
| 006D0940 | 006D0680 | 47 | static-ref | PASS | 85 c9 74 07 e8 e7 3d 05 00 eb 03 83 c4 04 | 0x6d094b | 0 | A |
| 006D09FA | 006D09C0 | 18 | static-ref | PASS | 85 c9 74 07 e8 2d 3d 05 00 eb 03 83 c4 04 | 0x6d0a05 | 0 | A |
| 006D1293 | 006D1200 | 46 | static-ref | PASS | 85 c9 74 07 e8 94 34 05 00 eb 03 83 c4 04 | 0x6d129e | 0 | A |
| 006D1308 | 006D1200 | 50 | static-ref | PASS | 85 c9 74 07 e8 1f 34 05 00 eb 03 83 c4 04 | 0x6d1313 | 0 | A |
| 006D137E | 006D1200 | 54 | static-ref | PASS | 85 c9 74 07 e8 a9 33 05 00 eb 03 83 c4 04 | 0x6d1389 | 0 | A |
| 006D13F3 | 006D1200 | 58 | static-ref | PASS | 85 c9 74 07 e8 34 33 05 00 eb 03 83 c4 04 | 0x6d13fe | 0 | A |
| 006D1541 | 006D14F0 | 30 | zero-static-ref | PASS | 85 c9 74 07 e8 e6 31 05 00 eb 03 83 c4 04 | 0x6d154c | 3 | A |
| 006D155C | 006D14F0 | 25 | zero-static-ref | PASS | 85 c9 74 07 e8 cb 31 05 00 eb 03 83 c4 04 | 0x6d1567 | 0 | A |
| 006D15CB | 006D1570 | 22 | zero-static-ref | PASS | 85 c9 74 07 e8 5c 31 05 00 eb 03 83 c4 04 | 0x6d15d6 | 0 | A |
| 006D1605 | 006D15F0 | 6 | zero-static-ref | PASS | 85 c9 74 07 e8 22 31 05 00 eb 03 83 c4 04 | 0x6d1610 | 0 | A |
| 006D1632 | 006D1610 | 11 | static-ref | PASS | 85 c9 74 07 e8 f5 30 05 00 eb 03 83 c4 04 | 0x6d163d | 0 | A |
| 006D16C2 | 006D1660 | 34 | static-ref | PASS | 85 c9 74 07 e8 65 30 05 00 eb 03 83 c4 04 | 0x6d16cd | 3 | A |
| 006D16DD | 006D1660 | 29 | static-ref | PASS | 85 c9 74 07 e8 4a 30 05 00 eb 03 83 c4 04 | 0x6d16e8 | 0 | A |
| 006D1744 | 006D1660 | 53 | static-ref | PASS | 85 c9 74 07 e8 e3 2f 05 00 eb 03 83 c4 04 | 0x6d174f | 0 | A |

### P1：0x6CD8CD（非 call，直接解引用）

```asm
006CD8C2  A1 E0 71 88 00     mov eax, [0x8871E0]     ; 保留
--- 在 006CD8C7（push 0）处插入 4 字节 ---
          85 C0              test eax, eax
          74 11              jz  0x6CD8DC      ; 跳过 push/lea/deref/call
006CD8C7  6A 00              push 0                  ; 原
006CD8C9  8D 54 24 14        lea edx,[esp+0x14]      ; 原
006CD8CD  8B 88 50 02 00 00  mov ecx,[eax+0x250]     ; 原（NULL 时崩溃点）
006CD8D3  E8 ...             call 0x750E20           ; 原
006CD8D8  <原下一指令>                               ; 汇合
```
插入字节 `85 c0 74 11`；`jz` 目标 `0x6CD8DC`（重链后）。NULL 路径跳过整块，未 push 故 ESP 平衡；`ecx` 来源在 `DESIGN_FACTS.txt`。等级 A；`space_ok=N`。
⚠️ `0x750E20` 的 ret 是路径相关的（`ret 4` ×3、`ret` ×2，`EVIDENCE/query_750e20.txt`）；NULL 路径整块跳过故不走它，但被跳过的副作用（edx/ecx、调用 0x750E20）须在 `RISKS.md` 评估。

## P2（调用点替换，C 级）：代码洞桩

把 5 字节 `call 0x724730` 换成 `E8 rel32 → cave`，cave 内 `test ecx,ecx / jz add_esp4 / call 0x724730 / ret`。
**需额外空间（代码洞或新增段），很可能不在授权范围**；且新增段改变 PE 布局与所有绝对寻址，风险最高 ⇒ 建议不做（C）。本卡不生成可用字节，仅在 `RISKS.md` 登记。

## P3（上游修复，C 级）：在 NULL 写入处保证非 NULL

`[0x887368]` 3 个写者：`0x7777B8`（存 esi=成功对象）、`0x7777C3`/`0x777803`（存 ebx，宿主入口 `xor ebx,ebx` ⇒ 写 NULL，分配失败/析构清零）。
把后两处改成"保留旧非 NULL 值/回退默认对象"可根除全部 30 处，但：写者函数 `0x7775C0` 的入边只由回调取址 `0x777C79` 支撑、语义是资源生命周期；改动影响面远大于 30 处调用点，且会掩盖真实分配失败 ⇒ **语义有风险，建议不做（C）**。
`[0x8871E0]` 同理（`0x52BAFA`/`0x6BEABD` 写 NULL）。

## 证据索引
- `EVIDENCE/core.json`：30 站点全字段、callee ret、跳表、NULL 写者。
- `EVIDENCE/UNIT_TEST.txt` / `.json`：30/30 八项离线检查 + 逐处 retarget。
- `EVIDENCE/BASELINE.txt` / `.json`：BNUL 0/200、B1/B2/F1/U7/RETARGET 基线。
- `EVIDENCE/DESIGN_FACTS.txt`：逐处 push/this/nop 与 gap 边界。
- `work/`：全部脚本可复跑（`explore.py`→`analyze.py`→`unit_test.py`→`baseline.py`→`make_deliverables.py`）。
