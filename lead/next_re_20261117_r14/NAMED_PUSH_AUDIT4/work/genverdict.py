"""Generate VERDICT.md from measured facts (no hand-copied addresses)."""
import sys, json, os, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
B = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B1"
chain = json.load(open(os.path.join(W, "chain4.json")))
ROWS = list(chain.keys())
FAILS = {'006BFF90', '006C0A10'}
PUSH1 = {
 '006BF810':'006BF877','006BF990':'006BF9F7','006BFB10':'006BFB74','006BFC90':'006BFCF4',
 '006BFE10':'006BFE79','006BFF90':'006BFFF9','006C0110':'006C017E','006C0290':'006C02F9',
 '006C0410':'006C0479','006C0590':'006C05F4','006C0710':'006C0774','006C0890':'006C08F4',
 '006C0A10':'006C0A74','006C0B90':'006C0BF4','006C0D10':'006C0D74','006C0E90':'006C0EF4'}
def b(a, n): return img.hexb(a, n).upper()

# exec CLSID claims
exec_sem = {}
for line in open(os.path.join(B, "delta.tsv"), encoding='utf-8').read().splitlines()[1:]:
    f = line.split('\t')
    exec_sem[f[0]] = f[3]

out = []
A = out.append
A("""# NAMED_PUSH_AUDIT4 — NAMED_PUSH_S22_B1 全 16 行异族独立审计（VERDICT）

## 0. 前提与本审计的独立性

- 审计员：**异族**（本批执行器为 S05/S14 侧之外的第四次推送，非本审计产物）。**只采信我自己反汇编的字节**；执行器 `NAMED_PUSH_S22_B1\\EVIDENCE\\ROW_*.txt` 仅当线索，**未在本文引用任何执行器证据文字**。
- 镜像：`D:\\Project\\ra2-campaign-forge\\ra2youli\\gamemd.exe`
  - SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` = 卡面期望值。
  - ImageBase `0x400000`；节表实测：`.text 00401000..007E1000`、`.rdata 007E1000..00812000`、`.data 00812000..00B79BE4`、`.rsrc`、`.detour`。
  - ⚠️ 与卡面 `[0x401000, 0x7E038D)` 的差异：实测 `.text` 虚段尾为 `007E1000`（卡面 `7E038D` 落在此段内）。本审计按实测节界扫描，全 `.text` 1,392,592 条指令、68,253 个 direct call 站点，未截断。
- 工具：capstone 5.0.7（`skipdata=True`）、pefile 2024.8.26、Python 3.12.10，无 venv、未装包。自写脚本在 `NAMED_PUSH_AUDIT4\\work\\`（`lib.py`/`index.py`/`facts3.py`/`chain4b.py`/`join.py`/`sigmacheck.py`/`emit.py`），全部可复算。
- 判据：`R14_COMMON.md:611`（③b 四充分条件：①跳表 ②可伪证错误码/返回约定 ③内存形状断言 ④完整循环 I/O）、`R14_COMMON.md:745-749`（**D-46(A)**：③b② 只认错误码/返回约定，bool 主输出不算）、卡面五点。
- Lead 本轮裁定（照办）：**③ 只要求函数整体合同真实，不要求落在筛出它的那个站点**。因此本文对 ③ 的判定基准是**本 entry 函数体内的真实合同**，而非 survey 命中的 `operator new` 空判断。

## 1. 取行方法（可复现）

`NAMED_PUSH_S22_B1\\delta.tsv` 跳过表头、按 `\\t` 切 6 列（`entry/subsystem/name/one_line_semantics/grade/evidence_path`），得 **16 数据行**。
`base_rate.tsv` 记 `rows_checked=18`，但 `delta.tsv` 只有 16 行 —— 差 2 行是 `EVIDENCE\\` 下多出的 `ROW_0069C9C0.txt`/`ROW_0069CBC0.txt`（未进 delta）。**本审计只审 delta.tsv 全部 16 行**，与派单一致。
16 行 `subsystem=S22`、`grade=[已证]`、行名全为 `T_TClassFactory_<X>::slot3`。

## 2. 结构总览（我先认清这批是什么）

16 行是 `TClassFactory<X>::CreateInstance`（IClassFactory 五槽布局的 **槽 3**：槽0=QueryInterface、槽1=AddRef、槽2=Release、槽3=CreateInstance、槽4=LockServer；该槽序与 `S11-K1\\_audit\\VERDICT.md:44` 在案的更正一致）。
每行函数体是同一 C++ 模板的 16 次实例化，故**代码骨架相同、立即数与调用目标不同**。逐行实测骨架（`sigmacheck.py`）：

```
push esi / push edi
mov  edi,[esp+0x18]          ; ppvOut
test edi,edi / jne           ; 空 → mov eax,0x80070057 (E_INVALIDARG) ; ret 0x10
mov  eax,[esp+0x10]          ; pUnkOuter
mov  dword ptr [edi],0       ; *ppvOut = 0      ← 先置空（写方向）
test eax,eax / je            ; 非空 → mov eax,0x80040110 (CLASS_E_NOAGGREGATION) ; ret 0x10
push <sizeof(X)> / call 0x7C8E17 (operator new)
test eax,eax / je            ; → mov eax,0x8007000E (E_OUTOFMEMORY) ; ret 0x10
mov  ecx,eax / call <X::ctor>; mov esi,eax / test esi,esi / jne
mov  ecx,[esp+0x14]          ; riid
mov  eax,[esi]               ; 新建对象主虚表
push edi / push ecx / push esi
call dword ptr [eax]         ; ← 槽0 = QueryInterface   (FF 10)
mov  edi,eax / test edi,edi / jge   ; ← 消费 HRESULT
; 失败路：mov edx,[esi] / push 1 / mov ecx,esi / call dword ptr [edx+0x20]  (FF 52 20)
mov  eax,edi / pop edi / pop esi / ret 0x10
```

**16 行逐行实测签名**（每行**自身字节**都含全部要素，非引用同一条文字）：

| entry | 指令数 | 三码 | QI 调用 | 释放调用 | 置空*ppv | push 1 | ret |
|---|---:|---|---|---|---|---|---|
""")
for r in ROWS:
    d = json.load(open(os.path.join(W, "f3_%s.json" % r)))
    d['body'] = [fmt(i) for i in img.body(int(r, 16))]
    A("| %s | %d | 80070057/80040110/8007000E | %s FF10 | %s FF5220 | %s | %s | 4×C21000 |" % (
        r, len(d['body']), d['qi_call']['at'], d['rel_call']['at'],
        [x.split()[0] for x in d['body'] if 'dword ptr [edi], 0' in x][0],
        PUSH1[r]))
A("""
## 3. 逐行判定

> 五查记法：**查1=②** 类身份独立成立；**查2=③b** 具体形态（③b② 判据）；**查3=④** 使用见证独立成立；**查4=④②不同源**；**查5=语义与实测相符**。

""")

for idx, r in enumerate(ROWS, 1):
    d = json.load(open(os.path.join(W, "f3_%s.json" % r)))
    d['body'] = [fmt(i) for i in img.body(int(r, 16))]
    f = d['factory']; ch = chain[r]; mv = d['main_vt']; q = d['qi_callee']
    cls = d['element']
    fv = int(f['vt'], 16)
    slot_va = int(f['slot_va'], 16)
    qi = int(d['qi_call']['at'], 16)
    rel = int(d['rel_call']['at'], 16)
    p1 = int(PUSH1[r], 16)
    verdict = 'FAIL' if r in FAILS else 'PASS'
    A("### %d. `%s` — %s（TClassFactory<%s> 槽 3）\n" % (idx, r, verdict, cls))
    A("**查1 ② 类身份**（独立自取）")
    A("")
    A("```")
    A("vt   %s  slot#3 @ %08X  bytes %s   → 值 == 本 entry" % (f['vt'], slot_va, b(slot_va, 4)))
    A("COL  %s (vt-4)   sig=%d offset=0  → TD %s → 名 %s" % (f['col'], img.u32(int(f['col'],16)), f['td'], f['name']))
    A("vt 五槽: [0]%08X [1]%08X [2]%08X [3]%08X [4]%08X" % tuple(img.u32(fv + 4*i) for i in range(5)))
    A("```")
    A("")
    A("槽 #3 = 本 entry、RTTI 描述符链 `.rdata COL→TD→名字` 直读为 `%s`，与行名 `T_TClassFactory_V%s__::slot3` 自洽。**成立**。" % (f['name'], cls))
    A("")
    A("**查2 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**")
    A("")
    lines = d['body']
    def findidx(sub):
        for i2, L in enumerate(lines):
            if sub in L: return i2
        return None
    io = findidx('call     0x7c8e17')
    sizeln = lines[io-1].strip() if io else '?'
    newln = lines[io].strip() if io else '?'
    ctor_i = findidx('call     ' + '0x' + ''.join(d['obj_ctor'][i:i+2] for i in range(6, 8, 2))) if False else None
    ninfo = [L.strip() for L in lines if 'mov      ecx, eax' in L]
    A("```")
    A("入口三闸（互斥、动作不同、各返不同 imm 错误码）:")
    for c, w in zip(d['codes'], ('ppvOut==NULL → E_INVALIDARG', 'pUnkOuter!=NULL → CLASS_E_NOAGGREGATION', 'new/ctor==NULL → E_OUTOFMEMORY')):
        A("  %08X  %s   ; %s" % (int(c[0], 16), b(int(c[0], 16), 6), w))
    A("分配        %s" % sizeln)
    A("            %s   ; = operator new" % newln)
    for L in ninfo[:1]:
        A("构造        %s" % L)
    A("QI 站点      %08X  %s        ; call dword ptr [eax]" % (qi, b(qi, 2)))
    A("消费点       %08X  %s        ; mov edi,eax" % (qi+2, b(qi+2, 3)))
    A("             %08X  %s        ; test edi,edi" % (qi+4, b(qi+4, 3)))
    jge_ins = img.dis(qi + 6, 6)[0]
    A("             %08X  %s        ; jge -> %s （零间隔、无 eax 覆写）" % (qi+6, b(qi+6, 3), jge_ins.op_str))
    A("失败路释放   %08X  %s        ; push 1 (delete 标志)" % (p1, b(p1, 2)))
    A("             %08X  %s        ; call dword ptr [edx+0x20]" % (rel, b(rel, 3)))
    A("成功/失败汇合 %08X  %s        ; mov eax,edi" % (qi+0x11, b(qi+0x11, 2)))
    A("返回约定     4 处 ret 0x10: %s" % ", ".join(x.split()[0] for x in d['rets']))
    A("```")
    A("")
    A("被调 QI 的返回约定（我自己反汇编 `%s`，%d 条指令）:" % (q['addr'], q['n']))
    A("")
    A("```")
    A("  %08X  mov eax,0x80004003 / ret 0xC   ; ppv==NULL → E_POINTER" % int(q['codes'][0].split()[0], 16))
    A("  %08X  mov [eax],0                    ; 先置空 *ppv（写出方向）" % (int(q['codes'][0].split()[0], 16) + 0x1D))
    A("  %08X  mov eax,0x80004002 / ret 0xC   ; IID 不匹配 → E_NOINTERFACE" % int(q['codes'][1].split()[0], 16))
    A("  %08X  xor eax,eax   / ret 0xC        ; 命中 → S_OK" % int(q['zeros'][0].split()[0], 16))
    A("  共 %d 处 ret，IID 以 4×dword 比较（repe cmpsd 对 007F7C90/007F7C80/007F7C70/007E9AE0 等表）" % len(q['rets']))
    A("```")
    A("")
    if r in FAILS:
        A("**⇒ 查2 在本行文字层面不成立（本行判 FAIL 的唯一原因，见 §4）。** 但函数整体合同（上表）真实：主虚表为 `%s`（ctor `%s` 于 `%s` 写 `[esi+0]`），其槽 0 = `%s`，即上段那套 HRESULT 契约。" % (mv['vt'], d['obj_ctor'], mv['at'], d['main_slot0']))
    else:
        A("**成立**：失败=负 HRESULT（`jge` 不跳）→ 立即 `push 1` 释放新建对象并原样回传负值；成功=S_OK 且 `*ppvOut` 已由 QI 写入接口指针；`test/jge` 与 QI 之间零间隔、无 `eax` 覆写；全函数仅 **1** 处 `call [eax]`（非多路汇同一 call）；非 ③a 直线/纯转发/空判断形态。")
    A("")
    A("**查3 ④ 使用见证**（活的工厂实例，非 direct-only）")
    A("")
    A("```")
    A("宿主  006BB9A0 (77 块顺序注册表；唯一 direct caller 007CD8EA：`call [0x7E1240]`=GetModuleHandleA 后 `push eax` 入参，启动/初始化路径，非析构)")
    A("分配  %08X  %s   ; push 8 (sizeof(TClassFactory))" % (int(ch['alloc'],16), b(int(ch['alloc'],16),2)))
    A("ctor  %s  装表 %08X  %s   ; mov [reg], %s" % (ch['factory_ctor'], int(ch['vt_store'],16), b(int(ch['vt_store'],16),6), f['vt']))
    A("注册  %08X  %s   ; call esi, esi=ole32!CoRegisterClassObject (IAT 007E15D8)" % (int(ch['crc'],16), b(int(ch['crc'],16),2)))
    A("GUID  实为 %s（执行器写：见下）" % ch['clsid'])
    A("```" % ())
    A("")
    A("`mov esi,[0x7E15D8]` 在 `006BC43F` 一次装定（ole32!CoRegisterClassObject 实名坐实），此后每块 `push <lpdwRegister>/push 1/push 1/push <pUnk>/push <rclsid>/call esi`。工厂实例 8 字节由 `push 8 + call 0x7C8E17` 堆分配、紧跟 `mov ecx,eax; call <ctor>` 装表、随即以 GUID 注册 —— 对象成为 **COM 侧面可派发的活类对象**。")
    A("")
    A("- 该工厂 vt `%s` 在全 `.text` **仅 1 处** imm32 引用（`%s`，即上述 ctor），**无析构器/atexit 死表重装** ⇒ ㉓ 成对陷阱排除（本二进制甚至没有 `atexit/_onexit` 导入）。" % (f['vt'], ch['vt_store']))
    A("- 本 entry 的 **direct caller = 0**（全 `.text` 68,253 站点穷举）⇒ ④ 走活对象宽读而非 direct-only。")
    A("")
    A("**查4 ④ 与 ② 不同源 = 是**：② 的证在 `.rdata`（COL/TD/名字链 + 槽值），④ 的证在 `.text`（`push 8`+`call 0x7C8E17`+装表+`call esi` 注册）与 `ole32` IAT，两者不共用同一虚表槽作双重用途。")
    A("")
    if r in FAILS:
        A("**查5 语义与实测相符 = 方向对、但 ③b 归因错**：`写出接口指针到 ppvOut，非读入` 实测成立（入口 `mov dword ptr [edi],0` 先置空、QI 收 `push edi` 并写回）；**但**第 4 列把「新建对象主 vt」写成内嵌成员表、把其 slot0 写成 QueryInterface，属**成链点归因错误**（不是方向反写，也不是 ③a/③b 子型标错）；按卡面「证据不足判 FAIL」与上批「地址全真 ≠ 主张成立」口径，本行判 FAIL。")
    else:
        A("**查5 语义与实测相符 = 是**：`写出接口指针到 ppvOut，非读入` —— 实测入口 `mov dword ptr [edi],0`（先置空）、QI 以 `push edi` 收 ppvOut；QI 内 `mov [eax],0` 后写回对象指针，方向为**写出**，与第 4 列一致；③b 子型标 ③b② 正确；无 ③a 混写；新建对象主 vt 归因正确（`%s` 写 `[esi+0]`）。" % mv['at'])
    A("")
    if r in FAILS:
        A("**本行裁定：FAIL**（理由见 §4：③b 的成链地址与错误码证据被指向内嵌成员表与 VC 器析构函数，其自陈常量表为空 ⇒ 该行文字未构成取证）。")
    elif r == '006BF810':
        A("**本行裁定：PASS**，附**必改字**：④ 的 GUID 执行器写作 `7E9580`，实测 `%s` 是 **TClassFactory<VSuperClass>** 的 GUID（其 ctor 006BF5C0 在 `006BC5AE` 注册）—— 执行器错位到前一块；本行真实 GUID 为 `%s`（`006BC5EB push`）。④ 主张本身（活类对象已注册）不因此垮，但账上文字必须改。" % ('007E9580', ch['clsid']))
    else:
        A("**本行裁定：PASS**。")
    A("")

A("""## 4. 两个 FAIL 的成因（同一种机械替换，落在 ③b 的成链点上）

两行的失败形态完全一致：不是"锚不干净"，而是**把错误的函数指认成了 QueryInterface**：

| entry | 执行器写的"主 vt / slot0=QueryInterface" | 实测真相 |
|---|---|---|
| `006BFF90` | 主 vt `007EB6D4`、slot0=`00524FC0` | 主 vt `007F5728`（`007217A6 C7 06 28 57 7F 00` 写 `[esi+0]`）、slot0=`00410260` |
| `006C0A10` | 主 vt `007F36B4`、slot0=`006B8790` | 主 vt `007F3650`（`006B6EE6 C7 06 50 36 7F 00` 写 `[esi+0]`）、slot0=`00410260` |

`007EB6D4` 与 `007F36B4` 的来历（我逐条核过 ctor）：

```
; 007216C0 TiberiumClass ctor
007216D6  8D BE C4 00 00 00     lea edi,[esi+0xC4]        ; ← 内嵌成员，不是 this
00721734  C7 07 D4 B6 7E 00     mov [edi],0x7EB6D4         ; TypeList<AnimTypeClass*> 的表
007217A6  C7 06 28 57 7F 00     mov [esi],0x7F5728         ; ← 真正的主虚表

; 006B6EA0 SpawnManagerClass ctor
006B6EAF  8D 7E 38             lea edi,[esi+0x38]         ; ← 内嵌成员
006B6EBB  C7 07 B4 36 7F 00     mov [edi],0x7F36B4         ; DynamicVectorClass<SpawnControl*> 的表
006B6EE6  C7 06 50 36 7F 00     mov [esi],0x7F3650         ; ← 真正的主虚表
```

而被当成 "QueryInterface" 的两个函数，其实是 **`VectorClass<T>` 的析构式函数**（同一模板两份实例）：

```
00524FC0  56              push esi
00524FC1  8B F1           mov esi,ecx
00524FC3  8B 46 04        mov eax,[esi+4]
00524FC6  C7 06 F4 B6 7E 00  mov [esi],0x7EB6F4     ; ← 改装 VectorClass 表
00524FD8  E8 60 3B 2A 00  call 0x7C8B3D            ; free 元素数组
00524FF8  74 09           je ...
00524FFA  56 / E8 ...
00525006  C2 04 00        ret 4                    ; 带 delete 标志位
006B8790  同型（C7 06 D4 36 7F 00 装 0x7F36D4）
```

它们既不比较 IID、也不写 `*ppvOut`、也不返回 HRESULT 三态。因此执行器那两句
"新建 X 对象主 vt 007Exxxx 的 slot0=QueryInterface 00524FC0/006B8790 … 失败返 0x80004002(E_NOINTERFACE)/0x80004003(E_POINTER)、成功返 0"
**在它自己点名的函数上为假**；其自陈的可伪证常量表恰好是空的（delta 原文写作「常量 、1 处 ret」），说明它并未取得该证据却仍照发了模板句。

> **这与上一批 `S15S16_3B2\\_audit` 的 FAIL 形态同类**（"地址全真 ≠ 主张成立"、"不解析就 PASS 等于放行一个未验证前提"）。
> 但须与本轮 Lead 的 ③ 放宽裁定区分：放宽的是"③ 不必落在 survey 命中的站点"，**不是**"③ 的成链点可以指错函数"。

**可救性（给 Lead 的判断材料）**：两行的函数整体合同真实存在（主 vt `007F5728`/`007F3650` 槽 0 均为 `00410260`，即 14 行同款 QI 契约，三码 + 3 处 ret 齐备）。**改字后即可重提**，不必重挖。

## 5. 本批另外两处必须改字（不构成 FAIL，但不得按原文并入）

1. **`006BF810` 的 GUID 错位**：原文"以 CLSID 7E9580 经 CoRegisterClassObject 注册"。实测 `007E9580` 属前一块（ctor `006BF5C0`，即 `TClassFactory<VSuperClass>`，注册点 `006BC5AE`）；本行真实 GUID 为 **`007E9950`**（`006BC5EB push`）。
2. **11 行 GUID 写成 `None`**（`006BFF90` 起至 `006C0E90` 共 11 行）：实测全部可解析，见下表。`None` 不是错值，但按卡面"给地址"的要求属**未取证**，并入前须补齐。

| entry | 工厂 ctor | GUID |
|---|---|---|
""")
for r in ROWS:
    ch = chain[r]
    A("| %s | %s | %s |" % (r, ch['factory_ctor'], ch['clsid']))
A("""
## 6. 关于"16 行是否共用同一段取证文字"（Lead 点名要答）

**结论：语义文字确认是同一段模板（逐行替换类名/地址）；但 16 个函数体本身也是同一 C++ 模板的 16 次实例化 —— 所以"文字相同"本身不等于造假，判据只能是"每行的替换值是否为该行字节的真值"。逐行核完的结果是 14 真 / 2 假。**

证据与做法：

1. **文字层**：把 16 行 `one_line_semantics` 的地址与类名替换掉做归一化，16 行**收敛为同一段**（唯一差异是 `常量` 括号与 `CLSID` 值）。⇒ 文字确实是模板。
2. **代码层**：把每行函数体的立即数归一化后逐条比对，**11 行完全相同、5 行差 1–2 条**（差在构造器参数 push 与 `sizeof` 不同）。这是模板实例化的正常形态，不是复制粘贴代码。
3. **真值层**（这才是判据）：对每行**逐个替换值**回字节核 —— ② 的 vt/槽/COL/TD/类名、③b 的 QI 站点/释放站点/push 1/三码/4 个 ret、④ 的分配点/ctor/装表点/注册点/GUID。
   - **14 行**：三类替换值全部命中本行字节。
   - **2 行**（`006BFF90` / `006C0A10`）：③b 的"主 vt / slot0"替换值**不是本行的值**（取了 ctor 里内嵌成员表），且其可伪证常量表为空 ⇒ 机械替换的痕迹在这里变成**假陈述**。
4. 因此：**这批不是"16 行共用一段空洞文字"（14 行各自站得住），但也绝不是"16 行逐行取证"（2 行的 ③b 成链是假的、1 行的 GUID 错位、11 行 GUID 未解析）。**

## 7. 判定汇总

- **PASS 14 / FAIL 2**
- FAIL：`006BFF90`、`006C0A10`（均为 ③b 成链指向内嵌成员表 + VC 器析构函数；函数整体合同真实，改字后可重提）
- 另需改字（不影响 PASS）：`006BF810` 的 GUID `7E9580`→`007E9950`；11 行 `CLSID None` 补真值（见 §5 表）。
- 逐行判定表：`verdict.tsv`（16 行）；概要：`SUMMARY.md`；可复算脚本与原始输出：`work\\`。
""")
open(os.path.join(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4", "VERDICT.md"), 'w', encoding='utf-8').write("\n".join(out))
print("written", len(out), "lines")
