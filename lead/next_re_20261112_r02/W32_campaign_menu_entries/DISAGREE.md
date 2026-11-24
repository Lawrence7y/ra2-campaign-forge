# W32 · DISAGREE.md（与前提 / 前序卡口径不符处，不迁就）

> 只列**有字节级证据**的分歧与必须澄清的口径。无损结论标「澄清」，实质冲突标「DISAGREE」。

---

## D1 【DISAGREE】W27 §9.1 建议的「`0x46CE10` 之后的 UI 构建路径」不是 UI 构建路径

**前序原文**（`W27_campaign_live/CAMPAIGN_LIVE.md:173`）：
> 「定位 `GUI:CampaignMenu` 的徽章生成条件（静态逆向 `0x46CE10` 之后的 UI 构建路径 + 真机 D4 重跑）」

**本卡复核** `[本次实测]`：
- `0x46CE10` 的函数体是 `Register_Battles`（W29 已定谳）：`0x46CE17 push 0x81B1D8 ("Battles")` → 枚举 `[Battles]` 条目名 → 与 `0xA83CFC` 用 `_stricmp` 比对合并（`0x46CE77 call 0x7C8D20`）。它属于**配置装载层**，`ret 4`；其**前** `0x46CE03..0x46CE0F` 是 13 个 `NOP` 填充（函数对齐），再往前是 `0x46CCD0` (`Battle::Read_INI`) 的尾部，**没有 UI 构建代码**。
- 真正的菜单构建链是另一条：`0x52DF25 → 0x52CB90`（`LoadBattleMdIni`）→ `0x52DF48 mov edx,0x52EC00` / `0x52DF4D mov ecx,0x94` → `0x52DF65 call 0x622650` → `0x6226CB call [0x7E1450] = CreateDialogIndirectParamA` → WndProc `0x52EC00`。
- 两者地址相差 `0xC3D90`（约 802 KB），跨不同子系统；把「`0x46CE10` 之后」当 UI 路径会指向错误代码。

**裁定**：W27 的建议地址不可用；本卡改从 `RT_DIALOG id=148` 模板 + 唯一 WndProc xref 入手。**这不改变 W27 的实测结论**（只有 2 颗徽章），只纠正其下一步逆向入口。

---

## D2 【DISAGREE】「`LB_GETCOUNT=0` ⇒ 列表本应有条目但没填」不是真正的破绽

**卡面设问**（核心任务 §5）：「`LB_GETCOUNT=0` 是否说明『列表本应有条目但没填』是真正的破绽」。

**本卡证据** `[本次实测]`：
- `0x52F00B: A0 AD F7 A8 00 = mov al,[0xA8F7AD]`；`0x52F012: 74 48 = je 0x52F05C`。
- 该字节为 0 时（`0x52F05C`–`0x52F07E`）：`ShowWindow(ListBox, SW_HIDE)`、`GetDlgItem(0x40E)` + `ShowWindow(hide)` + `EnableWindow(FALSE)`，**加条目循环 `0x52F018..0x52F048` 被整体跳过**。
- 官方 `BATTLEMD.INI` 自带注释「temporary campaigns to assist us in debugging」/`DebugOnly = this campaign is not for final release`，且 `0x81B18C = " - for debug/testing"`、`0x835630 = "STT:CampaignList"` ⇒ 这是**零售态被刻意关掉的调试列表**，不是「应该填而没填」。

**裁定**：`LB_GETCOUNT=0` 是**设计结果**。真正的破绽是 (a) 可见徽章区由模板写死 2 个控件 + 3 个硬编码 battle 名，**没有按 Battle 表生成条目的通路**；(b) 调试列表门控 `[0xA8F7AD]` 在正常启动为 0 且写入者未定位（见 `UNKNOWNS.md` U1）。**不迁就「填表失败」这一假设。**

---

## D3 【澄清，非冲突】「追加 battle id 不生成条目」需要按两个 UI 区域拆开说

**前提表述**：「`GUI:CampaignMenu` 为什么只显示 2 个战役徽章、追加的 battle id 不生成条目」+ 报告口径要求「区分『结构上不可能』与『有条件可达』」。

**本卡结论**：同一个对话框里存在**两条互不派生**的路径，笼统说「不生成条目」会丢掉一半事实：

| 区域 | 是否生成追加条目 | 定性 |
|---|---|---|
| 可见徽章区（1770/1772） | **不生成**，与 Battle 表 Count 无关 | `结构上不可能`（不改 exe） |
| 隐藏调试 ListBox 1109 | **门控关时不生成；门控开时无过滤全表生成** | `有条件可达`（`[静态推断]`+`[待运行验证]`） |

证据：`0x52F018..0x52F048` 循环上界 = `[0xA83D08]`，`Items[i]+0x2A0` 逐条加入；门控 `0x52F00B`。两者**结论完全相反**，必须连写，不能只写一句「不可能」或只写一句「可达」。

---

## D4 【澄清】`GUI:CampaignMenu=1684` 是**控件 id**，不是对话框资源 id

**卡面**给的「控件 id 参考」写 `GUI:CampaignMenu=1684`。本卡解析 `RT_DIALOG id=148` 发现：
- `1684 (0x694)` 是模板里第 6 个 **Static 控件的 id**，其文本才是 `"GUI:CampaignMenu"`（`VA 0xB83410`，UTF-16）；
- 整张对话框的资源 id 是 **`148 (0x94)`**（`0x52DF4D: B9 94 00 00 00`）；
- 另外 `GUI:Load=1038`、`GUI:Back=1670`、`GUI:Difficulty=1822`、`GUI:Harder=1648`、`Slider3=1295`、`ListBox=1109`。

卡面用词是「控件 id」，故**无冲突**；但若后续有人把 1684 拿去当 `CreateDialogParamA` 的资源号会找错地方，此处先钉死。

---

## D5 【澄清】「徽章贴图资源名 / id」不是 `ALL1.SHP` / `SOV1.SHP` 之类

镜像里 `ALL1.SHP`、`SOV1.SHP`、`"ALL1"`、`"SOV1"` 的 ASCII 字面量 **0 命中**（`recon1_stdout.txt` / `verify.py §7`）。徽章相关的字面量是：

- `0x8263B0 "STT:SovietCampaignIcon"`、`0x8263C8 "STT:AlliedCampaignIcon"`（CSF/提示标签，经 `0x734E60` 查表，见 `0x52F09E` / `0x52F0D1`）；
- `0x8263E0 "BootCampSelect"`、`0x8263F0 "AlliedCampaignSelect"`、`0x826408 "SovietCampaignSelect"`（经 `0x7514D0` 查索引，见 `0x52EFCE`）。

而 battle id 以**小写**静态初值放在 `.data`：`0x825CA0 "all1"` / `0x825C98 "sov1"` / `0x825C90 "tut1"`，靠 `_stricmp` 不区分大小写匹配 INI 里的 `ALL1`/`SOV1`。**别按大写字面量去搜，会得出「硬编码不存在」的相反错判。**

---

## D6 【澄清】调试列表不是「CSF 文本没配好」导致的

W27 D1 把 `Description` 换成有效 CSF 标签 `DESC:ALL1` 后 `MISSING:` 消失但菜单逐项不变 `[转引 W27 §3.1]`。本卡给静态解释：`Description` 只被读进 `[battle+0x2A0]`（`0x46CD67 add ebx,0x2A0` + `0x46CD7B call 0x529160`），只作为 **ListBox 条目文本**；可见徽章区根本不读 Battle 表。⇒ CSF 修复**只改显示文本，不改可见性**，与 D1 一致。把 CSF 当 Q1 修复是前序已排除的伪解，本卡再次钉死。

---

## D7 【无分歧，记录在案】与前提逐条复核一致

| 前提 | 复核 |
|---|---|
| 镜像 4,825,360 B / SHA-256 `73201cc…f67476` | ✅ `verify.py §0` |
| `ImageBase=0x400000` / `RELOCS_STRIPPED=True` / `.text` FOFF=VA−0x400000 | ✅ |
| `CCFileClass::Get_File=0x473D10` / `MixFileClass::Find=0x5B4430` | ✅ `recon1_stdout.txt` 的 `0x473D2D`/`0x473D68` 调用点；W29 已定谳 `[转引]` |
| `BATTLEMD*.INI` 通配枚举 + 按 `[Battles]` 名 `_stricmp` 合并进 `0xA83CF8`、同 ID 后装载者覆写 | ✅ `0x52DF25 → 0x52CB90 → 0x46CE10`；W29 `[转引]` |
| W27：`Count=15`、`RA2F1` 含 `CD=2 / ECH01.MAP` | 静态只证代码用 `0xA83D08/0xA83CFC`、`+0x98/+0x9C`；运行期数值 `[转引 W27]`，本卡未重测 |
| 控件 id 1684 / 1109 / 1672 / 1673 / 1401 | 1684、1109 本卡模板级证实；1672/1673/1401 在 `0x52D6xx` 的 `WM_COMMAND` 比较中出现（`recon1_stdout.txt`），属单人菜单层，未逐项解析该模板 |

---

## D8 【方法论自纠，留痕】探索期两处工具缺陷（不影响交付结论）

1. `recon2.py` 初版 `foff2va()` 用 `max(VirtualSize, RawSize)` 判段，`.data` 的 VirtualSize `0x367BE4` 覆盖了 `.rsrc` 的文件偏移，把 `FOFF 0x487200` 错映成 `VA 0x887200`（正确 `0xB83200`）。**已修正为只用 RawSize 判段并重跑**（`run_all.ps1` 全 exit 0）。`parse_dialog.py` / `verify.py` 从一开始就用正确的 RAW/VIRTUAL 双映射。
2. `recon4/5` 中「从任意回溯偏移线性反汇编找 xref」会产生 `sbb eax,0xA8F7A0` 之类的**错边界解码**。**不作为事实**；权威判据全部来自 `verify.py` 的逐字节断言与 `parse_dialog.py` 的结构解析。呼应卡面纪律：线性扫描 ≠ 完整 xref、`ret` 不是函数结束判据、等距指针表 ≠ vtable（本卡把 `0x52E161/0x52E287/0x52E356` 的跳转表判为主菜单状态机而非战役 vtable，因目标均落在指令边界但语义是 `mode[0xA8B238]` 分支，不是对象 vtable）。
