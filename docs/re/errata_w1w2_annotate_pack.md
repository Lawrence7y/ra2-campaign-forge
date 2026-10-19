# Lead 批注包 · R-ERR-PACK · W1/W2 就地加注模板

> [META]
> 任务=R-ERR-PACK · 日期 2026-09-30 · 性质=**只出模板不改冻结源**
> 依据：`docs/re/errata_sync_master_table.md`（R-E01..E10）+ `out/re_work/re_sprint/R_errata_sync/annotate_list_for_lead.md` + `batch_order.md`
> 本包范围：**W1（机器码类 E08/E10/E01/E03）+ W2（语义 E09/E04）**
> 可写域：本文 + `out/re_work/re_sprint/R_err_pack/**`
> 禁写：台账 `REVERSE_ENGINEERING_AND_PATCHES.md` / 看板 / 实际改 deep_dive 本体（本卡**只出模板**）
> 加注格式（项目惯例）：`【勘误 2026-09-30 · R-Exx · errata_sync】原文「…」→ 订正为：…原文保留不删字。`
> 硬约束：**原文保留不删字**；只追加【勘误】块或行内标注；波及文件全覆盖后才可关波次。

---

## 一、W1 · 机器码类（地址 / 字节序 / 指令长度 / 取模编码）

### W1-1 · R-E08 · 槽 69 原 DWORD 字节序 BE→LE

| 项 | 内容 |
|:---|:---|
| 状态 | **已加注**（F-04 订正 9 处，含勘误块）；本波 = **回归确认 + 残留模板** |
| 旧文 | `00 62 CE C0` / `00 62 E2 80`（大端书写） |
> 【W3 勘误 · W3-A6/ISSUE-PARTICLE-BE-BYTES】改前：00 62 CE C0；改后：C0 CE 62 00 / 80 E2 62 00 (小端 LE)；依据：errata_sync_master_table.md:23 (R-E08); FIXPACK_F01-F13_report.md F-04；分级：P0
| 新文 | **LE** `C0 CE 62 00` / `80 E2 62 00`（= DWORD `0x0062CEC0` / `0x0062E280`） |
| 风险 | BE 照抄写入 `0xC0CE6200` → 崩 |
| 证据 | `gamemd.exe` 机读；`anchor_claims.txt:72-73`；`FIXPACK_F01-F13_report.md` F-04 |

**主加注点**：`landing_pack_particle.md:66,67`（F-04 已完成，原文已保留 + 勘误块在 `:76`）

**残留可就地加注模板**（若全库回归扫描再命中 BE 旧值，粘贴于命中行下方）：

```
【勘误 2026-09-30 · R-E08 · errata_sync】原文 DWORD 字节序为大端书写「00 62 CE C0 / 00 62 E2 80」。订正为小端 LE「C0 CE 62 00 / 80 E2 62 00」（= 0x0062CEC0 / 0x0062E280）。BE 照抄将写入 0xC0CE6200 → 崩。权威：FIXPACK F-04 / anchor_claims.txt:72-73。原文保留不删字。
```

**回滚写回值同步口径**（凡引用回滚表处）：`RemoveVTableHooks` 写回 **`C0 CE 62 00` / `80 E2 62 00`（LE）**，不得写 BE。

---

### W1-2 · R-E10 · H-D5 取模 `83 E0 FF` → `0F B6 C0`

| 项 | 内容 |
|:---|:---|
| 状态 | **已加注**（`landing_pack_net_fix.md:400` 已含勘误修复注）；本波 = **回归确认 + 历史产物只登记** |
| 旧文 | `83 E0 FF`（注释写 `and eax,0xFF`） |
| 新文 | **`0F B6 C0`**（`movzx eax,al`） |
| 风险 | `83 /4 ib` 立即数符号扩展 ⇒ `and eax,0xFFFFFFFF` = **no-op**，高位不清零 → 帧>255 越界写 → 1024 帧 `0xC0000005` |
| 证据 | `landing_equivalence_static_proof.md:90-93`；`cross_doc_consistency_audit.md:291-293,401`；ATLAS `:315,:2172`；Lead v20–v22 |

**主加注点**：`landing_pack_net_fix.md:400`（已完成，行内已含「★ 勘误修复」）

**历史产物只登记不改**（保持冻结，作时间线）：`out/re_work/re_sprint/S15/**` / `S18/**` 内 `TRAMP_HD5` 草案与 `calc_tramp_bytes.py` 旧字节串、`verify_trampolines.py` 历史注记（`b_class_static_closeout.md:101` 已标）。

**残留可就地加注模板**（若在非历史报告中再命中生产引用 `83 E0 FF`）：

```
【勘误 2026-09-30 · R-E10 · errata_sync】原文「83 E0 FF」注释为 and eax,0xFF，实为符号扩展 no-op（and eax,0xFFFFFFFF），高位不清零会导致帧>255 越界写、1024 帧 0xC0000005。订正为「0F B6 C0」（movzx eax,al，等长 3B）。跳板 +0x10 已采纳。权威：landing_pack_net_fix.md:400 / ATLAS:315,2172 / Lead v20-v22。原文保留不删字。
```

**生产红线**：全跳板 `+0x10` 必须 `0F B6 C0`；TC-ST-01 一票否决项。

---

### W1-3 · R-E01 · `0x568297` → `0x0056829A`（★ 本波主加注）

| 项 | 内容 |
|:---|:---|
| 状态 | **未加注**（冻结卡）；**代码轨已勘误**（`ra2render.h:96` / `ra2render.ini:140` / 日志 `:591` 均 `0x56829A`） |
| 旧文 | `0x568297` = `or [ecx+0x12C],0x10` |
| 新文 | 实际 VA **`0x0056829A`**（`83 89 2C 01 00 00 10`）；`0x568297` 处是 `50 DC AB 00`（`mov ecx,0xABDC50` 立即数尾巴） |
| 证据 | `RESULT_GAP_P21.md` §5 E-1；`p223_readiness_check.md:105`；`landing_pack_gap_p21_a3.md:205` |
| 落地风险 | **无**（G0 门禁不引用此 VA） |

#### 模板 A（表行 / 语义边界表，粘贴于命中行**下一行**或行后注释列）

```
【勘误 2026-09-30 · R-E01 · errata_sync】原文 VA「0x568297」错误。该指令实际在 VA 0x0056829A（83 89 2C 01 00 00 10 = or dword [ecx+0x12C], 0x10）；0x568297 处字节为 50 DC AB 00，属上一条 mov ecx,0xABDC50 的立即数尾巴。权威：RESULT_GAP_P21.md §5 E-1。原文保留不删字。
```

#### 模板 B（行内短注，适用于表格单元格 / 语义边界列，可跟在原 VA 后）

```
【勘误 R-E01：实址 0x0056829A，非 0x568297】
```

#### 逐锚点粘贴表

| # | 目标文件:行 | 锚点（原文保留） | 模板 |
|:---:|:---|:---|:---:|
| 1a | `landing_pack_gap_p21.md:39` | ``\| `0x568297` \| `83 89 2C 01 00 00 10` \|`` | A |
| 1b | `landing_pack_gap_p21.md:47` | ``\| `0x568297` `or [ecx+0x12C], 0x10` \|`` | A 或 B |
| 1c | `gap_protection_install_spec.md:39` | `0x568297 CopyFlags\|=0x10` | A 或 B |
| 1d | `landing_pack_gap_merge_checklist.md:37` | `0x568297 CopyFlags\|=0x10`（P-2.1 语义边界列） | A 或 B |
| 1e | `gap_psychic_reveal_deep_dive.md` §3.3 | §3.3 内引用 `0x568297` 处 | A |

**代码轨口径（不改，仅核对）**：现码/ini/日志已是 `0x56829A`，与本文订正一致。

---

### W1-4 · R-E03 · T-a 指令长度 5B→7B（★ 本波主加注）

| 项 | 内容 |
|:---|:---|
| 状态 | **部分**：`h20c_private_sweep_spec.md:40-43` / `zcode_master_implementation_ticket_v2.md:73` 已注；`radar_sweep_sw_deep_dive.md` **仍写 5B 未加注** |
| 旧文 | `0x6CD7C4` 处 5B 补丁点；`s_origCase11Bytes[5]` |
> 【W3 勘误 · W3-A6/ISSUE-RADAR-SWEEP-5B】改前：0x6CD7C4` 处 5B；改后：0x006CD7C4 处指令为 7B (8A 84 24 EC 01 00 00)；依据：ra2youli/gamemd.exe:0x2CD7C4; errata_sync_master_table.md:18 (R-E03); h20c_private_sweep_spec.md:40-43；分级：P0
| 新文 | 该指令为 **7B** `mov al,[esp+0x1EC]`（`8A 84 24 EC 01 00 00`）；T-a **必须 7B**（`E9`+2×`90`），禁 5B 切断指令 |
| 证据 | `h20c_private_sweep_spec.md:40-43`（定谳）；`R_h20c/EVIDENCE_INDEX.md:18`；ticket v2 `:73` |
| 连带 | `s_origCase11Bytes[5]` → `[7]` |

#### 模板（粘贴于锚点下方）

```
【勘误 2026-09-30 · R-E03 · errata_sync】原文「5B」错误。实测 0x6CD7C4 处指令为 7 字节 mov al,[esp+0x1EC]（8A 84 24 EC 01 00 00）；T-a 必须 7B 补丁（E9+2×90），5B jmp 会切断指令。推荐改挂 T-b（ClickFire 0x6CB920 / Launch 0x6CC390 5B）。权威：h20c_private_sweep_spec.md §T-a 边界勘误。原文保留不删字。
```

#### 逐锚点粘贴表

| # | 目标文件:行 | 锚点（原文保留） | 连带订正 |
|:---:|:---|:---|:---|
| 3a | `radar_sweep_sw_deep_dive.md:120` | `` `0x6CD7C4` 处 `mov al,[esp+0x1EC]` 前，5B `` | 加模板 |
| 3b | `radar_sweep_sw_deep_dive.md:140` | `5B E9 rel32 + 跳板` / `还原 5B` | 加模板 + 注「T-a 则 7B」 |
| 3c | `radar_sweep_sw_deep_dive.md:204` | `` `0x6CD7C4` 5B（若 T-a）` / `s_origCase11Bytes[5]` `` | 加模板 + `[5]`→`[7]` 行内标注（原文保留） |

**推荐模板短注（表格内）**：

```
【勘误 R-E03：T-a 必须 7B，备份 s_origCase11Bytes[7]】
```

---

## 二、W2 · 语义不变量 / 红线

### W2-1 · R-E09 · `OccuredEvents` 位序 = 事件链位次

| 项 | 内容 |
|:---|:---|
| 状态 | **已加注**（新文档均已钉死；`trigger_system_manifest` DA2-T1 已修字段名）；本波 = **回归确认 + 早期未钉死处补钉** |
| 旧文 | （隐含）位序或与 event kind 号相关 / 未明确 |
| 新文 | **硬不变量**：`bit i` = 事件链中第 i 个 Event 是否已发生（**与 kind 数值无关**，`ebx` 逐轮 `inc`）。`[Events]` 序重排 = 位图整体错位 |
| 证据 | `trigger_runtime_deep_dive.md:161`；`trigger_save_pollution.md:121-123`（G6）；ATLAS `:2758`（C10）；`0x72650B = D3 E5`（`1<<eventIndex`） |
| 红线 | 存档敏感序三元组；**禁重排 `[Events]`** |

#### 模板（用于任何「位序语义未钉死」或可能被读成 kind 号的段落旁）

```
【勘误 2026-09-30 · R-E09 · errata_sync】位序硬不变量：OccuredEvents bit i = 事件链中第 i 个 Event 是否已发生，与 event kind 数值无关（ebx 逐轮 inc；0x72650B = D3 E5 = 1<<eventIndex）。[Events] 序重排 = 位图整体错位，存档必坏。TriggerClass Save/Load 必须严格保持链序。权威：trigger_runtime_deep_dive.md:161 / trigger_save_pollution.md G6 / ATLAS C10。原文保留不删字。
```

#### 回归确认点（不改文，只核对口径一致）

| 文件 | 应含口径 | 动作 |
|:---|:---|:---|
| `trigger_runtime_deep_dive.md:161` | 位序 = 链位次，与 kind 无关 | 已钉，回归 |
| `trigger_save_pollution.md:121-123` | G6 硬不变量 | 已钉，回归 |
| `ARCHITECTURE_ATLAS.md:2758` | C10 链序契约 | 已钉，回归 |
| `trigger_system_manifest.md` | 字段名 DA2-T1 已修 | 已修，回归 |
| 早期未钉死文档 | 若 grep 发现「位序」无不变量句 | **补钉模板** |

---

### W2-2 · R-E04 · `SW+0xF8` 死键

| 项 | 内容 |
|:---|:---|
| 状态 | **已加注**（`sw_radius_deadkey_fix_spec.md` 即定谳文档；deep_dive 亦已写「死写」）；本波 = **回归确认 + ini 注释残留动作** |
| 旧文 | `RadarSweepRadiusCells` 写 `SW+0xF8` 可改开图/杀伤半径 |
| 新文 | **死写**：12/12 发射 case 均不读 `+0xF8`；唯一活消费 = 鼠标瞄准圈 `fld [edi+0xF8]@0x6DC1C6`。真实开图半径 = `Rules+0xFEC`（i32），被 `min(10,·)` 夹紧。`SW+0xF8`=float ≠ `Rules+0xFEC`=i32 |
| 证据 | `sw_radius_deadkey_fix_spec.md` §1/§2；`radar_sweep_sw_deep_dive.md` §3.1；`gap_psychic_reveal_deep_dive.md:124`（C-4） |
| 红线 | **禁止**把发射半径改读 `SW+0xF8`（float 当 i32 ⇒ 爆炸半径） |

#### 模板（用于任何仍把 `SW+0xF8` 写成「开图/杀伤半径」的段落旁）

```
【勘误 2026-09-30 · R-E04 · errata_sync】原文「SW+0xF8 可改开图/杀伤半径」为死写定谳：12/12 发射 case 均不读 +0xF8；唯一活消费 = 鼠标瞄准圈 fld [edi+0xF8]@0x6DC1C6（UI-only）。真实开图半径 = Rules+0xFEC（i32），被 min(10,·) 夹紧。SW+0xF8=float ≠ Rules+0xFEC=i32，禁止把发射半径改读 SW+0xF8。权威：sw_radius_deadkey_fix_spec.md §1/§2。原文保留不删字。
```

#### 残留动作（配置注释，非 deep_dive）

| 目标 | 现文 | 订正 | 状态 |
|:---|:---|:---|:---|
| `ra2render.ini:92-93`（及 `ra2bench`/`ra2youli` 同款） | `; 雷达扫描超武探测半径（格子数…）` | `; 瞄准圈显示半径（UI-only）；真实开图半径见 Rules.PsychicRevealRadius / 私有窗` | **待执行**（本卡不出 ini 改动，只登记） |

---

## 三、执行顺序与范围清单

### 3.1 波次执行顺序（对齐 `batch_order.md` W1/W2）

| 序 | 波次 | 条目 | 动作性质 | 依赖 |
|:---:|:---:|:---:|:---|:---|
| 1 | W1 | R-E08 | 回归确认（F-04 已加注）+ 残留模板 | 无 |
| 2 | W1 | R-E10 | 回归确认（net_fix:400 已加注）+ 历史只登记 | 无 |
| 3 | W1 | **R-E01** | **就地加注 ×5**（主任务） | 无（可与 4 并行） |
| 4 | W1 | **R-E03** | **就地加注 ×3**（主任务） | 无（可与 3 并行） |
| 5 | W2 | R-E09 | 回归确认 + 未钉死处补钉 | 独立于 W1 |
| 6 | W2 | R-E04 | 回归确认 + ini 注释残留登记 | 独立于 W1 |

> W1 与 W2 文件集不相交，**可并行派工**。同文件多条合并一次开封，减少冻结源写次数。

### 3.2 可加注文件（Lead 解冻后粘贴）

| 条目 | 文件 | 动作 |
|:---:|:---|:---|
| E01 | `docs/re/landing_pack_gap_p21.md` | :39,:47 加注 |
| E01 | `docs/re/gap_protection_install_spec.md` | :39 加注 |
| E01 | `docs/re/landing_pack_gap_merge_checklist.md` | :37 加注 |
| E01 | `docs/re/gap_psychic_reveal_deep_dive.md` | §3.3 加注 |
| E03 | `docs/re/radar_sweep_sw_deep_dive.md` | :120,:140,:204 加注 |
| E08 | `docs/re/landing_pack_particle.md` 等 | 已加注；仅残留命中时补 |
| E10 | `docs/re/landing_pack_net_fix.md` | 已加注；仅残留命中时补 |
| E09 | trigger 系文档未钉死处 | 补钉模板 |
| E04 | 仍写「开图半径」的段落 | 补钉模板 |

### 3.3 保持冻结 / 只登记不改

| 类别 | 路径 | 理由 |
|:---|:---|:---|
| 台账 | `REVERSE_ENGINEERING_AND_PATCHES.md` | 禁写 |
| 看板 | `docs/RE_COORDINATION.md` | 禁写 |
| E10 历史产物 | `out/re_work/re_sprint/S15/**`、`S18/**`（TRAMP_HD5 草案、`calc_tramp_bytes.py`、`verify_trampolines.py` 历史串） | 保留时间线 |
| E06 历史扫描 | 引用 `_delete` 4498 的旧扫描报告 | 只标口径，不回改 |
> 【W3 勘误 · W3-A6/ISSUE-DELETE-CALLERS-COUNT】改前：_delete` 4498；改后：_delete 调用点 >= 4499 处 (模式扫描口径，含 0x0074836A)；依据：errata_sync_master_table.md:21 (R-E06); ARCHITECTURE_ATLAS.md:4626；分级：P2
| 已定谳源 | `sw_radius_deadkey_fix_spec.md`、`h20c_private_sweep_spec.md` | 自带勘误，不再叠加 |
| ATLAS 定谳注 | `ARCHITECTURE_ATLAS.md` 内已有注记处 | 已加注，不重复 |
| 配置文件 | `ra2render.ini` 等 | 本卡**只登记**残留动作，不改 |

---

## 四、验收（加注后不得删原文 + diff 自检）

### 4.1 硬验收

1. **原文保留不删字**：所有锚点原句/原数字/原 VA 仍在文件中（只追加，不替换删除）。
2. **勘误块可机械定位**：补丁块前 40 字符锚点 grep 命中。
3. **波及文件全覆盖**：E01×5 + E03×3 全部有注。
4. **不触碰台账 / 看板 / 冻结历史产物**。
5. **代码轨一致**：`0x56829A` / `0F B6 C0` / LE 槽值与现码一致。

### 4.2 diff 自检命令（PowerShell，仓库无 git，用哈希 + 内容双检）

**Step 0 · 加注前先做基线快照**（执行加注的代理必做）：

```powershell
$targets = @(
  'docs/re/landing_pack_gap_p21.md',
  'docs/re/gap_protection_install_spec.md',
  'docs/re/landing_pack_gap_merge_checklist.md',
  'docs/re/gap_psychic_reveal_deep_dive.md',
  'docs/re/radar_sweep_sw_deep_dive.md'
)
$base = 'out/re_work/re_sprint/R_err_pack/baseline'
New-Item -ItemType Directory -Force -Path $base | Out-Null
foreach ($f in $targets) {
  $n = Split-Path $f -Leaf
  Copy-Item -LiteralPath $f -Destination (Join-Path $base $n) -Force
  (Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash + "  $f" |
    Out-File -Append (Join-Path $base 'MANIFEST.sha256')
}
```

**Step 1 · 原文仍在（不得删字）** — 以下每条应 **hits≥1**：

```powershell
# E01 原文锚点（旧 VA 必须仍可 grep 到）
Select-String -Path 'docs/re/landing_pack_gap_p21.md' -Pattern '0x568297' -SimpleMatch
Select-String -Path 'docs/re/gap_protection_install_spec.md' -Pattern '0x568297' -SimpleMatch
Select-String -Path 'docs/re/landing_pack_gap_merge_checklist.md' -Pattern '0x568297' -SimpleMatch
# E03 原文锚点（旧 5B 必须仍可 grep 到）
Select-String -Path 'docs/re/radar_sweep_sw_deep_dive.md' -Pattern '5B' -SimpleMatch
Select-String -Path 'docs/re/radar_sweep_sw_deep_dive.md' -Pattern 's_origCase11Bytes[5]' -SimpleMatch
```

**Step 2 · 勘误块已加** — 以下每条应 **hits≥1**：

```powershell
Select-String -Path 'docs/re/landing_pack_gap_p21.md','docs/re/gap_protection_install_spec.md','docs/re/landing_pack_gap_merge_checklist.md','docs/re/gap_psychic_reveal_deep_dive.md' -Pattern 'R-E01'
Select-String -Path 'docs/re/radar_sweep_sw_deep_dive.md' -Pattern 'R-E03'
```

**Step 3 · 只增不删（行数不减 + 新增行含勘误）**：

```powershell
$base = 'out/re_work/re_sprint/R_err_pack/baseline'
foreach ($f in $targets) {
  $n = Split-Path $f -Leaf
  $old = Get-Content -LiteralPath (Join-Path $base $n)
  $new = Get-Content -LiteralPath $f
  $oldCnt = $old.Count; $newCnt = $new.Count
  $added = Compare-Object $old $new | Where-Object SideIndicator -eq '=>' | ForEach-Object InputObject
  $removed = Compare-Object $old $new | Where-Object SideIndicator -eq '<=' | ForEach-Object InputObject
  # 验收：removed 为空（或仅为空行/空白），added 含【勘误
  "FILE=$n  old=$oldCnt new=$newCnt removed=$($removed.Count) added=$($added.Count)"
  $removed | ForEach-Object { "  REMOVED: $_" }   # 必须无输出或仅空白
  $added | Select-String -Pattern '【勘误' | ForEach-Object { "  ERRATA: $($_.Line.Substring(0,[Math]::Min(60,$_.Line.Length)))" }
}
```

**Step 4 · 禁写面未动**（哈希不变）：

```powershell
Get-FileHash -LiteralPath 'REVERSE_ENGINEERING_AND_PATCHES.md','docs/RE_COORDINATION.md' -Algorithm SHA256
# 与加注前基线比对应完全一致
```

**Step 5 · 机器码口径回归（W1）**：

```powershell
# E08：无残留 BE 旧值（若命中则必须带 F-04/R-E08 勘误块）
Select-String -Path 'docs/re/*.md' -Pattern '00 62 CE C0|00 62 E2 80'
# E10：生产引用无 83 E0 FF（历史 S15/S18 冻结件除外）
Select-String -Path 'docs/re/landing_pack_net_fix.md' -Pattern '83 E0 FF'
# E01：代码轨已是 0x56829A
Select-String -Path 'ra2render/ra2render.h','ra2render/ra2render.ini' -Pattern '56829A'
# E03：deep_dive 加注后 7B 口径可定位
Select-String -Path 'docs/re/radar_sweep_sw_deep_dive.md' -Pattern '7B|s_origCase11Bytes\[7\]'
```

**Step 6 · 语义红线回归（W2）**：

```powershell
# E09：位序不变量句可定位
Select-String -Path 'docs/re/trigger_runtime_deep_dive.md','docs/re/trigger_save_pollution.md','docs/re/ARCHITECTURE_ATLAS.md' -Pattern '位序 = 事件链|位序 = 链'
# E04：死键定谳句可定位
Select-String -Path 'docs/re/sw_radius_deadkey_fix_spec.md' -Pattern '死写|12/12'
```

### 4.3 波次出口判据

| 波次 | 出口 |
|:---:|:---|
| W1 | 所有「会写进补丁字节/回滚表」的地址、字节序、指令长度、取模编码无旧值误用；E01×5、E03×3 加注完成且原文保留 |
| W2 | 存档/联机红线文档无歧义：位序不变量与死键语义均可机械定位；ini 注释残留已登记待办 |

---

## 五、产物索引

| 产物 | 路径 |
|:---|:---|
| 本批注包 | `docs/re/errata_w1w2_annotate_pack.md` |
| 执行清单（勾选用） | `out/re_work/re_sprint/R_err_pack/exec_checklist.md` |
| 自检脚本 | `out/re_work/re_sprint/R_err_pack/verify_annotate.ps1` |
| 上游总表 | `docs/re/errata_sync_master_table.md` |
| 上游可加注清单 | `out/re_work/re_sprint/R_errata_sync/annotate_list_for_lead.md` |
| 上游批次卡 | `out/re_work/re_sprint/R_errata_sync/batch_order.md` |

---

*依据：R-E01..E10 总表 · annotate_list_for_lead · batch_order W1/W2 · 本卡只出模板不改冻结源 · 原文保留不删字。*
