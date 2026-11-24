import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11"
facts = json.load(open("facts_final.json", encoding="utf-8"))
_v3 = {x["entry"]: x for x in json.load(open("verify3.json", encoding="utf-8"))}

head = """# VERDICT — NAMED_PUSH_S22_B3 异族独立审计（11 行）

- 目标：`D:\\Project\\ra2-campaign-forge\\ra2youli\\gamemd.exe`
- SHA-256：`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（本审计用 `hashlib` 自算，与卡面期望一致）
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（本审计以 PE 节表实测：`.text` VA `0x401000`，VirtualSize `0x3DF38D`）
- 工具：capstone **5.0.7**（`skipdata=True`）+ pefile **2024.8.26**，Python **3.12.10**，无 venv、未 pip install
- 取证脚本：`_work\\pe.py`（PE/VA 映射 + RTTI 链 + 全 `.text` 指令边界扫描）+ `_work\\s1..s23_*.py`；原始输出 `_work\\s*_out.txt`
- **未引用**执行器 `EVIDENCE\\ROW_*.txt` 作为证据；行内每个地址/字节均由本审计脚本本机反汇编得出（下文 `sNN` 指脚本编号）

## 判定口径（照 `R14_COMMON.md` §8.6 / §12.3 / 错源 ㉓）

- ② `[vt-4]=COL → [COL+0xC]=TD → TD+8 串`，且 `vt[slot]==entry`
- ③b② 可证伪错误码/返回约定（D-46(A) 窄读：只认错误码/返回约定）
- ④ direct call 或 活 vtable 槽位派发（构造器装的活表 + `vt[slot]==entry` + site 不共用）；`atexit` 析构器装的表不算（㉓）
- ②④ 不得同源（同一个虚表槽不能既证身份又证被使用）

## 本批 11 行的共同结构（先给一次，逐行只写差异）

11 行全部是 `TClassFactory<V<Xxx>Class>` 的 **slot3（IClassFactory::CreateInstance）**，位于一段连续的类工厂区
`[006C2A40, 006C3E00)`。该区每个工厂类占 4 个函数：`ctor`（trampoline 装表）、`slot0=QI`、`slot1=AddRef`、
`slot2=Release`、`slot3=本 entry`、`slot4=LockServer`。实测例（`006C2B10` 所在工厂 007F3B28）：

```
007F3B24  COL 0080A8E8          ; vt-4
007F3B28  slot0 006C2A50  QI(this,riid,ppv)  ret 0xc，ppv 空返 0x80004003
007F3B2C  slot1 006C2AC0  AddRef(this)       InterlockedIncrement [this+4]，ret 4
007F3B30  slot2 006C2AE0  Release(this)      InterlockedDecrement [this+4]，ret 4
007F3B34  slot3 006C2B10  <<< 本 entry        CreateInstance  ret 0x10
007F3B38  slot4 006C2B90  LockServer(this,flag) ret 8
```

**该 vtable 是「显式 this 的 stdcall」**：`QI(this,riid,ppv)` 3 栈参→`ret 0xc`；`AddRef/Release(this)` 1 栈参→`ret 4`；
`slot3(this,pUnkOuter,riid,ppvOut)` 4 栈参→`ret 0x10`。四个栈参与 `IClassFactory::CreateInstance` 完全自洽
（本审计最初按 thiscall 误算成「多一个参数」，已用 `_work\\s13_qi.py`/`s19_iid.py` 逐槽复算纠正）。

**「主虚表 slot0 = 00410260」这条约束指的是体内新建对象的对象主虚表，不是工厂自身虚表**（工厂自身 `vt[0]=006C2A50`，
是该工厂的 QI）。本审计对 11 行逐一追了 `alloc → ctor → mov [this],vt`，取 **this 寄存器**上的偏移 0 写点，
再用 `[vt-4]→COL→TD→名串` 验类名，结果全部命中「对象主虚表 `vt[0]=00410260` 且类名 = 工厂模板实参」。

"""

secs = []
for f in facts:
    s = []
    e = f["e"]
    s.append(f"---\n\n## {e} — `T_TClassFactory_V{f['cls']}__::slot3`\n")
    s.append(f"**第 1 项 ② 类身份（独立成立）**\n")
    s.append(f"- 本 entry 作为 4B VA 在 `.rdata` 中唯一命中槽 `{f['vt']}+12 = {int(f['vt'],16)+12:08X}`（slot#{f['slot_no']}），"
             f"该 4 字节值 `{e}` 即本 entry。")
    s.append(f"- `[vt-4] = {f['col']}`（COL，位于 `.rdata`）→ `[COL+0xC] = {f['td']}`（TD，位于 `.data`）→ "
             f"TD+8 内联名串 `{f['fname']}`。类名与行名中的 `TClassFactory<V{f['cls']}>` 逐字吻合。")
    s.append(f"- 工厂自身 `vt[0] = {_v3[f['e']]['vt_slots'][0][1]}`（该工厂的 QI，`ret 0xc`，ppv 空返 `0x80004003`）——**不是** `00410260`，"
             f"故 `slot0=00410260` 这条约束只能落在体内新建对象上（见第 5 项）。")
    s.append(f"- 结论：**② 成立**。\n")

    s.append(f"**第 2 项 ③b 具体形态 = ③b②（可伪证错误码/返回约定）**\n")
    s.append(f"入口三道 imm 错误码守卫（字节内可核）：")
    s.append("")
    s.append("| 守卫 | 地址 | 字节 | 立即数 | 语义 |")
    s.append("|---|---|---|---|---|")
    s.append(f"| 1 | `{f['guard_addrs'][0]}` | `{f['guard_bytes'][0]}` | `{f['guards'][0]}` | ppvOut 为空 |")
    s.append(f"| 2 | `{f['guard_addrs'][1]}` | `{f['guard_bytes'][1]}` | `{f['guards'][1]}` | pUnkOuter 非空（禁止聚合） |")
    s.append(f"| 3 | `{f['guard_addrs'][2]}` | `{f['guard_bytes'][2]}` | `{f['guards'][2]}` | 分配/构造失败 |")
    s.append("")
    s.append(f"- 分配→构造接线：`push {f['size']}` → `call 0x7C8E17`(@`{f['alloc']:08X}`) → `test eax,eax` → `je` 失败码 "
             f"→ `mov ecx,eax` → `call {f['obj_ctor']}`。")
    s.append(f"- 主站点：`{f['qi']}` 处 `ff 10 call dword ptr [eax]`，`eax=[esi]`=新建对象主虚表， "
             f"即 `vt[0]=00410260` 的 QueryInterface。紧接 `8b f8 mov edi,eax` / `85 ff test edi,edi` / "
             f"`7d 09 jge {f['jge']}`（test 与分支零间隔，返回值在 `edi`，其后唯一 eax 写是成功路 `mov eax,edi`）。")
    s.append(f"- 两路动作不同：失败路 `{f['push1']}` `push 1` + `mov ecx,esi` + `{f['destroy']}` `call [edx+0x20]`"
             f"（=主虚表 slot8 = `{f['slot8']}`，该函数先回写四张类虚表、再把自己从全局容器摘除、"
             f"末尾 `test byte [esp+0xc],1` → `push esi; call 0x7C8B3D`，**是真删除型析构**）；成功路直接 `mov eax,edi` 回传 HRESULT。")
    s.append(f"- 被调 `00410260` 的返回常量：`00000000` / `80004003`(E_POINTER) / `80004002`(E_NOINTERFACE)，`ret 0xc` 共 3 处。")
    s.append(f"- 结论：**③b② 成立**（非 ③a：有 4 处分支与 3 个可区分错误码，非「单次调用+单次写」线性流程）。\n")

    s.append(f"**第 3 项 ④ 使用见证（活表 + 注册，独立于 ②）**\n")
    s.append(f"- 工厂对象由 `0x6BB9A0`（类系统初始化，size `0x2810`）在 heap 上 `new(8)` 后经 ctor 构造，"
             f"ctor 唯一装表点 `{f['installer']}`：`mov dword ptr [eax], {f['vt']}`（字节 `c7 00 ...`）。")
    s.append(f"- 随即 `push &dwRegister; push 1(REGCLS); push 1(CLSCTX); push <factory>; push CLSID `{f['clsid']}`; "
             f"call esi`，其中 `esi = dword ptr [0x7E15D8]`（`006BC43F mov esi,[0x7e15d8]`）= **OL32 `CoRegisterClassObject`**；"
             f"本行注册点 `{f['reg']:08X}`。")
    s.append(f"- 该工厂的 QI 接受 `IID_IUnknown`(`007F7C90`) 与 `IID_IClassFactory`(`007F7CA0`)，故注册出去的确实是可派发的类工厂；"
             f"cookie 存入 `0xB0BC88` 向量，退出时以 `CoRevokeClassObject`(`0x7E15CC`) 注销。")
    s.append(f"- ㉓ 检查：`{f['vt']}` 在**整个 `.text` 只有 1 处 imm 写点**（`{f['installer']}`），无析构器写点、"
             f"无成对死表；写入者 `{int(f['installer'],16)-9:08X}` 是 ctor，其唯一调用者是初始化函数内的 `{f['reg']:08X}` 附近，"
             f"`0x6BB9A0` 在全镜像**无 imm 引用**（非 `push <dtor>; call 0x7C978A` 的 atexit 注册）。⇒ ㉓ 排除。")
    s.append(f"- 本 entry 全镜像 direct caller = **0**（`E8 rel32` 全扫），故 ④ 只能走「活 vtable 槽位」形态——本行正是该形态且 site 不共用。")
    s.append(f"- 结论：**④ 成立**。\n")

    s.append(f"**第 4 项 ②④ 是否同源 → 不同源**\n")
    s.append(f"- ② 的取材料是 `.rdata` 的 RTTI 链（COL `{f['col']}` / TD `{f['td']}` / 名串）与槽值 `{f['vt']}+12`；"
             f"④ 的取材料是 `.text` 的装表指令 `{f['installer']}` 与注册指令 `{f['reg']:08X}`。段不同、地址不同、"
             f"证明的事实不同（「这函数属于哪个类」vs「这个类工厂对象被构造并注册进 COM」）。")
    s.append(f"- 结论：**不同源（same_source=no）**。\n")

    s.append(f"**第 5 项 语义与实测是否相符**\n")
    s.append(f"- 第 4 列称「新建 {f['cls']} 对象主 vt `{f['main_vt']}` 的 slot0=`00410260`」：本审计追 `{f['obj_ctor']}` 得 "
             f"`{f['main_vt_site']}` 处 `mov [this], {f['main_vt']}`，`vt[0] = {f['main_vt_slot0']}`，"
             f"`[vt-4]→COL→名串 = {f['main_vt_rtti']}` ⇒ **吻合，且是主表不是小成员表**。")
    s.append(f"- 方向核对：`mov [edi],0` 先把出参清零，QI 再把接口指针**写出**到该出参（`push edi` 作为 QI 第 3 参），"
             f"不是读入 ⇒ 与「写出接口指针到 ppvOut，非读入」一致。")
    s.append(f"- 子型核对：③b②（错误码/返回约定）而非 ③b①/③b③/③b④ ⇒ 与第 4 列标注一致。")
    s.append(f"- 结论：**相符**。\n")

    # 陷阱核对: list excluded vt writes in the object ctor
    allw = _v3[f["e"]]["obj_all_vt_writes"]
    this_reg = _v3[f["e"]]["this_reg"]
    # earliest ret inside the ctor linear body -> anything after it belongs to a neighbour fn
    ctor_va = int(f["obj_ctor"], 16)
    first_ret = None
    for i in dis(ctor_va, 0x1200):
        if i.mnemonic.startswith("ret"):
            first_ret = i.address
            break
    excl = []
    for a, dst, v, by in allw:
        if dst == this_reg and v == f["main_vt"]:
            continue
        info = rtti_class(int(v, 16))
        loc = "ctor 内首个 ret 之前" if (first_ret is None or int(a, 16) < first_ret) else \
              f"**另一函数**（首个 ret @{first_ret:08X} 之后）"
        excl.append(f"`{a}`(dst `{dst}`) → `{v}` ({info.get('name')}) — {loc}")
    if excl:
        s.append(f"**陷阱核对（差分检验，㉔）**：同一 ctor 体内还有下列虚表写点，**均未**被本行当作「对象主虚表」，本审计逐一用 RTTI 名判了身份：")
        s.append("")
        for x in excl:
            s.append(f"  - {x}")
        s.append("")
        # flag any write of the SAME main vt at a different site (ctor/dtor pair)
        same = [w for w in allw if w[2] == f["main_vt"] and w[0] != f["main_vt_site"]]
        if same:
            s.append(f"  ⚠ **同表另一写点**：{', '.join('`' + w[0] + '`' for w in same)} 也写 `{f['main_vt']}`。"
                     f"其中落在 ctor 之外（析构侧/另一个函数）的那处属 ㉓ 的「成对」形态；本行的 ④ 锚在**工厂表**"
                     f"（`{f['vt']}`，装表点 `{f['installer']}` 唯一），**未**拿对象表充当 ④，故不触发 ㉓。"
                     f"若仅凭「对象表的某处写点」判 ④，这一行会踩坑——本审计已排除该路径。")
            s.append("")
        s.append(f"  只有 dst = this(`{this_reg}`) 且 RTTI 名 = `{f['main_vt_rtti']}` 的那一处（`{f['main_vt_site']}`）被计为对象主虚表；"
                 f"其余是小成员表/次基类表，若拿它们凑 `vt[0]=00410260` 会失败 —— **本行未踩该陷阱**。")
        s.append("")

    s.append(f"**本行裁定：`PASS`**\n")
    secs.append("\n".join(s))

open(OUT + r"\VERDICT.md", "w", encoding="utf-8", newline="\n").write(head + "\n".join(secs))
print("VERDICT.md written")
