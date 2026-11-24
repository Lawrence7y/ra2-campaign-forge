# NAMED-PUSH — S17 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录 → 先写骨架 → 逐行核完即落 `EVIDENCE/`；`PROGRESS.md` 每 5 行追加。上一轮残留的未完成骨架已被本文件整体重写，交付中无任何未完成状态残留。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S17` AND `p3b2_named==True`，**再排除地址式伪名 `fn_XXXXXXXX` / `sub_XXXXXXXX`**，按 entry 升序取本批（≤18 行）。S17 named=True 共 **6** 行，伪名 **0** 个 ⇒ 本批 **6 行全取**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S17_B1\`。
> 定位：S17 是唯一严格达标子系统（named 94/102、proved 56、strict 55，门槛 92/51），proved 已过门槛；本批**只为补齐覆盖，不为凑数放宽判据**（宁严不宽）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；本批现场 `Get-FileHash` 复算一致。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize 0x3DF38D）；核验 `sha256_exe()==EXPECT_SHA`、`TEXT=[00401000,007E038D)` 均通过。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`、`W130_atlas\function_atlas.tsv`（仅取函数边界）。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `SURVEY_3B2` / `S04_PUSH_*`。写域仅本目录。

## 筛选命令（得到本批 6 个 entry）

```python
import csv
p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
named_all, rows = [], []
with open(p, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if row["subsystem"] == "S17" and row["p3b2_named"] == "True":
            named_all.append(row)
            n = row["name"]
            if n.startswith("fn_") or n.startswith("sub_"):   # 排除地址式伪名（② 物理不可得）
                continue
            rows.append(row)
rows.sort(key=lambda x: int(x["entry"], 16))
batch = rows[0:18]                                            # B1：≤18 行，S17 仅 6 行全取
# 结果：S17 named=True 共 6 行，fn_/sub_ 伪名 0 个 ⇒ 本批 6 行全取。
```

落盘于 `work/filter_b1.py`（含 SHA256 自校验）。筛选结果 6 行（entry 升序）：

| # | entry | name(原样) | ②线索槽号 | ②RTTI钉住 | ③③b | ④ | 产出 |
|---:|---|---|---:|---|---|---|---|
| 1 | 004A2B60 | CStreamClass::slot3 | 3 | PASS(.?AVCStreamClass@@) | FAIL(被调未钉虚调用) | PASS(004A285E) | 否 |
| 2 | 004A2CD0 | CStreamClass::slot4 | 4 | PASS(.?AVCStreamClass@@) | **PASS(③b② E_FAIL)** | PASS(004A285E) | **是** |
| 3 | 00539AE0 | Load_StreamFields | (非slotN) | FAIL(0引用) | FAIL(被调未钉虚调用) | FAIL(direct-only) | 否 |
| 4 | 0055AAC0 | Load_SwizzledObject | (非slotN) | FAIL(0引用) | FAIL(被调未钉虚调用) | FAIL(direct-only) | 否 |
| 5 | 006BEF10 | T_TClassFactory_VCStreamClass__::slot3 | 3 | PASS(.?AV?$TClassFactory@VCStreamClass@@@@) | **PASS(③b② E_NOINTERFACE)** | PASS(006BEE49) | **是** |
| 6 | 006BF690 | T_TClassFactory_VSuperClass__::slot3 | 3 | PASS(.?AV?$TClassFactory@VSuperClass@@@@) | **PASS(③b② E_NOINTERFACE)** | PASS(006BF5C9) | **是** |

## 判定口径（严格 D-40 / D-43，宁严不宽）
1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、skipdata=0、末条 ret/jmp 落函数体内。
2. **②类身份**：必须独立取证——`.rdata` 中 entry 作 4B VA 的槽 → 回扫 `[vt-4]=COL(sig=0)` → `[COL+0xC]=TD` → `TD+8` 内联名串；要求 `slot offset/4 == 线索槽号`，且 `slotN` 的类名由 RTTI 名串独立钉死（不凭 slotN 猜）。**pTD/pCHD 存绝对 VA 非 RVA；TD+8 是内联串非指针**。钉不死判 FAIL。② 走 `.rdata` 数据链，与 ④ 的 `.text` 构造安装链不同源。
3. **③整体合同**：只认 ③b。本批成立形态全为 **③b②**：站点 `call → test/cmp eax → jcc`，被调钉死且其失败返回可从字节伪证为多值状态码（E_FAIL 0x80004005 / E_POINTER 0x80004003 / E_NOINTERFACE 0x80004002，**非 {0,1} 布尔**），调用方真拿它分支、两路动作真不同，`test` 与 `jcc` 间无 eax 覆写，非多路同一 call，非对象初始化/清零模板假句。禁把「被调用者内部的写」当循环内非栈写；禁 ③a（malloc 空判断/纯转发/零+默认/无分支直线）。
4. **④使用见证**：真实调用者或活虚表派发，direct-only 不足，且与 ② 不同源。**㉓ 析构器陷阱**：锚点落析构器判 FAIL——枚举该虚表**全部**写点，排除 atexit 注册的全局析构器与删除析构器两类；合法锚点须为非 atexit 的构造器安装点。**小成员表陷阱**：副表（如 007E5D94）非主表，QI 被调须取主表 slot0（常见 00410260）。
5. **三陷阱逐行排查**：eax 覆写、多路同一 call、模板假句。

## 基础率（诚实报数）

分母 = 本批 6 行（S17 named=True 且非伪名的全部候选）。

| 档 | 行数 | 口径 |
|---:|---:|---|
| 本批行数 | **6** | S17 named=True 非伪名，全取 |
| ①入口 PASS | **6** | 全部在 `.text`、`skipdata=0`、末条 ret |
| ②类身份钉住 | **4** | 004A2B60/004A2CD0/006BEF10/006BF690；2 行自由函数 0 引用物理不可得 |
| ③③b 成立 | **3** | 004A2CD0/006BEF10/006BF690（全 ③b②） |
| ④使用见证成立 | **4** | 同 ② 四行（构造器活表安装点、非析构器、非 atexit）；2 行 direct-only 不足 |
| **四环齐全** | **3** | rate = 3/6 = **0.5000** |

`base_rate.tsv`：`B1	6	4	3	4	3	0.5000`

## 本批 6 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ① | ② | ③ | ④ | ②④独立 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 004A2B60 | CStreamClass::slot3 | PASS | PASS(.?AVCStreamClass@@) | FAIL(被调未钉虚调用) | PASS(004A285E) | 是 | 不成立 | 否 |
| 2 | 004A2CD0 | CStreamClass::slot4 | PASS | PASS(.?AVCStreamClass@@) | **PASS(③b② E_FAIL)** | PASS(004A285E) | 是 | **成立** | **是** |
| 3 | 00539AE0 | Load_StreamFields | PASS | FAIL(全镜像0引用) | FAIL(20站点均未钉虚调用) | FAIL(direct-only) | – | 不成立 | 否 |
| 4 | 0055AAC0 | Load_SwizzledObject | PASS | FAIL(全镜像0引用) | FAIL(未钉虚调用) | FAIL(direct-only) | – | 不成立 | 否 |
| 5 | 006BEF10 | T_TClassFactory_VCStreamClass__::slot3 | PASS | PASS(.?AV?$TClassFactory@VCStreamClass@@@@) | **PASS(③b② E_NOINTERFACE)** | PASS(006BEE49) | 是 | **成立** | **是** |
| 6 | 006BF690 | T_TClassFactory_VSuperClass__::slot3 | PASS | PASS(.?AV?$TClassFactory@VSuperClass@@@@) | **PASS(③b② E_NOINTERFACE)** | PASS(006BF5C9) | 是 | **成立** | **是** |

## 逐行裁定依据（每行自身地址锚；完整字节见 `EVIDENCE/ROW_<entry>.txt`）

**② 4 行钉住（槽号由字节复算，非仅凭 slotN 猜类名）**
- `004A2B60`：槽 `007E5DB8`=`60 2B 4A 00`(vt `007E5DAC`+0xC，slot#3)→COL `007FF9B8`(sig 0)→pTD `0081FC30`→TD+8 内联串 `.?AVCStreamClass@@`。
- `004A2CD0`：槽 `007E5DBC`=`D0 2C 4A 00`(vt `007E5DAC`+0x10，slot#4)→同 COL/TD→`.?AVCStreamClass@@`。
- `006BEF10`：槽 `007F3774`=`10 EF 6B 00`(vt `007F3768`+0xC，slot#3)→COL `00809C68`→pTD `00840F68`→`.?AV?$TClassFactory@VCStreamClass@@@@`（TClassFactory<VCStreamClass>，钉死名字线索的类部分）。
- `006BF690`：槽 `007F37EC`=`90 F6 6B 00`(vt `007F37E0`+0xC，slot#3)→COL `00809DF8`→pTD `00841068`→`.?AV?$TClassFactory@VSuperClass@@@@`（TClassFactory<SuperClass>）。

**② 2 行 FAIL（自由函数，② 物理不可得）**
- `00539AE0`/`0055AAC0`：全镜像以 4B VA 搜索各 **0 命中**，无虚表槽、无可回扫 RTTI 链；名字为 `Load_StreamFields`/`Load_SwizzledObject` 自由函数名（非 `Class::slotN`），无 Class 部分可钉 ⇒ ② FAIL。与 S04「② 取不到」同类（② 是硬约束）。

**③ 成立 3 行（均为 ③b②，被调钉死 + 多值状态码可伪证 + 调用方真分支 + 两路动作不同）**
- `004A2CD0`：`004A2D8D E8 8E 02 00 00`(call 0x4A3020)→`004A2D92 85 C0`→`004A2D94 7C 61`(jl→0x4A2DF7)；第二站点 `004A2DB1 E8 6A 02 00 00`→`004A2DB6 85 C0`→`004A2DB8 7C 3D`。被调 0x4A3020 `004A3089 B8 05 40 00 80`(E_FAIL)/`004A30CD 25 05 40 00 80`(and eax,E_FAIL) ⇒ 失败 0x80004005、成功 0（字节可伪证，非 bool）。jl 失败路带负 HRESULT 中断、不跳路续填分块后 `004A2DF5 33 C0` 返 0，两路动作真不同；test 紧邻 jl 无 eax 覆写；两站点为两处独立 call 指令非多路同一 call。
- `006BEF10`：`006BEF6A FF 10`(call [eax])——eax=[esi]=`006BEF4C` 构造器 0x4A2820 装的主表 `007E5DAC`(004A285E `C7 06 AC 5D 7E 00`)，其 slot0=`004A2990`(QueryInterface，已钉死)→`006BEF6C 8B F8`→`006BEF6E 85 FF`→`006BEF70 7D 09`(jge)。被调 004A2990 `004A2999 B8 03 40 00 80`(E_POINTER)/`004A2A02 B8 02 40 00 80`(E_NOINTERFACE)/`004A2A11 33 C0`(成功0) 可伪证、非 bool。jge 成功路保留对象返 0、失败路 `006BEF72 FF 52 38`(Release) 释放后返负 HRESULT，两路真不同；无 eax 覆写、非模板假句（入口 operator new 空判断属 ③a 不计）。
- `006BF690`：`006BF6ED FF 10`(call [eax])——eax=[esi]=`006BF6CF` 构造器 0x6CAEC0 装的主表 `007F3FE8`(006CAF10 `C7 06 E8 3F 7F 00`)，其 slot0=`00410260`(QueryInterface，已钉死；**符合「主表 slot0 常见 00410260」**，确认取主表非副表)→`006BF6EF 8B F8`→`006BF6F1 85 FF`→`006BF6F3 7D 09`。被调 00410260 `00410269 B8 03 40 00 80`(E_POINTER)/`004102E6 B8 02 40 00 80`(E_NOINTERFACE)/`004102F5 33 C0`(成功0) 可伪证、非 bool。jge 成功路保留对象、失败路 `006BF6F5 FF 52 20`(Release) 释放后返负 HRESULT，两路真不同；无覆写、非模板假句。

**③ FAIL 3 行（逐行独立理由）**
- `004A2B60`：两处被检 call 均为 `call [ecx+0xc]`（`004A2C3E FF 51 0C`/`004A2C73 FF 51 0C`），ecx=[[esi+8]] 是入参对象字段，槽+0xC 目标运行期不确定 ⇒ 被调不可钉、返回约定无法从字节伪证（pass1 两站点 falsy=None）。本体错误码 0x80004003/0x80070057/0x80004005 均为入参校验 ③a 直排，不构成 ③b②。
- `00539AE0`：20 处被检 call 全为 `call [reg+0xc]` 未钉虚调用（pass1 全 falsy=None）；循环内非栈写 `00539CE5 89 0C 82` 的读流仍是未钉虚调用，不构成可独立验证的 ③b④；入口校验 ③a。
- `0055AAC0`：唯一被检 call `0055AADE FF 50 0C`(call [eax+0xc]) 未钉；入口 `0055AAC9 B8 03 40 00 80` 为空指针 ③a 直排。

**④ 4 行成立、2 行 FAIL（㉓ 析构器陷阱已按全写点枚举复核）**
- `004A2B60`/`004A2CD0`（vt 007E5DAC）：全部写点 `004A285E`(004A2820 构造器)、`004A2889`(004A2880 删除析构器)、`004A3119`(004A3110 删除析构器)；排除两类析构器（删除析构器 + atexit 注册，三处 `atexit_sites=[]`），合法锚点落构造器 `004A285E`。004A2820 由工厂 `006BEF4C`(operator new 后) 调用装活对象主表 ⇒ ④ PASS。
- `006BEF10`（vt 007F3768）：唯一写点 `006BEE49`(16B 构造器 006BEE40)，无删除析构器、`atexit=[]`，由 `006BC468` 装活对象 ⇒ ④ PASS。
- `006BF690`（vt 007F37E0）：唯一写点 `006BF5C9`(16B 构造器 006BF5C0)，无删除析构器、`atexit=[]`，由 `006BC599` 装活对象 ⇒ ④ PASS。
- `00539AE0`（1 direct caller 0067FB09）/`0055AAC0`（11 direct callers）：无虚表槽（dword_refs=0）⇒ 无活虚表派发链、direct-only 不足 ⇒ ④ FAIL。
- ②④ 不同源：② 锚 `.rdata` RTTI 数据链，④ 锚 `.text` 构造器安装指令；四段/地址/产物类型均不同，不复用同一虚表槽作双证。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- **S04**：73 个 ③b② 机械命中 `p3b2_named=0`（全无名字）——entry 作 4B VA 全镜像 0 命中、无虚表槽、无可回扫 RTTI 链 ⇒ ② 物理不可得，30+ 行实测全败。
- **本批 S17 B1**：6 行里 **4 行 ② 被 RTTI + 虚表独立钉死**（slot offset/4 逐行复算自洽，RTTI 名串与线索类名一致），与 S04 的决定性差异复现。2 行自由函数（`Load_StreamFields`/`Load_SwizzledObject`）虽 `p3b2_named=True` 且是真名，但全镜像 0 引用、无虚表 ⇒ ② 与 S04 同类物理不可得。
- 结论：② 从 S04 的 0 → 本批 **4/6**；瓶颈在 ③——4 个有 ② 的行里 1 行（004A2B60）③ 因被调不可钉而 FAIL；其余 3 行 ③b② 成立。本批 ② 真钉住 4 行，四环齐全 3 行。

## 汇总
- rows_checked：**6**
- ② 钉住行数：**4**（004A2B60/004A2CD0/006BEF10/006BF690）
- ③b 成立行数：**3**（004A2CD0/006BEF10/006BF690，全 ③b②）
- ④ 成立行数：**4**（同 ② 四行；构造器活表安装点、非析构器、非 atexit）
- all_four_rings（严格 D-40）：**3**，rate = **0.5000**
- delta 产出：**3 行**（004A2CD0 / 006BEF10 / 006BF690）
- 结论：如实交 3 行；S17 已过门槛，本批不为凑数放宽判据。

## 输出清单
- `REPORT.md`（本文件，已整体重写）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`（3 行）
- `EVIDENCE/ROW_<entry>.txt` × 6（每行自身四环地址与字节）
- `work/`：filter_b1 / np_core / pass1 / detail_* / deep_verify / final_checks / witness2 / anchors / verify_independent / verify_006BF690 / verify_qi_tail（全部只读目标、可复算）
