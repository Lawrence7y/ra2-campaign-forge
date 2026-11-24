# P0-RESIDUAL · 剩余缺口裁定（收口卡）

> 卡号 **P0-RESIDUAL**｜目标 `ra2youli\gamemd.exe`（只读，未改）
> SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（现场重算一致）
> ImageBase `0x400000`｜`.text=[0x401000,0x7E038D)`｜capstone 5.0.7 `skipdata=True`
> 写域仅 `lead\next_re_20261117_r14\P0_RESIDUAL\`；未改 `ra2youli\`/`COVERAGE\`/台账；未 git commit。
> 复跑：`work\resid_common.py` → `work\pipeline.py` → `work\verify_final.py` → `work\two_readings.py`。
> 不读 `vtables_v2.json`；虚表由 `.rdata` 自定界（复现 1214 表 / 14,044 槽）。
> 站点归属用「函数区间包含」(`Atlas.owner`)，未用 `entry_at_or_before`。

---

## 0 · 核心数字（给审计）

| 指标 | 值 |
|---|---:|
| **候选总数**（A–E 五通道并集，distinct 地址，in `.text` ∧ 不在任何 atlas 区间） | **2,972** |
| **去重排除数** | **481**（coverage 476+4 / probe 1；其中 476 与 outside_atlas 重合） |
| **去重后待裁定数** | **2,491** |
| **FUNC** | **1,096** |
| **NOT_FUNC** | **1,395** |
| **UNDECIDABLE** | **0** |
| 裁定轨分布 | vt_direct 0 / true_entry 2,491（413 个 vt 目标全部已在 coverage，去重阶段排除） |
| **各通道贡献（候选 distinct）** | A(E8/E9 rel32)=**404**；B(EB rel8)=**993**；C(虚表槽)=**597**（COL 413 + 无 COL 裸游程 184）；D(前向孤儿)=**1,365**（序言 487 + 叶形态 878）；E(atlas size 可疑)=**4**（0 个新反例，见 §4） |
| **FUNC 按通道** | D **1,054**；A **85**；C **1**（其余为多通道重叠标签，见 EVIDENCE） |
| **新分母 = 13,397 + FUNC** | **14,493** |
| **是否落入 13,755～13,792** | **否**（超出上界 701）⇒ 推翻估计区间，证据见 §3 |

> **停机核验已执行**：自算 FUNC=1,096 与给卡预期 358~395 不符，按 §954 纪律**先停下诊断、不凑数**。诊断确认差额不是枚举错误，而是估计区间的口径来源比定稿判据窄（详见 §3），故按定稿 R14-R10 如实报告并推翻区间。

---

## 1 · 方法（五通道互不依赖）

| 通道 | 定义 | 候选数(in `.text` ∧ 不在 atlas) |
|:--|:--|--:|
| A | capstone 线性扫 `skipdata=True` 全部 `E8/E9 rel32` 指令目标 | 404 |
| B | 全部 `EB rel8` 指令目标 | 993 |
| C | 自 `.rdata` 定界 vftable 的槽值（COL 验签极大游程）；另列**无 COL 裸游程**（函数指针表/无 RTTI 子表，敏感性） | 597（413+184） |
| D | 前向孤儿扫描：16B 对齐 ∧ 不在 atlas ∧ 前驱∈{nop,ret,jmp,int3} ∧ 非 JCC 起手 ∧ (栈帧序言 c4a **或** 叶形态 c4b) | 1,365（487+878，两集不交） |
| E | atlas `size` 列(decimal)可疑项：`entry+size` 处无「恰好以 pend 结尾」的 `ret/jmp` | 0 新反例（60 处 pend 无终止符，但落点非 16 对齐/非洞入口；见 `EVIDENCE\CHANNEL_E_SUSPICIOUS.tsv`） |

- 并集 distinct = 2,972；atlas `size` 十进制读取已核（如 `00401000 117` = 117 B）。
- 512 处 (vt,slot) 行去重为 413 不同地址；槽可被多表引用，按**地址**计数（避免重复计函数）。

---

## 2 · 去重明细（`DEDUP_VS_COVERAGE.tsv`，481 条）

| 排除原因 | 条数 | 说明 |
|---|---:|---|
| `in_coverage;in_outside_atlas` | 476 | 476 条 P0-GATE 已裁定入口，全部 ⊆ coverage；重复通道标注 |
| `in_coverage` | 4 | coverage 中非 outside 的非 atlas 入口（5 早期新增中 4 条被通道命中） |
| `in_probe` | 1 | `0x4824D4` = `Layer2_draw_prep_atlas_hole`（call_site）；§926 曾定为洞内真入口，probe 标为非函数——**已知冲突，按任务要求以 probe 排除**，见 §5 |
| 合计 | **481** | 去重后 2,491 待裁定 |

- 探针表 112 条中仅 1 条（`0x4824D4`）落在候选内；其余为 field_offset/global/call_site 等，不在候选地址。
- `DynamicVectorClass Items` 区（`0xA8EC7C/BC`、`0xB0F4EC`）无候选命中（c6 通过）。

---

## 3 · 裁定结果与差额归因（关键）

### 3.1 分轨判据（R14-R10，未增删）
- **vt_direct**（来源=COL 虚表槽）：A1 槽值在 `.text` / A2 前驱∈{nop,int3,ret,jmp} / A3 结构良好 vftable / A4 未入 coverage。全过即 FUNC。
  - ⚠️ 未用「体长≥16B」或「首字节非 E8」当否定（§943 教训）。本卡 413 个 COL 目标全部在 coverage ⇒ A4 失败在去重阶段，vt_direct 轨残余 0。
- **true_entry**（来源=分支目标/前向）：c1 16B 对齐 / c2 首字节∉{E8,E9,EB} / c3 前驱非 fall-through / c4 栈帧序言 **或** 叶形态(体长≥2B 且以 ret/jmp 终结) / c5 非跳表 / c6 非已知非函数容器。

### 3.2 裁定分布（严格 R14-R10，主交付）
| verdict | 数 |
|---|---:|
| FUNC | **1,096** |
| NOT_FUNC | **1,395**（subkind：jump_target/call_site/internal_label/jump_table/data/stub，见 EVIDENCE） |
| UNDECIDABLE | **0** |

### 3.3 FUNC 的构成与三口径（差额归因）
| 口径 | FUNC 构成 | FUNC | 新分母 | 与 13,755~13,792 |
|---|---|---:|---:|---|
| **严格 R14-R10（主交付）** | c4a 399 + c4b(有引用) 85 + c4b(纯叶,无引用) 612 | **1,096** | **14,493** | 超上界 **+701** |
| 保守：c4a + 有引用 c4b | 399 + 85 | 484 | 13,881 | 超上界 +89 |
| 基线：仅 c4a（=旧 R14-R9 口径） | 399 | 399 | 13,796 | 超上界 **+4** |

**差额根因（证据）**：
1. §952/§954 给的估计区间 13,755~13,792 = 12,916 + 839~876，其可证项 839 = 413 VT + 65 分支 + **361 FW-only**。而 361 FW-only 是 P0-CLOSE 用 **c4a-only**（首字节 `55`/`83 EC`/`81 EC`）前向通道测得（见 `P0_CLOSE\d1_orphan.py:57-59`）。
2. §954 §2.1 明确记载：**R14-R9 的 c4 仅 c4a ⇒ 系统性误杀叶函数 389 条**；R14-R10 才加入 c4b（体长门槛后由 16B 放宽为 ≥2B）以补回。本卡按**定稿 R14-R10** 执行，故纳入 c4b。
3. 本卡 c4a-only 实测 **399**（= 361 FW-only + 38 条 P0-CLOSE 贪心 c5 抑制、R14-R10 不抑制的近距入口），新分母 13,796 —— 与估计上界 13,792 **仅差 4**。⇒ 估计区间的下沿/上沿基本对应 c4a-only 口径。
4. 严格的 c4b 额外纳入 **697** 条无引用叶形态孤儿（16B 对齐 + 前驱 nop/ret/jmp/int3 + 首指令为 `push ebx/esi/edi` 或 `mov reg,[reg+disp]` + 自包含体以 ret/jmp 终结）。抽样 18 条（seed 20261117，见 `work\sample_c4b.py`）逐条形如真实函数入口（见 §6）。基线检验：在「16 对齐∧前驱终止符∧非 JCC∧非 c4a」的 6,998 个合格地址中 12.5% 过 leaf_pattern；随机 2,000 个 16 对齐地址仅 3.6% —— leaf_pattern 有 ~3.5x 富集，非纯噪声，但**无引用**，属 `[静态推断]`。

⇒ **结论**：13,755~13,792 是 c4a-only 口径的估计，未覆盖定稿 c4b 的叶函数；按 R14-R10 定稿判据，新分母应为 **14,493**（FUNC=1,096）。保守下界（只认有引用的 c4b）为 13,881。

---

## 4 · 通道 E（atlas size 审计）结论

- 对每个 atlas entry 取 `pend=entry+size`（size 十进制），在 `[pend-15,pend)` 找「恰好以 pend 结尾」的指令：
  - **60 处** pend 处无 `ret/jmp` 结尾；但逐一核对，其落点均非 16 对齐、或不在任何洞内、或首字节为典型函数中部（`push/pop/mov` 中段），**未发现新的「size 吞掉后一函数」反例**。
  - 60 条明细见 `EVIDENCE\CHANNEL_E_SUSPICIOUS.tsv`。
- 与 P0-CLOSE §2.3「上一函数 413/413 已在 pend 以 ret/jmp 终结」一致 ⇒ C10 审计的 size 质疑仍不成立。

---

## 5 · 已知冲突与限制（如实披露）

1. **`0x4824D4`**：probe 标 `call_site`（非函数），§926 定为 `.text` 洞内真入口（自然解码 ≥339 条）。本卡按任务「减去 probe」排除，但同时它是本卡通道 A 的候选。**判据冲突未在卡内裁定**（本卡不产新语义结论），留 P1。
2. **`0x7775C0`**（`WndProc_registered`，S09，coverage 中非 atlas 真函数）未被 A–E 任一通道命中 —— 它是 5 早期新增之一，靠注册调用点入表、无标准入口签名。⇒ 本卡五通道并非全镜像枚举的完备证明，只是「不在 atlas 区间候选」的可复核重建。
3. **c4b 无引用叶形态 612 条**为 `[静态推断]`：有对齐+前驱+自包含+形态四证，但无任何直接引用（既非分支目标、也非虚表槽、也非数据指针）。是否真为独立函数需 P1 用数据段函数指针表/异常表/注册回调裁定；本卡按定稿判据判 FUNC，未凑数、未硬判。

---

## 6 · 证据抽样（c4b 纯叶形态，seed=20261117，18 条）

```
00407330 body=47   term=ret  prev=nop  push esi | mov esi,[edx+8] | push edi
0040B010 body=66   term=ret  prev=nop  push ebx | mov bl,[esp+8] | push esi
0042E800 body=17   term=ret  prev=nop  mov eax,[esp+4] | mov ecx,[ecx+8] | shl eax,4
0047A6D0 body=19   term=ret  prev=nop  mov eax,[esp+8] | push eax | call [0x7E11E0]
004A5E50 body=79   term=ret  prev=nop  push ebx | mov ebx,[esp+0x10] | push ebp
00517360 body=134  term=ret  prev=nop  push ebx | mov bl,[ecx+2] | push esi
0052D790 body=92   term=jmp  prev=nop  mov eax,[esp+0x10] | push ebx | mov ebx,[esp+0x10]
00561350 body=122  term=ret  prev=nop  mov eax,[esp+0x10] | push ebx | mov ebx,[esp+0x10]
005C9AE0 body=25   term=ret  prev=nop  mov eax,[esp+4] | mov ecx,[esp+8] | mov eax,[eax]
005D9060 body=97   term=ret  prev=nop  push ebx | mov ebx,[esp+8] | push ebp
005EFF00 body=65   term=ret  prev=nop  mov eax,[esp+0x10] | push ebx | mov ebx,[esp+0xc]
00632A70 body=36   term=ret  prev=nop  mov eax,[esp+0xc] | mov edx,[esp+4] | push esi
00632AA0 body=30   term=ret  prev=nop  mov eax,[esp+4] | push esi | mov esi,ecx
00633AA0 body=4    term=ret  prev=nop  mov eax,[ecx+8] | ret
006E0ED0 body=25   term=ret  prev=nop  mov eax,[esp+4] | test eax,eax | je
006E3FB0 body=93   term=ret  prev=nop  mov eax,[esp+4] | push esi | mov esi,ecx
0070FE40 body=13   term=ret  prev=nop  mov eax,[esp+4] | mov [ecx+0x1D0],eax | ret 4
```

全部 16B 对齐、前驱 `nop` 填充、首指令合理、体自包含以 `ret/jmp` 终结 —— 形如 MSVC 无栈帧/短叶函数入口。

---

## 7 · 分级

| 结论 | 分级 |
|---|---|
| SHA256 / PE 段归属 / 五通道枚举计数 / 集合交集 / 去重 481 / verdict 三数 / 通道贡献 | `[已证]` |
| c4a 序言入口（399）为函数 | `[静态推断]`（对齐+前驱+序言+自包含，无运行期确认） |
| c4b 有引用入口（85）为函数 | `[静态推断]`（分支引用+对齐+前驱+体自包含） |
| c4b 纯叶形态入口（612）为函数 | `[静态推断]`（四证但无引用，需 P1 复核） |
| 推翻 13,755~13,792 | `[静态推断]`（估计口径来自 c4a-only，本卡定稿口径含 c4b；差额 697 逐条有形态证据） |
| `0x4824D4` 归属冲突、612 条是否有调用者 | `[未证]` |

---

## 8 · 交付

| 文件 | 内容 |
|---|---|
| `CANDIDATES_ALL.tsv` | 2,972 行：addr / chan / first_insn / prev_byte / align16 / source_detail |
| `DEDUP_VS_COVERAGE.tsv` | 481 行去重明细 |
| `RESIDUAL_ADJUDICATION.tsv` | 2,491 行：addr / chan / verdict / subkind / evidence |
| `RESIDUAL_SUMMARY.md` | 本文件 |
| `PROGRESS.md` | 进度（≤60 行） |
| `EVIDENCE\ADJUDICATION_FULL.tsv` | 全部 2,491 行逐条完整列（不截断） |
| `EVIDENCE\TWO_READINGS.tsv` / `CONSERVATIVE_FUNC.tsv` | 双口径交叉核对 |
| `EVIDENCE\CHANNEL_E_SUSPICIOUS.tsv` / `VT_TABLES.tsv` / `stats.json` | 通道 E、虚表定界、统计 |
| `work\*.py` | 可复跑脚本（resid_common / explore / diag_* / pipeline / verify_final / two_readings / sample_c4b） |
