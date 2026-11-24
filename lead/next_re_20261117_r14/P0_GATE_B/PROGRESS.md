# P0-GATE-B · PROGRESS.md

> 卡号 P0-GATE-B｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读，开工/收尾同值）｜纯静态
> 分级仅 `[已证]` / `[静态推断]` / `[未证]`。证据相对本卡目录。

## 一句话结论
**拒绝闸找到了（结构 `[已证]`、放置场景可达性 `[静态推断]`）：`0x47C620` 体内 `0x47C738` / `0x47C805` 对 `0x47C3D0` 的「选择子=0」调用——「head A 上有任一 `[obj+0x14]&1` 对象即 `al=0` 拒绝」，类型无关，故 WhatAmI 15/1 从未被比较却被拒。卡面「选择子=1 分支」假设在放置路径被证伪（5 个 setg 站点全在运动函数）。**

## 结论表（三级分级 + 证据路径）
| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| 1 | `0x47C620` 直接 E8 调用点=10；含等价形式总数=10（jmp尾跳/数据指针/lea-mov+间接 全 0） | `[已证]` | `EVIDENCE\t1_callsites_scan.txt`、`t1_d_equiv.txt`、`baseline_check.txt` |
| 2 | `0x47C620` 比较集 {6,2,0x24}，15/1 一次未比；读 `+0xE4`5次、`+0xE8`0次；`ret 0xc`（3 栈参） | `[已证]` | `EVIDENCE\47c620_full2_disasm.txt` |
| 3 | `0x47C3D0` 真入口 `0x47C3D0..0x47C4C7`，`ret 0xc`；选择子 `[ebp+0xC]`：0→`+0xE4`(head A)、1→`+0xE8`(head B) 各 1 分支 | `[已证]` | `EVIDENCE\47c3d0_clean_full.txt` |
| 4 | `0x47C3D0` 函数内 WhatAmI 虚调用=0；唯一对象过滤 `[obj+0x14]&1` + 距离最近 ⇒ **类型无关** | `[已证]` | `EVIDENCE\t_final_verify.txt`、`47c3d0_clean_full.txt` |
| 5 | **拒绝闸**：`0x47C738 call 0x47C3D0`(选择子0) → `test eax; jne 0x47C853`(`xor al,al`)；`0x47C805` 同构 ⇒ 命中任一对象即拒 | `[已证]`（结构） | `EVIDENCE\47c620_full2_disasm.txt` |
| 6 | 该闸在真机「步兵格」上被触发（可达性取决于 HouseClass 标志 `[arg2+0x16BF/BE/B7/E58]`、`[0xA8E9A0]`） | `[静态推断]` | `GATE.md` T2-b、`UNKNOWNS.md` U1 |
| 7 | 放置链 WhatAmI 15/1 比较=0（`0x43F180`/`0x449440`/`0x47C620` 三函数内） | `[已证]` | `EVIDENCE\t3_whatami_scan.txt` |
| 8 | BuildingClass vtable `+0x1AC`=`0x449440`；放置主循环 `0x43F218`/`0x43F678` 的 can-place vcall 即此函数，后端 `0x47C620` | `[已证]` | `EVIDENCE\t4_vtable_check.txt`、`t4_chain_verify.txt` |
| 9 | 放置主循环判据 9 道；会因步兵失败的是 `0x43F218`(整次中止) 与 `0x43F678` | `[静态推断]` | `EVIDENCE\t4_checkmap.txt`、`43f180_full_disasm.txt` |
| 10 | 5 个 setg 动态选择子站点 `0x4B2BCD/0x4B30B2/0x516A41/0x6A221D/0x6A2702` 全在运动函数 `0x4B2630/0x5164D0/0x6A1C80`，不在放置路径 | `[已证]` | `EVIDENCE\t2_setg_containing.txt` |

## 给审计员的 3 个核心数字（可独立复算）
1. **`0x47C620` 调用点总数（含等价形式）= 10**：`python work\t1_callsites.py` → E8 direct=10、jmp=0；`python work\t1_d_equiv.py` → imm 命中=同一 10 条、data-ptr LE dword=0、lea/mov+间接=0。`baseline_check.py` 证随机目标 direct-E8=0，判据特异。
2. **`0x47C3D0` 选择子=1 分支数 = 1**（`test al,al`@0x47C403，非零读 `+0xE8`@0x47C407）；**放置路径上选择子=1 调用 = 0**（两次 `0x47C620→0x47C3D0` 均 `push 0`）；全镜像动态(setg)选择子站点 = 5（全在运动函数）。复算 `python work\t_final_verify.py`、`EVIDENCE\t2_setg_sites.txt`。
3. **放置路径 WhatAmI 15/1 比较数 = 0**；**放置主循环判据道数 = 9**。复算 `python work\t3_whatami_scan.py`、`work\t4_checkmap.py`。

## 停机核验（纪律 9：先测基线 + 与已入账值比对）
- 已入账值：10 个直接调用点、比较集 {6,2,0x24}、5 个 setg 选择子站点 ⇒ 本卡三项**全部实测吻合**，未凑数。
- 基线：随机目标 direct-E8=0/8（本例 10 显著）；LE-dword 随机值=0/8；WhatAmI 虚调用总数 1109 作分母，15/1 比较只占少数 ⇒ 「某处有 WhatAmI 比较」不构成放置路径证据。
- 未改动 `COVERAGE\coverage.tsv`、`ra2youli\`、台账；未 git commit。`coverage_delta.tsv` 无新增入口（本次均为已有函数的语义复核，入口已入账）。

## 交付物
`PROGRESS.md`｜`CALLSITES.tsv`｜`GATE.md`｜`UNKNOWNS.md`｜`DISAGREE.md`｜`EVIDENCE\`（不截断）｜`work\`（可复跑）｜`coverage_delta.tsv`（表头，0 数据行）
