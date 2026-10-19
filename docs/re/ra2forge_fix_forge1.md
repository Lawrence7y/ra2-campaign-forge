# ra2forge FORGE-1 修复报告：NextScenario 断链（P0）+ 打包方案 B + 文档/注释同步

> 任务卡 **FORGE-1** · 执行方 **DSH 子代理** · 工作区 `D:\Project\ra2-campaign-forge`
> 基线二进制 `ra2youli\gamemd.exe` MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`（**只读**，改动前后一致，LastWriteTime 2026/09/25 16:10:48 未变）
> 证据等级：[实证] = 文件:行 或 VA+原始字节（`tools/audit_bytes.py` 复算）；[推演]；[待实测]

---

## 0. 结论摘要

1. **P0 断链已修**：`builder` 现在按设计关卡顺序回填每张地图的 `[Basic] NextScenario`，并在**写盘后读回**断言（非末关为空即抛 `BuildError`，构建失败）。示例三关链 `ECH01.MAP -> ECH02.MAP -> ECH03.MAP -> 空` 已实证。
2. **打包改方案 B**：产出**散装 `BATTLEMD98.INI`**（自有战斗 ID `RA2F****`、`[Battles] 15=` 只**追加**，官方 `BATTLEMD.INI` 永不写入）；`expandmd98.mix` **0 个 INI**（只放地图）；安装对既有同名文件**强制备份**、卸载**完整还原**（清单驱动）。
3. **命名与注释统一**：代码/README/INSTALL 一律 `BATTLEMD98.INI`；`mixlib.py` 关于「通配经 XCC 数据库解析」的错误注释已改写为 **FS-only 通配 + MIX 内同名不被命中**。
4. **自建验证 51/51 PASS**（F4 四项 + 设计级 `next` 覆盖），复现脚本 `out/re_work/forge1/verify_forge1.py`，全部证据在 `out/re_work/forge1/`。
5. **最大风险（未闭环）**：`[Battles]` **索引**与**跨文件归并顺序**仍无真机实测（§6 U-FORGE1-1/U-FORGE1-2）；本机 `ra2youli\` 仍是旧版安装，需按 §5 迁移（**本任务未改动游戏目录任何文件**）。

---

## 1. 改动清单

| 文件 | 位置 | 改前 | 改后 | 目的 |
|---|---|---|---|---|
| `ra2forge/builder.py` | 全文重排（24.7 KB） | `_build_mission` 直接返回文本；`battle_lines` 写 `BATTLEMD.INI` 覆盖段；`mix_files["BATTLEMD.INI"]=...` | `build()` 先串链再输出；`mission_chain()` L121、`_verify_next_scenario_chain()` L142、`battle_id_for()` L196、`_battle_ini()` L206、`_verify_mix_contents()` L176、`BUILD_REPORT.txt` L492 | F1 关卡链 + 自检；F2 方案 B；F3 命名 |
| `ra2forge/install.py` | **新增**（11.8 KB） | 无（安装逻辑内联在 `cli.py`，只备份 mix） | `install_package()` L92 / `uninstall()` L154 / `_uninstall_legacy()` L210 / `preinstall_warnings()` L61；清单 `ra2forge_install.json`、备份后缀 `.ra2forge.bak` | F2 强制备份 + 完整还原 |
| `ra2forge/cli.py` | L12, L28-51, L87-119, L141 | `--install` 内联复制 `*.MAP/*.INI`，写 `ra2forge_uninstall.txt` | 新增 `install` / `uninstall` 子命令（`--legacy`、`--drop-legacy-battlemd`、`--force`）；`build --install` 复用同一安装器 | F2 卸载路径 |
| `ra2forge/cli.py` | L152-166 | `_load` 按 utf-8 读设计 JSON（带 BOM 的文件直接崩）；`inspect` 按 utf-8 读 GBK 地图（中文乱码）；`validate` 失败抛未捕获异常栈 | `utf-8-sig` 容忍 BOM；新增 `_read_map_text()`（UTF-8 -> GBK 回退）；`validate`/设计校验失败打印 `INVALID: ...` 并返回 1 | 顺手修的可用性问题（不改变产物） |
| `ra2forge/design.py` | L5-11, L78-86, L159-168 | 无 `next` 字段 | 可选 `"next": "<关卡名>"`（空串 = 到此结束）；越界/自指即 `DesignError`，提前结束给 warning | F1「或按设计指定」 |
| `ra2forge/maplib.py` | L8-10, L496 | 无读回解析器 | 新增 `read_basic_section()`；docstring 注明链由 builder 回填并读回自检 | F1 自检 |
| `ra2forge/mixlib.py` | L304-331, L332-345 | 注释称「BATTLEMD*/RULEMD* 通配经本数据库解析」 | 注释改为 **FS-only 通配**（`0x52CBA0`->`FindFirstFileA`、回退 `0x52CCCD`）+ **MIX 内同名不被通配命中** + 引擎根本不读该库（`0x5B44D5` 只做 CRC32）；`write_mix(..., include_database=True)` 新增开关 | F3 注释纠错 |
| `ra2forge/__init__.py` | L5, L8 | `__version__ = "0.1.0"` | `0.2.0`，公开 API 列出 `install` | 版本 |
| `README.md` | 快速开始 / 代码结构 / 格式依据 / 验证状态 | 「卸载 = 删 expandmd98.mix」；输出为覆盖式 | 新增 `install`/`uninstall` 用法、清单式安装说明、老用户迁移指引、`next` 字段说明、FORGE-1 自检证据 | F3 + F5 |
| `out/re_work/forge1/verify_forge1.py` | **新增**（22.9 KB） | — | F4 四项 + `next` 覆盖 + 5 个安装/卸载演练场景 | 验证 |
| `examples/demo_campaign.json` | **未改** | — | 用默认顺序自动串链，正好验证默认行为 | — |

---

## 2. 任务卡背景四条复核（逐条）

| # | 卡片说法 | 判定 | 证据（改动前） |
|---|---|---|---|
| 1 | `maplib.py:105 self.next_scenario=""`、`:214` 写 `NextScenario={...}`，builder 从未赋值 => 已装 `expandmd98.mix` 内地链为空 | **成立** [实证] | 旧产物三图 `[Basic] NextScenario=` 全空；旧哈希 `ECH01.MAP 14217B be2dd960...`、`ECH02.MAP 13597B 5af5f947...`、`ECH03.MAP 15482B 0fb0e01d...`（`docs/re/ra2forge_packaging_audit.md` §4.2） |
| 2 | 引擎只以 `FindFirstFileA` 通配 FS 上的 `BATTLEMD*.INI`（0x8261A8）+ 回退 `BATTLEMD.INI`（0x826198）；MIX 内 `BATTLEMD98.INI` 永不加载；`MixFileClass::Find` 只按 CRC32 命中 | **成立** [实证] | 本次复算：`0x52CBA0 = 68 A8 61 82 00`（push 0x8261A8）、`0x52CBA9 = FF 15 08 12 7E 00`（call [0x7E1208] = FindFirstFileA）、`0x52CCCD = 68 98 61 82 00`（push 0x826198）、`0x8261A8 / 0x826198` 字符串逐字节吻合（`out/re_work/forge1/audit_bytes_out.txt`，5/5 OK） |
| 3 | README 写 `BATTLEMD98.INI`，代码实际产出 `BATTLEMD.INI` | **成立** [实证] | 旧 `builder.py:83` 写 `BATTLEMD.INI`、`:87` 把同名副本塞进 mix；README 记 `BATTLEMD98.INI` |
| 4 | `mixlib.py:305-308`「通配经 XCC 数据库解析」注释与事实不符 | **成立** [实证] | 改前原文见 §3.4；引擎无 `local mix database` 字符串、MIX 查找只做 CRC32（0x5B44D5），且通配来自 `FindFirstFileA`（FS） |

**顺带确认的旧行为缺陷（已一并消除）**：旧安装把 `BATTLEMD.INI`（覆盖官方 `[ALL1]/[SOV1]` 段）散装写进游戏目录且**无备份**，卸载只删 mix => 官方战役列表永久被改（`docs/re/ra2forge_packaging_audit.md` §2.1/§2.4）。

---

## 3. 落地实现（方案 B 规格 -> 代码）

### 3.1 关卡链（F1）

- `builder.mission_chain()`：默认「下一关 = missions[i+1] 的 NAME.MAP」，末关空串；某关若写了 `"next": "ECH03"` 则跳转，写 `"next": ""` 则在此结束（`design.validate()` 负责校验目标存在、不自指）。[实证 `ra2forge/builder.py:121`、`ra2forge/design.py:78,159`]
- `MissionMap.next_scenario` 在**输出文本之前**赋值（`ra2forge/builder.py:73`），因此 `[Basic] NextScenario` 与实际 .MAP 一致。
- **构建期硬自检** `_verify_next_scenario_chain()`（`ra2forge/builder.py:142`）：把**磁盘上的字节**按 GBK 解码、用 `maplib.read_basic_section()` 解析 `[Basic]`，逐关断言：值 == 设计顺序要求；非末关的值必须落在本次产物地图集合内；不一致直接 `raise BuildError`（CLI 返回 1）——**断链不可能再被安静写出**。

### 3.2 战役注册：散装 `BATTLEMD98.INI`（追加语义，F2）

示例产物（`out/forge1_verify/build/钢铁残响/BATTLEMD98.INI`，374 B，sha256 `84242a0b9ede...`）：

```ini
; Generated by RA2 Campaign Forge - APPENDED campaign entry.
; The game scans the GAME DIRECTORY for BATTLEMD*.INI and merges the
; entries by battle id, so this file only ADDS a campaign; the official
; BATTLEMD.INI is left untouched. Delete this file to unregister.
[Battles]
15=RA2FD4D6

[RA2FD4D6]
CD=2
Scenario=ECH01.MAP
FinalMovie=
Description=钢铁残响（3关）血色黎明
```

- **自有 ID**：`RA2F<crc16(战役名)>`（本例 `RA2FD4D6`）——官方 `[Battles]` 的 ID 是 `ALL1/SOV1/ALL02...SOV07`，本 ID 与全部官方 ID、与官方使用的**索引 1..14** 都不冲突（脚本实测断言）。
- **只写追加段**：文件里**不出现** `[SOV1]/[ALL1]`，因此不会再改写官方条目（旧实现正是靠改写 `SOV1.Scenario` 挂载，靠目录枚举顺序取胜，属未定义行为）。
- 官方语义依据：`extracted/found_battlemd.ini:5-6` 原文 "Additional files that begin with BATTLE will augment this list"。

### 3.3 MIX 内容（F2）

- `expandmd98.mix` 现在**只装 3 张地图**（43360 B，sha256 `08ac82fa22ad...`）：`mixlib.write_mix(..., include_database=False)`。
- 两个理由 [实证+推演]：(1) 引擎通配是 FS-only，MIX 内 INI 是死代码；(2) `expandmd##.mix` 在 `ra2md.mix` **之前**装载 => 同 CRC 条目覆盖，若放 `local mix database.dat` 会**遮蔽官方**那份（外部工具用），故不再写入；引擎本身不读该库（无字符串命中，查找只做 CRC32）。
- 构建期自检 `_verify_mix_contents()`（`ra2forge/builder.py:176`）：重新打开产物，断言条目集合 == 地图名 CRC 集合，且没有任何名字以 .INI 结尾（写 INI 进 MIX 直接抛错）。

### 3.4 注释纠错（F3）

`ra2forge/mixlib.py:304-331` 改前：

```text
The game's BATTLEMD*.INI / RULEMD*.INI wildcard loading resolves file
names through this database, so mixes that rely on wildcard lookup must
ship one listing their file names.
```

改后要点：数据库只给 XCC/WAE 等外部工具枚举名字用，**引擎不读**（0x5B44D5 只做 CRC32 命中）；战役/规则列表走**文件系统** `FindFirstFileA("BATTLEMD*.INI")`（VA 0x8261A8，push 0x52CBA0；回退 0x826198，push 0x52CCCD）=> **MIX 内同名文件永不被该通配命中，只有游戏目录里的散装文件才行**。

### 3.5 安装 / 卸载（F2）

`ra2forge/install.py`（清单驱动）：

| 阶段 | 行为 |
|---|---|
| 安装前置检查 | 目标目录必须有 `gamemd.exe`；包目录必须有散装 `BATTLEMD98.INI`（否则报「旧版包，请重建」） |
| 残留告警 | (1) `BATTLEMD.INI` 带标记 `Generated by RA2 Campaign Forge` => 旧版覆盖告警并给出 `uninstall --legacy`；(2) 其它 `BATTLEMD*.INI` => 提示归并顺序由目录枚举决定；(3) `expandmd99.mix` 存在 => 提示 99 先于 98 装载；(4) 旧清单 `ra2forge_uninstall.txt` => 提示可一并清理 |
| 强制备份 | 每个被替换文件先复制成 `<名字>.ra2forge.bak`；**备份槽已被占用时不覆盖**（最早的那份原件优先），改成 kept 记录 |
| 清单 | 写 `ra2forge_install.json`（工具/版本/时间/包路径/逐文件 action+bytes+sha256+backup） |
| 卸载 | 读清单：sha256 与安装时一致才删（被外部改过则保留 + 告警，除非 `--force`）；随后用 .bak 原样还原并删掉备份；最后删清单 |
| 旧版清理 | `uninstall --legacy`：按旧清单逐条清理（地图/mix 删除并还原 .bak）；旧版 `BATTLEMD.INI` 覆盖**有备份则还原**，无备份则只告警不删（除非 `--drop-legacy-battlemd`，会移动到 `BATTLEMD.INI.ra2forge.removed.bak`）；清单已处理过的文件名不再二次删除 |

---

## 4. 验证证据（F4 四项 + 门禁）

复现脚本：`out/re_work/forge1/verify_forge1.py`（**不读不写 ra2youli/**，演练目录在 `out/forge1_verify/_rehearsal/`）

```bash
python -X utf8 out\re_work\forge1\verify_forge1.py      # -> summary: 51/51 PASS, 0 FAIL
python  tools\verify_anchors.py                        # -> 323/323 PASS
python  tools\audit_bytes.py out\re_work\forge1\claims_forge1.txt --verbose   # -> 5/5 OK
```

产物快照：`out/re_work/forge1/verify_console.txt`（327 行完整实录）、`verify_output.txt`（51 条断言）、`verify_anchors_out.txt`、`audit_bytes_out.txt`。

### 4.1 (1) 关卡链（读回自证）

```text
[PASS] F4-1 ECH01.MAP NextScenario='ECH02.MAP' (want 'ECH02.MAP') - Name='血色黎明' Player='Russians'
[PASS] F4-1 ECH02.MAP NextScenario='ECH03.MAP' (want 'ECH03.MAP') - Name='冰原伏击' Player='Russians'
[PASS] F4-1 ECH03.MAP NextScenario='' (want '') - Name='终结之火' Player='Russians'
[PASS] F4-1 ECH01.MAP chain target ECH02.MAP present in package
[PASS] F4-1 ECH02.MAP chain target ECH03.MAP present in package
[PASS] F4-1 raw bytes of ECH01.MAP contain NextScenario=ECH02.MAP
[PASS] F4-1 raw bytes of ECH03.MAP contain an empty NextScenario
```

产物地图体积随链值变化（旧->新）：`ECH01 14217->14226 B`、`ECH02 13597->13606 B`、`ECH03 15482->15482 B`（末关为空，体积不变，哈希与旧件一致 `0fb0e01d...`）——与「只多了 NextScenario 值」相符。

### 4.2 (2) MIX 条目清单不含 INI

```text
expandmd98.mix: 3 entries
  0x8067D343     14226 B  ECH01.MAP
  0xC7C7A993     13606 B  ECH02.MAP
  0xFAA78023     15482 B  ECH03.MAP
[PASS] F4-2 mix holds exactly the 3 map ids
[PASS] F4-2 no INI / name-database id in the mix - hits=[]
[PASS] F4-2 packed ECH01.MAP still carries the chain - 14226 B extracted
```

### 4.3 (3) 散装 `BATTLEMD98.INI` 与地图一致

```text
[PASS] F4-3 BATTLEMD98.INI exists loose (not only inside the mix)
[PASS] F4-3 [Battles] has exactly one entry - entries={'15': 'RA2FD4D6'}
[PASS] F4-3 battle id is a self-owned RA2F**** id - id=RA2FD4D6
[PASS] F4-3 battle entry Scenario=ECH01.MAP
[PASS] F4-3 battle entry carries a Description
[PASS] F4-3 no official section (ALL1/SOV1/...) is overridden - overrides=[]
[PASS] F4-3 the file holds no [ALL1]/[SOV1] text at all
[PASS] F4-3 battle id collides with no official id - official_ids=['ALL02'..'SOV07','ALL1','SOV1']
[PASS] F4-3 [Battles] index collides with no official index - official_indexes=['1'..'14']
```

### 4.4 (4) 备份 / 卸载演练（临时目录，前后文件清单）

5 个场景（清单原文见 `verify_console.txt`）：

| 场景 | 起始 | 动作 | 关键断言（全 PASS） |
|---|---|---|---|
| A | 干净目录：官方 `BATTLEMD.INI`(2733 B) + `expandmd99.mix` | install -> uninstall | 官方 `BATTLEMD.INI` 哈希前后**不变**；`expandmd99.mix` 不变；卸载后目录只剩 4 个原有文件、无 .ra2forge.bak；告警含 99 优先/官方文件未动 |
| B | 已有**用户自己的** `BATTLEMD98.INI` + `ECH01.MAP` | install -> uninstall | 两者各生成 .ra2forge.bak；安装后内容确被替换；卸载后用户文件**逐字节还原**，备份槽清空 |
| C | 旧版安装（散装覆盖式 `BATTLEMD.INI` + 旧清单 + 3 张散装地图 + mix + `expandmd98.mix.ra2forge.bak`） | `uninstall --legacy` | 散装地图删除；mix 由旧 .bak 还原；旧 `BATTLEMD.INI` 无备份 => 保留 + 告警（不静默删）；旧清单删除；备份槽清空 |
| D | 旧版覆盖且无备份 | `uninstall --legacy` -> `--drop-legacy-battlemd` | 第一次：保留并解释原因；第二次：移动到 `BATTLEMD.INI.ra2forge.removed.bak` |
| E | 旧版安装后**直接装新版**（不带 --legacy） | install -> uninstall | 4 个既有文件全部进入备份保护；告警含旧版覆盖与旧清单；卸载后**回到安装前状态**（`expandmd98.mix` 还原为**最早的**原始备份，即备份槽不被覆盖的语义） |

场景 A 原文摘录：

```text
BEFORE install:  BATTLEMD.INI 2733 B / expandmd99.mix 256 B / gamemd.exe / ra2md.mix
install 报告:    created BATTLEMD98.INI / created ECH01-03.MAP / created expandmd98.mix / written ra2forge_install.json
                 warning: expandmd99.mix exists: expandmd* mixes load in descending order, so 99 is loaded BEFORE 98 ...
AFTER uninstall: BATTLEMD.INI(2733 B, 与安装前同哈希) / expandmd99.mix / gamemd.exe / ra2md.mix
```

CLI 端到端（`out/forge1_verify/cli_e2e_out.txt`）：`build --install` / `install` / `uninstall` 三条命令跑通，装后目录多出 4 个产物文件 + 清单，卸后目录**与装前完全一致**。

### 4.5 CLI 冒烟（含顺手修的可用性问题）

```text
python -m ra2forge validate examples/demo_campaign.json          -> OK: 3 mission(s)
python -m ra2forge validate <带 BOM 的设计 JSON>                 -> OK: 3 mission(s)   （改前：JSONDecodeError: Unexpected UTF-8 BOM）
python -m ra2forge validate <next 指向不存在的关卡>               -> INVALID: missions[0].next 'NOPE' does not name a mission of this campaign ; exit=1（改前：未捕获异常栈）
python -m ra2forge inspect .../ECH01.MAP                        -> Name=血色黎明 / NextScenario=ECH02.MAP / Briefing=指挥官，同盟国...（改前：GBK 被当 UTF-8，中文乱码）
python -m ra2forge build --design examples/demo_campaign.json --out out/forge1_verify/cli_e2e --install <临时游戏目录>
python -m ra2forge uninstall --game <临时游戏目录>
  装后目录：BATTLEMD.INI(2733B 官方原件未动) + BATTLEMD98.INI(374B) + ECH01-03.MAP + expandmd98.mix + ra2forge_install.json
  卸后目录：BATTLEMD.INI(2733B) + gamemd.exe        <- 与装前完全一致
```

（命令与输出原文：`out/forge1_verify/cli_smoke_out.txt`、`out/forge1_verify/cli_e2e_out.txt`）

### 4.6 门禁原文

```text
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
* 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
----
0x52cba0   68 a8 61 82 00        OK   push 0x8261A8 -> "BATTLEMD*.INI"
0x52cba9   ff 15 08 12 7e 00     OK   call [0x7E1208] = FindFirstFileA
0x52cccd   68 98 61 82 00        OK   回退分支 push 0x826198 -> "BATTLEMD.INI"
0x8261a8   42 41 ... 49 4e 49 00 OK   "BATTLEMD*.INI\0"
0x826198   42 41 ... 49 4e 49 00 OK   "BATTLEMD.INI\0"
合计 5 条：OK=5  MISMATCH/NOREAD=0
```

---

## 5. 已安装用户迁移步骤（F5，**纸面步骤，本次未执行**）

> 适用对象：在 FORGE-1 之前装过 ra2forge 包的游戏目录（会看到散装 `BATTLEMD.INI` 被改写、3 张 `ECH0x.MAP` 断链、`expandmd98.mix` 内还塞着 `BATTLEMD.INI`）。

1. **先备份**：把游戏目录里的 `BATTLEMD.INI`、`ECH01-03.MAP`、`expandmd98.mix`、`expandmd98.mix.ra2forge.bak`、`ra2forge_uninstall.txt` 复制到游戏目录外的一份存档目录（人工保险）。
2. **清理旧安装**（在仓库内执行，`<游戏目录>` 换成真实路径）：`python -m ra2forge uninstall --game "<游戏目录>" --legacy`
   - 会删掉旧版散装地图 + 旧 mix（有 .bak 则还原成安装前的 mix）+ 删旧清单；
   - 旧版 `BATTLEMD.INI` 若**有** `.ra2forge.bak` 会自动还原；**没有**则只告警（因为那份被改写的文件就是官方列表，工具不能凭空造回官方内容），此时按第 3 步处理。
3. **还原官方战役列表**（仅第 2 步告警时）：
   - 首选：用游戏安装介质/整合包里的 `BATTLEMD.INI` 覆盖回去，或对游戏目录做一次「校验/修复」；
   - 次选：以 `extracted/found_battlemd.ini` 为模板重建 `[ALL1]/[SOV1]` 两条官方条目（**注意**：该样例含 RA2 调试占位条目 `ALL02...SOV07`，正式版未必相同，重建前先确认自己的发行版）；
   - 若只想让新包能跑、暂时不管官方列表：`python -m ra2forge uninstall --game "<游戏目录>" --legacy --drop-legacy-battlemd`（把旧覆盖改名保留为 `BATTLEMD.INI.ra2forge.removed.bak`，之后必须补回官方文件）。
4. **装新版**：`python -m ra2forge build --design examples/demo_campaign.json --out out --install "<游戏目录>"`
   - 现在产出散装 `BATTLEMD98.INI`（追加条目）+ 只含地图的 `expandmd98.mix`；安装器会给被替换文件留 `.ra2forge.bak` 并写 `ra2forge_install.json`。
5. **验收**：启动 `gamemd.exe` -> 单人游戏 -> 战役，官方两条战役按钮/列表**保持原样**，列表里**多一条**本战役；第 1 关通关应自动进第 2 关（NextScenario 生效）。
6. **回滚**：`python -m ra2forge uninstall --game "<游戏目录>"` => 逐文件还原到安装前；若要连第 2 步的旧版残留也回滚，直接用第 1 步的人工存档目录覆盖回去。

---

## 6. 未闭环清单

| ID | 缺口 | 为何无法静态闭环 | 下一步取证 | 级别 |
|---|---|---|---|---|
| U-FORGE1-1 | `[Battles]` **索引**语义：追加文件的 `15=RA2F****` 与官方 1..14 如何共存（是否要求连续/是否按值归并） | 需运行期 INI 合并逐指令跟踪 | 真机：目录里同时放官方 `BATTLEMD.INI` + 本 `BATTLEMD98.INI`，看战役列表条目；或在 0xA83CF8（全局战役表）下断观察索引处理 | **P1**（不挡交付；方案 B 的核心「按 ID 归并」已由前序实证） |
| U-FORGE1-2 | 多个 `BATTLEMD*.INI` 的装载顺序（FindFirstFileA 目录枚举序） | 依赖 NTFS 枚举顺序 | 真机：放两个同 ID 不同 Description 的散装文件对照 | P2（本方案刻意**不复用官方 ID**，故不受影响） |
| U-FORGE1-3 | 末关 `NextScenario=` 空 + `EndOfGame=no` 是否被引擎接受为「战役结束」 | 需运行期验证 | 真机打通第 3 关，观察是否回主菜单/卡死；对照官方末关 `EndOfGame=yes`（`extracted/yr_maps/map_133A0CB2.map:267`） | **P1** |
| U-FORGE1-4 | 新条目在战役 UI 中的落位（是否出现在固定双图标界面、条目名如何显示） | 需运行期验证 | 真机进「新战役」看列表 | **P1**（方案 B 的产品验收点） |
| U-FORGE1-5 | 通配大小写/短名（`BATTLEMD98.INI` 命中 `BATTLEMD*.INI`） | Win32 API 行为 | 真机改名对照 | P2 |
| U-FORGE1-6 | 旧版 `BATTLEMD.INI` 无备份时的「官方原文重建」 | 不知道用户发行版原文 | 与安装介质比对哈希 | P2（迁移步骤 §5.3 已给人工兜底） |

---

## 7. 风险与红线

| 红线 | 是否触及 | 说明 |
|---|---|---|
| (1) 同步语义 / 命令序 | **否** | 仅改本仓 Python 生成器与安装器；未改游戏代码、未注入、未改 exe（MD5 `4F37486E...` 前后一致） |
| (2) 随机数消费序 | **否** | 同上 |
| (3) 存档结构 | **否** | 产物只影响战役注册与地图内 `NextScenario` 文本；不新增/改动任何存档块 |
| (4) 渲染像素等价性 | **否** | 未触及渲染路径 |

安装路径变更对**已安装用户**的影响（本次唯一的破坏性面）：

1. 旧安装会在游戏目录遗留**被改写的官方 `BATTLEMD.INI`**（无备份）——新版安装器**不会**自动删它，只在安装时告警；必须按 §5.2/§5.3 迁移，否则「官方战役列表被改」这一状态会一直存在。
2. 新包的注册文件是**另一个文件**（`BATTLEMD98.INI`）。若用户只做「覆盖升级」而不清理旧的 `BATTLEMD.INI`，两个文件会被引擎同时归并：本战役**仍能启动**（自有 ID 不冲突），但官方 `[SOV1]` 仍被旧文件改写 —— 所以迁移的第 2/3 步不能省。
3. 本机 `ra2youli\` 属于上述第 1/2 类：**本任务未改动该目录任何文件**（MD5/LastWriteTime 与开工时一致），迁移动作留给用户决定。

---

## 8. 勘误 / 越界登记（**未获授权改写**，仅登记，交 Lead 处理）

| 目标文件:行 | 改前 | 建议改后 | 理由 | 影响面 |
|---|---|---|---|---|
| `mcp/ra2forge_mcp.py:65-69` | `tool_build()` 内联安装逻辑只复制 `expandmd98.mix`（方案 B 之前的行为） | 改为 `from ra2forge.install import install_package; install_package(mix.parent, install_dir)`，并打印 backup/warning | 现在「只放 mix」**不会**注册战役（注册靠散装 INI），MCP 通道会给出「装好了但游戏里看不到」的错觉 | MCP 用户；产品决策级 |
| `mcp/ra2forge_mcp.py:109` | 描述串已写 `BATTLEMD98.INI` | 保留，补「loose, appended」 | 文案与实现现已一致 | 文档 |
| `ra2opt/audit.py:175-180,456-461` | 以 `BATTLEMD.INI` 是否存在 / 其头部内容判定「ra2forge 战役包」 | 追加识别散装 `BATTLEMD98.INI`（`[Battles]` 内自有 ID） | 新版安装后 `BATTLEMD.INI` 不再存在，旧判定会漏报 | ra2opt 体检报告 |
| `ra2opt/tests.py:394-404,437-440` | 造 `BATTLEMD.INI` 假战役文件做「不改战役产物」回归 | 追加造 `BATTLEMD98.INI` | 覆盖新命名，回归更贴近现状 | 测试覆盖 |
| `docs/DESIGN.md` | 未提关卡链/`next` 字段与产物命名 | 增「关卡链与 next」「安装产物」两节 | 设计者文档缺新契约 | 设计者文档 |

（`README.md` 属本次授权范围内的产品 README，已直接更新，不列入勘误。）

---

## 9. 交付物清单

| 类别 | 路径 | 说明 |
|---|---|---|
| 产品代码 | `ra2forge/builder.py`（617 行）、`ra2forge/install.py`（286 行，新增）、`ra2forge/cli.py`、`ra2forge/design.py`、`ra2forge/maplib.py`、`ra2forge/mixlib.py`、`ra2forge/__init__.py` | F1~F3 |
| 文档 | `README.md`（更新）、`docs/re/ra2forge_fix_forge1.md`（本文件） | F3 / F5 |
| 验证脚本 | `out/re_work/forge1/verify_forge1.py` | F4，51 条断言 |
| 验证产物 | `out/re_work/forge1/verify_console.txt`（327 行完整实录）、`verify_output.txt`（51 条断言汇总）、`verify_anchors_out.txt`、`audit_bytes_out.txt`、`claims_forge1.txt`（5 条） | 证据 |
| 端到端产物 | `out/forge1_verify/build/钢铁残响/`（地图 x3、`BATTLEMD98.INI`、`expandmd98.mix`、`BUILD_REPORT.txt`、`INSTALL.txt`、`story.md`）、`out/forge1_verify/next_override/`、`out/forge1_verify/_rehearsal/{caseA..caseE}/`、`out/forge1_verify/cli_e2e_out.txt` | 可复算 |

---

## 10. 待裁决项

| # | 分叉 | 现状 | 建议 | 需谁决定 |
|---|---|---|---|---|
| R1 | 追加条目的 `[Battles]` 索引值 | 现用 15 | 保持；若 U-FORGE1-1 实测要求连续，则改为「官方最大索引 + 1」并在构建期读游戏目录现成文件（会牺牲确定性，需权衡） | Lead/用户 |
| R2 | 战役 ID 形态 | 现为 `RA2F<crc16>`（如 RA2FD4D6） | 保持（稳定、不可与官方冲突）；若希望人类可读，可在 design JSON 增自定义 ID 字段 | 用户 |
| R3 | 末关结束语义 | 现为 `NextScenario=` 空、`EndOfGame=no` | 建议真机验证后改为 `EndOfGame=yes`（官方末关即如此） | 用户（U-FORGE1-3） |
| R4 | 是否需要「图标挂载」兼容开关 | 方案 B 只追加条目、不占用 SOV1 | 若 U-FORGE1-4 显示追加条目在 UI 里不可达，再议「是否允许显式改写 SOV1」的开关（默认关闭） | Lead/用户 |
| R5 | MCP 通道修复归属 | 见 §8 第 1 条（越界，未改） | 建议开小卡片由有写权限的执行方改 `mcp/ra2forge_mcp.py` | Lead |
| R6 | 本机 `ra2youli\` 是否执行迁移 | 未动（只读） | 由用户按 §5 执行；建议顺序：备份 -> `uninstall --legacy` -> 补官方 `BATTLEMD.INI` -> 装新版 | **用户** |
