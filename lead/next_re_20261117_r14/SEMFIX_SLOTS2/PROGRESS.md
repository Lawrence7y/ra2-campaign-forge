# SEMFIX-SLOTS2 PROGRESS — 已审计 ③b 结论搬入语义栏 + grade 提升

卡号 SEMFIX-SLOTS2｜执行员 agent-39｜2026-11-19。`ra2youli\gamemd.exe` 只读，SHA-256 现场复算 `73201CC0…F67476` 全值吻合，ImageBase 0x400000，`.text`=[0x401000,0x7e1000)。Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26；未建 venv / 未 pip install / 未改游戏文件 / 未改 COVERAGE / 未改台账 / 未 git commit。前述骨架（≥5 行）已先落。

任务边界：不重新取证。③b 结论与证据锚取自 `S03_C6`（PROGRESS/THREE_B_DETERMINATION/_audit/VERDICT）与 `S10_KPROVED3`（PROGRESS/EVIDENCE/per_row/_audit/VERDICT）；本卡只做「逐行反汇编核锚 → 写新语义 → grade 提升」。不处理 00431F70/004322A0（M43 已并入）、00432050/004DDDE0（审计否决）。name 逐字照抄 coverage.tsv 盘上现值（含盘上用 CDFileClass/AircraftClass 而卡面按⑯归基类的差异，见 DISAGREE）。

## 核锚方法
`work/verify_anchors.py`：按 VA→RVA→节文件偏移，从真入口 capstone 线性解码，`work/check_jumptables.py` 读跳表字节核目标。结果逐行落 `EVIDENCE/ANCHOR_<entry>.txt`（顶部锚点表 + 全量解码），跳表目标落 `EVIDENCE/JUMPTABLE_TARGETS.txt`。11 行入口相对 +0xNN 锚点除 3 处「卡面写值/偏移错」外均与实际指令逐字符相符（见下）。

## 11 行逐行结论（全部 grade=[已证]，均可升）
| entry | ③b 档位 | 核锚结果 | 核心数字 / 整体合同 | 处置 |
|---|---|---|---|---|
| 0047AE10 | ③b④ | 10/10 精确 | 路径链循环 +0x68 rep movsd 写、+0xAD is-open 可证伪、+0xBB 回边；7 站点 | 可升已证 |
| 0065CDD0 | ③b②① | 11/11 精确 | +0x52 WriteFile、+0x58 GetLastError、+0x96 push 9、+0xAB cmp -1；8 站点 | 可升已证 |
| 0065D0D0 | ③b② | 10/10 精确 | +0x1C GetFileSize、+0x24 cmp edi,-1、+0x32 GetLastError、+0x46 写回缓存；3 站点 | 可升已证 |
| 0065D190 | ③b②（①不达由②兜底） | 11/11 精确 | +0x15 push 2、+0x35 DeleteFileA、+0x3D 成功返1、+0x47 GetLastError；5 站点 | 可升已证 |
| 004D82B0 | ③b④ | 6/6 精确 | +0x10E mov[...-4],edx 写、+0x11A jl 回边；3 站点 | 可升已证 |
| 004D5690 | ③b④ | 6/6 精确 | +0x403 mov[...-4],edx 写、+0x40F jl 回边；2 站点 | 可升已证 |
| 004DB260 | ③b④ | 8/8 精确 | +0x7D dec dl、+0x83 mov[esi+0x122],dl 写、+0x89 jl 回边；5 站点 | 可升已证 |
| 00702D40 | ③b①（五路跳表） | 4/4；跳表 5 目标全核 | +0x2E8 mov cl、+0x2EE jmp [ecx*4+0x703200]；5 目标 0070315F/007030D3/007031F8/00703035/00703115 | 可升已证 |
| 00706640 | ③b①（四路跳表+2循环） | 5/5；跳表 4 目标全核 | +0x24 jmp [eax*4+0x706bb8]；4 目标 00706683/0070668A/0070666B/00706BAD；循环写 +0x51C | 可升已证 |
| 00708C30 | ③b①（五路跳表） | 4/4；跳表 5 目标全核 | +0x15 cmp eax,4、+0x1E jmp [eax*4+0x708d54]；5 目标 00708C55/00708CD9/00708CB4/00708D4D/00708C7A | 可升已证 |
| 004D94B0 | ③b②（HRESULT 返回约定） | 6/6 精确 | +0xD1 cmp eax,ebx、+0xD5 cmp eax,0x80004002、+0xDD call 断言失败；6 站点 | 可升已证 |

## 判据自检
- **可升已证 11 行 / 应维持静态推断 0 行**。无一行落在 ③a（单次调用加单次写/纯转发桩/清零加置默认/无分支线性）：3 行完整写回循环（004D82B0/004D5690/004DB260）、1 行路径链循环（0047AE10）、3 行相异目标跳表（00702D40/00706640/00708C30）、3 行可证伪错误码或返回约定（0065CDD0/0065D0D0/004D94B0）、1 行布尔+错误码删除约定（0065D190）——全部给出 ③b 级整体合同。
- **S10 004DDDE0 先例对照**：三张跳表经 `JUMPTABLE_TARGETS.txt` 实读字节为 5/4/5 个**相异** .text 目标（非「多闸汇入同一 call」），细则#1 成立，不按同标准降 ③a。
- **0065D190**：审计判据6 指出两条错误出口同 `call [vptr+0x40]` 仅参数不同 ⇒ ① 不达，但 0/1 返回 + 错误码 2 + 可证伪 DeleteFileA 满足 ③b②，档位记 ③b②（①不达由②兜底）。
- 11 行新语义全文扫描「未证/未定/弱信号/线索」= 0 命中；name/subsystem 逐字节未改；仅替换第 4 列占位括号并升第 5 列 grade。

## 与卡面不符（按实际写，不沿用卡面写值）
1. 00702D40：卡面 `mov cl,[eax+0x703214]@+0x2EE`，实际在 **+0x2E8**（审计更正#4）；+0x2EE 为 `jmp [ecx*4+0x703200]`。语义栏按 +0x2E8 写。
2. 004D82B0：卡面 `cmp eax,[esi+0x598]@+0x118`，实际该处 `cmp eax,ecx`（审计「+0x118 值误写」）；循环合同用写点 +0x10E 与回边 +0x11A 表达，未引用该操作数。
3. 004D5690：卡面 `cmp eax,[ebx+0x598]@+0x40D`，实际同类值误写；合同用 +0x403 写点与 +0x40F 回边表达。
4. 0047AE10：卡面链尾恢复原名 +0xBD，实际在 **+0xC7**（审计更正）；语义栏未引用该偏移，EVIDENCE 已标。

## 核心数字（给审计）
11/11 可升已证，0 应维持；③b 档位分布：③b④×4（0047AE10/004D82B0/004D5690/004DB260）、③b②①×1（0065CDD0）、③b②×3（0065D0D0/0065D190/004D94B0）、③b①×3（00702D40/00706640/00708C30）。新语义栏 0 处自陈未证字样；核锚精确率 61/64（3 处为上述卡面写值/偏移错，均按实际落盘）。

## 交付
`PROGRESS.md` / `coverage_delta.tsv`（11 数据行 + 表头）/ `EVIDENCE\`（ANCHOR_<entry>.txt ×11 + JUMPTABLE_TARGETS.txt + ANCHOR_SUMMARY.txt）/ `work\`（verify_anchors.py + check_jumptables.py）/ `UNKNOWNS.md` / `DISAGREE.md`。
