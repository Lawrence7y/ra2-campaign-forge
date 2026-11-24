# NAMED_PUSH_AUDIT18 — SUMMARY（异族独立审计）

> 审计对象：`NAMED_PUSH_S15_B1\delta.tsv` 全部 **10 行**（DeepSeek/S14 家族产出，执行器自报 rate 1.0000）
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT18`
> 身份：**异族独立审计员**（非 Hy4、非 DeepSeek）；只采信本人自写脚本反汇编的字节；执行器 `ROW_*.txt`/`REPORT.md` 仅当线索。
> 二进制：`ra2youli\gamemd.exe` SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ✅
> 工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26；证据脚本 `work\re_lib.py`/`scan_all.py`/`verify1..3.py`，原始输出 `work\scan_all.txt`/`verify1.txt`/`verify2.txt`/`verify3.txt`（全部可复算）。

## 取行方式（卡面要求写进报告）

`Import-Csv NAMED_PUSH_S15_B1\delta.tsv -Delimiter "`t"`，6 列 10 数据行全部属 S15：
`006E3E30 / 006E57A0 / 006E6470 / 0071F930 / 0071FA80 / 00726860 / 007268D0 / 00726950 / 00727BF0 / 00727C80`（大写无 0x）。

## 总裁定

# **PASS 10 / FAIL 0**

- 执行器自报 rate 1.0000 在逐行字节复核下**得到确认**；无 FAIL 的 entry。
- 逐行五环结论 + 地址字节见 `VERDICT.md`；逐行判定见 `verdict.tsv`（10 行）。

## 重点冲突两行 — 认同新 ③ 依据，判 PASS

`006E3E30`、`006E57A0` 在早先 `a-S15S16-3B2` 审计被判 FAIL（理由：29B 纯转发壳，两路汇于同一 ret 仅差 eax，语义栏「成功路径继续对象初始化」是不存在的模板假句，查 3 不成立）。**本轮认同新依据，判 PASS。**

**与早先 FAIL 的依据差异**（逐字写清）：
- 早先 FAIL 的**唯一实质理由**是第 4 列语义栏那句「成功路径继续对象初始化」——该动作在 29B 函数体内不存在（fall-through 仅 `xor eax,eax` 两条），属从 006E3DB0/006E5730 族复制来的假句；早先审计自己也写明「call/test/jl 地址全真且被调可伪证（`E_POINTER@0x0041032B` vs 成功 `ret 0xC@0x00410374`）」，即**它并不否认 ③b② 的分支与被调契约**。
- 本批 `NAMED_PUSH_S15_B1` 第 4 列**已删除该假句**，改写为字节真实具备的两态返回约定：「三参转交 00410320 写包装…`test eax,eax + jl` 让负码原样返回、成功路 `xor eax,eax` 返回 S_OK ⇒ 多值错误码被本行分支消费（③b②）」。
- 该改写与 `R14_COMMON` §12.2 判 ③b② 成立的 `test eax,eax / jl / 失败落点保留 eax / 成功 xor eax,eax` 逐字同构，并与 `NAMED_PUSH_AUDIT2` 中同包装（00410320）、同形态（29B）的 `005F9950` 判 PASS 先例一致。
- 因此早先 FAIL 的根据（假句）已消失，语义栏现与实测相符（第 5 项由 FAIL 转 PASS），③b② 四查本就成立 ⇒ 判 PASS。

## 四项口径风险独立裁定（执行器主动披露）

| # | 风险 | 独立裁定 | 依据 |
|---|---|---|---|
| 1 | **②④ 枢轴共用** | 张力真实、但按现行口径不构成 FAIL（`same_source=no`） | ② 锚 `.rdata` 的 COL/TD/RTTI 链；④ 锚 `.text` 构造器装表指令（独立 artifact）。遵 D-43(A) 先行（R14_COMMON §13.4，盘上 16 行已落盘）+ `NAMED_PUSH_AUDIT2` 11 行 `no` 先例。D-47 未解；若改采 §12.3 严格读法须**一次性整批翻转**本批 10 行，不得零散改判。 |
| 2 | **装表点共用** | 确认存在，不减行 | 10 行落 6 条 ctor 装表指令，3 组复用：`0071E6C1`→0071F930+0071FA80；`00725FCE`→00726860+007268D0+00726950；`00726CD2`→00727BF0+00727C80。取 `NAMED_PUSH_AUDIT16`/S13_B1 先例（同型共用 6/6 PASS 已并表）；各行槽号仍由独立 `vt[4N]==entry` 钉死，共享的只是「表是活的」这一命题。 |
| 3 | **2 行主体是删除析构器**（0071FA80/00726950） | 字节坐实，但**不 FAIL** | 两行确含 `test byte[esp+0xc],1` + `call 0x7C8B3D` + `ret 4`（0071FB88/0071FB90/0071FB9C 与 00726A58/00726A60/00726A6C）。但卡面只禁「④ 锚点落析构器」，本批两行 ④ 锚另取本类构造器（0071E6C1/00725FCE），行内析构器写点 0071FA86/00726956 按 ㉓ 已排除。卡面未禁析构器作主体。 |
| 4 | **6 行 SAVE 是 29B 薄转交** | 确认 29B，但**非 ③a、③b② 成立** | 被调 00410320 多值：空输入 `E_POINTER 0x80004003@0041032B`、内层流写失败经 `0041034D jl`/`00410364 jl` 透出负 HRESULT（work\verify2.txt L38-78）；本行 `jl` 真在区分「负码原样 / xor→S_OK」两态，两路返回值不同。与 §12.2 及 `NAMED_PUSH_AUDIT2` 的 005F9950（同包装同形态 PASS）逐字同构。 |

## 技术条自查（卡面点名）

- **pTD/pCHD 存绝对 VA 不是 RVA**：10 行 `COL+0xC=pTD`、`COL+0x10=pCHD` 全部 ≥ ImageBase(0x400000)，如 006E3E30 `COL=0080BAF0 → pTD=00842B78 / pCHD=0080BAE0`；若当 RVA 解（`0x400000+0x842B78=0xC42B78`）越界。✅
- **装饰名在 TD+8 是内联串不是指针**：实测 `u32(TD+8)=0x56413F2E`（正为 ".?AV" 四字节本身），`mapped_as_ptr=False`；按内联串读到 6 个类名 `.?AVTActionClass@@`/`.?AVTagClass@@`/`.?AVTagTypeClass@@`/`.?AVTEventClass@@`/`.?AVTriggerClass@@`/`.?AVTriggerTypeClass@@`。若按指针读必失败。✅

## 五环总览

| entry | ① | ② 类名/槽 | ③b 形态 | ④ 锚点 | ④≠② | 语义 | 裁定 |
|---|---|---|---|---|---|---|---|
| 006E3E30 | OK | TActionClass/slot6 | 3b2 写包装 29B | 006DD036 ctor | no | 相符 | PASS |
| 006E57A0 | OK | TagClass/slot6 | 3b2 写包装 29B | 006E4E07 ctor | no | 相符 | PASS |
| 006E6470 | OK | TagTypeClass/slot6 | 3b2 写包装 29B | 006E5B8E ctor | no | 相符 | PASS |
| 0071F930 | OK | TEventClass/slot6 | 3b2 写包装 29B | 0071E6C1 ctor | no | 相符 | PASS |
| 0071FA80 | OK | TEventClass/slot8 | 3b2 Find-1 哨兵 | 0071E6C1 ctor | no | 相符 | PASS |
| 00726860 | OK | TriggerClass/slot5 | 3b2 读包装+就地构造 | 00725FCE ctor | no | 相符 | PASS |
| 007268D0 | OK | TriggerClass/slot6 | 3b2 写包装 29B | 00725FCE ctor | no | 相符 | PASS |
| 00726950 | OK | TriggerClass/slot8 | 3b2 Find-1 哨兵 | 00725FCE ctor | no | 相符 | PASS |
| 00727BF0 | OK | TriggerTypeClass/slot5 | 3b2 读包装+就地构造 | 00726CD2 ctor | no | 相符 | PASS |
| 00727C80 | OK | TriggerTypeClass/slot6 | 3b2 写包装 29B | 00726CD2 ctor | no | 相符 | PASS |

## 执行纪律确认

- 先建目录、先写 SUMMARY 骨架 ✅；先裁两冲突行并落盘、其余逐行核完即在 `VERDICT.md`/`verdict.tsv` 落盘 ✅
- 只读输入：执行器目录 `NAMED_PUSH_S15_B1\*`、`R14_COMMON.md`、`a-S15S16-3B2`/`NAMED_PUSH_AUDIT2` 先例（均只读）
- **未修改** `coverage.tsv`/`PANEL.md`/`R14_COMMON.md`/台账/`NAMED_PUSH_*` 下任何文件；只写 `NAMED_PUSH_AUDIT18\`

## 产出清单

- `VERDICT.md`：逐行一节，五环结论 + 地址字节 + 两冲突行「与早先 FAIL 的依据差异」+ 四项风险裁定
- `verdict.tsv`：10 行判定，表头 `entry subsystem verdict ring2_at ring3b_form ring4_at same_source reason`
- `SUMMARY.md`：本文件
- `work\`：自写 PE/反汇编库与原始输出，全部证据可复算
