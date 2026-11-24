# W178-PATCH · PROGRESS（②-a 收尾件：候选补丁，不落地）

> 卡号 W178-PATCH｜`ra2youli\gamemd.exe` SHA-256 全值一致｜**只写本卡目录**；未改游戏目录、未注入、未写进程内存、未跑真机。授权：D-13（候选件+离线单测）+ D-34（静态卡不调用）。

## 结论表（分级 + 证据路径）
| 项 | 分级 | 结论 | 证据 |
|---|---|---|---|
| 30 处 `call 0x724730` 复核 | `[已证]` | 全 `.text` skipdata 线性反汇编得 30 命中、全为指令边界、直接 E8 thiscall | `EVIDENCE/core.json`, `EVIDENCE/EXPLORE.txt` |
| 26 处可达 NULL | `[静态推断]` | CFG 从宿主入口可达 + 宿主静态引用 + 全局 NULL 写者；BNUL 基线 0/200 排除基线假象 | `EVIDENCE/core.json`, `EVIDENCE/BASELINE.txt` |
| 4 处零静态引用 | `[未证]` | `006D1541/006D155C/006D15CB/006D1605` 宿主三通道全零，运行期入边未证 | `EVIDENCE/DESIGN_FACTS.txt` |
| P1 候选（31 处） | A（可离线验证） | `work/unit_test.py` 8 项检查 31/31 PASS；`space_ok=N`（无就地空间），重链后方可部署 | `EVIDENCE/UNIT_TEST.txt`, `EVIDENCE/BASELINE.txt` |
| P2 代码洞桩 | C（建议不做） | 需额外空间/新增段，可能不在授权范围 | `CANDIDATES.md` §P2, `RISKS.md` §4 |
| P3 上游 NULL 修复 | C（建议不做） | 改 4 处全局写者，语义影响面大且掩盖分配失败 | `CANDIDATES.md` §P3 |
| `0x6CD8CD` | A（P1）/`[静态推断]`（可达） | 无判据解引用 `[0x8871E0]+0x250`；跳表 case 9 可达 48 节点；P1 `85 C0 74 11` | `EVIDENCE/core.json:s6`, `EVIDENCE/DESIGN_FACTS.txt` |

## 给审计员的 3 个核心数字（可独立复算）
**① 复核后可达 NULL 的处数 = 26（30 中）**
复算：跑 `python -X utf8 work\analyze.py`；`EVIDENCE/core.json` 中 `sites[]` 过滤 `reachable==true AND host_grade=='static-ref'` 计数。基线对照：`python -X utf8 work\baseline.py` 的 `BNUL`（200 个随机直接调用点中同判据命中 0）。
**② A 级候选件数 = 31（30 处 call + `0x6CD8CD`）**
复算：跑 `python -X utf8 work\unit_test.py`；`EVIDENCE/UNIT_TEST.json` 的 `passed` 应为 31，`results[]` 全 `status=PASS`（30 处 call + 1 处 `0x6CD8CD`）。
**③ 就地空间不足的处数 = 31（全部）**
复算：`EVIDENCE/CalleeAndSpace.txt` 的 `nop/int3 runs` 在各 call 点 `[]`；`PATCH_MAP.tsv` `space_ok` 列全 N。P1 需 14 字节替换 5 字节，无填充可覆盖 ⇒ 必须重链。

## 复跑命令（全部只读目标、只写本卡目录）
```bash
python -X utf8 lead\next_re_20261117_r14\W178_PATCH\work\explore.py
python -X utf8 lead\next_re_20261117_r14\W178_PATCH\work\analyze.py
python -X utf8 lead\next_re_20261117_r14\W178_PATCH\work\callee_space.py
python -X utf8 lead\next_re_20261117_r14\W178_PATCH\work\unit_test.py
python -X utf8 lead\next_re_20261117_r14\W178_PATCH\work\baseline.py
python -X utf8 lead\next_re_20261117_r14\W178_PATCH\work\make_deliverables.py
```

## 交付文件
`PROGRESS.md` / `CANDIDATES.md` / `PATCH_MAP.tsv` / `RISKS.md` / `UNKNOWNS.md` / `DISAGREE.md` / `coverage_delta.tsv`（表头） / `EVIDENCE\`（不截断） / `work\`（可复跑）。
