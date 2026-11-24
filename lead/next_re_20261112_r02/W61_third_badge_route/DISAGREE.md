# W61 · DISAGREE（与既有件/卡面的分歧与更正）

> 只列**本卡第一手证据**能支撑的分歧；每条给证据路径与影响面。不扩展到 W21–W60 的其它结论。

## D1 · 「第三槽没有 tooltip / 没有教程文案」——**本卡更正为：有**
- 既有口径（`LEAD_VERDICT_campaign_menu_q1.md`、W58 的 "counter-hypothesis: no bitmap wired up"、以及本卡早期中间结论）：第三槽是"模板无控件 + INI 无条目的残留分支"，除 `all1/sov1/tut1` 三串外没有配套资源。
- **本卡实测**（`EVIDENCE\anim_xrefs_stdout.txt`、`EVIDENCE\csf_check_stdout.txt`）：
  - 通用 tooltip 分派函数 `0x6041E5` 在"对话框 id=0x94(148)"下按控件 id 返回 CSF 标签：`0x6EA→STT:AlliedCampaignIcon`、**`0x6EB→STT:CampaignAnimTutorial`**、`0x6EC→STT:SovietCampaignIcon`（`0x6041ED / 0x6041FD / 0x60420D`）。
  - `ra2md.csf`（`langmd.mix` `BD835079`，332,973 B）含 `STT:CampaignAnimAllied` / `STT:CampaignAnimSoviet` / **`STT:CampaignAnimTutorial`** / **`GUI:TutorialCampaign`** / **`DESC:TUT1`**。
  - SOUND.INI（`extracted\all_inis\expandmd01_mix_7A742519.ini`）`534=BootCampSelect`，`[BootCampSelect] Sounds=$igisea Volume=90`。
- ⇒ 第三槽保留的是**完整数据链**：控件 id、battle 名、音效、tooltip、描述标签。**"残留分支"措辞过弱**，应为"被裁掉的产品功能，数据未清干净"。
- 影响：Q4 里 `[TUT1] Description=DESC:TUT1` **不需要新造 CSF 标签**（此前若按"必须自己写 CSF"规划会多做工作）。但 **Q2 的图仍然缺失**，见 D2。

## D2 · 「路线 (c) 补个控件就能有第三徽章」——**本卡否证视觉层**
- 卡面待评估的路线 (c) 表述："改 `RT_DIALOG 148` 补一个 `id=1771` 的 STATIC，让 `tut1` 战役槽可用"。
- **本卡实测**：
  - 战役菜单代码区 `0x52D800..0x52F400` 只引用 15 个字符串，**无任何 `.SHP`/`.PCX`/`Load_*`/`CCFileClass`/按 battle 名拼的文件名**（`EVIDENCE\menu_strings_stdout.txt`）。
  - `.rsrc` **无 RT_BITMAP / RT_RCDATA**（`EVIDENCE\recon_stdout.txt`）。
  - 全 MIX 递归（5,630 容器 / 1,168,759 CRC id）对 `TUT*`/`BOOT*`/`BADGE*`/`EMBLEM*`/`CAMP3`/`YURICAMP` 等候选美术名 **0 命中**；唯一 campaign 名资源是 `CAMPAIGN.PCX`（640×480×8bpp，76,884 B，`work\CAMPAIGN.PCX/.png`）。
  - 两个徽章控件是 `WS_EX_TRANSPARENT` + 空 title 的 STATIC（透明点击热区），视觉来自通用 `GraphicMenu`/背景绘制子系统而非按槽加载的图。
- ⇒ 补 1771 控件后引擎**会按 id 收消息、查 `tut1`、播 `BootCampSelect`、显示 `STT:CampaignAnimTutorial` 提示**，但**没有第三颗可见徽章的图**。路线 (c) **资源层静态可行、视觉层不成立**，必须另造美术并同步改背景/动画定义。
- 影响：这是路线 (c) 成败关键，也是本卡最有价值的结论之一。请勿把"补丁回读 14 控件 PASS"读成"第三徽章可用"。

## D3 · 「查表失败会降级/报错」——**本卡更正为：本处无失败分支**
- `LEAD_CHECK_menu_3slot.md` §5 把"1771 分支是否真的会绘制/响应第三徽章，以及 `tut1` 查表失败时的降级行为"列为**未复核**。
- **本卡读码**（`EVIDENCE\recon_stdout.txt`、`EVIDENCE\deep_stdout.txt`）：
  - `0x46CC90` 失败返回 **`-1`（数组下标），不是 NULL 指针**（`0x46CCC2 or eax,-1; ret`）。
  - `0x52F265 mov [edi],eax` 存 `-1`；`0x52F267 mov byte [edi+4],1` **无条件**置有效标志；`0x52F26B` 检查该标志因而恒通过。
  - 后续照常发 `0x4D5`/`0x4D4`、读滑条 `TBM_GETPOS(0x400)`、播 `0x750920` 音效，**本处没有任何错误串/MessageBox/降级跳转**。
- ⇒ 不存在"查表失败时的可见降级"这回事；`-1` 被静默传给上层 `0x52DE00`（`[0xA8B230+0x34CC]`）。上层后果 `[待运行验证]`。

## D4 · 「资源补丁必须整体重排/扩 `.rsrc` 段 / 重算校验和」——**本卡给出反例与量化**
- 卡面 Q5 预设：插入 item 需要"重排/扩尺寸、更新资源目录 Size、必要时更新 `.rsrc` 段大小与 PE 校验和"。
- **本卡实测**（`EVIDENCE\patch_stdout.txt`）：
  - 本镜像 `.rsrc` `VirtualSize=0x18128` 但 `SizeOfRawData=0x19000`，尾部有 **3,800 字节全零 padding**；插入 32 字节**不需要扩段、不需要改文件长度、不需要动 `.detour.PointerToRawData`、不需要改 `SizeOfImage`**。
  - `CheckSum` 原本就是 **0** ⇒ 保持 0 即可，用户态 EXE 加载器不校验；若要求非零才需 `CheckSumMappedFile` 重算。
  - 原地插入法的真实代价是 **61/113 个 `IMAGE_RESOURCE_DATA_ENTRY.OffsetToData` 各 +0x20**（`EVIDENCE\resource_integrity_stdout.txt` 已验证 61 个全部正确、112 个资源字节一致）；另有更省的 **repoint 法**（只改 1 个 data entry，0 个 RVA 重排，利用 3,800 B padding 放 696 B 新模板）。
- ⇒ "不可行 / 代价极大"不成立；**能，且代价可量化**。但 SHA-256 变化与版本守卫冲突（卡面已明示为设计意图）依然成立，本卡不反对。

## D5 · 与 W32 原结论的关系（顺带收口，不扩大范围）
- W32 签发的「新增第 3 徽章产品上不支持 / 结构性封死」**已被 Lead 的 `LEAD_CHECK_menu_3slot.md` 推翻**；本卡独立复核**支持推翻**（1771 分支 + 三表项 + tooltip/音效/CSF 描述齐全）。
- 但本卡**同时**给出新的限定：推翻的是"引擎不支持"，**没有**推翻"零售资源/美术不支持"。两条要分开写，否则会外溢成"第三徽章可用"。

## D6 · 工具链说明（非结论分歧）
- 本会话无 REA MCP 工具注册；`reverse-engineer-anything` skill 的 `doctor`/`setup` 需要网络与写配置，与红线冲突。故未使用 REA 的 `open_binary`/`analyze_function`，改用本地 pefile 2024.8.26 + capstone 5.0.7 + 自写资源/模板解析器。所有脚本与 stdout 在 `work\` / `EVIDENCE\`，可独立复跑。
