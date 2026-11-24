# W178 · ②-a 剩余缺口风险分级（纯静态）

> 卡号 W178｜项目根 `D:\Project\ra2-campaign-forge`｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（本卡复算一致）。
> 只写本卡目录；未改 `ra2youli\`、未注入、未写进程内存。

## 核心数字（给审计）

1. **`30`** 个 `call 0x724730` 字节算术命中全部经全 `.text` skipdata 线性反汇编验证为指令边界；`30/30` 的 `ecx` 最后一次写入均为 `mov ecx,[0x887368]`；`0/30` 在最后一次写入后有 `test ecx,ecx` / `cmp ecx,0`。
2. **`26/30`** 有可给 Caller→Host→Site→`FUN_00724730` 上下各一层静态证据的可达 NULL 路径；另 **4** 点宿主函数（0x6D14F0/0x6D1570/0x6D15F0）直接 call、dword 指针、立即数引用均为 0，入边 `[未证]`，不计入。
3. **`0x6CD8CD`**：`eax=[0x8871E0]`（0x6CD8C2）→ `[eax+0x250]`（0x6CD8CD），无 NULL 判据；经 `FUN_006CC390` 12 项跳表 case 9 可达，宿主有 3 个直接调用者；预测 AV：`EIP=0x6CD8CD`, fault `0x250`。

## 结论表

| 项 | 分级 | 结论 | 证据 |
|---|---|---|---|
| 30 点复核 | `[已证]` | 30 个 `E8 rel32` 直接调用 `FUN_00724730`，全部为真实指令边界；卡面“30”成立 | `EVIDENCE/FINAL_COUNTS.txt`, `EVIDENCE/w178_core.json`, `EVIDENCE/query_anomalies.txt` |
| 调用形态口径 | `[已证]` | 这 30 个是 **直接调用**，不是 `call [vptr+…]` 间接虚调用；沿用卡面称呼但不外推 | 同上；`EVIDENCE/w178_dump.txt` REMOVE_HEAD |
| `this` 来源 | `[已证]` | 30/30 的 `ecx` 最后写入为 `mov ecx,dword ptr [0x887368]`；全部写入点已逐条落盘 | `EVIDENCE/site_table.tsv`, `EVIDENCE/w178_dump.txt` (`ECXW` 行) |
| 无守卫复核 | `[已证]` | 最后一次 `ecx` 写入之后，0/30 有以 `ecx` 为对象的零测试；旧“4 个守卫”测的是参数对象指针 | `EVIDENCE/site_table.tsv`, `EVIDENCE/w178_dump.txt` |
| 26 点可达 NULL | `[静态推断]` | 宿主函数有 ≥1 个直接调用者，CFG 从宿主入口可达站点；`[0x887368]` 有 NULL 写入分支且真机现场 Access=`0x250`（台账 §876） | `EVIDENCE/w178_core.json`, `EVIDENCE/w178_dump.txt` |
| 4 点不可证入边 | `[未证]` | `0x6D1541/0x6D155C/0x6D15CB/0x6D1605` 宿主静态零引用；局部 CFG 可达，但运行期入边未证 | `EVIDENCE/FINAL_COUNTS.txt`, `EVIDENCE/w178_core.json` |
| 30 点崩溃预测 | `[静态推断]` | 若 `ecx=0`，`FUN_00724730` 序言 `mov ebp,ecx` 后首访 `[ebp+0x250]` ⇒ `EIP=0x724737`, fault `0x250` | `EVIDENCE/w178_dump.txt` REMOVE_HEAD |
| `0x6CD8CD` | `[静态推断]` | 无判据解引用 `[0x8871E0]+0x250`；跳表 case 9 路径已打完；预测 `EIP=0x6CD8CD`, fault `0x250` | `EVIDENCE/query_jumptable_6cd8cd.txt`, `EVIDENCE/w178_dump.txt` |
| 全局 NULL 写入 | `[已证]` | `[0x887368]`：3 写者；`[0x8871E0]`：3 写者（Init 失败 0x52BAFA、清理 0x6BEABD） | `EVIDENCE/w178_dump.txt` GLOBAL 段；台账 §878 |

## 复算方法（审计可原样重跑）

```bash
python -X utf8 lead\next_re_20261117_r14\W178_guards\work\analyze.py
python -X utf8 lead\next_re_20261117_r14\W178_guards\work\make_deliverables.py
```

- 通道 A（不依赖 `function_atlas.tsv`）：pefile 取 `.text`，`capstone.Cs(..., detail=True)` 且 `skipdata=True`，全段线性反汇编得 `1,394,120` 条真指令、`66` skipdata 字节；从 `call` 助记符＋rel32 目标取 30 点，并用同一反汇编的起始地址集合验证指令边界（未用“最近 E8”）。
- 通道 B：`function_atlas.tsv` **区间包含**（`entry <= site < entry+size`）归属宿主；0x6D1570/0x6D15F0 两处 atlas 空洞用 `ret` + `nop` 填充独立定界，未用 `entry_at_or_before`。
- 每站点从宿主入口重新线性解码，列出入口到站点**全部** `ecx` 写点；反向解析器只取最后一次写入的来源；零守卫判定只认最后一次写入后的 `ecx` 零测试。
- 可达性：宿主函数内 CFG BFS（条件跳＝目标＋fallthrough，`ret` 终止）；`0x6CC390` 的头跳表 `0x6CDE44` 12 项全部解析后 BFS，得到 48 步路径到 0x6CD8CD。
- 入边证据：对宿主函数扫全镜像直接 `call/jmp` 目标、全段 dword 指针、`.text` 立即数；三者全零才标 `zero-static-ref`，不写“死代码”。
- 崩溃地址是**静态预测**，不是本卡新真机观测；字节与首访指令已逐字符核对。
