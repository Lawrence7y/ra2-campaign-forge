# VERSION_GUARD_CONTRACT.md · W38 / B 线（RE-N09）S1

> 卡：`W38_version_guard_s1`｜切片 **S1：版本守卫契约与写入口盘点**｜2026-11-13（Asia/Shanghai）
> 工作目录：`D:\Project\ra2-campaign-forge`｜**纯离线**：未启动 `gamemd.exe`、未 attach、未写 `ra2youli`、未改仓库 `ra2forge/`、未动 `W21`–`W37` 任何目录、`git` 只读、未写生产代码。
> 输入：`W36_b_line_kickoff\B_LINE_PLAN.md` §3.1/§4-S1、`DISAGREE.md` D1–D10、`UNCOVERED.md` U1–U21、`docs\re\NEXT_RE_TASKS_20261112.md` L272–L287（RE-N09 原文）、v11 = `lead\next_re_20261112_r02\W34_mapselmd\ra2forge_patched_v11\ra2forge\`（14 个 `.py`，`TOOL_VERSION="1.0"`，`__version__="0.3.0"`）。
> 交付性质：**契约与盘点，不是实现**。本卡不接线、不改 `install.py`、不新增回归脚本；实现属于 S2+。

## 0 · 结论分级与红线

| 标记 | 本卡口径 |
|---|---|
| `[本次实测]` | 本卡 `EVIDENCE\` 下只读脚本对当前盘面直接取得并核对（模块数 / `file:line` / 调用点 / stdout / exit code / git 快照 / 进程数） |
| `[本次读码]` | 本卡逐行读 v11 / `ra2opt` 源码、W36 文档、RE-N09 原文得到的代码事实 |
| `[静态推断]` | 由多项读码/盘面事实组合推出的契约规则与工程判定（本卡新增的规范） |
| `[转引]` | 来自 W36 / `FINAL_RULING.md` / 任务书的既有结论，本卡未独立复算 |
| `[待运行验证]` | 须真机/脚本/实算才能定谳；本卡未做 |

**红线（全卡适用）**

1. **不得写「已实现版本守卫」**。本卡只出契约与盘点。`[本次实测]` 结论：v11 全包 **0 处**构建身份判定调用；`install.py:1140` 只有 `(game/"gamemd.exe").is_file()`；`uninstall` 更弱，只有 `game.is_dir()`（`install.py:2184`）；`verify.py` 零写。
2. **不得把「回归全绿」写成「行为正确」**。盘上 `W34\out\SUMMARY.txt` = `cases: 51 passed: 51 failed: 0` / `462 passed / 0 failed` 是 `[转引]` + `[待运行验证]`（本卡**未复跑**），且 `W34\UNCOVERED.md` U9 明写沙箱内 `gamemd.exe` 是 inert 占位、从不执行 `[转引]`。
3. **`db264305…` 基线本身含 `.detour` 段**（Westwood Detours，原生），**不能当"干净零售金标准"** `[转引]`（W36 `B_LINE_PLAN.md` §3.1.1、`ra2opt\__init__.py:25` `[本次读码]`）。
4. 本机存在多个物理副本 ⇒ 任何判据必须绑定**绝对路径 + 该份字节**，不得用「本机那份 1.001」 `[转引]`（W36 §3.1.3 第 5 条）。
5. `TOOL_VERSION="1.0"` ≠ `__version__="0.3.0"`；仓库基线 `TOOL_VERSION="0.4"` ≠ `0.3.0` `[本次实测]`（`facts_check.stdout.txt` §3）。

---

## 1 · 契约范围、术语与写入口分类

### 1.1 术语 `[静态推断]`

| 术语 | 定义 |
|---|---|
| `TARGET_ID` | 一次判定的**输出**：`{state, baseline_id, identity_digest, edition_label, evidence, confidence}`。**不是** `ra2forge` 的 `package_id`（PKG-IDENT01）。 |
| `KNOWN_GOOD` | 全部 L1 强制判据可读、且与 `BASELINE.json` 中**恰好一条**已定谳条目逐字段精确相等（无宽匹配），且所有原始字节窗口匹配。 |
| `UNKNOWN` | 证据不足：无已定谳基线 / 任一 L1 判据不可读或缺失 / 多副本歧义未消解 / 无任何条目全字段吻合但无法证明"确定不是"。**包含 RE-N09 L278 的「未知镜像」**。 |
| `MISMATCH` | 有**正向证据**表明目标不是登记的那一份：某个已读 L1/L2 判据与声明的 `baseline_id` 冲突、原始字节窗口不符、或 `patched`/第三方 Detours 标志置位。**包含「已被其他补丁覆盖或入口窗不符」**（RE-N09 L278）。 |
| `DIR_INVALID` | L0 前置不满足（目录不存在 / `gamemd.exe` 缺失 / 路径越界）。不是身份三态，直接拒绝一切操作。 |
| `BASELINE.json` | 由 **Lead 定谳**后才可写入的已登记目标清单；S1 只给 schema 与取值方式，**不产出任何真实哈希基线** `[待运行验证]`（见 `UNCOVERED.md` U-W38-2）。 |
| 原始字节窗口 | 任一二进制 patch 写前的「改前 N 字节 + 改后 N 字节 + VA/RVA/FOFF」三元组（RE-N09 L278「入口窗不符」，`PROJECT_DIRECTION.md` L37 `[转引]`）。 |

### 1.2 写入口分类（决策表行） `[静态推断]`

| ID | 写入口 | 落点 | 当前 v11 实际入口 |
|---|---|---|---|
| `E1` | `install` / `build --install` 产物投放 | **游戏目录** | `install.install_package()`（`install.py:1821`；`cli.py:312` / `cli.py:326`） |
| `E2a` | `build` 产物输出（包目录） | 构建输出目录 `out\<Campaign>\` | `builder.build()`（`builder.py:63`） |
| `E2b` | `build --csf-out PATH` 任意路径副作用 | **用户给定路径；若落在游戏目录内即等价于 E1** | `builder._emit_csf_artifacts()`（`builder.py:418`）→ `csf.write_csf` / `csf.append_or_set_label` |
| `E3` | `uninstall` / 还原路径 | **游戏目录** | `install.uninstall()`（`install.py:2155`）、`install._uninstall_legacy()`（`install.py:2502`） |
| `E4` | `verify` 修复类动作（未来 `--fix` / seal 自愈） | **游戏目录** | **当前不存在**：`verify.verify_install()` 零写（`verify.py:107-306`，docstring L111「Never writes, never deletes」）`[本次实测]` |
| `E5` | `verify` / `inspect` / `audit` 只读 | 无写 | `verify_install()`、`cli.py:372-382`、`cli.py:384-400` |
| `E6` | `ra2opt apply / restore / seed --verify`（**XCHAIN 补充，非 v11**） | 游戏目录 / `.ra2opt` 备份区 | `ra2opt\optimize.py:112`、`ra2opt\backup.py:158` / `:307`、`ra2opt\cli.py:304` `[本次读码]` |

> **路径归属规则** `[静态推断]`：任何写目标经 `realpath` + `commonpath` 解析后落在任一已识别游戏目录内，即按 **E1/E3 级**处理，不得因「它是 build 子命令」而降级为 E2a。`--csf-out` 与 `example <path>` 均受此规则约束。

---

## 2 · 判据清单（每判据：取值方式 / 判别力 / 失效风险 / 成本）

> 成本口径 `[静态推断]`：`1R` = 一次顺序全文件读（4.8 MB 级），`1P` = 一次 PE 头/节表解析，`1M` = 一次 MIX 索引解析 + 条目抽取，`1V` = 一次 VS_VERSION_INFO 资源读取；实机耗时 `[待运行验证]`，本卡不编造毫秒数。
> 「单独放行」列：`否` 表示该判据**不得单独作为放行依据**，只能作描述/线索/组合项。

### 2.1 七项必列判据

| # | 判据 | 取值方式 | 判别力 | 失效风险 | 成本 | 单独放行 |
|---|---|---|---|---|---|---|
| C01 | **镜像整文件 SHA-256**（`gamemd.exe`） | `Get-FileHash -Algorithm SHA256 <abs>` / `hashlib.sha256(Path.read_bytes())`；同时登记**字节数**与**绝对路径**（RE-N00 L100 `[转引]`）。v11 `install.sha256_of()`（`install.py:698`）已有等价实现 `[本次读码]` | 精确标识「**这一份具体字节**」；能发现任何 1 字节改动（LAA/栈/堆改头、资源节改写、加壳、重打包、Detours 注入） | 任一 PE 头改动即变值 ⇒ **同一引擎版本有多个合法整文件哈希**；`db264305…` 本身含 `.detour`；本机多副本；不能区分发行版/语种；不能当「干净零售」判据 | `1R` | **否**（必须与 C02/C04/C13 同登记） |
| C02 | **`.text` 段 SHA-256** | 用**同一 PE 解析口径**取 `.text` 的 `raw_offset/raw_size`，对这段原始字节算 SHA-256。现成先例：`ra2opt\pe.text_section_sha256()`（`pe.py:364-380`）、`ra2opt\game.identity()`（`game.py:104-124`），`KNOWN_GAMEMD` 以该值为键（`__init__.py:19-27`）`[本次读码]` | **主判据**：标识引擎代码版本；LAA/栈/堆只改 PE 头，代码段不变 ⇒ 打完 ra2opt 补丁仍可认出版本 `[本次读码]` | ① 代码级 hook / syringe / Ares / Phobos / 第三方 Detours 改 `.text` ⇒ 失配；`game.py:120-121` 只能回落「未知（被第三方 Detours 补丁改过）」`[本次读码]`；② 同一代码段可对应不同语种/发行版/资源包 ⇒ **不能区分发行版**；③ 段范围定义随 PE 解析实现而异，必须固定口径 | `1P + 1R(.text)` | **否**（与 C01/C04 组合） |
| C03 | **PE 时间戳 `TimeDateStamp`** | `IMAGE_FILE_HEADER.TimeDateStamp`（`e_lfanew+0x08`）；`ra2opt\pe.PEInfo.timestamp` 已解析（`pe.py:85`）`[本次读码]`；W36 记「签名时间 2001-10-31」`[转引]` | **仅描述性元数据**：可提示构建批次、排查「为何整文件哈希不同」 | 可任意伪造（链接器开关 / 手工改字段）；可复现构建使不同产物同戳；同戳可跨语种/发行版；与「是否被补丁改过」无关 | `1P`（已含在 C04 解析内） | **否** |
| C04 | **`SizeOfImage` / 节表特征** | `pe.PEInfo`：`size_of_image`、`number_of_sections`、`entry_point`、`image_base`、`checksum`、`characteristics`、`dll_characteristics`、`stack_reserve/heap_reserve`、每节 `{name, VA, virtual_size, raw_offset, raw_size, characteristics}`（`pe.py:80-101`）；特别登记 **`.detour` 有无**、`has_detour_section`（`game.py:54`）`[本次读码]` | 中–高：能区分「是否含第三方 Detours 段」「PE 头是否被改过」「节布局是否同一构建」；`SizeOfImage` 与节表组合可排除「只改头字段」的伪差异 | 加壳/重打包/新增节会改布局；合法 1.001 本身就带 `.detour` ⇒ **有 `.detour` ≠ 被污染**；单独看 `checksum` 会被加载器忽略（`pe.py:29-30`）；不同 PE 解析器对节的口径可能不同 | `1P` | **否**（L1 组合项） |
| C05 | **`RA2MD.INI` 结构特征** | 读 `ra2md.ini` / `ra2.ini`（`install.py:748` 注释仅提及路径安全 `[本次读码]`），记录「节名集合 / 键名集合 / 键值类型与取值范围 / 字节数 / 全文 SHA」；`ra2opt\inifile.IniFile.load()` 可解析 `[本次读码]` | **低**：仅能判「配置兼容性」与「本轮基线是否被逐字节还原」（HANDOFF §5 每趟还原 `[转引]`） | 用户可编辑、随分辨率/渲染后端/`maxfps`/音频/限帧变化（W36 §3.1.1 `[转引]`）；同一镜像有多份合法配置；**配置项集合不能区分哪个 exe / 哪个发行版**；它是每趟要还原的**可写配置**，不是只读身份凭据 | `1R`（小文件） | **否**（不参与身份判定） |
| C06 | **关键文件存在性** | `(game/"gamemd.exe").is_file()` 等；v11 唯一现存实现 `install.py:1140-1143`；`uninstall` 只 `game.is_dir()`（`install.py:2184`）；`cli.py:246` 明写 verify「`gamemd.exe` is NOT required」`[本次实测]` | **最弱**：只能判「能否开始只读检查」 | 复制几个文件名即可伪造；不区分版本/语种/是否被改；「有 `gamemd.exe`」连「是不是尤复」都不能严格证明；`verify` 故意不要求它 ⇒ 存在性与「可写操作」无必然联系 | `0`（stat） | **否**（仅 L0 目录有效性前置） |
| C07 | **`ddraw.dll` 身份** | 全文 SHA-256 + 字节数 + VS_VERSION_INFO 版本资源 + `pe` 节表 + `components()` 的 `cnc_ddraw/ddraw_ini/xwis/ares/phobos/syringe` 标志；现成 `ra2opt\game.ddraw_version()`（`game.py:144-148`）、`components()`（`game.py:127-142`）`[本次读码]`；任务书 L83-85 登记 `ddraw.dll`=`85e0f7d5…` `[转引]` | 中：能区分「官方 ddraw / cnc-ddraw / 其它 wrapper 版本」，是 L2 发行版标签的重要输入；能发现「渲染层已被别的工具改过」 | 可被任意替换/升级/删除；不同 cnc-ddraw 版本很多；同一 `ddraw.dll` 可配不同 `ddraw.ini`；**不能证明引擎 exe 身份**；与 C01/C02 无必然绑定 | `1R + 1V` | **否** |

### 2.2 补充判据（L2/L3，用于补强与消歧） `[静态推断]`

| # | 判据 | 取值方式 | 判别力 | 失效风险 | 成本 | 单独放行 |
|---|---|---|---|---|---|---|
| C08 | 字节数 / `size` | `stat().st_size`；`KNOWN_GAMEMD` 记 `size=4825360`（`ra2opt\__init__.py:22`）`[本次读码]` | 低但必要：与 C01 一起排除「同哈希前缀/截断」歧义 | 可人为填充/截断；必须精确相等 | `0` | 否（L1 组合） |
| C09 | `ra2md.mix` / `langmd.mix` 内关键条目字节哈希 | MIX 索引解析（v11 `mixlib.MixFile`，`mixlib.py:241-308`）后抽取 `MAPSELMD.INI`、`ra2md.csf` 等条目全文 SHA-256 `[本次读码]` | 中–高：区分语种/发行版/资源包（W36 §3.1.1 建议项 `[转引]`） | 用户/其它 mod 可替换 MIX；需固定「哪个 MIX、哪条条目、哪种哈希口径」；`expandmd99.mix` 会遮蔽 98（`install.py:1003-1008`）`[本次读码]` | `1M + 1R(条目)` | 否 |
| C10 | `ra2md.csf` / 散装 `MAPSELMD.INI` 全长哈希 | 官方 `MAPSELMD.INI` 5,573 B、`ra2md.csf` 5,211 标签（`mapselmd.py:187-199` 已对 bundled 官方 INI 做全文 SHA 校验 `[本次读码]`） | 中：能发现 whole-file 被替换/最小化（W34 D4 `[转引]`） | 散装 vs MIX 内同名哪个生效**未真机定谳** `[待运行验证]`（W30/W34 `UNCOVERED.md` `[转引]`）；因此只能作 L2 描述，不能作 L1 放行 | `1R`（小文件） | 否 |
| C11 | `present_exes()` / `components()` 集合 | `ra2opt\game.py:99-142` `[本次读码]` | 中：识别「已装 ra2opt / cnc-ddraw / Ares / Phobos / syringe」等第三方态 | 组件名可伪装；集合随用户安装变化；不能证明 exe 字节 | `0`（目录枚举） | 否 |
| C12 | **原始字节窗口** | 写前读目标文件 `N` 字节（按 `VA/RVA/FOFF` 定位），记 `{before_sha256, after_sha256, n, rva, foff, va}`；`ra2opt\optimize.py:230, 255-258` 已有「先 `pe.read` 再只改需要字段」的模式 `[本次读码]` | **高**：直接对应 RE-N09 L278「入口窗不符均拒绝」；能发现「已被其它补丁覆盖」 | `N`、对齐、编码未固定则口径不一致；只适用于二进制 patch，对文件级 whole-file 覆盖需改用「目标全文 SHA」形式 | `1R`（局部） | 否（写前强制项） |
| C13 | **绝对路径 + 副本标识** | `os.path.realpath()` + `commonpath` 越界拒绝（`ra2opt\safewrite.py:40-53` 已有先例 `[本次读码]`）；记录绝对路径、卷标、该份 C01 值、`observed_at` | 消除「本机多个物理副本」歧义（W36 §3.1.3 第 5 条 `[转引]`） | 路径可重命名/替换；须每次写入口调用前重算（任务书 L79「后续执行前仍须重新比对」`[转引]`） | `0` | 否（强制绑定项） |

### 2.3 判据分层 `[静态推断]`

| 层 | 内容 | 输出 | 作用 |
|---|---|---|---|
| **L0** | C06 + C13（目录有效性、路径规范化） | `DIR_OK / DIR_INVALID` | 只允许进入只读检查；**绝不作身份放行** |
| **L1（强制，全部登记）** | C01 + C02 + C04 + C08 + C13（整文件 SHA / `.text` SHA / 节表+SizeOfImage / 字节数 / 绝对路径） | `TARGET_ID` 候选 | 与 `BASELINE.json` **逐字段精确比对**，任一不符/不可读 ⇒ `UNKNOWN` 或 `MISMATCH`，**禁止宽匹配** |
| **L2** | C07 + C09 + C10 + C11（`ddraw.dll` / MIX 条目 / CSF·MAPSELMD 全长 / 组件集合） | `EDITION_LABEL` | 发行版 / 语种 / 第三方态；冲突时不改变 L1 结论，只影响标签与 `MISMATCH` 原因码 |
| **L3（弱，仅描述）** | C03 + C05（PE 时间戳 / `RA2MD.INI` 结构） | 元数据 | **C03 / C05 / C06 明确标「不得单独放行」**；C05 只用于「本轮配置是否逐字节还原」 |
| **写前附加** | C12（原始字节窗口） | `WINDOW_OK / WINDOW_MISMATCH` | 任何二进制 patch 写前必须比对；不符 ⇒ `MISMATCH` + `ORIGINAL_BYTE_WINDOW_MISMATCH` |

---

## 3 · 判定算法（可执行规格，非散文） `[静态推断]`

```
classify(game_dir, baseline_json, declared_baseline_id, criteria_cache=None) -> GuardVerdict

 0  ev = collect_l0(game_dir)                    # C06 + C13
    if not ev.dir_ok: return verdict(DIR_INVALID, ["GAMEMD_ABSENT"/"DIR_INVALID"],
                                     write_allowed=False)

 1  ev = ev + collect_l1(game_dir)               # C01,C02,C04,C08  MUST be readable
    missing = [c for c in L1_REQUIRED if ev[c].obtained is False]
    if missing: return verdict(UNKNOWN, ["CRITERION_MISSING"]+missing,
                               write_allowed=False)          # 不得沉默放行

 2  entries = [e for e in baseline_json.entries if e.adjudicated is True]
    if not entries: return verdict(UNKNOWN, ["NO_ADJUDICATED_BASELINE"], ...)

 3  exact = [e for e in entries if all(ev[c] == e.identity[c] for c in L1_FIELDS)]
    if len(exact) == 1 and window_ok(ev): return verdict(KNOWN_GOOD, [],
                                     baseline_id=exact[0].id, write_allowed=True)
    if len(exact) >  1: return verdict(UNKNOWN, ["MULTI_COPY_AMBIGUOUS"], ...)

 4  # 有正向冲突证据 ⇒ MISMATCH
    if declared_baseline_id is not None:
        b = find(entries, declared_baseline_id)
        conflicts = [c for c in L1_FIELDS+L2_FIELDS if ev[c].obtained
                     and ev[c].value != b.identity[c].value]
        if conflicts or not window_ok(ev):
            return verdict(MISMATCH, ["TEXT_SHA_MISMATCH"/"FULL_SHA_MISMATCH"/
                                      "SECTION_TABLE_MISMATCH"/"ORIGINAL_BYTE_WINDOW_MISMATCH"
                                      ...] , write_allowed=False)

 5  return verdict(UNKNOWN,
        ["NO_BASELINE_MATCH","EDITION_UNKNOWN","BASELINE_NOT_ADJUDICATED" ...],
        write_allowed=False)
```

**硬规则**：

- `KNOWN_GOOD` 要求 L1 **全字段可读且精确相等**；不得用前缀/模糊哈希/文件名/旧哈希替代。
- `MISMATCH` 与 `UNKNOWN` **都拒绝一切游戏目录写入**；差别只在原因码与是否允许 `--force-unknown` 只读降级。
- `DIR_INVALID` 直接拒绝，连 `verify` 只读也不进入（避免对错误目录出报告）。
- 每次写入口调用**重新实算** L1，不复用缓存（`任务书 L79` `[转引]`）。
- `patched` 标志（`ra2opt\game.py:122`）或 `has_detour_section` 且基线声明「不含第三方段」 ⇒ 直接 `MISMATCH` + `PATCHED_BY_THIRD_PARTY`。
- `BASELINE.json` 每条必须带 `provenance`（来源、是否含 `.detour`、由谁在何时定谳）；`db264305…` 的 `provenance` 必须显式写「含原生 `.detour` 段，非干净零售金标准」。

---

## 4 · 决策表（三态 × 每个写入口：允许什么 / 拒绝什么）

`[静态推断]`；`allow` / `deny` 均为**穷举动作类**，不是示例。机器可检实例见 §6.2。

| 写入口 | `KNOWN_GOOD` | `UNKNOWN` | `MISMATCH` |
|---|---|---|---|
| **E1 install / `build --install` 产物投放** | **允许**：备份槽写入、`*.MAP`/`BATTLEMD98.INI`/`MAPSELMD.INI`/`expandmd98.mix` 原子替换、`ra2forge_install.json`、`…seal`、孤儿清理；**前提**：全部写前的 C12 窗口/目标全文 SHA 匹配。**拒绝**：任何未登记目标文件、越界路径、已释放冲突类之外的静默覆盖 | **拒绝全部游戏目录写入**（零写入，含 stage 临时文件、备份槽、清单/seal）；允许 `verify`/`inspect`/`audit` 只读；允许把产物输出到**隔离沙箱目录**并标 `UNKNOWN`；`--force-unknown` **不得**放行 E1；退出码 `20` + 原因码 | **拒绝全部写入**（零写入）；`--force-unknown` 直接拒绝（`21`）；输出「哪个判据与哪条基线冲突」；禁止 `--allow-content-conflict` / `--force` / `--adopt-legacy` 影响本判定 |
| **E2a `build` 产物输出（包目录）** | 允许（`out\<Campaign>\` 全部产物） | **允许**（构建期不落游戏目录），但产物必须打 `guard_state=UNKNOWN` 标签，`BUILD_REPORT.txt` 增加「目标未定谳，禁止投放游戏目录」条目；不得声称「已可安装」 | **允许**构建产物，但同上打 `guard_state=MISMATCH` + 禁止投放；若 `--install` 同时给出 ⇒ 整体按 E1 拒绝 |
| **E2b `build --csf-out PATH`（任意路径副作用）** | 允许**当且仅当** `PATH` 经 realpath 解析**不落在任何游戏目录内**；若落在游戏目录内 ⇒ 按 E1 全流程（含 C12）处理 | **拒绝**：禁止写 `PATH`（含 `p.parent.mkdir()`、stage、`os.replace`），除非 `PATH` 明确落在隔离沙箱且显式 `--allow-sandbox-write`；`--force-unknown` 不得放行；退出 `20` | **拒绝**：整体拒绝该写点，即使 `PATH` 在包目录也拒绝（保守，避免「构建期就能污染目标」）；退出 `21` |
| **E3 uninstall / 还原路径** | **允许**：按已验 seal 的清单删除/还原、移除备份槽、移除记录与 seal；**前提**：`evaluate_seal()` 为 `ok`，且每个目标文件全文 SHA 与清单一致或用户显式 `--force`（只释放「已变更文件」，不释放 seal 门）；**拒绝**：清单/seal 不匹配对上的任何删除或还原、越界名、alias 槽 | **拒绝全部删除/还原/记录移除**（零写入）；允许只读 `verify` 并标 `UNKNOWN`；**不**因「UNKNOWN 所以保守还原」而执行还原 —— 还原本身也是写；退出 `20` | **拒绝全部写**（零写入）；退出 `21`；原因码含冲突判据；**不**允许 `--force`/`--legacy` 越过 |
| **E4 `verify` 修复类动作（未来 `--fix` / seal 自愈）** | **允许**，但必须作为**新的注册写入口**接入 §6.1 `WriteEntryPolicy`，并在写前重跑 L0–L2 + C12；`verify` 默认仍只读 | **拒绝**任何 `--fix` 写；只读 `verify` 允许并必须标 `UNKNOWN` | **拒绝**任何修复写；只读 `verify` 允许并标 `MISMATCH` |
| **E5 `verify` / `inspect` / `audit` 只读** | 允许，报告 `guard_state=KNOWN_GOOD` | 允许，报告**必须**含 `guard_state=UNKNOWN` + `missing_criteria[]` + 全部已读判据值；**禁止**输出 `OK` / `installed` / `no drift` 之类可能读作放行的措辞；`--force-unknown` 仅在此处生效（记录到 `guard_report.json`） | 允许，报告 `guard_state=MISMATCH` + 冲突详情；`--force-unknown` 在此处也**不**生效 |
| **E6 ra2opt `apply` / `restore` / `seed --verify`（XCHAIN）** | 允许（且 `apply` 必须先把 `identity()` 接进零写预检；当前**未接** `[本次读码]`） | 拒绝 `apply` / `restore` / `seed` 的全部写；`status` / `audit` 只读允许并标 `UNKNOWN` | 拒绝全部写；`seed --verify` 的 `expected`（`KNOWN_GAMEMD` 的 `full_sha256`）冲突 ⇒ `MISMATCH` + 原因码 |

**跨态不变式** `[静态推断]`：

- `UNKNOWN` / `MISMATCH` 下，**E1/E2b(游戏目录)/E3/E4/E6 的写入字节数必须为 0**（可由 fsdiff / 目录快照机检，见 `ACCEPTANCE.md` A1/A3）。
- 任何 `-force`、`--allow-content-conflict`、`--adopt-legacy`、`--legacy`、`--drop-legacy-battlemd` 都**不得**改变 `guard_state` 判定；它们只作用于 `KNOWN_GOOD` 下的既有业务门禁。
- `verify` 必须保持只读；`E4` 一旦实现即为新写入口，必须重新走本表。

---

## 5 · 降级策略：判据不足不得沉默放行 `[静态推断]`

| 规则 | 内容 |
|---|---|
| **R1 全判据强制** | L1（C01/C02/C04/C08/C13）**全部**为必读项；任一不可读/缺失 ⇒ `UNKNOWN`，**不得**因「其余判据都匹配」而判 `KNOWN_GOOD`。 |
| **R2 禁止宽匹配** | 禁止哈希前缀、模糊匹配、「文件名对得上」、「看起来像游戏目录」、旧哈希回退、`--force` 放行身份。`UNKNOWN` 就是 `UNKNOWN`。 |
| **R3 写全拒** | `UNKNOWN` ⇒ 拒绝 E1/E2b(游戏目录)/E3/E4/E6 一切写；零写入；输出 `TARGET_ID=UNKNOWN` + `missing_criteria[]` + 实际读到的**全部**判据值 + `reason_codes[]`。对应 RE-N09 L278「未知镜像…均拒绝，并给出原因」。 |
| **R4 只读降级** | 允许 `verify` / `inspect` / `audit` / `status` 只读，但报告必须带 `guard_state=UNKNOWN`、`verdict_evidence`、`missing_criteria`，且不得出现可被读作「已放行/已安装」的措辞；构建产物只允许落在**隔离沙箱目录**并打 `UNKNOWN` 标签。 |
| **R5 `--force-unknown`** | **只允许只读降级**，**不允许任何游戏目录写入**。必须显式传入、必须写入 `guard_report.json`（flag / 操作者 / 时间 / 判据快照 / 原因）；未传时只读命令虽可运行但不得声称已定谳。`MISMATCH` 下该 flag **直接拒绝**（exit `21`），`DIR_INVALID` 下亦拒绝。 |
| **R6 上报 Lead** | 生成 `guard_report.json`（§6.1）到**本卡/S2+ 自己的写域**，不写游戏目录；`reason_codes` + 全部已读判据 + 缺失清单 + 绝对路径 + 该份 C01。Lead 定谳后才可向 `BASELINE.json` 追加条目；未定谳前版本矩阵该行标 `[待运行验证]`。 |
| **R7 多副本歧义** | 必须显式 `--target-dir <realpath>` + `--baseline-id`；否则 `UNKNOWN` + `MULTI_COPY_AMBIGUOUS`。禁止「本机那份 1.001」式无路径指代。 |
| **R8 基线非金标准** | `db264305…` 的 `provenance` 必须声明「含原生 `.detour` 段」；**不得**以「分析镜像 = 官方未修改原版」为前提（任务书 L89 `[转引]`）；`has_detour_section` 为真本身不构成 `MISMATCH`，只有与基线 `provenance` 冲突才构成。 |
| **R9 每次重算** | 每个写入口调用前重新实算 L1 + C12，不复用上次结果（任务书 L79 `[转引]`）；缓存只允许用于只读展示且必须带 `observed_at`。 |
| **R10 原始字节窗口** | 任何二进制 patch 写前比对 `before_N` 并保存 `after_N` + VA/RVA/FOFF；不符 ⇒ `MISMATCH` + `ORIGINAL_BYTE_WINDOW_MISMATCH`，零写入。 |
| **R11 退出码（S2 预留）** | `20 = GUARD_UNKNOWN`、`21 = GUARD_MISMATCH`、`22 = GUARD_DIR_INVALID`、`23 = GUARD_EVIDENCE_INCOMPLETE`。**与 v11 现有 0–10 不冲突**（`install.py:405-416`、`cli.py:27` `[本次读码]`）；本卡不改动 CLI。 |
| **R12 不声称行为正确** | 本契约只判「这份字节是不是登记的那份」；`KNOWN_GOOD` **不等于**「补丁行为正确/游戏行为正确」，也不等于「回归全绿」。安装态/执行态/行为态三态证据属 S4/S5。 |

---

## 6 · 机器可检形式（供 S2/S3 直接引用）

### 6.1 JSON Schema（draft 2020-12，`$defs` 可分拆落盘）

完整可解析副本：`EVIDENCE\guard_contract_schema.json`；示例实例：`EVIDENCE\guard_contract_example.json`；结构自检脚本：`EVIDENCE\shape_check.py`（均**只读/数据，不是生产代码**）。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ra2-campaign-forge.local/schema/w38-s1/version-guard.json",
  "title": "W38-S1 Version Guard Contract",
  "$defs": {
    "sha256Hex": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
    "criterion": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "obtained", "value", "source"],
      "properties": {
        "id": { "type": "string", "enum": ["C01","C02","C03","C04","C05","C06","C07","C08","C09","C10","C11","C12","C13"] },
        "obtained": { "type": "boolean" },
        "value": { "type": ["string", "integer", "boolean", "null", "array", "object"] },
        "source": { "type": "string" },
        "observed_at": { "type": "string" },
        "abs_path": { "type": "string" }
      }
    },
    "l1Identity": {
      "type": "object",
      "additionalProperties": false,
      "required": ["c01_full_sha256","c02_text_sha256","c04_size_of_image","c04_sections","c08_size","c13_abs_path"],
      "properties": {
        "c01_full_sha256": { "$ref": "#/$defs/sha256Hex" },
        "c02_text_sha256": { "$ref": "#/$defs/sha256Hex" },
        "c04_size_of_image": { "type": "integer", "minimum": 1 },
        "c04_number_of_sections": { "type": "integer", "minimum": 1 },
        "c04_has_detour_section": { "type": "boolean" },
        "c04_sections": {
          "type": "array",
          "items": {
            "type": "object", "additionalProperties": false,
            "required": ["name","virtual_address","virtual_size","raw_offset","raw_size","characteristics"],
            "properties": {
              "name": {"type":"string"}, "virtual_address":{"type":"integer"},
              "virtual_size":{"type":"integer"}, "raw_offset":{"type":"integer"},
              "raw_size":{"type":"integer"}, "characteristics":{"type":"integer"}
            }
          }
        },
        "c08_size": { "type": "integer", "minimum": 1 },
        "c13_abs_path": { "type": "string" }
      }
    },
    "baselineEntry": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id","adjudicated","provenance","identity","allowed_write_entries"],
      "properties": {
        "id": { "type": "string" },
        "adjudicated": { "const": true },
        "provenance": {
          "type": "object", "additionalProperties": false,
          "required": ["source","contains_native_detour","is_clean_retail_gold","adjudicated_by","adjudicated_at"],
          "properties": {
            "source": {"type":"string"},
            "contains_native_detour": {"type":"boolean"},
            "is_clean_retail_gold": {"const": false},
            "adjudicated_by": {"type":"string"},
            "adjudicated_at": {"type":"string"}
          }
        },
        "identity": { "$ref": "#/$defs/l1Identity" },
        "l2_edition": { "type": "object" },
        "allowed_write_entries": {
          "type": "array", "items": { "enum": ["E1","E2a","E2b","E3","E4","E5","E6"] }
        }
      }
    },
    "baselineFile": {
      "type": "object", "additionalProperties": false,
      "required": ["schema_version","entries"],
      "properties": {
        "schema_version": { "const": "w38-s1-1" },
        "entries": { "type": "array", "items": { "$ref": "#/$defs/baselineEntry" } }
      }
    },
    "byteWindow": {
      "type": "object", "additionalProperties": false,
      "required": ["target_file","foff","rva","va","n","before_sha256","after_sha256"],
      "properties": {
        "target_file": {"type":"string"}, "foff":{"type":"integer"},
        "rva":{"type":"integer"}, "va":{"type":"integer"}, "n":{"type":"integer","minimum":1},
        "before_sha256": {"$ref":"#/$defs/sha256Hex"},
        "after_sha256": {"$ref":"#/$defs/sha256Hex"}
      }
    },
    "guardVerdict": {
      "type": "object", "additionalProperties": false,
      "required": ["state","write_allowed","reason_codes","evidence","missing_criteria","byte_windows_ok"],
      "properties": {
        "state": { "enum": ["KNOWN_GOOD","UNKNOWN","MISMATCH","DIR_INVALID"] },
        "write_allowed": { "type": "boolean" },
        "baseline_id": { "type": ["string","null"] },
        "edition_label": { "type": "string" },
        "reason_codes": {
          "type": "array", "items": {
            "enum": ["NO_ADJUDICATED_BASELINE","NO_BASELINE_MATCH","CRITERION_MISSING",
                     "CRITERION_UNREADABLE","MULTI_COPY_AMBIGUOUS","EDITION_UNKNOWN",
                     "FULL_SHA_MISMATCH","TEXT_SHA_MISMATCH","SIZE_MISMATCH",
                     "SECTION_TABLE_MISMATCH","DDRAW_IDENTITY_MISMATCH",
                     "ORIGINAL_BYTE_WINDOW_MISMATCH","PATCHED_BY_THIRD_PARTY",
                     "GAMEMD_ABSENT","DIR_INVALID","FORCE_UNKNOWN_READONLY_ONLY",
                     "BASELINE_NOT_ADJUDICATED"]
          }
        },
        "evidence": { "type": "array", "items": { "$ref": "#/$defs/criterion" } },
        "missing_criteria": { "type": "array", "items": { "type": "string" } },
        "byte_windows_ok": { "type": "boolean" },
        "force_unknown_used": { "type": "boolean" },
        "observed_at": { "type": "string" }
      },
      "allOf": [
        { "if": {"properties":{"state":{"const":"KNOWN_GOOD"}}},
          "then": {"properties":{"write_allowed":{"const":true}}} },
        { "if": {"properties":{"state":{"enum":["UNKNOWN","MISMATCH","DIR_INVALID"]}}},
          "then": {"properties":{"write_allowed":{"const":false}}} }
      ]
    },
    "writeEntryPolicy": {
      "type": "object", "additionalProperties": false,
      "required": ["entry_id","state","allow","deny","require","exit_code"],
      "properties": {
        "entry_id": { "enum": ["E1","E2a","E2b","E3","E4","E5","E6"] },
        "state": { "enum": ["KNOWN_GOOD","UNKNOWN","MISMATCH"] },
        "allow": { "type": "array", "items": {"type":"string"} },
        "deny": { "type": "array", "items": {"type":"string"} },
        "require": { "type": "array", "items": {"type":"string"} },
        "exit_code": { "enum": [0,20,21,22,23] }
      }
    },
    "decisionTable": {
      "type": "object", "additionalProperties": false,
      "required": ["schema_version","states","entries","cells"],
      "properties": {
        "schema_version": { "const": "w38-s1-1" },
        "states": { "type":"array", "items":{"enum":["KNOWN_GOOD","UNKNOWN","MISMATCH"]} },
        "entries": { "type":"array", "items":{"enum":["E1","E2a","E2b","E3","E4","E5","E6"]} },
        "cells": { "type":"array", "items": { "$ref": "#/$defs/writeEntryPolicy" }, "minItems": 21 }
      }
    },
    "guardReport": {
      "type": "object", "additionalProperties": false,
      "required": ["schema_version","verdict","report_written_to","wrote_game_dir"],
      "properties": {
        "schema_version": { "const": "w38-s1-1" },
        "verdict": { "$ref": "#/$defs/guardVerdict" },
        "report_written_to": { "type": "string" },
        "wrote_game_dir": { "const": false },
        "operator": { "type": "string" },
        "command_line": { "type": "string" }
      }
    }
  },
  "oneOf": [
    { "$ref": "#/$defs/baselineFile" },
    { "$ref": "#/$defs/guardVerdict" },
    { "$ref": "#/$defs/decisionTable" },
    { "$ref": "#/$defs/guardReport" }
  ]
}
```

**可直接断言的不变式（S2/S3 引用）**

1. `guardVerdict.state != "KNOWN_GOOD" ⇒ guardVerdict.write_allowed == false`（schema `allOf` 已编码）。
2. `guardVerdict.state == "UNKNOWN" ⇒ missing_criteria.length >= 1 OR reason_codes contains NO_*`。
3. `guardVerdict.state == "MISMATCH" ⇒ reason_codes` 至少含一个 `*_MISMATCH`。
4. `decisionTable.cells` 对 `(3 states × 7 entries)` 全覆盖且无重复；`UNKNOWN`/`MISMATCH` 行的 `deny` 必含 `ALL_GAME_DIR_WRITES`。
5. `baselineEntry.provenance.is_clean_retail_gold == false`（`const`，把「不得当干净零售金标准」写进 schema）。
6. `baselineEntry.adjudicated == true` 才参与 §3 步骤 2–4。
7. `guardReport.wrote_game_dir == false`（上报不得写游戏目录）。

### 6.2 决策表机器实例（`EVIDENCE\guard_decision_table.json` 的语义）

`cells` 共 **21** 行 = 3 态 × 7 写入口（E1 / E2a / E2b / E3 / E4 / E5 / E6）；`E2b` 与 `E5` 的 `UNKNOWN` 行分别携带 `ALLOW_SANDBOX_ONLY` / `REPORT_UNKNOWN_MANDATORY`；所有 `UNKNOWN`/`MISMATCH` 且 `entry_id ∈ {E1,E2b,E3,E4,E6}` 的行 `deny` 含 `ALL_GAME_DIR_WRITES` 且 `exit_code ∈ {20,21}`。`KNOWN_GOOD + E1/E3` 的 `require` 含 `L1_RECOMPUTED_AT_CALL` 与 `BYTE_WINDOW_OK`。

### 6.3 与 ACCEPTANCE.md 的锚点

| 断言 | 引用本契约 |
|---|---|
| A1 / A3 | §4 跨态不变式、§6.1 不变式 1 |
| A2 | §2.3 L1、§3 步骤 1 |
| A4 | §4 E5、§5 R4/R5 |
| A5 | §2.3 写前附加、§3 步骤 4、§5 R10 |
| A6 | §6.1 不变式 4/5/7 |
| A7 | §4 E2b 路径归属规则 |
| A8 | §4 跨态不变式（flag 不得改变 guard_state） |
| A9 | §5 R9 |
| A10 | §4 E4 + `verify.py` 零写事实 |

---

## 7 · 现状结论（本卡只盘点，不实现） `[本次实测]` / `[本次读码]`

1. v11 = **14 个 `.py`**、`TOOL_VERSION="1.0"`（`install.py:388`）、`__version__="0.3.0"`（`__init__.py:9`）；仓库 `ra2forge\` = **11 个 `.py`**、`TOOL_VERSION="0.4"` `[本次实测]`（`facts_check.stdout.txt` §1–§3）。
2. **v11 全包 0 处构建身份判定调用**：`KNOWN_GAMEMD` / `text_section_sha256` / `SizeOfImage` / `TimeDateStamp` / `ddraw.dll` / `force_unknown` 在 v11 的 grep 命中均为 0 `[本次实测]`（`grep_scan.stdout.txt` §2）；`identity` 仅出现在 **PKG-IDENT01 包身份**语境（`install.py:457 _read_package_identity`、`builder.py:189 _write_package_identity`）`[本次读码]` —— **包身份 ≠ 构建身份**，不可误读为守卫。
3. `install` 前置守卫仅 `(game/"gamemd.exe").is_file()`（`install.py:1140-1143`）；`uninstall` 仅 `game.is_dir()`（`install.py:2184`）；`verify` 明写不需要 `gamemd.exe`（`cli.py:246`）`[本次读码]`。
4. `verify.py` **零写动作**（AST 扫描 `verify.py` 无任何写点；`verify.py:111` docstring）`[本次实测]`；因此 E4 目前是空集，S2 一旦加 `--fix` 必须按 §4 重新注册。
5. `build --csf-out` 会**直接写用户给定路径**（`builder.py:434` `write_csf(csf_out, …)` / `builder.py:435-437` `append_or_set_label(csf_out, …)`），全程**无任何目录/身份守卫** `[本次读码]`；这是 E2b 的高风险根因。
6. `ra2opt` 侧：`identity()` 存在（`game.py:104-124`）但 `apply()` 函数体 L112–325 内调用数 = **0**（`ra2opt_scan.stdout.txt` §3）；`identity()` 只在 `audit.py:109` 与 `optimize.py:344 status()` 被调用 `[本次实测]`。与 W36 D4 / `FINAL_RULING.md` §4 第 2 条一致 `[转引]`。
7. `W34\out\SUMMARY.txt` 的 `51/51 PASS` 为 `[转引]` + `[待运行验证]`，本卡未复跑，**不得**据此写「行为正确」或「守卫已具备」。

> **本卡交付边界**：判据清单、决策表、降级策略、机器可检结构、写入口穷举表、验收断言设计。接线、`BASELINE.json` 实算、`--force-unknown`、回归用例实现均属 S2+。
