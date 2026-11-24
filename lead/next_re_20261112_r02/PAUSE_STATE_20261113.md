# PAUSE_STATE_20261113 · 暂停点快照

> 状态：**按用户指令暂停**（2026-11-13 14:4x，「这几个子智能体跑完之后先暂停」）
> run_id = `NEXT_RE_20261112_R02` ｜ goal `goal-afc2db61` 已处于 `phase=paused` / `activation=disarmed`（17/24 轮）
> 暂停含义：**不再派新卡、不再启动真机、不再改仓库/游戏目录**；只保留已跑完的产物与判定。

---

## 1. 停止时的在跑项

| 项 | 停止时状态 | 处置 |
|---|---|---|
| W27 真机卡 | **已结束并出具报告**（`CAMPAIGN_LIVE.md` 14:42:19 / `DISAGREE.md` 14:43:55 / `UNCOVERED.md` 14:43:08），锁已还原 `owner=lead`（14:39:24），真机逐项零改动 | Lead 已复核原始产物 + 亲自读 3 张截图 → `REVIEW/LEAD_W27_RAW_VERDICT.md` |
| W30 CSF 能力（agy `gemini-4-hydrogen-high`） | **已结束**，45/45 用例经 Lead **亲自复跑**通过 | `W30_csf_capability/` |
| W28 NextScenario 形式 | **已结束并出具报告**（`NEXTSCENARIO_FORM.md`/`UNCOVERED.md`/`DISAGREE.md`） | Lead 已独立复算 14 张官方图 + ra2forge 产物字节 → `REVIEW/LEAD_W28_VERIFY.md`，**T3 形式相同已签发** |
| W29 资源覆盖顺序 | **已交付报告后被运行时中止**（`OVERRIDE_ORDER.md` 28,061 B @14:58:48、`UNKNOWNS.md`、`DISAGREE.md`、`EVIDENCE/README.md` @15:01:39；中止于 ~15:04） | Lead 已字节级复核其承重指令（含 3 处 `rel32` 手算）→ `REVIEW/LEAD_W29_VERIFY.md`，**「散装优先于 MIX」已签发** |

> W28/W29 若在暂停后自行写完产物，**其结论一律不得直接引用**：必须由 Lead 复核原始证据后才可签发。本会话已两次出现代理自述与原始产物不符（W25 自述全绿实为 36/39；W27 脚本 `chain_results.q2` 自述「未出现胜利/结算屏」实为假阴性——截图里「任務完成」清晰可见）。

---

## 2. 三条线的位置

### A 线（真实卡顿/崩溃）—— 已停放
`REVIEW/LEAD_VERDICT_Aline_FINAL.md`：四臂实测，单 tick CPU 中位 1.336–1.767 ms（单核 4.26–5.67%），未越过 20% 阈值；结构/单位静态声明不是负载来源；战斗真实但 600 s 仅 +0.8%。**渲染侧在禁止注入的前提下不可测**。
口径纪律：只能说「在本镜像/本机/单臂/零输入/240–600 s 下，单 tick CPU 1.34–1.77 ms，未观测到 >20% 负载上升；渲染侧与更重战斗未测」。

### B 线（安全改造能力）—— **未开工**
RE-N09 尚未触碰。当前实际具备的是：版本守卫、`verify`、seal、独立卸载（install-transaction 链 W21→W26），但「改造前后行为等价性验证」与「独立开关」无交付。

### C 线（战役包流水线）—— 作者→构建→安装 已通；**运行在 as-built 入口不可达**

W27 真机卡已跑完并出具报告（`W27_campaign_live/CAMPAIGN_LIVE.md` 24,562 B + `DISAGREE.md` + `UNCOVERED.md`），Lead 已对原始产物与截图复核，见 `REVIEW/LEAD_W27_RAW_VERDICT.md`。

| 环节 | 判定 | 依据强度 |
|---|---|---|
| 作者→构建 | 成立（`build`/`validate` exit 0，`BUILD_REPORT.txt` 逐项 PASS，A1 目标 `survive(8)` 编译为引擎原生 `ElapsedTime(8)→WinnerIs`） | `[转引]` |
| 安装 | 成立但**需 `--allow-content-conflict`**：裸装 **exit 1**（2 条 definite content conflict，`no file has been written`），加参数后 exit 0（9 项动作逐条留痕） | `[本次实测]` 日志 |
| `verify` | 成立（exit 0，seal OK，4 文件 ok，2 个 `.ra2forge.bak` 孤儿仅列出不改退出码） | `[本次实测]` 日志 |
| **运行（Q1 菜单可见性）** | **不成立**：`GUI:CampaignMenu` 只有盟军/苏联两颗徽章，无第三条；隐藏 ListBox `LB_GETCOUNT=0`；方向键/徽章/槽位穷举无果 | `[本次实测·截图]` + `[转引]` |
| **运行（Q2 链式推进）** | **不成立**：A1 结算出「任務完成」→ 点 `GUI:Continue` → 弹「無法啟始選取地圖！」/「確定」，frame 冻结 210，A2 未启动 | `[本次实测·截图]` |
| 地图本身可加载 | 成立（`ECH01`/`ECH02` 均实测；A2 在 D3 变体下正常入局，雪地图+基地） | `[本次实测]` |
| 存读档（Q3） | **成立但仅 D3 诊断变体**（`[SOV1] Scenario=ECH02.MAP`）；as-built 入口下未验证 | `[本次实测]` |
| CSF 是否为不可见根因 | **已否证**：`Description=DESC:ALL1` 后 `MISSING` 消失，菜单逐项不变 | `[本次读码]`+`[转引]` |
| 卸载 | W26 回归 39 例在 v9 通过；W30 v10 复跑 45/45 | `[本次复算]` |

**C 线根因收敛为两条正交问题**：
1. **菜单不可达**（Q1）：追加 battle id 已入 Battle 表、已进内存，但菜单不生成条目 → 追加式 DLC 路线的**前置阻塞**。
2. **下一关解析失败**（Q2）：结算后启动 `NextScenario` 目标图失败，弹「無法啟始選取地圖！」；图文件本身没问题。**是否由「劫持 `[SOV1]`」这一诊断手法引起，未分离。**

**Q2 的两条互斥假设（均未判决，见 `REVIEW/LEAD_W28_VERIFY.md` §3 与 `LEAD_W29_VERIFY.md` §2）**：
- **H-A「NextScenario 是死字段」**：14 张官方图的 `NextScenario` 全是 `GDI2A.map`（泰伯利亚之日的占位名，官方容器内不存在）⇒ 官方自身也无可用链，战役推进更可能按 `BATTLEMD.INI [Battles]` 序号走。
- **H-B「Scenario 走文件系统、Continue 走 MIX/CRC」**：**已被 W29 削弱** —— W29 字节级证明 `CCFileClass::Get_File(0x473D10)` 是**磁盘优先**、MIX 仅回落（Lead 已独立验算 3 处 `rel32`）。故 H-B 仅在「下一关推进**绕过** `Get_File`、直接调 `MixFileClass::Find(0x5B4430)`」时才成立。
- **最小判决实验（未执行）**：
  - **E0（最便宜，纯静态，应先做）**：定位 `NextScenario` 解析后打开目标图的调用，看是 `0x473D10` 还是直接 `0x5B4430` ⇒ 一刀判 H-A/H-B
  - **E1**：官方 `[SOV1]` 原样打到胜利点 Continue（同样报错 ⇒ H-A）
  - **E2**：把 `ECH02.MAP` 打进 `expandmd98.mix` 再 Continue
  - **E3**：给 A2 单独登记 battle 序号
  - **E4**：沙箱投放「仅我方标签的最小 CSF」⇒ 预期**启动失败**（`Unable to initialize 'ra2.csf'`）

**W29 已签发的引擎事实**：散装文件优先于 MIX 内同名条目（磁盘命中即跳过 MIX）；`BATTLEMD*.INI` 通配枚举后**合并**进全局 Battle 表 `0xA83CF8`（同 ID 后装载者覆写）。

**⚠ CSF 安全警示（恢复后第一件要验的事）**：散装 `ra2md.csf` **必须是完整合法 CSF**（含全部官方标签），否则引擎 `0x734799` 魔数检查失败 → `0x6BD85A` 弹 `Unable to initialize 'ra2.csf'` 并**启动失败**。W30 的 `append_or_set_label()` 必须以官方 CSF 为 `--csf-base` 克隆后追加；W30 自身「未让 `install.py` 写入游戏目录」的保守决定**因此是对的**。

**W28 已签发的一条否证**：`NextScenario` **写法不是成因**（官方与我方均为「裸文件名+扩展名」；差异仅大小写与行尾）。ra2forge **不需要改写法**。

---

## 3. 已签发 vs 未签发

**已签发（Lead 亲自复算过）**
- W30：`python regress_dlc_v10.py` → **45 cases / 45 passed / 0 failed / exit 0**
- W30 补丁可干净应用：`git -c core.autocrlf=false -c core.eol=lf apply --check …` → **exit 0**
- W30 基线自洽：v9→v10 仅 5 文件改动 + 1 新增（`csf.py`），`verify.py` 哈希与 v9 完全相同 → 既有 verify 语义未被削弱
- 真 `ra2youli` 零改动：`IDENTICAL_TREE=True`（647 文件 / 277 maplike / `RA2MD.INI`=`c91c6a47…`）
- W27 Q1 = **不成立**（亲自读图：只有 2 颗徽章）
- W27 Q2 = **不成立**（亲自读图：「任務完成」+「無法啟始選取地圖！」）
- W27 Q3 = **成立但仅 D3 诊断变体**
- W27 D1 = **CSF 不是不可见根因**（亲自 diff INI）
- W27 安装预检在旧包残留目录上 **exit 1 + 2 条 content conflict**，加 `--allow-content-conflict` 后 exit 0（亲自读日志）
- W27 真机还原自证：`RA2MD.INI`/`ddraw.ini`/`BATTLEMD.INI`/`BATTLEMD98.INI` 全 `byte_identical=true`，gamemd 残留 0

**未签发**
- W28（NextScenario 形式）—— 产物未复核
- W29（覆盖顺序）—— 产物未复核
- 第三战役徽章可达性（D4 未定谳：换 `YURI1` 后条目进了内存，但没进到 CampaignMenu）
- Q2 失败**是否由劫持 `[SOV1]` 引起**（未分离）
- CSF 散装覆盖 MIX 的引擎优先级（未做真机）
- `Q3_load_selected.selected=null` → 未证明加载的就是 `SAVE4823.SAV`

---

## 4. 恢复时必须先做的三件事

1. 读 `REVIEW/LEAD_W27_RAW_VERDICT.md` 第 7 节「不得再出现的表述」，避免把限定结论外溢。
2. 复核 W28/W29 的 `out/` 原始证据（对照其自述），不采信其总结。
3. 确认 `.game_instance.lock` 仍为 `owner=lead`、无 gamemd 残留，再启动真机。

## 5. 需要用户裁决的悬留项

- 真 `ra2youli` 中存在**既存旧包 v0.3**（`ra2forge_install.json` `fe3bdf62…`，「钢铁残响」，`BATTLEMD98.INI` + 替换过的 `ECH01.MAP`）。卸载它会改变 A 线基线且不可逆 —— **未动，等用户决定**。
