# SEMANTICS.md — 这类入口是什么（T3）

## 0 结论先行
这 3,944 项是 **MSVC `_initterm` 静态初始化表项**：进程启动时由 `0x7CBDD3` 调用 `_initterm(0x812000, 0x815da4)`，后者在 `0x7CBEDE..0x7CBEE9` 逐槽 `mov eax,[esi] / test eax,eax / call eax` 执行。⇒ **每一项都是"启动时被调用一次的函数入口"**，即"静态初始化函数"。

但**"静态对象构造器（写 vptr / 调 ctor 的 thunk）"这个说法对本表并不贴切**：实测 3,944 项里 **0 项**在其限定函数体内直接 `C7 /0 <.rdata vptr>` 写虚表指针；主体是**全局变量的运行时初始化器**（浮点常量计算后写入全局、plain store、调用 `_ftol`/数学辅助/CRT 辅助）。这一区分见 §3 与 DISAGREE.md。

## 1 判定依据（强力证据 > 形态证据）
- **槽值即函数（本卡最强判据）**：MSVC `_initterm(pfBegin,pfEnd)` 的契约就是遍历 `void (**)()` 表并 `call` 每个非空槽；`0x7CBEE4 call eax` 是唯一的调用形式。表内 3,944 槽全非空且全落 `.text`（`0x00401000..0x007E038D`）。⇒ 3,944 全判 FUNC，形态异常只标注、不否定（派卡 T2 明确规定）。
- 反证：若槽值是数据，`call eax` 会在启动时立即崩溃；而这是 shipped 游戏的标准 CRT 初始化路径。

## 2 分桶结果（`EVIDENCE/t3_buckets_refined.tsv` 全量逐项；`EVIDENCE/t3_bucket_disasm.txt` 逐桶代表反汇编）
分桶方法：对每个 target 从入口扫到**下一个表项地址**（避免读进相邻函数），按优先级归类：A(直接 C7 写 .rdata vptr) > B(有 E8 call) > C(x87 计算) > D(plain mov 写全局) > E(其它)。

| 桶 | 项数 | 在 coverage | 判定依据 | 代表地址（3 个） |
|---|---:|---:|---|---|
| **A_VPTR_WRITE** | **0** | 0 | 体内 `C7 /0 imm32`，imm ∈ `.rdata` `0x7E1000..0x811074` —— 全表 0 命中 | — |
| **B_CALL_THUNK** | **1,962** | **22** | 体内有 `E8 rel32` 调辅助函数/构造器；典型 `fld/fadd → sub esp,8 → fstp [esp] → call 0x4CAC40(_ftol 类) → fstp [global] → ret` | `00403CE0`(idx1) / `00403DB0`(idx7) / `00403DF0`(idx8) |
| **C_FP_INIT** | **1,148** | 0 | 纯 x87 常量计算写全局，无 call；典型 `fld qword[.rdata] / fdiv / fstp qword[0x87E280] / ret` | `00403D10`(idx2) / `00403D30`(idx3) / `00406950` |
| **D_PLAIN_STORE** | **818** | 0 | 无 call/无 x87；`mov dword[global], imm/reg` 直接写全局后 `ret` | 见 t3_bucket_disasm.txt |
| **E_OTHER** | **16** | 0 | 5 项首字节是跳转/调用 thunk（4×`E9`+1×`E8`）+ 11 项形态特殊（前驱 0x00 等）；仍是合法槽值 | 见 t2_anomaly_detail.txt |

**合计 1,962+1,148+818+16=3,944**。22 条 coverage 全部落在 B_CALL_THUNK（其中 2 条同时在 atlas）；C/D/E 共 1,982 条**全部未被 coverage 收编**。

## 3 代表反汇编（逐字符核对，来自 EVIDENCE/t3_bucket_disasm.txt）
**B_CALL_THUNK / `00403CE0`（idx1，表项第 1 项）** — 全局 FP 常量计算 + 调辅助：
```
00403CE0  dd0510177e00  fld qword ptr [0x7E1710]
00403CE6  dd0508177e00  fld qword ptr [0x7E1708]
00403CEC  e8bf523c00    call 0x7C8FB0
00403CF1  dcc0          fadd st(0), st(0)
00403CF3  83ec08        sub esp, 8
00403CF6  dd1c24        fstp qword ptr [esp]
00403CF9  e8426f0c00    call 0x4CAC40
00403CFE  dd1da0e18700  fstp qword ptr [0x87E1A0]
00403D07  c3            ret
```
**C_FP_INIT / `00403D10`（idx2）** — 纯 x87 常量写入全局：
```
00403D10  dd05a0e18700  fld qword ptr [0x87E1A0]
00403D16  dc35f8167e00  fdiv qword ptr [0x7E16F8]
00403D1C  dd1d80e28700  fstp qword ptr [0x87E280]
00403D22  c3            ret
```

## 4 "该怎么计量"的语义结论
- 每项的**可证语义上限**就是"被 `_initterm` 调用的静态初始化函数"；具体初始化了哪个全局、属于哪个类，需要逐项分析（P1 工作），本卡**不逐一定名**（派卡明确要求）。
- 因此 `coverage_delta.tsv` 统一 grade=`[未证]`、name=`initterm_thunk_NNNN`、sem="调用静态对象构造器（附实际 target）" —— 只裁"是入口"，不裁精确语义。
- 可直接引用的类别语义：**"MSVC CRT 静态初始化表项：启动时执行一次的全局/对象初始化 thunk"**（覆盖全部 3,944 项，不夸大）。
