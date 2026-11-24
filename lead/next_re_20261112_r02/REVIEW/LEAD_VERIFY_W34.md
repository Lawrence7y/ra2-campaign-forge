# LEAD_VERIFY_W34 · `MAPSELMD.INI` 生成能力（v11）复核与签发

> 复核人：Lead（本会话）｜ 日期：2026-11-13 18:25
> 卡：**W34**（Hy4 `work/cn:hy4free`）`lead\next_re_20261112_r02\W34_mapselmd\`
> 交付：`MAPSELMD_SPEC.md` 17,390 B / `ra2forge_patched_v11\` / `regress_dlc_v11.py` 159,407 B / `APPLY.md` 10,998 B / `DISAGREE.md` 8,143 B / `UNCOVERED.md` 7,004 B / `PATCH_RELATIVE.diff` 38,896 B / `V11_FILES.sha256.txt`

---

## 1. Lead 亲自复跑（不采信其汇总）

| 检查 | 我跑出来的结果 |
|---|---|
| `python -B -X utf8 regress_dlc_v11.py` | **cases 51 / passed 51 / failed 0 / exit 0** ✅ |
| 用例构成 | 45 个既有（含 W26 的 39 个 + W30 的 CSF1–CSF6）全保留，新增 `MS1..MS6` |
| `verify.py` v11 vs v10 | 两侧 SHA-256 均 `051C2E214B0D9862358C5732EAA91F70346231050B82DF9F48419D64012E5E85` ⇒ **逐字节相同** ✅ |
| 官方基底 `ra2forge\data\MAPSELMD.OFFICIAL.INI` | 5,573 B、SHA-256 `074CCCCD9E156D586D0ED099CEAB78B3D72384C808725D8B5BEE2C9799691D52` |
| 与我从 `ra2md.mix` 独立算出的对照 | **完全一致** ✅（我按偏移 `0x71D050` 切片，见 `REVIEW\LEAD_W33_VERIFY.md` §3.1） |
| 模块数 | 14 个（v10 的 13 个 + 新增 `mapselmd.py` 18,754 B） |

`[本次实测]` 四条硬证据都成立：**回归全绿、verify 语义零削弱、官方基底与真实文件逐字节相同、模块增量最小**。

---

## 2. 我接受的更正（W34 纠正了 W33 与我文档里的措辞）

| 项 | 原措辞 | 更正为 | 依据 |
|---|---|---|---|
| 比较前归一化方向 | 转**大写**（W33、我的文档） | 转**小写**（`0x7B5B30` → `0x7CAFF4` 对 `'A'..'Z'` 加 `0x20`，再用 `0x7B4780` 做敏感比较） | W34 `[本次读码]`；"大小写不敏感"结论两边一致，方向错 |
| `0x005CF6B0` / `0x005CF760` | 未区分 | `0x005CF6B0` 按**阶段名**（`[stage+0]`）；`0x005CF760` 按 `Scenario=`（`[stage+4]`） | W34 `[本次读码]` |
| 阵营段的 `N=名字` | 我理解成"下一阶段" | 形式上是「ClickMap 颜色索引 N → 候选子阶段名」（数字键 0..255，`0x005CFFF5` 存 1 字节，`0x005D0037 cmp eax,0x100`）；线性官方战役里恰好等于下一阶段 | W34 `[本次读码]` |
| 官方结构完整性 | 只列了 `[GDI]/[Nod]/[ALL01..07]/[Sov01..07]` | **还必须有** `[ALL00]`/`[Anims]`/`[GDISFX]`/`[NODSFX]` 与各阶段的 7 类 UI 字段（`Anims/Sounds/TextRect/Palette` 加载器确实读） | 这是"必须完整克隆"的字节级依据 |
| 行尾 | 未定 | `0x65D5C0` 证明 CRLF 可行、单 LF 可行、**单 CR 会吞下一行首字节** ⇒ v11 一律 CRLF | W34 `[本次读码]` |

`[我的判断]` 这些更正让规格更严也更可用，我全部采纳，并已在 `REVIEW\LEAD_W33_VERIFY.md` 与 `REVIEW\LEAD_VERDICT_map_start_root_cause.md` 里把"转大写"改口。
`[补注（21:25，据 W52 审计）]` **W31 也犯了完全相同的「转大写」错误**（`W31_map_start_failure\WHY_MAP_FAILS.md:129,141`），我此前只点名 W33、漏了 W31。两卡**同向共误**这一点必须写明，否则会误以为只有一张卡错、另一张可作独立佐证。

---

## 3. 【已撤回】我此前对 `0xFBE0D09D` 的「证伪」是错的 —— W34 原本就是对的

> **本节原写「我不签发 W34 的 `0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")`，15 种变体全不匹配，属结果对、理由错」。该判断已被推翻，现予撤回并向 W34 更正。**
> 触发：W43 交叉审计（`REVIEW\agy_w43_handoff.md` BLOCKER-1）指出我用的填充方案不是 Westwood 规则；Lead 随即用项目内真实实现复算（`W30_csf_capability\ra2forge_patched_v10\ra2forge\mixlib.py::ts_crc_hash`）。

### 3.1 真实算法与复算结果（`[本次实测]`）

`mixlib.ts_crc_hash` 的真实实现（不是简单零填充）：
```python
b = filename.upper().encode("ascii", "replace")
length = len(b); aligned = length >> 2
if length & 3:
    b = b + bytes([length - (aligned << 2)]) + bytes([b[aligned << 2]]) * (3 - (length & 3))
return zlib.crc32(b) & 0xFFFFFFFF
```
即：**先追加一个「长度余数」字节，再重复「末组首字节」若干次**，而不是补 `\x00`。

`[本次实测]` 用它复算：
```
ts_crc_hash("LOCALMD.MIX")          = 0xFBE0D09D   ← 与 W34 完全一致
ts_crc_hash("MAPSELMD.INI")         = 0x922B8CE7   ← 与已知值一致
ts_crc_hash("RA2MD.CSF")            = 0xBD835079   ← 与 langmd.mix 实测 entry id 一致（W31/W30 已证）
```

⇒ `[签发]` **`0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")` 成立；W34 的结论正确。**
⇒ 我此前那 15 个变体（`pad0->4=0x62E98127`、`pad_space`、`lower`、`utf16le/be`、去扩展名、带路径前缀……）**全部用错了填充规则**，所以必然全不匹配。**不是 W34 错，是我不懂这套哈希。**

### 3.2 连带更正

- `REVIEW\LEAD_W33_VERIFY.md` §3.1b 的「结果对、理由错」结论**撤回**。
- `REVIEW\LEAD_VERDICT_map_start_root_cause.md` §4 里「`0xFBE0D09D` 来历未定谳」**改为已定谳**。
- `REVIEW\LEAD_VERIFY_W37.md` §1 里「容器名的具体字符串仍未定谳」**改为已定谳（`LOCALMD.MIX`）**。
- 我先前下的「**不得**把该等式当事实引用」这条禁令**作废**；相反，正确写法就是 `0xFBE0D09D = ts_crc_hash("LOCALMD.MIX")`。

### 3.3 这暴露的方法论问题（比结论本身重要）

我犯的错是**用自己临时写的 15 个变体去否定一个已落地的实现，而没有先读实现**。项目内 `mixlib.ts_crc_hash` 就在那里、W30 已交付并被我复跑过 45 例，我却没去调用它。
⇒ 纪律：**否决他人结论前，先跑「对方使用的那条实现」**；否则我的"独立验算"只是独立地重复了我自己的错误。
`[保留]` W34 的字节产物本已用 SHA-256 独立验证正确；现在连它的**理由**也被证实正确。W34 无需更正。



---

## 4. v11 的实质能力（我读代码与用例后确认）

- 新增 `mapselmd.py` + `data/MAPSELMD.OFFICIAL.INI`；**必须完整克隆官方再追加**，`validate_official_base()` 对最小/部分文件抛 `MapselmdError` 且**不落盘**（MS3 实测拒绝）
- 按 `campaign.side` 映射 `allied→[GDI]`、`soviet→[Nod]`；**`yuri` 明确拒绝而不是臆造**（这点很重要——YR 的第三阵营段名未定谳，它没有瞎猜）
- 每关生成 `[RA2F_<任务>_<8hex>]` 段，含 `Scenario=<MAP>.MAP` + 克隆官方末关 UI 字段 + 非末关一条候选子项，**末关无子项**（配合 builder 的 `EndOfGame=yes` 终止）
- 开关 `--mapselmd` / `--mapselmd-base`，**默认全关**
- **向后兼容**：不启用时 v10 vs v11 同一 design 的 7/7 产物 SHA-256 全同（我未逐一复算这 7 个哈希，属 `[转引]`；但 MS4 用例在我复跑中 PASS）
- `install.py`：`MAPSELMD.INI` 纳入清单/备份/卸载还原；**已存在的非我方 `MAPSELMD.INI` 是 definite conflict，且 `--allow-content-conflict` 也不释放**

`[我的评价]` 最后这条是**正确的保守设计**：`MAPSELMD.INI` 是整文件注册，静默合并会打断官方战役。代价是"多包共存"暂时不可用，已列在它的 `UNCOVERED.md`。

---

## 5. 仍未闭环（必须保留的分级）

`[待运行验证]` **真机一次都没跑过**。以下全部未验证：
1. 散装 `MAPSELMD.INI` 是否真的被引擎读取并生效（虽然散装优先已由 W29 字节级证明）
2. 加了登记后 `GUI:Continue` **是否真的推进到第 2 关**
3. 生成的文件能否被引擎的 INI 解析器接受而不崩（段名/键名/行尾任一不合规都可能炸）
4. 交互式 MapSelect 点击（颜色索引区）是否可用
5. 末关终止行为

`[说明]` 这五条正是 **W35（Gemini 4 Hydrogen 真机卡）** 的任务，已于 18:19 派出，正在跑。**在 W35 回来之前，本卡只能算「离线实现完成」，不能算「功能可用」。**

---

## 6. 一句话交接

`[签发]` v11 离线实现与回归通过（51/51 我复跑）、`verify` 未削弱、官方基底字节正确、向后兼容有硬证据。
`[未签发]` 真机能否推进；`0xFBE0D09D` 来历；Yuri 阵营段名；多包共存。
