# NAMED-PUSH — S18 B4 REPORT

批次：S18 B4。范围：S18 中 `p3b2_named==True` 且名字非 `fn_`/`sub_` 伪名的候选，减去已被 NAMED_PUSH_S18_B1/B2/B3 核过的 54 行，按 entry 升序取剩下前 18 行。
输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S18_B4`

判据：D-40 四环，②与④须独立证据链；③只认 ③b（③b② 可伪证错误码/返回约定；③b① 跳转表可逐路验证；{0,1} 布尔不算可伪证）。三陷阱：eax 覆写 / 多路同一 call / 模板假句；另主动排查 ㉓（④ 锚点落析构器判 FAIL）、小成员表 vtable 非主虚表。
目标：`gamemd.exe` SHA-256=`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（现场复核一致）；ImageBase=0x400000；.text=[0x401000,0x7E038D)。capstone 5.0.7 `skipdata=True`；pefile 2024.8.26；Python 3.12.10。

执行纪律：先建目录、先写本骨架，再逐行核、每核完一行立刻落盘 EVIDENCE。

## 筛选命令

完整可复现脚本见 `work/filter_b4.py`。等价逻辑：

```python
# 读 SURVEY_3B2/hits_detail.tsv，逐行:
#   subsystem == "S18" and p3b2_named == "True"
#   and not name.startswith(("fn_", "sub_"))        # 排除地址式伪名
# 去掉 entry ∈ (B1∪B2∪B3 EVIDENCE/ROW_*.txt) 的 54 个 entry
# 按 int(entry,16) 升序，取前 18 行 —— 即本批候选。
```

实测：`S18 named 非伪名 = 82`，B1/B2/B3 已核 54 → 剩 28 → 本批取前 18 → 剩余池 10。
本批 18 行中无 `fn_`/`sub_` 伪名（筛选阶段已排除）；17 行为 `T_CComObject_*EventSink___ATL::slotN` / 1 行为 `IPXInterfaceClass::slot15`。

## 本批 18 行逐行总表

| 序 | entry | name | ① | ② | ③③b | ④ | 四环齐全 | 产出 |
|---:|---|---|---|---|---|---|---|---|
| 1 | 007A9110 | T_CComObject_VCChatEventSink___ATL::slot41 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 2 | 007A9200 | T_CComObject_VCChatEventSink___ATL::slot28 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 3 | 007A9550 | T_CComObject_VCChatEventSink___ATL::slot44 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 4 | 007A9800 | T_CComObject_VCChatEventSink___ATL::slot27 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 5 | 007A9970 | T_CComObject_VCChatEventSink___ATL::slot26 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 6 | 007AA6D0 | T_CComObject_VCChatEventSink___ATL::slot19 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 7 | 007AA870 | T_CComObject_VCChatEventSink___ATL::slot8 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 8 | 007AAFB0 | T_CComObject_VCChatEventSink___ATL::slot13 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 9 | 007AB0A0 | T_CComObject_VCChatEventSink___ATL::slot42 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 10 | 007AB170 | T_CComObject_VCChatEventSink___ATL::slot14 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 11 | 007AB260 | T_CComObject_VCChatEventSink___ATL::slot43 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 12 | 007AB440 | T_CComObject_VCChatEventSink___ATL::slot30 | PASS | PASS | FAIL(p3=0) | PASS | 否 | 否 |
| 13 | 007AB8E0 | T_CComObject_VCChatEventSink___ATL::slot33 | PASS | PASS | FAIL(p3=0) | PASS | 否 | 否 |
| 14 | 007AC220 | T_CComObject_VCChatEventSink___ATL::slot37 | PASS | PASS | FAIL(bool/null) | PASS | 否 | 否 |
| 15 | 007AC700 | T_CComObject_VCChatEventSink___ATL::slot0 | PASS | PASS | FAIL(ATL QI 模板判空) | PASS | 否 | 否 |
| 16 | 007AC870 | T_CComObject_VCNetUtilEventSink___ATL::slot0 | PASS | PASS | FAIL(ATL QI 模板判空) | PASS | 否 | 否 |
| 17 | 007AD690 | T_CComObject_VCDownloadEventSink___ATL::slot0 | PASS | PASS | FAIL(ATL QI 模板判空) | PASS | 否 | 否 |
| 18 | 007B10C0 | IPXInterfaceClass::slot15 | PASS | PASS | **PASS(③b②)** | PASS | **是** | **delta 1 行** |

逐行地址与字节见 `EVIDENCE/ROW_<entry>.txt`（18 份，每份含本行①入口字节、②RTTI 链与 vtable 槽、③站点 call/test/jcc 字节、④构造安装点与 dispatch 样例）。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住了）

- **本批 18/18 行 ② 全部钉住**（RTTI 描述符→类名字串链完整，且 slot_offset/4 与名字槽号逐行一致）。这与 S04「36 行 ② 全灭（named=0，身份取不到）」形成鲜明对照：本批全部来自 `p3b2_named==True` 有名字候选，② 硬约束全部满足。
- 但是 **③ 成为决定性瓶颈**：18 行里仅 1 行（007B10C0）有可伪证的返回约定；其余 17 行都是 ATL EventSink 的 `call→test eax,eax→je/jne` 布尔/null 探测（被调 0x775940 返回 0 或指针、0x7B54B0 返回 0 或 this、0x7C8D20/0x7B5340/0x7B4940/0x79D110 返回 unknown/布尔），属 {0,1} 布尔不算可伪证；slot0 三行是 ATL QueryInterface 模板假句；007AB440/007AB8E0 通道A p3=0。
- ④ 全部 PASS：18 行均有活虚表派发链（构造安装点写入活对象 + `call [reg+disp]` dispatch sites），无 direct-only，且 ②④ 不同源（② 走 .rdata RTTI 数据链，④ 走 .text 构造安装/派发链）。
- 三陷阱核查：eax 覆写陷阱 0 行触发（唯一 PASS 行 007B10C0 的 cmp eax,-1 与 jne 之间只有 `mov [mem],eax`/`pop edi`，不写 eax）；多路同一 call 不改变裁定（相关行本就 ③ FAIL）；模板假句命中 3 行（slot0 QI）判 FAIL。㉓ 析构器陷阱：所有 ④ 构造安装点 `atexit=False`，无落析构器者。小成员表陷阱：相关 vtable 均 80+ 槽且 `vtable[-4]` 为合法 COL 指针，是主虚表。

## 唯一产出行的成立要点（007B10C0）

`IPXInterfaceClass::slot15`，③b②：本体多次 `call Winsock` 后 `cmp eax,-1` → `jne` 分支。
- `socket()`(0x7c899e)@0x007B1147 → `cmp eax,-1`@0x007B114C → `jne`@0x007B1156：失败路 `WSAGetLastError`+日志+`xor al,al;ret`，成功路继续 `bind`/`setsockopt` 建链。
- `bind()`(0x7c8998)@0x007B126B → `cmp eax,-1`@0x007B1270 → `jne`@0x007B1273；`setsockopt()`(0x7c89a4)@0x007B12D9/132A/137B 各 `cmp eax,-1`+`jne`。
- 约定：socket 失败返 `INVALID_SOCKET=-1`、成功返有效句柄/0；bind/setsockopt 失败返 `SOCKET_ERROR=-1`、成功返 0。调用方真拿 `-1` 分支，两路动作真不同。属「Find 返 -1 / 多值状态码」可伪证类（与 B1 接受的 `mov eax,0xffffffff;ret` + `cmp eax,-1` 同类）。IAT 解析见 `work/iatout.txt`（thunk→WSOCK32.dll 的 socket/bind/setsockopt）。
- ② RTTI `COL=0080EA60→TD=0084D8F8→.?AVIPXInterfaceClass@@`，vt `007F794C` slot+0x3C 槽 `007F7988` 驻本 entry（80+ 槽主虚表）；④ 构造安装点 `007B0DA4 mov [esi],0x7f794c`（in_func 007B0D90，非 atexit/析构）+ `call [reg+0x3C]` dispatch 119 处，与 ② 的 .rdata RTTI 链不同源。

## 计数

| batch | rows_checked | ring2_ok | ring3b_ok | ring4_ok | all_four | rate |
|---|---:|---:|---:|---:|---:|---:|
| NAMED_PUSH_S18_B4 | 18 | 18 | 1 | 18 | 1 | 0.0556 |

- delta 行数 = 1（007B10C0）。
- 剩余池（S18 named 非伪名，减 B1/B2/B3/B4 已核 72 行）= 10 行（007B13D0 / 007B1BC0 / 007B2630 / 007B26D0 / 007B30B0 / 007B31E0 / 007B3450 / 007B36C0 / 007B3890 / 007B3AA0，均 IPXInterfaceClass/UDPInterfaceClass slot）。

如实交 1 行；不凑数、不虚报。
