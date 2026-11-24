# NAMED_PUSH_AUDIT18 — VERDICT（异族独立审计，逐行）

> 审计对象：`NAMED_PUSH_S15_B1\delta.tsv` 全部 10 行（DeepSeek/S14 家族产出，执行器自报 rate 1.0000）
> 二进制：`ra2youli\gamemd.exe` SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ✅
> 工具：本人自写 `work\re_lib.py` + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26，Python 3.12.10；执行器 `ROW_*.txt`/`REPORT.md` **只当线索**，本文件全部地址/字节来自本人反汇编（`work\scan_all.txt` / `verify1.txt` / `verify2.txt` / `verify3.txt` 可复算）。
> 五环标准：①入口 ②类身份 ③b具体形态 ④使用见证 ④≠②同源；外加第 5 项「语义与实测相符」。

## 取行方式（卡面要求写进报告）

```
Import-Csv NAMED_PUSH_S15_B1\delta.tsv -Delimiter "`t"  # 6 列，10 数据行，全部属于 S15
```
10 行 entry：006E3E30 / 006E57A0 / 006E6470 / 0071F930 / 0071FA80 / 00726860 / 007268D0 / 00726950 / 00727BF0 / 00727C80（大写无 0x）。

## 技术条自查（卡面点名）

- **pTD/pCHD 存绝对 VA 不是 RVA**：实测 10 行的 `COL+0xC=pTD`、`COL+0x10=pCHD` 全部 ≥ ImageBase(0x400000)，如 006E3E30 的 `COL=0080BAF0 → pTD=00842B78 / pCHD=0080BAE0`，落在 `.data`/`.rdata`；若当 RVA 解（`0x400000+0x842B78=0xC42B78`）越界。✅
- **装饰名在 TD+8 是内联串不是指针**：实测 `u32(TD+8)=0x56413F2E`（正是 ".?AV" 四字节本身），`mapped_as_ptr=False`，按内联串读到 `.?AVTActionClass@@` 等 6 个类名。✅

---

## 重点冲突行 1 · 006E3E30 — **PASS**（认同新依据）

**② 类身份**：`vt=007F443C`（slot0=`00410260` QueryInterface ⇒ 主虚表），`[vt+0x18]=007F4454 → 006E3E30`（slot#6，与名字 slot6 自洽）；`COL=u32(vt-4)=0080BAF0`（sig=0）、`pTD=00842B78`（绝对VA）、TD+8 内联串 `.?AVTActionClass@@`。

**③b② 具体形态**（本行体 29 字节，work\scan_all.txt L8-19）：
```
006E3E3F  e8 dcc4d2ff  call 0x410320        ; 写包装
006E3E44  85 c0        test eax,eax         ; 零间隔检查点
006E3E46  7c 02        jl   0x6E3E4A         ; 失败→保留 eax(负码) 直达 ret
006E3E48  33 c0        xor  eax,eax         ; 成功→归零 S_OK
006E3E4A  c2 0c 00     ret  0xc
```
失败返回什么：`00410320` 空流入参 `0041032B b8 03400080 → EAX=0x80004003`，且内层流写失败经 `0041034D 7c23` / `00410364 7c0c` 把负 HRESULT 原样透出（work\verify2.txt L38-78）；本行 `jl` 落入 006E3E4A 时 eax 未被改写 ⇒ 负码原样返回。成功返回什么：`xor eax,eax` → S_OK。调用方哪条指令拿它分支：本行 `test@006E3E44` + `jl@006E3E46`，`test` 与 `jl` 间 0 条指令（无 eax 覆写）。两路返回值不同（负码 vs 0），非 ③a 纯转发。

**④ 使用见证**：构造器装表点 `006DD036 c7 06 3c447f00 mov [esi],0x7F443C`（宿主 `006DD000`，`006DD004 call 0x410170` 基类构造在前，非 atexit、非析构；work\verify2.txt L4）。㉓ 全枚举该表写点：`006DD036/006DD18D/006DD1B6/006E3DD4/006E4666` 共 5 处，前 4 处均有基类构造调用、无 `test byte,1`+`call 0x7C8B3D` 析构签名；`006E4666` 经核为 006E4660 体内装表（非删除析构器，无 delete 标志），④ 锚点取 006DD036 独立于本行体（本行 006E3E30 体内无装表）。

**④≠②同源**：`same_source=no` — ② 锚在 `.rdata` 的 COL/TD/RTTI 链，④ 锚在 `.text` 的构造器装表指令；遵循 D-43(A) 先行（R14_COMMON §13.4，16 行已落盘）与 `NAMED_PUSH_AUDIT2` 同型行裁定；D-47 枢轴张力见 SUMMARY 风险 1 披露。

**语义与实测相符**：第 4 列「三参转交 00410320 写包装…负码原样返回、成功路 xor eax,eax 返回 S_OK」与上述字节逐项一致（写方向 ✅；00410320 确为写包装：其 `00410348 FF 50 10` / `0041035E FF 53 10` 走流虚表 +0x10 写槽，读包装 00410380 走 +0xC）。

**★ 与早先 FAIL 的依据差异（卡面点名必答）**：早先 `a-S15S16-3B2` 审计判 006E3E30 FAIL，理由是「29 字节纯转发壳：两路径汇于同一条 ret 0xC 仅差 eax 值，主张的『成功路径继续对象初始化』在本行字节中不存在（fall-through 仅 xor eax,eax 两条），系同族模板假句，查 3 不成立」。**本批语义栏已删去那条不存在的「对象初始化」假句**，改写为「负码原样返回、成功路 xor eax,eax 返回 S_OK ⇒ 多值错误码被本行分支消费」——这正是本行字节真实具备的两态返回约定，与 R14_COMMON §12.2 判 ③b② 成立的 `test eax,eax/jl/失败保留 eax/成功 xor eax,eax` 逐字同构，并与 `NAMED_PUSH_AUDIT2` 中同形态同包装的 `005F9950`（29B，PASS）先例一致。**早先 FAIL 的根据是语义栏的假句，不是分支本身不存在**（该审计自己写明「call/test/jl 地址全真且被调可伪证」）；假句既已更正，FAIL 依据不再成立，故本轮认同新 ③ 依据判 PASS。

---

## 重点冲突行 2 · 006E57A0 — **PASS**（认同新依据）

**② 类身份**：`vt=007F44E0`（slot0=`00410260` 主虚表），`[vt+0x18]=007F44F8 → 006E57A0`（slot#6，与名字 slot6 自洽）；`COL=0080BBA0`（sig=0）、`pTD=008249E8`（绝对VA）、TD+8 内联串 `.?AVTagClass@@`。

**③b② 具体形态**（29 字节，work\scan_all.txt L29-40）：
```
006E57AF  e8 6cabd2ff  call 0x410320
006E57B4  85 c0        test eax,eax
006E57B6  7c 02        jl   0x6E57BA
006E57B8  33 c0        xor  eax,eax
006E57BA  c2 0c 00     ret  0xc
```
失败返回：`00410320` 空输入 `E_POINTER 0x80004003@0041032B`、内层负 HRESULT 经 `0041034D/00410364 jl` 原样透出；`jl@006E57B6` 落入 006E57BA 时 eax 保留负码。成功返回：`xor eax,eax@006E57B8` → S_OK。消费点：本行 `test@006E57B4`+`jl@006E57B6`（零间隔）。两路返回值不同，非 ③a。

**④ 使用见证**：装表点 `006E4E07 c7 06 e0447f00 mov [esi],0x7F44E0`（宿主含 `call 0x410170` 基类构造，非 atexit/非析构；work\verify2.txt L11）。该表写点枚举 `006E4E07/006E4F69/006E5754`，④ 锚点 006E4E07 在本行体外。

**④≠②同源**：`same_source=no`，同上 D-43(A)/AUDIT2 先例。

**语义与实测相符**：第 4 列「TagClass 流写出…负码原样返回、成功路 xor eax,eax 返回 S_OK」与字节一致；00410320 写包装方向 ✅。

**★ 与早先 FAIL 的依据差异**：早先 `a-S15S16-3B2` 判 FAIL 同 006E3E30——「29B 纯转发壳，两路汇于 ret 0xC@006E57BA 仅差 eax，主张的『成功路径继续对象初始化』在字节中不存在，模板假句，查 3 不成立」。本批已删除该假句，改写为真实两态返回约定（负码原样 / xor→S_OK），与 §12.2、005F9950 先例同型。早先 FAIL 只针对假句、不否认 test/jl 与可伪证被调；假句更正后依据消失，故认同新依据判 PASS。

---

## 行 3 · 006E6470 (TagTypeClass::slot6) — **PASS**

- **②**：`vt=007F45C4`（slot0=`00410260` 主表），`[vt+0x18]=007F45DC=006E6470`（slot#6 自洽）；`COL=0080BCF0 sig=0`、`pTD=00842CB0`（绝对VA）、TD+8 内联 `.?AVTagTypeClass@@`。
- **③b②**：`call 00410320@006E647F / test@006E6484 / jl@006E6486→006E648A / xor eax,eax@006E6488 / ret@006E648A`（29B）；失败 E_POINTER@0041032B + 内层负码透出，jl 路 eax 保留，成功 xor→S_OK；`test/jl` 零间隔。
- **④**：ctor 装表 `006E5B8E c7 45 00 c4457f00 mov [ebp],0x7F45C4`（`call 0x410800@006E5B6C` 基类构造在前，work\verify2.txt L16）；写点枚举 `006E5B8E/006E5CA7/006E6434`，锚点行外。
- **④≠②**：`no`（② .rdata / ④ .text ctor）。
- **语义**：「流写出 00410320 写包装…负码原样/xor→S_OK」与字节一致；写方向 ✅。
- 判 **PASS**。

## 行 4 · 0071F930 (TEventClass::slot6) — **PASS**

- **②**：`vt=007F5578`（slot0=`00410260`），`[vt+0x18]=007F5590=0071F930`（slot#6）；`COL=0080C5E0 sig=0`、`pTD=008446F8`、`.?AVTEventClass@@`。
- **③b②**：`call 00410320@0071F93F / test@0071F944 / jl@0071F946→0071F94A / xor@0071F948 / ret@0071F94A`（29B）；E_POINTER@0041032B + 负码透出；零间隔。
- **④**：ctor `0071E6C1 c7 06 78557f00 mov [esi],0x7F5578`（`call 0x410170` 在前，work\verify2.txt L21）；写点 `0071E6C1/0071E80D/0071E836/0071F8E4` 均 ctor 侧，锚点行外。
- **④≠②**：`no`。
- **语义**：写包装 ✅，两态返回 ✅。
- 判 **PASS**。

## 行 5 · 0071FA80 (TEventClass::slot8，删除析构器主体) — **PASS**

- **②**：`vt=007F5578`（slot0=`00410260`），`[vt+0x20]=007F5598=0071FA80`（slot#8）；`COL=0080C5E0`、`pTD=008446F8`、`.?AVTEventClass@@`。
- **③b②**（Find -1 哨兵，work\scan_all.txt L92-178）：
```
0071FABA  ff 52 10      call [edx+0x10]     ; 容器[0xB0F658] 虚表 Find
0071FABD  83 f8 ff      cmp eax,-1          ; 检查哨兵
0071FAC0  74 2d         je  0x71FAEF        ; 未命中→跳过
0071FACC..0071FAE1      dec Count + mov [ecx+eax*4-4],edx  ; 命中→前移压缩(非栈写)
```
  3 站点：`0071FABA/0071FB03/0071FB4C`（容器 0xB0F658/0xB0F670/0xB0F1A0），各自紧随 `cmp eax,-1@0071FABD/0071FB06/0071FB4F + je→0071FAEF/0071FB38/0071FB81`，零间隔；`call [edx+0x10]` 是 Find（容器活表 007E91EC slot4=`004E0550`，未命中 `004E056F 83 c8 ff or eax,-1`；0xB0F1A0 走 007F550C slot4=`0071FE30`，未命中 `0071FE4F`，work\verify1.txt/verify3.txt）。失败=-1 跳过、成功=下标命中并 dec Count+压缩，两路真不同。
- **④**：ctor `0071E6C1`（`call 0x410170` 在前），**非**本行体；本行 `0071FA86 mov [esi],0x7F5578` 是删除析构器自身装表点（特征 `test byte[esp+0xc],1@0071FB88 + call 0x7C8B3D@0071FB90 + ret 4@0071FB9C`），按 ㉓ **已排除、未取作锚点**。
- **④≠②**：`no`。
- **语义**：「删除析构器(slot8)…装 4 表调基类析构 0x7258D0@0071FAA1…3 容器 Find→摘除压缩…cmp/je 消费 -1」与字节逐项一致（0x7258D0=007258D0 ✅；3 容器地址 ✅）。
- **删析构主体风险裁定**：卡面仅禁「④ 锚点落析构器」，未禁析构器作主体；④ 锚点在构造器 0071E6C1，符合。判 **PASS**。

## 行 6 · 00726860 (TriggerClass::slot5，读入就地构造) — **PASS**

- **②**：`vt=007F5858`（slot0=`00410260`），`[vt+0x14]=007F586C=00726860`（slot#5）；`COL=0080C968`、`pTD=00842CE8`、`.?AVTriggerClass@@`。
- **③b②**（work\scan_all.txt L188-221）：
```
0072686B  call 00410380    ; 读包装
00726870  test eax,eax
00726872  jl   0x7268CB    ; 负码→pop esi;ret 8,eax 原样保留
           (成功路) test esi,esi / call 004101C0 基类构造 / 装4表@00726884 / 3×call 0x6CF240 / xor eax,eax@007268C9
```
  失败 E_POINTER@00410389（读包装 00410380 空输入，work\verify1.txt L14-21）；jl 路直接收尾、eax 保留负码；成功路构造+装表+字段读入+xor→S_OK，两路真不同；`test/jl` 零间隔。
- **④**：ctor `00725FCE c7 06 58587f00 mov [esi],0x7F5858`（`call 0x410170` 在前）；本行 `00726884` 是 Load 就地构造写点，按「④ 须行外」已排除、④ 取 00725FCE。
- **④≠②**：`no`。
- **语义**：「读包装 00410380…jl 负码收尾…成功构造基类装 4 表逐字段读入末尾 S_OK」与字节一致；**读方向 ✅**（00410380 走流虚表 +0xC，`0041039E FF 50`）。
- 判 **PASS**。

## 行 7 · 007268D0 (TriggerClass::slot6) — **PASS**

- **②**：`vt=007F5858`，`[vt+0x18]=007F5870=007268D0`（slot#6）；COL=0080C968、pTD=00842CE8、`.?AVTriggerClass@@`。
- **③b②**：`call 00410320@007268DF / test@007268E4 / jl@007268E6→007268EA / xor@007268E8 / ret@007268EA`（29B）；E_POINTER@0041032B + 负码透出；零间隔。
- **④**：ctor `00725FCE`（`call 0x410170` 在前），行外。
- **④≠②**：`no`。
- **语义**：写包装 ✅，两态返回 ✅。
- 判 **PASS**。

## 行 8 · 00726950 (TriggerClass::slot8，删除析构器主体) — **PASS**

- **②**：`vt=007F5858`，`[vt+0x20]=007F5878=00726950`（slot#8）；COL=0080C968、pTD=00842CE8、`.?AVTriggerClass@@`。
- **③b②**（work\scan_all.txt L252-338）：3 站点 `0072698A/007269D3/00726A1C`（容器 0xA8EAE8/0xB0F670/0xB0F708），各 `call [edx+0x10] → cmp eax,-1@0072698D/007269D6/00726A1F → je→007269BF/00726A08/00726A51`，零间隔；命中路 `dec Count + mov [ecx+eax*4-4],edx@007269B1/007269FA/00726A43` 前移压缩（非栈写）；容器 0xA8EAE8 活表 007E9BE4 slot4=`004EA650` 未命中 `004EA66F or eax,-1`，0xB0F670 走 007E91EC/`004E0550`，0xB0F708 走 007E9BE4/`004EA650`。失败=-1 跳过、成功=压缩，两路真不同。
- **④**：ctor `00725FCE`（`call 0x410170` 在前），**非**本行；本行 `00726956 mov [esi],0x7F5858` 是删除析构器写点（`test byte[esp+0xc],1@00726A58 + call 0x7C8B3D@00726A60 + ret 4@00726A6C`），按 ㉓ 已排除。
- **④≠②**：`no`。
- **语义**：「3 容器 0xa8eae8/0xb0f670/0xb0f708 Find→摘除压缩，004EA66F or eax,-1，cmp/je 消费」与字节逐项一致 ✅。
- **删析构主体风险裁定**：同 0071FA80，④ 锚点在构造器非析构器，判 **PASS**。

## 行 9 · 00727BF0 (TriggerTypeClass::slot5，读入就地构造) — **PASS**

- **②**：`vt=007F5904`（slot0=`00410260`），`[vt+0x14]=007F5918=00727BF0`（slot#5）；`COL=0080CA20`、`pTD=00842D08`、`.?AVTriggerTypeClass@@`。
- **③b②**（work\scan_all.txt L348-385）：`call 00410380@00727BFB / test@00727C00 / jl@00727C02→00727C75`；失败 E_POINTER@00410389，jl 路 `pop esi;ret 8` eax 保留；成功路 `call 00410960@00727C0F` 基类构造 + 装 4 表@00727C14 + 4×`call 0x6CF240` + `xor eax,eax@00727C73`；`test/jl` 零间隔，两路真不同。
- **④**：ctor `00726CD2 c7 06 04597f00 mov [esi],0x7F5904`（`call 0x410800` 在前）；本行 `00727C14` 是 Load 就地构造写点，已排除、取行外 00726CD2。
- **④≠②**：`no`。
- **语义**：「读包装 00410380…jl 负码收尾…成功构造基类装 4 表逐字段读入 S_OK」与字节一致；读方向 ✅。
- 判 **PASS**。

## 行 10 · 00727C80 (TriggerTypeClass::slot6) — **PASS**

- **②**：`vt=007F5904`，`[vt+0x18]=007F591C=00727C80`（slot#6）；COL=0080CA20、pTD=00842D08、`.?AVTriggerTypeClass@@`。
- **③b②**：`call 00410320@00727C8F / test@00727C94 / jl@00727C96→00727C9A / xor@00727C98 / ret@00727C9A`（29B）；E_POINTER@0041032B + 负码透出；零间隔。
- **④**：ctor `00726CD2`（`call 0x410800` 在前），行外。
- **④≠②**：`no`。
- **语义**：写包装 ✅，两态返回 ✅。
- 判 **PASS**。

---

## 四项口径风险独立裁定（执行器主动披露，逐项）

1. **②④枢轴共用**：**张力真实但不构成字节级 FAIL**。② 用 `.rdata` 的 COL/TD/RTTI 链 + `vt[slot]==entry`；④ 用 `.text` 的构造器装表指令（独立 artifact），按 D-43(A) 先行（R14_COMMON §13.4，盘上 16 行已落盘）与 `NAMED_PUSH_AUDIT2` 11 行 `same_source=no` 先例判 `no`。D-47 未解；若 Lead 改采 §12.3 严格读法，**须一次性整批翻转**（本批 10 行同型），不得零散改判。本审计按现行口径不减行。
2. **装表点共用**：**确认**（10 行落 6 条 ctor 装表指令，3 组复用：`0071E6C1`→0071F930+0071FA80；`00725FCE`→00726860+007268D0+00726950；`00726CD2`→00727BF0+00727C80）。取 `NAMED_PUSH_AUDIT16`/S13_B1 先例（同型共用，6/6 PASS 已并表）不因共用减行，显式披露。注意槽号仍独立（各 `[vt+4N]==entry` 已在 ② 验证），共享的只是「表是活的」这一个命题。
3. **2 行主体是删除析构器**（0071FA80/00726950）：**字节坐实**（`test byte[esp+0xc],1`+`call 0x7C8B3D`+`ret 4`），但 ④ 锚点另取本类构造器（0071E6C1/00725FCE），未把析构器当 ④，卡面未禁析构器作主体 ⇒ 不 FAIL。
4. **6 行 SAVE 是 29B 薄转交**：**确认 29B**，但非 ③a：被调 00410320 确为多值（E_POINTER 0x80004003 + 内层负 HRESULT 透出，work\verify2.txt L38-78），本行 `jl` 真在区分「负码原样 / xor→S_OK」两态，与 R14_COMMON §12.2 及 `NAMED_PUSH_AUDIT2` 的 005F9950（同包装同形态 PASS）逐字同构 ⇒ ③b② 成立，不 FAIL。

## 总裁定

**PASS 10 / FAIL 0**。10 行四环 + 语义均独立成立；执行器自报 rate 1.0000 在逐行字节复核下**得到确认**。重点冲突两行 006E3E30/006E57A0 认同新 ③ 依据（早先 FAIL 的「对象初始化」假句已删除），判 PASS。
