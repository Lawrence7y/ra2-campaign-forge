# W177 DISAGREE（与 PROBE_TABLE / 上游期望不符）

| # | 上游条目 | 上游期望 | 真机实测 | 分级 | 证据 |
|---|---|---|---|---|---|
| D1 | PROBE_TABLE O6 (`obj+0x520`) | 「指向 MapClass 类结构（非空）」 | 实为 **BuildingTypeClass\***：解引用后 `+0x24` 为类型 ID 串（YAPOWR / YACNST / CAAIRP / CATHOSP / YABRCK …），`+0x3d` 为 `Name:<id>`。非 MapClass。 | [已证] | `work\read_types.py`, `EVIDENCE\FINAL_TYPES.json`, `EVIDENCE\` 中 dump（type `0x10fb7058` 含 `CAAIRP`/`The Apartment`） |
| D2 | PROBE_TABLE O5 (`obj+0x30`) | 「格链 next，=链上下一对象地址」 | 全部 11–25 个 BuildingClass 的 `+0x30` 读数为 `0x0`。若确为 next，则每个建筑独占格链（无多对象格）；亦可能该偏移在此镜像不是格链 next。两解未区分。 | [未证]（读数已证，语义未定） | `EVIDENCE\FINAL_TYPES.json`(next 全 `0x0`) |
| D3 | PROBE_TABLE G1 (`0xA8B238`) | 「局内=5（暂停亦 5）」 | 遭遇战局内 =5 ✓；但**加载战役存档后 mode=0** 且 frame 正常递增、有 149 建筑 ⇒ mode=0 并非总是"菜单页族"。G1 判据需加限定。 | [已证] | `EVIDENCE\campaign_loaded` 快照(frame 递增 mode=0), `EVIDENCE\FINAL_SNAPSHOT.ndjson`(mode=5) |
| D4 | PROBE_TABLE O7 / O8 | 基址为 `*[obj+0x520]` | 因 D1（`+0x520` 非 MapClass），O7=`*[obj+0x520]+0xE58`、O8=`+0x1571` 的"短路门控"基址假设不成立；未观测到预期语义。 | [已证]（基址错） | 同 D1 |
| D5 | 卡正文「连续放置 ≥10 次」 | 可连续放置 10 次 NAPOWR | 净增 5 座；定点循环 33 次点击未逐次生建筑。实际次数 < 10，原因见 LIVE.md 归因说明。 | [已证]（未达标） | `EVIDENCE\PLACE_ALL.jsonl`, `EVIDENCE\PLACE_ALL2.jsonl`, `EVIDENCE\FINAL_TYPES.json` |

## 一致项（无分歧）
- O1(`+0x81`)：世界中=0、Limbo=1 —— 与 PROBE_TABLE 期望**一致**，实测确认。
- O2(`+0x74`)：在世界中=1、离链=0 —— 一致。
- G0/G2：frame 单调递增、objects>0 —— 一致。
- 卡候选假设均为猜测（纪律 11），以上实测独立判定，未先入为主。
