# W177 真机执行报告 · ②-b「建造重叠 10 格」验证

> 卡号 W177｜2026-11-17｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（未改）
> 全程只读 RPM/线程上下文 + 合成输入；无写内存/注入/Hook；无越界。

## 结论表

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| 1 | G0 frame `0xA8ED84` 单调递增、G1 mode `0xA8B238`=5、G2 objects `0xB0F730`>0 ⇒ 局内活跃 | [已证] | `EVIDENCE\FINAL_SNAPSHOT.ndjson`, `EVIDENCE\random_ingame_snap.txt` |
| 2 | BuildingClass 定位：AbstractClass::Array(基 `0xB0F720`, items `+4`, count `+0x10`) 中 `vt==0x7E3EBC`；命中建筑对象 | [已证] | `work\find_buildings.py`, `EVIDENCE\find_buildings_campaign.txt` |
| 3 | O1(`+0x81`)：世界中建筑恒 `0`；Limbo/不在世界恒 `1`。与 O2(`+0x74`) 反相（世界=1,离链=0）。多场景、多帧稳定复现 | [已证] | `EVIDENCE\FINAL_SNAPSHOT.ndjson`(o1_hist `{0:20,1:1}` 连续5帧), `EVIDENCE\FINAL_TYPES.json` |
| 4 | 成功放置的 NAPOWR：`+0x81=0`, `+0x74=1`（未出现 o1=1 的失败/离链电厂） | [已证] | `EVIDENCE\FINAL_TYPES.json`(6 个 YAPOWR 全 0/1/0), `EVIDENCE\PLACE_ALL.jsonl` |
| 5 | O6(`obj+0x520`) 实为 **BuildingTypeClass\***（+0x24 处是类型 ID 串 YAPOWR/YACNST/CAAIRP…），**否证** PROBE_TABLE「指向 MapClass」的假设 | [已证] | `work\read_types.py`, `EVIDENCE\FINAL_TYPES.json` |
| 6 | O5(`obj+0x30`) 在全部建筑读数为 `0`（链尾/单节点）；C1/C2(`cell+0xE4/E8`) 因未定位独立 CellClass 对象未读 | [未证] | `EVIDENCE\FINAL_TYPES.json`(next 全 `0x0`) |
| 7 | MCV 需按 D 部署成建造厂，sidebar 建造栏才出现 NAPOWR（磁能反應爐）图标；未部署时建造栏恒空 | [已证] | `EVIDENCE\mcv_deploy_sidebar.png` vs `EVIDENCE\random_ingame_wait.png` |
| 8 | 建造放置模式可激活（绿色建造光标/虚影可见） | [已证] | `EVIDENCE\napowr_ghost.png`, `EVIDENCE\ghost_try1.png` |
| 9 | 连续放置 NAPOWR ≥10 次：未达成。净新增 5 座（地址见核心数字），POINT 定点循环的 33 次点击未能逐次归因 | [未证] | `EVIDENCE\PLACE_ALL.jsonl`, `EVIDENCE\PLACE_ALL2.jsonl` |
| 10 | 「重叠 10 格」现象复现：未确认。无 crash/hang，except.txt 未变 | [未证] | `EVIDENCE\` 全量截图 |

## 核心数字（给审计）

- **[+0x81] 取值序列（O1）**：`0 → 0 → … → 0`（所有世界中建筑，含全部成功放置的 NAPOWR）；Limbo 建筑样本 `0x15eccf78`(YAYARD船坞)、早局 `0x14c99e90` 为 `1`。
  - 计算：`m.u8(obj+0x81)`，按 `AbstractClass::Array` 遍历；histogram 见 `FINAL_SNAPSHOT.ndjson` 的 `o1_hist`。
- **净放置 NAPOWR**：初始预置 1 座（`0x10cca370`），结束 6 座 ⇒ **净增 5 座**。新增地址 `0x1015d8f8 / 0x1015e040 / 0x1015eed0 / 0x1015fd60 / 0x10bfbf20`（前 4 个连号，典型连续放置分配特征）。
  - 计算：两次 `count_types.py` 的 `types.YAPOWR` 差分 + 对象地址集合比对。
- **重叠复现次数**：`0`（未观测到可归因的「放置落到已占用格」现象）。
- **格链长（C1/C2 展开）**：未取得；所有已定位 BuildingClass 的 `+0x30`=0（无法区分"链尾"与"该偏移非格链 next"）。

## 方法/纪律符合性
- 双通道：BuildingClass 定位用 vftable(`vt==0x7E3EBC`, R14 §2) + 类型 ID 串(`+0x24`) 两条独立通道，均不依赖 `function_atlas.tsv` entry+size。
- 未做静态反汇编定位，故 capstone/boundary_check 纪律不适用。
- 候选假设（PROBE_TABLE 期望值）均以实测证明/否证，未直接采信。

## 真机收尾
- 进程：`gamemd.exe`(pid 17316) 关闭；确认系统无残留进程。
- except.txt：长度 26272 B / mtime `2026-11-12T22:29:17Z`，**未变**（与开工前一致）。
- SHA-256：gamemd.exe `73201CC0…F67476`、ddraw.dll `85E0F7D5…83B03A9`，**均未变**。
- LIVE_LOCK：`RELEASED by W177`。
