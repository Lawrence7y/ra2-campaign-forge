# S16-K2 DoD 对账表（针对 PLAN §1 六条）

| # | DoD 条件 | 本卡状态 | 说明 / 证据 |
|---|---|---|---|
| 1 | 本子系统函数 ≥90% 有名字与一行语义，且 ≥50% `[已证]` | ✅ **本卡跨阈** | atlas 分母 90：named 73→**83 (92.22%)**、proved 42→**46 (51.11%)**。全 coverage 92：named **85 (92.39%)**、proved **48 (52.17%)**。两口径同向跨阈。`coverage_delta.tsv` 14 行；复算见 `PROGRESS.md §核心数字`。 |
| 2 | 核心类完整字段布局（偏移/类型/读写者），与 `GetSize` 一致 | ✅ **已闭合**（前序 §943 + 本卡补） | S16-K1 已入账：`SuperClass` GetSize **0x80**、`SuperWeaponTypeClass` GetSize **0x100**，双向核对吻合（R14_COMMON §8.2 技术② / STATUS_BOARD §943）；字段数 27/31、写读双支撑见 `S16-K1\LAYOUT.md`。本卡对账全 4 项：SuperClass(0x80, 27 具名行, v[12]=`0x6CE210`, ctor 分配 `push 0x80`)✓；SWType(0x100, 31 行, v[12]=`0x6CE900`, 工厂 `push 0x100`)✓；两者类名 RTTI 复验（E01）✓；本卡新增 4 条 Save/dtor 提级不改变布局。 |
| 3 | 关键数据流（入口→每帧更新→销毁/存档）调用链图 | ⚠️ **部分，未独立成图** | 已有分散证据：`docs/re/superweapon_re.md` §Launch 12 路跳表、`HouseClass::Update→HasChargeProgressed` 每帧链（S16-K1 E10 + re_sprint_S2_report §四）；本卡新增 Save(0x6CDFD0/0x6CE8D0) 与 scalar deleting dtor(0x6CE220/0x6CEFE0) 补齐「存档/销毁」两末端。但未产出单一链图文件——本卡为定点卡，不做全链图。 |
| 4 | 涉及的 INI 键与全局变量表 | ⚠️ **前序已有，本卡未独立重出** | S16-K1 已入账 19 个 INI 键（`RechargeTime→+B0` 等，§943）；`superweapon_re.md` 有 Launch 全局变量。本卡未新增 INI 表（范围外）。 |
| 5 | 至少 1 张真机卡验证 ≥2 条关键运行时事实 | ❌ **仍缺** | `re_atlas\kb\00_INDEX.md` S16 行与 STATUS_BOARD LIVE_QUEUE 明示「无 S16 真机卡」。超武可真机（发射/充能/裂缝保护），但本静态卡不涉及；需另立 S16-V1 真机卡。 |
| 6 | `KB\Sxx_<名称>.md` 交付并通过异族审计；台账有结题节 | ❌ **仍缺（全 22 子系统同缺）** | `re_atlas\kb\00_INDEX.md` §E.1：全部 22 个 S01–S22 都没有 `KB\Sxx_<名称>.md`。**本卡按指示不创建 KB 文件**；台账结题节（S16 专节）亦未立。 |

## 本卡边界声明

- 本卡只针对 DoD 第 1 条补数字缺口（定点），第 2 条做对账确认，第 3/4 条为前序资产的引用而非新交付，第 5/6 条保持缺口不掩盖。
- 未改 `ra2youli\` 游戏文件、未改 `COVERAGE\coverage.tsv`、未写主台账、未 git commit/push。
