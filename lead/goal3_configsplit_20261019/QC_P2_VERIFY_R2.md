# QC_P2_VERIFY_R2 —— P2 配置拆分补丁【重交版】增量核验判定书

- 核验角色：独立补丁核验员（与实现者不同上下文，本件由本轮独立实测重写，取代同一路径下任何早期草稿）
- 核验日期：2026-10-19
- 被核目录：`out\re_work\work_chain\CONTINUE_20261003\lead\goal3_configsplit_20261019\`
- 母本目录：`ra2render\`
- 上一轮：`QC_P2_VERIFY.md`（R1 = REFUTED，唯一实质缺陷 F1 = 交付 ini :133 节头 `;[Gameplay]` 自身被注释）
- 核验范围：**只验重交增量五点**（a–e），不重跑 R1 已判定的其余各项。
- 纪律：只读核验；仓库内唯一写入 = 本判定书。全部测试脚手架位于 `C:\Users\Administrator\AppData\Local\Temp\qc_r2\`（`%TEMP%`），未落仓库。

---

## 0. 起跑实测基线（全部为本轮命令输出）

### 0.1 交付四件

```
$ cd .../lead/goal3_configsplit_20261019 && sha256sum ra2render.ini blitter_hooks.cpp ra2render.h RECEIPT.md
27c9a60c55a8a1b422d3ef06b90e3d343a93eb523a600286c937198b363ecee4 *ra2render.ini
656e6b4e48cdd251f42d55c6da7b5e6b5a354284924437396c63e60588daada1 *blitter_hooks.cpp
10410c98642dc51ae1426be179e091440257fd42434e84f82d5b8059e9cf0c07 *ra2render.h
09df88d886bed6623ad3ae0659966b8f877a7cb886d62fdcba6c412110e6822f *RECEIPT.md

$ wc -l
   205 ra2render.ini
  4006 blitter_hooks.cpp
   495 ra2render.h
   164 RECEIPT.md
```

| 件 | 实测 sha256(16) | 申报值 | 一致 |
|---|---|---|---|
| ra2render.ini | `27c9a60c55a8a1b4` | `27c9a60c55a8a1b4` | ✓ |
| blitter_hooks.cpp | `656e6b4e48cdd251` | `656e6b4e48cdd251` | ✓ |
| ra2render.h | `10410c98642dc51a` | `10410c98642dc51a` | ✓ |
| RECEIPT.md | `09df88d886bed662` | `09df88d886bed662` | ✓ |

ini 行数 205 = 申报值 ✓。起跑①通过，未触发「不符停手」。

### 0.2 母本三件（起跑）

```
$ cd ra2render && sha256sum ra2render.ini blitter_hooks.cpp ra2render.h
fd9ebb32dcb6cda7952381baa10d24183ee98a7ea3e8e71fd8953a3a8d17b696 *ra2render.ini
b461ed21aa92bd5f04f73c096cd562ffe66369d0227dad23b5ec8c648b7e557e *blitter_hooks.cpp
b70cbf8d620e340ef0a1de1f5707b990c3e0d7ceabff29fd73fe9556c4c22cd4 *ra2render.h
```

= 申报 `fd9ebb32 / b461ed21 / b70cbf8d`，逐位一致 ✓。起跑②通过。

---

## 1. 核验项 a：节头活性 —— **CONFIRMED**

### 1.1 活动节头（正则 `^\[[^;]`）

```
$ grep -n "^\[[^;]" ra2render.ini
10:[Render]
30:[Logic]
49:[Speed]
56:[System]
62:[FogOfWar]
151:[Gameplay]

$ grep -cE "^\[[^;]" ra2render.ini
6
```

**恰 6 个活动节头**，集合与要求完全一致：`[Render]/[Logic]/[Speed]/[System]/[FogOfWar]/[Gameplay]`；`[Gameplay]` 位于 **:151**（与「:151 附近」相符）。

### 1.2 真实 API 视角的节枚举（交叉验证，排除「看起来像节头但不被 API 识别」）

```
$ ./qc_harness2.exe <交付 ini>
SECTIONS: <Render> <Logic> <Speed> <System> <FogOfWar> <Gameplay>
```

`GetPrivateProfileSectionNamesA` 实测返回 **6 个节**，含 `Gameplay`。文件内另有若干以 `;` 开头的行内含方括号文字（如 `:101`「…[Gameplay] 由 Lead 裁决…」、`:115`「; [ZC-10B ①] L4DirtyMode…」、`:125`、`:143`、`:173`），均以分号起首、**未被 API 识别为节**——无幽灵节、无同名重复节。

### 1.3 13 玩法键保持注释

```
$ grep -nE "^; (TargetScanInterval|TargetScanKey|EnableStarCraftFog|VisibilityMode|EnableSpySatRadarSweep|RadarSweepCooldownFrames|RadarSweepRadiusCells|EnableBuildingFog|EnableBulletFog|EnableUnitFog|FadeFogTransition|EnableMinimapFog|RadarFogGuardMode)=" ra2render.ini
157:; TargetScanInterval=1
160:; TargetScanKey=position
167:; EnableStarCraftFog=0
174:; VisibilityMode=vanilla
180:; EnableSpySatRadarSweep=0
182:; RadarSweepCooldownFrames=600
184:; RadarSweepRadiusCells=16
189:; EnableBuildingFog=0
192:; EnableBulletFog=0
195:; EnableUnitFog=0
199:; FadeFogTransition=1
202:; EnableMinimapFog=0
205:; RadarFogGuardMode=3
```

13/13 全部为注释态，且全部位于 `[Gameplay]`（:151）之后、文件末尾之前 —— 即**落在 [Gameplay] 节体内**（R1 的失败形态「键落在 [FogOfWar] 节体」不再成立）。

全文活动键（非节头、非注释行）实测：

```
$ grep -nE "^[^;[:space:]]" ra2render.ini | grep -v "^[0-9]*:\["
12:EnableSIMD=1      28:EnableVxlCachePrewarm=0   47:EnableSWChargeOpt=0   54:UnlockGameSpeed=0
58:EnableLFH=1       60:HighPrecisionTimer=1       102:EnableGapProtection=0  112:FogStrengthPct=auto
122:L4DirtyMode=force-full  130:FogProbe=0
```

= 10 个优化键，0 个玩法键 ⇒ 出厂态「缺键 = 原版默认」。

**判定 a：CONFIRMED。** F1 的结构层修复已真实落地。

---

## 2. 核验项 b：★ 真 API 三态实测 —— **CONFIRMED**

### 2.1 方法（可复核）

- 从重交 `blitter_hooks.cpp:388-459` **原文切片**为 `%TEMP%\qc_r2\helpers.inc`（72 行；首行 `static const char *const kIniAbsentSentinel = ...`，末行 `}`），未改一字：

```
$ sed -n '388,459p' blitter_hooks.cpp > %TEMP%\qc_r2\helpers.inc && wc -l
72
```

- harness `%TEMP%\qc_r2\qc_harness2.cpp` 以 `#include "helpers.inc"` 直接复用原文 `GetIniStringEx` / `GetIniIntEx` / `GetGameplayIntEx` / `GetGameplayStrEx`；`RADAR_FOG_GUARD_NATIVE=3` 取自 `ra2render.h:243`。
- 编译（与 DLL 同架构 x86）：`vcvarsall.bat x86` + `cl /nologo /W3 /EHsc /utf-8 qc_harness2.cpp` → `CL_EXIT=0`（零 error / 零 warning）。
- 读取全部走**真实 `GetPrivateProfileStringA`**（绝对路径，`GetFullPathNameA` 归一后传入），非 ini 文本推断。
- 测试 ini（全部在 `%TEMP%`）：`A`=交付 ini 绝对路径；`B`=`ra2render\ra2render.ini`；`C1`=交付 ini 副本，仅把 :157 的 `; TargetScanInterval=1` 去注释并改为 `=8`；`C2`=母本 ini 副本末尾追加 `[Gameplay]` 段 `TargetScanInterval=0` / `EnableStarCraftFog=1`；`C2c`=母本 ini 副本末尾追加 `[Gameplay]` 段 `TargetScanInterval=1` / `EnableStarCraftFog=0` / `VisibilityMode=vanilla` / `EnableUnitFog=0`。

### 2.2 A 态（交付 ini）——13/13 落原版默认，10/10 优化键命中

```
$ ./qc_harness2.exe ...\lead\goal3_configsplit_20261019\ra2render.ini
SECTIONS: <Render> <Logic> <Speed> <System> <FogOfWar> <Gameplay>
GP_INT  TargetScanInterval       val=1      def=1    hit=0 migrated=0 rawGP=<ABSENT> rawLEG[Logic]=<ABSENT>
GP_INT  EnableStarCraftFog       val=0      def=0    hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_INT  EnableSpySatRadarSweep   val=0      def=0    hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_INT  RadarSweepCooldownFrames val=600    def=600  hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_INT  RadarSweepRadiusCells    val=16     def=16   hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_INT  EnableBuildingFog        val=0      def=0    hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_INT  EnableBulletFog          val=0      def=0    hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_INT  FadeFogTransition        val=1      def=1    hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_INT  EnableUnitFog            val=0      def=0    hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_INT  EnableMinimapFog         val=0      def=0    hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_INT  RadarFogGuardMode        val=3      def=3    hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_STR  TargetScanKey            val=position  def=position  hit=0 migrated=0 rawGP=<ABSENT> rawLEG[Logic]=<ABSENT>
GP_STR  VisibilityMode           val=vanilla   def=vanilla   hit=0 migrated=0 rawGP=<ABSENT> rawLEG[FogOfWar]=<ABSENT>
GP_TOTAL hits=0 migrated=0 of 13
OPT_INT [Render   ]EnableSIMD               val=1    hit=1
OPT_INT [Render   ]EnableVxlCachePrewarm    val=0    hit=1
OPT_INT [Logic    ]EnableSWChargeOpt        val=0    hit=1
OPT_INT [Speed    ]UnlockGameSpeed          val=0    hit=1
OPT_INT [System   ]EnableLFH                val=1    hit=1
OPT_INT [System   ]HighPrecisionTimer       val=1    hit=1
OPT_INT [FogOfWar ]EnableGapProtection      val=0    hit=1
OPT_INT [FogOfWar ]FogProbe                 val=0    hit=1
OPT_STR [FogOfWar ]FogStrengthPct           val=auto       hit=1
OPT_STR [FogOfWar ]L4DirtyMode              val=force-full hit=1
OPT_TOTAL hit=10 of 10
```

- 13 键读回值序列 = **1 / position / 0 / vanilla / 0 / 600 / 16 / 0 / 0 / 0 / 1 / 0 / 3**，与要求逐位一致；全部 `hit=0 migrated=0` ⇒ 三级回退的**第③级（原版默认）**。
- 优化键 **10/10 hit=1**，值与交付 ini 活动行（:12/:28/:47/:54/:58/:60/:102/:112/:122/:130）逐条对应；母本同键同值（母本 :3/:19/:46/:52/:56/:58/:199/:238/:251/:260）⇒ 「优化键原值命中」成立。

### 2.3 B 态（母本 ini 为源）——13/13 经旧节迁移命中，开启态保留

```
$ ./qc_harness2.exe ...\ra2render\ra2render.ini
SECTIONS: <Render> <Logic> <Speed> <System> <FogOfWar>
GP_INT  TargetScanInterval       val=8      def=1    hit=1 migrated=1 rawGP=<ABSENT> rawLEG[Logic]=8
GP_INT  EnableStarCraftFog       val=1      def=0    hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=1
GP_INT  EnableSpySatRadarSweep   val=1      def=0    hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=1
GP_INT  RadarSweepCooldownFrames val=600    def=600  hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=600
GP_INT  RadarSweepRadiusCells    val=16     def=16   hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=16
GP_INT  EnableBuildingFog        val=1      def=0    hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=1
GP_INT  EnableBulletFog          val=1      def=0    hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=1
GP_INT  FadeFogTransition        val=1      def=1    hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=1
GP_INT  EnableUnitFog            val=1      def=0    hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=1
GP_INT  EnableMinimapFog         val=0      def=0    hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=0
GP_INT  RadarFogGuardMode        val=3      def=3    hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=3
GP_STR  TargetScanKey            val=position  def=position  hit=1 migrated=1 rawGP=<ABSENT> rawLEG[Logic]=position
GP_STR  VisibilityMode           val=starcraft def=vanilla   hit=1 migrated=1 rawGP=<ABSENT> rawLEG[FogOfWar]=starcraft
GP_TOTAL hits=13 migrated=13 of 13
```

**13/13 `migrated=1`**，开启态原样保留（8 / starcraft / 1 / 1 / 1 / 1）。注意 `TargetScanKey=position`、`EnableMinimapFog=0` 等「值恰等于原版默认」的键也判 `hit=1`（哨兵口径区分「缺键」与「值=默认」）⇒ 迁移计数不丢项。

### 2.4 C1 态（[Gameplay] 去注释 TargetScanInterval=8）——读回 8，旧节遮蔽不存在

```
$ ./qc_harness2.exe %TEMP%\qc_r2\c1.ini
SECTIONS: <Render> <Logic> <Speed> <System> <FogOfWar> <Gameplay>
GP_INT  TargetScanInterval       val=8      def=1    hit=1 migrated=0 rawGP=8 rawLEG[Logic]=<ABSENT>
...（其余 12 键维持 A 态：hit=0，落原版默认）
GP_TOTAL hits=1 migrated=0 of 13
```

- 读回 **8**，`hit=1 migrated=0` ⇒ 命中来源 = `[Gameplay]`（①级）。
- `rawLEG[Logic]=<ABSENT>` ⇒ 交付 ini 的 `[Logic]` 节已无 `TargetScanInterval` 活动行（:31-32 为说明注释），**旧节遮蔽不存在**。
- 这正是 R1 失效的主路径（R1 实测 `value=1 hit=0`），现已修复。

### 2.5 C2 态（[Gameplay] 显式值压过旧节）

C2（`[Gameplay] TargetScanInterval=0` / `EnableStarCraftFog=1`，旧节为 8 / 1）：

```
$ ./qc_harness2.exe %TEMP%\qc_r2\c2.ini
GP_INT  TargetScanInterval       val=0      hit=1 migrated=0 rawGP=0 rawLEG[Logic]=8
GP_INT  EnableStarCraftFog       val=1      hit=1 migrated=0 rawGP=1 rawLEG[FogOfWar]=1
GP_INT  EnableSpySatRadarSweep   val=1      hit=1 migrated=1 ...
GP_TOTAL hits=13 migrated=11 of 13
```

C2c（`[Gameplay] TargetScanInterval=1` / `EnableStarCraftFog=0` / `VisibilityMode=vanilla` / `EnableUnitFog=0`，旧节为 8 / 1 / starcraft / 1）：

```
$ ./qc_harness2.exe %TEMP%\qc_r2\c2c.ini
GP_INT  TargetScanInterval       val=1      hit=1 migrated=0 rawGP=1 rawLEG[Logic]=8
GP_INT  EnableStarCraftFog       val=0      hit=1 migrated=0 rawGP=0 rawLEG[FogOfWar]=1
GP_INT  EnableUnitFog            val=0      hit=1 migrated=0 rawGP=0 rawLEG[FogOfWar]=1
GP_STR  VisibilityMode           val=vanilla  hit=1 migrated=0 rawGP=vanilla rawLEG[FogOfWar]=starcraft
GP_TOTAL hits=13 migrated=9 of 13
```

- `=0` 与 `=1` 两个方向都**显式命中并压过旧节**（0>8 的 `TargetScanInterval=0`；`EnableStarCraftFog=0` 压 `1`；`VisibilityMode=vanilla` 压 `starcraft`；`EnableUnitFog=0` 压 `1`）——opt-out 语义成立。
- 未显式键仍走旧节迁移（C2 的 11 项、C2c 的 9 项）⇒ 两级回退互不干扰。

**判定 b：CONFIRMED。** 四态（A/B/C1/C2，含 C2 双向）全部按要求实测通过；脚手架直接复用交付 cpp 原文辅助函数，非行为重述。

---

## 3. 核验项 c：cpp/h 不变性 —— **CONFIRMED**

```
$ sha256sum <交付>/blitter_hooks.cpp <交付>/ra2render.h
656e6b4e48cdd251f42d55c6da7b5e6b5a354284924437396c63e60588daada1 *blitter_hooks.cpp
10410c98642dc51ae1426be179e091440257fd42434e84f82d5b8059e9cf0c07 *ra2render.h
```

- 与 R1 判定书 `QC_P2_VERIFY.md` §0.2 记载的首版哈希 **`656e6b4e…` / `10410c98…` 逐位一致**。
- 行数 4006 / 495，与 R1 记载一致。
- ⇒ F1 修复**未波及代码件**；本轮唯一变更件 = `ra2render.ini`（`956e5d9a…` → `27c9a60c…`），与实现者申报一致。

**判定 c：CONFIRMED。**

---

## 4. 核验项 d：RECEIPT 勘误抽检 —— **CONFIRMED（1 条非阻断措辞观察）**

### 4.1 §0 的 R1 重交记录

- `RECEIPT.md:8` 标题：`## 0. 交付物与母本锚点（SHA-256 前 16 位；**R1 重交版**）`
- `RECEIPT.md:17`：`**R1 重交（2026-10-19，响应 QC_P2_VERIFY.md 判定 REFUTED）**：F1（:133 节头 ...）已修——现 ra2render.ini:151 为活动 [Gameplay] 节头 ...`
- `RECEIPT.md:154`：`## 9. R1 重交记录（响应 lead\goal3_configsplit_20261019\QC_P2_VERIFY.md）`，含 D2–D6 五行勘误表（:159-163）与重交哈希行（:163）。

⇒ §0 内的 R1 重交记录与独立 §9 重交记录**均存在**。
**观察（非阻断）**：文件内**不存在字面标记 `§0-R1`**（`grep -n "§0-R1" RECEIPT.md` → 无匹配，exit=1）；该记录以「§0 内加粗段 + §9 独立章」的形式承载，语义等价但标签与申报用词不同。

### 4.2 勘误后行号抽 3 条（对交付副本实测）

```
$ sed -n '706p;829p;911p' blitter_hooks.cpp
706:    int gapVal = GetIniIntEx("FogOfWar", "EnableGapProtection", 0, iniPath, &h_gap);
829:        h_fogcal = GetIniStringEx("FogOfWar", "FogStrengthPct", "auto", calBuf, sizeof(calBuf), iniPath);
911:        int fp = GetIniIntEx("FogOfWar", "FogProbe", 0, iniPath, &h_fp);
```

| 抽检项 | 勘误值（RECEIPT:160） | 实测 :706 / :829 / :911 | 判定 |
|---|---|---|---|
| `EnableGapProtection` | `:706` | :706 命中，键名/节名一致 | ✓ |
| `FogStrengthPct` | `:829`（另运行期 `:571`） | :829 命中；另测 `:571` 为 `GetPrivateProfileStringA("FogOfWar","FogStrengthPct","\x01[ZC10B:ABSENT]\x01",` | ✓ |
| `FogProbe` | `:911` | :911 命中 | ✓ |

三条抽检行号**全部命中且内容与键名匹配**，无错位。附测 `:726`（EnableSWChargeOpt）/`:895`（L4DirtyMode）亦命中。

**判定 d：CONFIRMED**（§0-R1 记录语义存在；3/3 抽检行号正确）。字面标签缺失仅属措辞层面，不影响交付内容。

---

## 5. 核验项 e：母本零写 —— **CONFIRMED**

起跑（§0.2）与终跑实测：

```
$ cd ra2render && sha256sum ra2render.ini blitter_hooks.cpp ra2render.h   [起跑]
fd9ebb32dcb6cda7952381baa10d24183ee98a7ea3e8e71fd8953a3a8d17b696 *ra2render.ini
b461ed21aa92bd5f04f73c096cd562ffe66369d0227dad23b5ec8c648b7e557e *blitter_hooks.cpp
b70cbf8d620e340ef0a1de1f5707b990c3e0d7ceabff29fd73fe9556c4c22cd4 *ra2render.h

$ cd ra2render && sha256sum ... && ls -la --time-style=full-iso ...   [终跑]
fd9ebb32dcb6cda7952381baa10d24183ee98a7ea3e8e71fd8953a3a8d17b696 *ra2render.ini
b461ed21aa92bd5f04f73c096cd562ffe66369d0227dad23b5ec8c648b7e557e *blitter_hooks.cpp
b70cbf8d620e340ef0a1de1f5707b990c3e0d7ceabff29fd73fe9556c4c22cd4 *ra2render.h
-rw-r--r-- 1 Administrator 197108 231875 2026-10-01 23:58:19.338774000 +0800 blitter_hooks.cpp
-rw-r--r-- 1 Administrator 197108 33415 2026-10-02 00:11:13.304955500 +0800 ra2render.h
-rw-r--r-- 1 Administrator 197108 24028 2026-09-30 21:50:07.069581700 +0800 ra2render.ini
```

- 三件 sha256 起跑 = 终跑，逐位一致。
- mtime 起跑 = 终跑（纳秒级一致），且均早于核验日 2026-10-19 达 17–19 天 ⇒ 母本在本轮**零写入**。
- 交付目录四件终跑 sha 亦与起跑一致（ini `27c9a60c…`、cpp `656e6b4e…`、h `10410c98…`、RECEIPT `09df88d8…`），核验未改动交付件。

**判定 e：CONFIRMED。**

---

## 6. 判定汇总

| 项 | 内容 | 判定 | 关键实测 |
|---|---|---|---|
| 起跑① | 交付四件哈希/行数 | 通过 | ini `27c9a60c55a8a1b4`/205 行、cpp `656e6b4e48cdd251`、h `10410c98642dc51a`、RECEIPT `09df88d886bed662` |
| 起跑② | 母本三件哈希 | 通过 | `fd9ebb32…` / `b461ed21…` / `b70cbf8d…` |
| a | 节头活性 | **CONFIRMED** | `grep -cE "^\[[^;]"` = 6；:10/:30/:49/:56/:62/**:151**；API `GetPrivateProfileSectionNamesA` = 6 节含 Gameplay；13 键全注释（:157…:205，均在 :151 之后） |
| b | 真 API 三态 | **CONFIRMED** | cpp :388-459 原文嵌入 + x86 cl（`CL_EXIT=0`）真实 `GetPrivateProfileStringA` 绝对路径：A 13/13 `hit=0` 落 1/position/0/vanilla/0/600/16/0/0/0/1/0/3 + 优化键 10/10；B 13/13 `migrated=1` 保留 8/starcraft/1；C1 读回 8、`rawLEG[Logic]=<ABSENT>`；C2 双向显式 0/1 压旧节 |
| c | cpp/h 不变 | **CONFIRMED** | `656e6b4e…` / `10410c98…` = R1 首版，逐位一致 |
| d | RECEIPT 勘误抽检 | **CONFIRMED**（1 条非阻断措辞） | §0:17 重交记录 + §9:154 记录；:706/:829/:911 三行号逐条命中；字面 `§0-R1` 标签不存在 |
| e | 母本零写 | **CONFIRMED** | 三件 sha 与 mtime 起跑=终跑；mtime 2026-09-30 / 10-01 / 10-02 |

---

## 7. 总判定

**CONFIRMED**

R1 的唯一实质缺陷 **F1（`[Gameplay]` 节头被注释，13 玩法键落 [FogOfWar] 节体、启用主路径失效）已真实修复**，且为可复核的行为级修复而非文本声称：

1. 结构层：交付 ini 恰 6 个活动节头，`[Gameplay]` 活动于 :151；真实 API 节枚举确认 `Gameplay` 可见；13 键全注释且位于该节体内。
2. 行为层：以交付 cpp **原文**辅助函数 + 真实 `GetPrivateProfileStringA` 实测，C1 态「去注释即生效」读回 8 且旧节无遮蔽；C2 态显式 `=0`/`=1` 双向压过旧节。
3. 无回归：A 态 13/13 落原版默认、10/10 优化键原值命中；B 态 13/13 旧节迁移、开启态保留。
4. 范围纪律：cpp/h 逐位未变，母本三件逐位未动、mtime 未刷新。

**非阻断瑕疵（1 条，不要求重交）**：`RECEIPT.md` 内不存在字面 `§0-R1` 标签（记录以 §0:17 加粗段 + §9 独立章承载，语义等价）。仅措辞层面，交付内容不受影响。

**未覆盖（如实标注，本轮未跑）**：
- 真机 `ra2render.log` 启动行读回（判据①运行时证据）——无游戏进程/未部署，**未跑**。
- 真机 DLL 卸载日志（判据④）、完整 DLL 构建链接与 `verify_hooks.py` 实跑——**未跑**（本轮仅编译了独立 harness，非 DLL 构建）。
- R1 已判定的其余各项（键位映射内容层、联机门控逐字节、卸载对称）未重开；本轮仅确认 cpp/h 未变，其结论据此延续。

---

## 8. 脚手架清单（全部 `%TEMP%\qc_r2\`，未落仓库）

`helpers.inc`（cpp:388-459 原文 72 行）、`qc_harness.cpp/.exe`、`qc_harness2.cpp/.exe`、`probe.cpp/.exe`、`probe2.cpp/.exe`、`probe3.cpp/.exe`、`build.bat`、`build2.bat`、`build_probe.bat`、`build_p23.bat`、`c1.ini`、`c2.ini`、`c2b.ini`、`c2c.ini`。

仓库内本轮唯一写入：本文件 `QC_P2_VERIFY_R2.md`。
