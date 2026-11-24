# RA2 Campaign Forge

> **本机 DSH 通信**：[DSH Bridge 插件](plugins/dsh-bridge/README.md)，用于连接、选择模型、发送任务与读取结果。

> **执行工作链**：[分工、并行与升级规则](docs/WORK_CHAIN.md)；首轮 [EXP001 实验任务卡](docs/re/dispatch/EXP001_work_chain.md)。

> **当前项目目标（2026-10-02）**：解决真实多单位卡顿与主要闪退问题，建立关键系统安全修改能力，并搭建 DLC / 游戏补充包框架与工具；逆向持续为这些交付补证。后续规划、优先级和验收以 [项目目标与后续逆向方向](docs/PROJECT_DIRECTION.md) 为准。

把一份 AI 编写的"战役设计 JSON"编译成《红色警戒2：尤里的复仇》**原版引擎可直接游玩**的
完整故事线战役：多张任务地图（剧情简报、目标触发器、增援、EVA 演出）+ 战役注册 + 一键安装包。

```
设计 JSON ──► ra2forge build ──► ECH01.MAP / ECH02.MAP / ...（[Basic] NextScenario 串成关卡链）
                                BATTLEMD98.INI      （散装追加战役条目，官方 BATTLEMD.INI 不动）
                                expandmd98.mix      （只装地图的归档，内含 0 个 INI）
                                BUILD_REPORT.txt    （关卡链 + 产物哈希 + 自检结果）
                                story.md            （给玩家看的剧情文档）
```

## 快速开始

```bash
cd D:\Project\ra2-campaign-forge
python -m ra2forge example demo.json          # 生成示例设计
python -m ra2forge validate demo.json         # 校验
python -m ra2forge build --design examples/demo_campaign.json --out out
python -m ra2forge build --design examples/demo_campaign.json --out out --install "D:\Path\To\YR"
python -m ra2forge uninstall --game "D:\Path\To\YR"      # 卸载并还原备份
```

安装后启动 `gamemd.exe` → 单人游戏 → 战役，战役列表里多出**一条追加条目**（官方战役保持原样）。
安装是**清单驱动**的：装前给每个被替换的文件留 `<名字>.ra2forge.bak` 备份并写
`ra2forge_install.json`；`uninstall` 按清单删掉自己写的散装文件、还原备份（文件被外部改动过
则拒绝删除，除显式 `--force`）。发现残留（旧版 `BATTLEMD.INI` 覆盖、`expandmd99.mix`、
旧版清单 `ra2forge_uninstall.txt`）会逐条告警。

**老用户迁移**（FORGE-1 之前安装过的人）：游戏目录里那个被旧版改写的**官方** `BATTLEMD.INI`
应当**先备份再删除**（`ren BATTLEMD.INI BATTLEMD.INI.ra2forge.bak`）——删掉后引擎会回退到
MIX 里的官方同名文件，官方战役列表自然恢复；**不要**用 `extracted/found_battlemd.ini` 去还原
（那份样例含 RA2 调试占位条目，权威性未定）。工具路径与完整步骤见
[docs/re/ra2forge_fix_forge2.md](docs/re/ra2forge_fix_forge2.md) §迁移（FORGE-1 的旧版步骤已在
那里修正）。

设计 JSON 的完整规范（国家表、建筑/单位代码、目标类型、坐标说明、给 AI 的设计建议）
见 **[docs/DESIGN.md](docs/DESIGN.md)**；示例见 **[examples/demo_campaign.json](examples/demo_campaign.json)**
（三关苏联战役《钢铁残响》，含剧情简报/计时防守/增援/摧毁指定建筑目标）。

关卡链默认按 `missions` 数组顺序自动串（末关留空），需要手工分叉时给单关加可选字段：

```json
{ "name": "ECH01", "next": "ECH03" }   // 或 "next": "" —— 让战役在这一关结束
```

## 代码结构

| 模块 | 作用 |
|---|---|
| `ra2forge/mixlib.py` | MIX 读写（支持官方加密头：Westwood RSA 公钥推导 blowfish 密钥） |
| `ra2forge/lzo.py` | LZO1X-1 压缩/解压（minilzo 移植），用于 IsoMapPack5 |
| `ra2forge/format80.py` | Format80 编解码，用于 OverlayPack |
| `ra2forge/maplib.py` | 地图构建器（菱形坐标、11 字节地形记录、触发器/队伍全节输出） |
| `ra2forge/triggers.py` | 事件/动作常量与目标触发器生成 |
| `ra2forge/design.py` | 设计 JSON 校验 |
| `ra2forge/builder.py` | 设计 → 地图（NextScenario 链 + 末关 EndOfGame）+ 散装 BATTLEMD98.INI（自有 ID `RA2F1`）+ expandmd98.mix（写盘后读回自检） |
| `ra2forge/install.py` | 安装/卸载：逐文件备份 + `ra2forge_install.json` 清单 + 完整还原，含旧版残留清理 |
| `ra2forge/cli.py` | 命令行：validate / build / install / uninstall / example / inspect |
| `mcp/ra2forge_mcp.py` | MCP stdio server（validate_campaign / build_campaign / inspect_map） |

MCP 注册（ZCode Desktop settings.json）：

```json
"mcpServers": {
  "ra2-campaign-forge": {
    "command": "python",
    "args": ["D:/Project/ra2-campaign-forge/mcp/ra2forge_mcp.py"],
    "env": { "PYTHONPATH": "D:/Project/ra2-campaign-forge" }
  }
}
```

## 格式依据（全部经真机数据验证）

- MIX 容器 / 加密：OpenRA `MixFile.cs` + WAE `CCCrypto.cs` 双重对照，已成功解密本机
  `ra2.mix`、`mapsmd03.mix` 等 7 个官方 MIX 并提取文件
- 地图格式：CnCNet **WorldAlteringEditor**（官方开源编辑器）源码 + 本机官方尤复战役地图
  逐节比对；触发器 8 字段/[Events] count+2 参数/[Actions] 9 字段块（P7 补 `A`）、
  航点 `Y*1000+X`、物件行格式均与官方地图完全一致
- 菱形坐标：对两张官方地图解码 IsoMapPack5 得出（cell 网格 `(W+H-1)²`，平地省略），
  生成器把 `(row, col)` 映射到钻石内部
- 战役机制：`gamemd.exe` 内嵌字符串证实游戏读取 **`BATTLEMD*.INI`**（官方 battlemd.ini
  的注释也说明追加文件会并入战役列表），描述支持纯文本；关卡链 = 地图 `[Basic] NextScenario`
- 战役注册路径（FORGE-1 定谳）：引擎在 **0x52CBA0** 用 `FindFirstFileA("BATTLEMD*.INI")` 扫
  **游戏目录**、在 **0x46CE10** 读 `[Battles]` 列表（`BATTLEMD.INI` 回退在 **0x52CCCD**）⇒
  通配**只看文件系统**、看不到 MIX 内条目；故注册文件必须是散装 `BATTLEMD98.INI`，且用自有 ID
  只**追加**、不覆写官方 `ALL1/SOV1`；`expandmd98.mix` 里不放任何 INI
- 条目 ID（FORGE-2 / 用户裁决 R1）：固定自有 ID **`RA2F1`**（不再用战役名哈希），
  `[Battles]` 索引 15（不占用官方 1..14）；设计 JSON 可用可选字段 `campaign.id` 覆盖，
  官方 ID 被校验拒绝
- `Description`（R3）= 设计文件 `campaign.description`，**不硬编码**；末关（链尾）写
  `EndOfGame=yes`（R5，依据：引擎在 **0x68A10E** 用 `push "EndOfGame"` + `push "Basic"`
  读取该键，官方末关 `extracted/yr_maps/map_133A0CB2.map:267` 亦为 `yes`）
- 中文：地图/INI 按 GBK（系统 ANSI 码页）写出，中文版游戏直接显示

## 验证状态

- ✅ 官方加密 MIX 解密 + 提取（ra2.mix / mapsmd03.mix / ra2md.mix / language.mix 等）
- ✅ LZO / Format80：30+50 组随机往返 + 官方地图真数据解码比对全部通过
- ✅ 生成战役自检：MIX 可被读取、坐标全部在菱形内、地形/遮罩编解码往返一致
- ✅ FORGE-1 关卡链：写盘后**读回**断言 `[Basic] NextScenario=ECH02.MAP / ECH03.MAP / 空`
  （非末关为空值即构建失败，不再产出断链地图）
- ✅ FORGE-1 打包：`expandmd98.mix` 条目清单 **0 个 INI**；散装 `BATTLEMD98.INI` 的
  `[Battles]` 条目与地图一致（复现：`out/re_work/forge1/verify_forge1.py` → `verify_output.txt`）
- ✅ FORGE-1 安装/卸载：临时目录演练「备份 → 覆写 → 卸载还原」，官方文件哈希前后一致
- ✅ FORGE-2 内容裁决：`[Battles] 15=RA2F1`（自有 ID，不碰官方条目）、`Description` 读自
  设计文件、末关 `EndOfGame=yes`、链 `ECH01→ECH02→ECH03→空` 不变；MCP 安装路径改为整套
  安装（散装 INI + 地图 + mix + 清单），ra2opt 体检与自检夹具同步认 `BATTLEMD98.INI`
  （复现：`out/re_work/forge2/verify_forge2.py` → 72/72 PASS，`verify_output.txt`）
- ⚠️ 本机 `ra2youli\` 仍是 **FORGE-1 之前**的安装（散装 `BATTLEMD.INI` 覆盖官方列表 +
  三图断链）；迁移步骤见 [docs/re/ra2forge_fix_forge2.md](docs/re/ra2forge_fix_forge2.md)
  （FORGE-1/FORGE-2 均**未改动**游戏目录任何文件）
- ⚠️ **游戏内实测**（进游戏看战役列表、通关节）需要玩家进行——启动 `ra2youli\gamemd.exe`
  试玩，若有问题回报即可迭代

## 已知限制 / 路线图

- 水面无海岸线过渡（方边），大面积水域观感一般
- 地图预览为占位图（游戏内缩略图不影响游玩；可用 WAE 打开地图重新生成）
- 暂不支持：任务间携带部队（CarryOver）、自定义 CSF 语音字幕、经济波次 AI
  （可后续在地图内嵌 rules 或用 Phobos 扩展）

## 另附：游戏本体的稳定性/性能优化（ra2opt）

`ra2forge` 造战役，`ra2opt` 让游戏本身**少闪退、少卡顿**——升级 cnc-ddraw（含多条
RA2 专项崩溃修复）、给引擎开 4GB 寻址与 4MB 栈、清理整合包遗留的有害兼容性标记、
生成高优先级启动器。全部改动可一键回滚，且不碰 `.mix`/地图/`BATTLEMD.INI`。

```bash
python -m ra2opt audit --online    # 只读体检
python -m ra2opt apply --profile perf
python -m ra2opt restore           # 完全还原
```

详见 **[docs/OPTIMIZE.md](docs/OPTIMIZE.md)**（含"多单位卡顿"能做到什么、做不到什么）。

## 另附：底层现代化的调研与路线（未开工，先看证据）

如果要走"保留玩法/UI 与数据契约、只替换渲染与数据布局等实现层"这条路（目标：摆脱 2001 年引擎的
多单位卡顿与结构性闪退，同时继续用原版资产与规则），先读这两份：

- **[docs/REWRITE_RESEARCH.md](docs/REWRITE_RESEARCH.md)** — 调研报告：`gamemd.exe` 的逆向友好度
  （实测 **988 个 RTTI 类型描述符 / 954 个 vtable / 698 条完整继承链**、38 个源文件锚点、
  导入表无 D3D/GL）、卡顿机理、OpenRA/ra2 与 vera20k 等 8 个先例的实测对照。
- **[docs/REWRITE_ROADMAP.md](docs/REWRITE_ROADMAP.md)** — 总体任务概览：按 ROI 排序的阶梯
  （L0 已完成 → L1 渲染解耦与 GPU 化 → L2 数据布局 → …）、里程碑可测验收门、
  复用清单、**反 ROI 清单**（不要先做的事）。

已有可复用的逆向产出（只读原版 exe，不改任何游戏文件）：

```bash
python -m ra2re rtti        # 988 类继承图 + vtable + 每个虚函数地址 → out/reverse/
python -m ra2re selftest    # 18 项自检
```

其中 `out/reverse/m1_blit_targets.txt` 是 **M1 接管点清单**：57 个软件 blit 实现
（50 个 16 位 RGB）带语义解码与虚函数地址，热点集中在 `0x007BC6xx` 与
`0x004924xx–0x004935xx` 两簇——这是"多单位卡顿"要动的地方。
