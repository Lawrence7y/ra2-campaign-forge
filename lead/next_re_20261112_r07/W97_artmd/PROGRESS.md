# W97 · PROGRESS

Card: `lead\next_re_20261112_r07\W97_artmd` — 裁掉 `TESLA` 底座尺寸的两卡矛盾。
只读；不启动游戏；不改 `ra2youli` 与别卡原件。

| 时间 (Get-Date) | 动作 | 结果 |
|---|---|---|
| 2026-11-14 17:01 | 建卡目录 + 读 `ra2forge/mixlib.py` 全文 | `MixFile(path)`；`get(filename)` 用 `crc_hash`/`classic_hash`；`names()` 是**存根**，只返回 `_%08X` |
| 17:03 | probe01：8 个 mix 的裸头 + `get()` 探针 | 全部 `get('artmd.ini'/'rulesmd.ini')` = `None`。**复现 Lead 的失败** |
| 17:05 | probe01 结论 | 不是 API 用错，是**这些 id 不是那几个文件名的 crc32**（见下） |
| 17:06 | probe02：枚举每个 mix 的全部 entry（id/size/首字节） | `expandmd01.mix` 有 `0x8218F9F4` = **743,215 B**，首行 `; RULE*.INI` ⇒ 就是 W89 的 `rulesmd_exp01.ini` |
| 17:08 | probe03：用 `expandmd98.mix` 的 ECH01/02/03.MAP 做哈希试金石 | `crc32(UPPER(name))` **逐字节命中**；但那 3 个是 ra2forge 自己写的 mix，不能证明零售 mix |
| 17:10 | probe04 | W89 的 `rulesmd_exp01.ini` 与 `expandmd01.mix:0x8218F9F4` **sha256 全等** ⇒ 该 entry 即规则文件；字典命中 `ISOTEMMD.MIX`/`TEMPERAT.MIX` ⇒ **方案仍是 crc32** |
| 17:12 | probe05：递归下钻（大 entry 的裸头是 `00 00 03 00` = 嵌套加密 MIX） | 顶层 `get('artmd.ini')` 全 miss ⇒ **artmd 在嵌套 mix 里**，`mixlib` 无递归能力 |
| 17:14 | probe06：取出两个含 `Foundation=` 的 INI | **拿到 artmd.ini**：`ra2md.mix → 0xFBE0D09D → 0x5B47D8D5`，336,535 B |
| 17:15 | probe06 读五个建筑 | `NAPOWR 3x2` / `NATSLA 1x1` / `NACNST 4x4` / `GAPOWR 2x2` / `GAPRIS 1x1` |
| 17:16 | 查 `rulesmd` 的 `[TESLA] Image=NATSLA`、`[ATESLA] Image=GAPRIS` | TESLA 的 art 节是 `[NATSLA]`；ATESLA 其实是「Allied Prism Cannon」⇒ `[GAPRIS]` |
| 17:18 | probe07：几何对账 | NAPOWR 3x2 → step2 重叠 **10**、step3 **0**（与 `§625-1` 的「10 格」逐格吻合）；TESLA 1x1 → **0**；TESLA 3x2 → **14**（正是 W95 的数） |
| 17:20 | probe08：读 C6 运行结论 | `outcome=VALID_WINDOW_target_reached`、`ok=true`、150 s、`A8ED50` 94.05 % |
| 17:22 | probe09：底座锚点约定敏感性 | `+x/-y` 约定下 W95 的 24→14 **完全复现** ⇒ 它算术没错，只是前提（3×2）错 |
| 17:24 | 定位台账 §625 / §630、W95 AUDIT 原文 | 取得逐句改前文本 |
| 17:26 | 复制 `w88_build.py` → 本卡并改成单常量 | 见 `EVIDENCE/w88_build_patched.py` + 对照表 |
| 17:28 | probe11：从 `gamemd.exe` 抽文件名串反查 archive id | 命中 100+ 条（`LOAD.MIX`/`ISOGENMD.MIX`/`BATTLEMD.INI`…）⇒ **hash 方案确是 crc32，mixlib 没用错** |
| 17:30 | probe12：`gamemd.exe` 自带 `'ARTMD.INI'`(0xAF902833) / `'RULESMD.INI'`(0x1F674573) | 引擎**按名字**找它们 |
| 17:32 | probe13：17 个顶层 mix + 一层嵌套的可达性普查 | 这两个 id **处处不存在**；loose 文件也全无 ⇒ 名字不是 `artmd.ini` |
| 17:34 | probe14：装饰名/NUL 终止/xor 恒定 检验 | xor 三个互不相同 ⇒ **换了名字**，不是换了种子 |
| 17:36 | probe15：证据清单 | art/rules key 普查证明取到的是 **art** 库（rules 键全 0） |
| 17:38 | `w97_mixget.py` 自检 | 恰好重新发现那两份 art 库 ⇒ 可复用取文件器成立 |
| 17:40 | `probe10` 对照表 + 守卫自测 | 修补前两臂皆 0（空检查）；修补后 step2=10、step3=0；守卫能判死 2×2 |
| 17:45 | 写 `FOUNDATION_RULING.md` / `UNKNOWNS.md` / `DISAGREE.md` | 交付完成 |

## 一句话结论

`TESLA` = **1×1**（`artmd.ini [NATSLA] Foundation=1x1`，sha256 `e1f03783…`）。W89 对，W95 的 3×2 前提错；
W95 的「14 格」是其错误前提下的**正确算术**（我逐格复现）。`§625-1` 的「NAPOWR 10 格」经我独立复算**逐格吻合**，不用改数字。

## 收官状态

- 交付：`FOUNDATION_RULING.md`（①-⑦）、`UNKNOWNS.md`（U1-U5）、`DISAGREE.md`（D1-D6）、本文件。
- 证据：`EVIDENCE/` 15 个 probe 脚本 + 全部 stdout + 取到的两份 art 库 + 工具修补件/原件。
- **只读确认**：`ra2youli` 未写；别卡原件未改（`w88_build.py` sha256 仍为 `A76D6A06…`）；未启动游戏、未注入。

