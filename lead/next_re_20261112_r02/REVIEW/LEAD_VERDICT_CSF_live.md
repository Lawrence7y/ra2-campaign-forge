# LEAD_VERDICT · CSF 真机三臂：散装覆盖成立，但「最小 CSF 会启动失败」被否证

> 签发人：Lead（本会话）｜ 日期：2026-11-13 19:15
> 依据：**W40**（Hy4 子代理，真机）`lead\next_re_20261112_r02\W40_csf_live\`
> Lead 独立复核：直接读 3 趟 ndjson 的 `deploy_done`/`startup_outcome`/`run_outcome` + **亲自读 A 与 B 两张主菜单截图**

---

## 1. 三臂结果（`[本次实测]`）

| 臂 | 投放的散装 `ra2md.csf` | SHA-256 | 启动结果 | 界面 |
|---|---|---|---|---|
| **A 最小** | 115 B、**合法 CSF 但仅 1 个标签** | `74be568d…` | `main_menu_ready`，**19.34 s** | **全部文字变 `MISSING:'GUI:…'`** |
| **B 完整克隆** | 333,053 B（官方 332,973 + 80）、**5,212 标签** | `a46596c9…` | `main_menu_ready`，19.36 s | **正常中文** |
| **C 无散装**（对照） | 无 | — | `main_menu_ready`，19.36 s | 正常中文 |

三趟 `step0_desktop_precheck` 全 `pass=true`（`WinSta0\Default`、`EnumWindows=383/382`、`ImageGrab OK`）。

### 1.1 Lead 亲自读图（一手证据）

`[本次实测·截图]` `screen_w40_A_minimal_main_menu.png`（`1a01021e…`）：主菜单按钮**逐个显示为**
`MISSING:'GUI:SinglePlayer'` / `MISSING:'GUI:WWOnline'` / `MISSING:'GUI:Network'` / `MISSING:'GUI:MoviesAndCredits'` / `MISSING:'GUI:Options'` / `MISSING:'GUI:ExitGame'` / `MISSING:'GUI:Version 1.001'`，左下角还有被截断的 `MIS…`。**游戏本体正常运行到主菜单。**

`[本次实测·截图]` `screen_w40_B_full_main_menu.png`（`982cde29…`）：**正常中文** —— 單人遊戲 / 網際網路路 / 網路 / 動畫及製作人員 / 選項 / 退出遊戲 / 版本 1.001。

---

## 2. 两条结论

### 2.1 ✅ 散装 `ra2md.csf` 确实覆盖 MIX（首次端到端实证）

`[签发]` W29 从 `CCFileClass::Get_File 0x473D10`（磁盘优先、MIX 仅回落）推出的「散装优先」结论，**在 CSF 上得到真机实证**：A 臂把整个界面打成 `MISSING`，说明引擎**读的是散装那份**，而不是 `langmd.mix` 里的官方 332,973 B。

### 2.2 ❌「最小 CSF 会导致启动失败」被**否证**

`[本次实测]` A 臂是合法但不完整的 CSF（1 标签），游戏 **19.34 s 正常进入主菜单**，与对照 C 的 19.36 s 无差异，**没有出现 `Unable to initialize 'ra2.csf'`，没有崩溃、没有退出**。

⇒ `[签发]` **W29 的静态预测在真机上未复现。**

**根因（我的判断）**：W29 把「**完整**」与「**合法**」混为一谈。引擎 `0x734799` 的 `" FSC"` 魔数/结构检查只要求文件**合法**；1 个标签的 CSF 完全合法。真实后果不是启动失败，而是**引用不到的标签全部降级显示为 `MISSING:'<标签名>'`**。

`[未定谳]` 什么情况下才真会弹 `Unable to initialize 'ra2.csf'`？最可能是**魔数/结构非法**（如截断、非 CSF 文件、魔数错），而不是「标签不足」。这一点本卡未做（需专门造一个坏魔数文件）。

---

## 3. 对既有签发文件的影响（已处理）

| 文件 | 原表述 | 处置 |
|---|---|---|
| `REVIEW\LEAD_W29_VERIFY.md` §3 | 「散装 CSF **必须是完整合法 CSF**，否则启动失败」 | **降级并更正**：合法即可启动；不完整会界面全 `MISSING`；「启动失败」未复现 |
| `REVIEW\LEAD_VERDICT_map_start_root_cause.md` 相关处 | 引用过该警告 | 加注指向本文件 |
| W41 任务前提（我写的派卡 prompt） | 「最小 CSF 是危险的，会启动失败」 | **理由错误**，但**结论仍成立**：完整性守卫应当保留，因为它防的是「界面全变 `MISSING`」这种可用性灾难，而不是崩溃。W41 交付后我会按其实际语义重述理由 |

`[纪律]` 不得再写「最小 CSF 会导致启动失败」；正确表述：**「合法的极小 CSF 不会阻止启动，但会让所有未覆盖的标签显示为 `MISSING:'…'`」**。

---

## 4. 追加两臂（W40 超出卡面要求自加，我复核后采纳）

### 4.1 D 臂：坏魔数 ⇒ 确实弹 `Unable to initialize 'ra2.csf'`（把「未定谳」补上了）

`[转引]` W40：把散装 CSF 的 4 字节魔数改成 `XXXX` → 弹出 Red Alert 2 三语弹窗 **「Unable to initialize 'ra2.csf', please reinstall Red Alert.」** + 「確定」，点确定后自然退出 `exit code=0`，无主窗口。

`[签发]` 这条把 W29 的 `0x734799` → `0x6BD85A` 分支**证实了**，同时精确切分了边界：
- **魔数/结构非法** ⇒ 弹窗 + 不启动（W29 原预测的分支，成立）
- **合法但标签不全** ⇒ 正常启动，UI 降级为 `MISSING:'…'`（W29 说错的部分）

⇒ W29 的错不是"分支读错了"，而是**把「魔数合法性」误绑到「标签完整性」**上。

### 4.2 E 臂：覆盖官方可见标签 ⇒ 我方文本真的渲染出来（价值最高）

`[转引]` W40：把完整 CSF 里官方可见标签 `GUI:SinglePlayer` 的值换成 `W40_CSF_LIVE_OK_20261113`（标签总数不变 5,211）→ 主菜单对应按钮渲染出该文本。

`[本次实测·截图]` Lead 亲自读 `screen_w40_E_override_main_menu.png`（`d373630f…`）：主菜单**第一个按钮显示黄色 `W40_CSF_LIVE_OK_20261113`**，其余按钮均为正常中文（網際網路路 / 網路 / 動畫及製作人員 / 選項 / 退出遊戲 / 版本 1.001）。

`[签发]` 这条**端到端闭合**了 CSF 的整条链：
1. 散装文件优先于 MIX（A 臂已证）
2. 文件的**值真的驱动 UI 渲染**（E 臂证）
3. 标签名与控件槽位的映射正常（`GUI:SinglePlayer` → 单人游戏按钮位）

⇒ **W30 `UNCOVERED.md §1`（「散装 `ra2md.csf` 能否覆盖 `langmd.mix` 内同名文件，未做验证」）与 W29 的 C13 一并在真机结案：能覆盖，且值生效。**

`[重要限定]` E 臂是**覆盖官方标签**，属于"改已有文案"，**不能**冒充「追加标签能显示在战役菜单」。追加的自定义标签（B 臂的 `RA2F:W40TEST`）在内存里被当 CSF 标签解析（utf16le 命中 6 处、旧 `MISSING:'W27LIVE…'` 消失），但**未出现在任何可见 UI** —— 与 W27/W32 的「菜单不生成条目」一致。

### 4.3 C 臂的对照价值

`[转引]` C 臂（无散装 CSF）内存出现 `MISSING:'W27LIVE two-mission chain probe A1 to A2'`；B 臂（改成 CSF 标签）该 MISSING 消失 ⇒ **单变量证明「`Description=` 写纯文本 → `MISSING`，写 CSF 标签 → 正常解析」**。这与 W27 的 D1 结论链一致。



---

## 5. 仍未闭合

1. `[待运行验证]` `install.py` 尚未接入 CSF（W41 在做）。
2. `[待运行验证]` **追加的自定义标签如何显示到可见 UI**——B 臂证明它被解析但不出现在任何界面；要显示出来必须先解决「战役菜单不生成条目」（W27 Q1 / W32），或改用 E 臂那种覆盖官方标签的方式（有副作用）。
3. `[未定谳]` 交互式 MapSelect、末关终止等（沿用 W39 的 `UNKNOWNS`）。
4. `[未定谳]` 坏魔数弹窗的三语文案来源（CSF 还是 exe 内建）未查。

---

## 6. 三条必须记住的追加裁决（W40 指出，我认可）

### 6.1 方法论：控件文本 ≠ 渲染文本（影响面超出 CSF）

`[本次实测]` A 臂里控件的**文本字段仍是 `GUI:SinglePlayer`**，而**画面上渲染的是 `MISSING:'GUI:SinglePlayer'`**。
⇒ **判断「某段文字是否显示」必须用截图，不能用 `EnumChildWindows` 的控件文本**；反过来判断「控件是否存在/是否可见」用控件文本是可靠的。

`[对我的影响]` 这条同样约束我此前基于控件文本做的显示类判断，例如 `REVIEW\LEAD_W27_RAW_VERDICT.md` §6 里「简介区是空白」的判断——那次我**也看了截图**（`screen_p2a_D1_campaign_menu.png`，官方徽章下有「點選盟軍圖示以開始盟軍戰役。」正常渲染），所以结论站得住，但**理由是截图而不是控件文本**。已在那边补注。

### 6.2 我派卡 prompt 里的 E 处路径笔误

`[本次实测]` 官方 CSF 在 **`langmd.mix`**（`id=0xBD835079`、offset 39,216、332,973 B、SHA-256 `1b90bb07…`），**不在** `ra2bench\ra2md.mix`（其 25 条目无此 id）。
`[我的错]` 我在 W40 任务卡 §1 写的是「从 `ra2bench\ra2md.mix` 取官方 CSF」——**路径写错了**。W40 按实际路径执行并记了 `DISAGREE D2`。
`[记忆点]` `ra2md.mix` 里那个 `0xFBE0D09D` 是 **LOCALMD.MIX** 容器（内含 `MAPSELMD.INI`）；**CSF 在 `langmd.mix`**。两个容器别混。

### 6.3 复用路径也写错一处

`[本次实测]` `W39_mapselmd_live2\sandbox_game` **不存在**；W39 的 `live_lib.py:39` 指向的是 `W35_mapselmd_live\sandbox_game`。
`[我的错]` 我写「可复用 W39 的 sandbox_game」——W39 只是**复用了 W35 的沙箱**，并未自建。W40 按实际路径处理，`verify` 前后均 exit 0。



### 6.4 W40 自身的一个工具缺陷（照录）

`[本次实测]` 其 `tools\summarize_live.py` 在输出时因 **GBK 控制台编码**遇 `\u0211` 抛 `UnicodeEncodeError` 中止（与 W39 首趟 `\xde` 同类）。**这是驱动缺陷，不是游戏行为**；原始 ndjson 完整无损，我据此复核。

---

## 7. 对 W29 需勘误的处

`[转引]` W40 建议：`W29 OVERRIDE_ORDER.md §0` 与 `DISAGREE.md D6` 的表述需勘误；W29 §4 的实验 A（4 字节 `XXXX`）**本身预测正确**。
`[我的处理]` 我已在 `REVIEW\LEAD_W29_VERIFY.md` §3 就地更正并保留原文以备核对。W29 卡自身文件（属该卡写域）我不改动，仅在本文件与 W29 复核里标注。

---

## 8. 交付物索引

- `W40_csf_live\out\`：`w40_A_minimal.ndjson`(14,985 B) / `w40_B_full.ndjson`(21,867 B) / `w40_C_nocsf.ndjson`(14,533 B) / `csf_variants.json`（含 11 项自检全 true）/ `official_ra2md.csf`(332,973 B) / `ra2md.csf.minimal`(115 B) / `ra2md.csf.full`(333,053 B) / 6 张截图 / `desktop_probe_standalone.json`
- W40 报告正文（`LIVE_RESULT.md` 等）以卡最终交付为准；本文件基于**原始产物**，不依赖其摘要
