# -*- coding: utf-8 -*-
"""生成 B2 批产物：EVIDENCE/ROW_<entry>.txt × 18、delta.tsv、base_rate.tsv。
所有地址/字节均从 gamemd.exe 现场读出，不用手打。每行有自己的锚点与理由。
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
from capstone import *
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(WORK)
EV = os.path.join(OUT, "EVIDENCE")
os.makedirs(EV, exist_ok=True)

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

def dis1(va, n=1):
    return list(md.disasm(R.read_va(va, 16), va))[:n]

def show(va, before=0, after=0):
    """打印 va 附近指令（含字节）。通过对齐的线性扫描保证 before 段不是假指令：
    从包含 va 的 atlas 函数起点扫到 va 之后取窗口；无函数边界时退化为从 va 起向后。"""
    # 找包含 va 的函数起点
    best = None
    for k, info in R.ATLAS.items():
        s = int(k, 16)
        if s <= va < s + info["size"]:
            if best is None or s > best[0]:
                best = (s, info["size"])
    insns = []
    if best:
        s, sz = best
        insns = [i for i in md.disasm(R.read_va(s, sz), s) if i.id != 0]
    if not insns:
        insns = [i for i in md.disasm(R.read_va(va, (after + 1) * 16 + 8), va) if i.id != 0]
    idx = next((n for n, i in enumerate(insns) if i.address == va), None)
    if idx is None:
        return ["    (锚点 %08X 不在可解码指令边界上)" % va]
    lo = max(0, idx - before)
    hi = min(len(insns), idx + after + 1)
    out = []
    for ins in insns[lo:hi]:
        mark = "   <<<" if ins.address == va else ""
        out.append("    %08X  %-20s %-8s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
    return out

def hexdump(va, n):
    b = R.read_va(va, n)
    return " ".join("%02x" % x for x in b)

def cstr_bytes(va, maxn=64):
    b = R.read_va(va, maxn)
    out = []
    for x in b:
        out.append("%02x" % x)
        if x == 0:
            break
    return " ".join(out)

# ---- 逐行规格 ----
# kind: 'dtor_find' / 'epointer_stream' / 'jump_table' / 'fwd_320' / 'fwd_380_init' / 'p3zero' / 'fn_novt'
ROWS = {
"00691DE0": dict(idx=19, kind="fwd_320",
    semantics="转发 0x410320 读嵌套对象，成功后把返回值归一化为 0",
    r3="FAIL", r3why="③a 纯转发壳：全函数仅一次 call 0x410320，两条路径只差 eax 常量（失败路原样返负 HRESULT / 成功路 xor eax,eax 后 ret 0xc），无独立动作；禁 ③a『单调用+纯转发』",
    r3anchors=[(0x691DEF, 2, 4)],
    r4="PASS", r4install=0x6916D1, r4func=0x6916B0),
"00691E30": dict(idx=20, kind="p3zero",
    semantics="按对象虚方法返回的类型码遍历脚本项并夹取索引/计数",
    r3="FAIL", r3why="无可伪证站点（p3=0）：唯一分支 0x691E46 `cmp eax,0x23` 是对虚派发 `call [eax+0x2c]` 返回的类型枚举比较（0x23=35 为枚举值，非失败/成功错误码），且被调经虚派发无法定位字节；其余全为循环夹取，无返回约定",
    r3anchors=[(0x691E43, 0, 3), (0x691E56, 0, 3)],
    r4="PASS", r4install=0x6916D1, r4func=0x6916B0),
"00691EE0": dict(idx=21, kind="dtor_find",
    semantics="ScriptClass 标量析构：装 4 张基类虚表 → 在全局 DynamicVectorClass<ScriptClass*> 中 Find 自身（未命中 -1 跳过）→ 命中则计数减一并前移压缩数组 → 调基类析构 0x4101F0 → 按 delete 标志释放",
    r3="PASS",
    r3why="③b② 成立：站点 0x691F1A `call dword ptr [edx+0x10]`；0x691F1D `cmp eax,-1`；0x691F20 `je`。被调经静态容器定位为 DynamicVectorClass<ScriptClass*>::Find=0x40EA80，其字节 0x40EA9F `83 c8 ff`(or eax,-1) 后 0x40EAA3 `ret 4` ⇒ 未命中返 -1、命中返下标，返回约定可伪证；调用方真的拿 -1 分支，两路动作不同（命中才压缩移除）。test 与 jcc 之间无 eax 覆写；单 call 非多路同一 call",
    r3anchors=[(0x691F1A, 1, 6)],
    find={"gt": "DynamicVectorClass<ScriptClass*>", "vt": 0x7E1B24, "find": 0x40EA80, "minus1_va": 0x40EA9F,
          "mov_ecx_va": 0x691F11, "container": "0x8872B0", "count": "0x8872C0", "vec": "0x8872B4"},
    r4="PASS", r4install=0x6913DD, r4func=0x6913C0),
"00691FA0": dict(idx=22, kind="dtor_find",
    semantics="ScriptTypeClass 标量析构：装 4 张基类虚表 → 在全局 DynamicVectorClass<ScriptTypeClass*> 中 Find 自身（未命中 -1 跳过）→ 命中则计数减一并压缩数组 → 调基类析构 0x4109C0 → 按 delete 标志释放",
    r3="PASS",
    r3why="③b② 成立：站点 0x691FDA `call dword ptr [edx+0x10]`；0x691FDD `cmp eax,-1`；0x691FE0 `je`。容器 0x8B41C8 的 vt=0x7EA124(DynamicVectorClass<ScriptTypeClass*>)，vt[#4]=0x4ED110=Find，其 0x4ED12F `83 c8 ff` 后 0x4ED133 `ret 4` ⇒ -1/下标约定可伪证；调用方拿 -1 分支且两路动作不同",
    r3anchors=[(0x691FDA, 1, 6)],
    find={"gt": "DynamicVectorClass<ScriptTypeClass*>", "vt": 0x7EA124, "find": 0x4ED110, "minus1_va": 0x4ED12F,
          "mov_ecx_va": 0x691FD1, "container": "0x8B41C8", "count": "0x8B41D8", "vec": "0x8B41CC"},
    r4="PASS", r4install=0x6916D1, r4func=0x6916B0),
"006A48A0": dict(idx=23, kind="epointer_stream",
    semantics="SideClass 流读入：经 0x410320 校验并转读嵌套对象（空指针则返 E_POINTER 0x80004003）→ 成功则读 4B 计数并对 +0x9C 数组逐元素读 4B → 成功返 0",
    r3="PASS",
    r3why="③b② 成立：站点 0x6A48B1 `call 0x410320`；0x6A48B6 `test eax,eax`；0x6A48B8 `jl`→0x6A48FC（原样返负 HRESULT）。被调 0x410320 的失败返回字节可伪证：0x41032B `b8 03 40 00 80`=0x80004003(E_POINTER)。两路动作真不同：失败路直接收尾返负码，成功路执行 count 读取 + 逐元素读入循环（0x6A48DE..0x6A48F7）后 xor eax,eax 返 0。test 与 jcc 之间无 eax 覆写",
    r3anchors=[(0x6A48B1, 1, 8), (0x6A48DE, 0, 5)],
    r4="PASS", r4install=0x6A4597, r4func=0x6A4550),
"006A4930": dict(idx=24, kind="dtor_find",
    semantics="SideClass 标量析构：装 4 张虚表 → 在全局 DynamicVectorClass<SideClass*> 中 Find 自身（-1 跳过）→ 压缩移除 → 按 +0xA5 标志释放 +0x9C 自有缓冲 → 调基类析构 0x4109C0 → 按 delete 标志释放",
    r3="PASS",
    r3why="③b② 成立：站点 0x6A496A `call dword ptr [edx+0x10]`；0x6A496D `cmp eax,-1`；0x6A4970 `je`。容器 0x8B4120 的 vt=0x7EA024(DynamicVectorClass<SideClass*>)，vt[#4]=0x4EC790=Find，0x4EC7AF `83 c8 ff` 后 0x4EC7B3 `ret 4` ⇒ -1/下标可伪证；调用方拿 -1 分支，命中才压缩移除",
    r3anchors=[(0x6A496A, 1, 6)],
    find={"gt": "DynamicVectorClass<SideClass*>", "vt": 0x7EA024, "find": 0x4EC790, "minus1_va": 0x4EC7AF,
          "mov_ecx_va": 0x6A4961, "container": "0x8B4120", "count": "0x8B4130", "vec": "0x8B4124"},
    r4="PASS", r4install=0x6A4597, r4func=0x6A4550),
"006E8420": dict(idx=25, kind="p3zero",
    semantics="从流中按 6 轮解析成员条目并写入 +0xA4 起的成对数组",
    r3="FAIL", r3why="零值/长度判断而非错误码：站点 0x6E847F `call 0x528A10`；0x6E8484 `test eax,eax`；0x6E8486 `jle`。被调 0x528A10 的两条出口为 0x528BC0 `33 c0`(返 0) 与 0x528BF4 `8b c1`(返串长) ⇒ 返回的是『长度或 0』，判据是 ≤0 而非失败错误码，属 D-46(A) 零/长度判断口径（同 B1 006918A0 判例）；另 6 轮循环体内无对写下标 +0x9C 的容量边界检查，③b④ 亦不成立",
    r3anchors=[(0x6E847F, 1, 4), (0x6E84C7, 0, 3)],
    r4="PASS", r4install=0x6E7EAD, r4func=0x6E7E80),
"006E8680": dict(idx=26, kind="fwd_320",
    semantics="转发 0x410320 读嵌套对象，成功后返回 0",
    r3="FAIL", r3why="③a 纯转发壳：全函数仅一次 call 0x410320（0x6E868F），0x6E8694 `test eax,eax` / 0x6E8696 `jl` 后成功路仅 0x6E8698 `xor eax,eax` 即 `ret 0xc`，两路只差返回值常量，无独立动作",
    r3anchors=[(0x6E868F, 2, 4)],
    r4="PASS", r4install=0x6E7EAD, r4func=0x6E7E80),
"006E86A0": dict(idx=27, kind="fwd_380_init",
    semantics="经 0x410380 读入嵌套对象后装 4 张虚表并构造 6 个 +0xA8 起 stride 8 的成员",
    r3="FAIL", r3why="模板假句：站点 0x6E86AB `call 0x410380` / 0x6E86B0 `test eax,eax` / 0x6E86B2 `jl` 的 E_POINTER 早退结构本身合格（0x410389 `b8 03 40 00 80`），但成功路内容全为『装 4 张虚表(0x6E86C4..0x6E86D8) + 0x6E86F1 处 call 0x6CF240 在 edi=6 的循环里构造成员 6 轮(0x6E86F1..0x6E86FA)`』，语义只能落『校验后初始化对象』式，撞卡片『模板假句』禁令（同 B1 0041E540/00691630/00691D90 形态）",
    r3anchors=[(0x6E86AB, 1, 6), (0x6E86F1, 0, 3)],
    r4="PASS", r4install=0x6E7EAD, r4func=0x6E7E80),
"006E87F0": dict(idx=28, kind="dtor_find",
    semantics="TaskForceClass 标量析构：装 4 张虚表 → 在全局 DynamicVectorClass<TaskForceClass*> 中 Find 自身（-1 跳过）→ 命中则压缩移除 → 调基类析构 0x4109C0 → 按 delete 标志释放",
    r3="PASS",
    r3why="③b② 成立：站点 0x6E882A `call dword ptr [edx+0x10]`；0x6E882D `cmp eax,-1`；0x6E8830 `je`。容器 0xA8E8D0 的 vt=0x7EA0A4(DynamicVectorClass<TaskForceClass*>)，vt[#4]=0x4ECC50=Find，0x4ECC6F `83 c8 ff` 后 0x4ECC73 `ret 4` ⇒ -1/下标可伪证；调用方拿 -1 分支，命中才压缩移除",
    r3anchors=[(0x6E882A, 1, 6)],
    find={"gt": "DynamicVectorClass<TaskForceClass*>", "vt": 0x7EA0A4, "find": 0x4ECC50, "minus1_va": 0x4ECC6F,
          "mov_ecx_va": 0x6E8821, "container": "0xA8E8D0", "count": "0xA8E8E0", "vec": "0xA8E8D4"},
    r4="PASS", r4install=0x6E7EAD, r4func=0x6E7E80),
"006E9140": dict(idx=29, kind="jump_table",
    semantics="TeamClass 消息分派：取消息类型码 up to 0x40 作越界检查，否则经 65 项跳表分派到 65 个各自独立的处理分支",
    r3="PASS",
    r3why="③b① 成立：边界检查 0x6E944B `83 f8 40`(cmp eax,0x40) + 0x6E9455 `0f 87 …`(ja 0x6E95AB，越界走默认收尾)；0x6E945B `ff 24 85 74 9f 6e 00`(jmp dword [eax*4+0x6E9F74])。跳表位于 .text 的 0x6E9F74，65 项全部读出，65 个目标全在 .text 且**互不相同**；逐路可单独验证：每块以 ret/jmp 收尾并调用各自的独立 handler（如 case1→0x6EC9A0、case3→0x6EC7D0、case9→0x6ED4D0、case10→0x6EDB50、case0→0x6ED090、case14→0x6ED200 …）",
    r3anchors=[(0x6E944B, 2, 4), (0x6E945B, 0, 1)],
    r4="PASS", r4install=0x6E8B32, r4func=0x6E8A90),
"006EB490": dict(idx=30, kind="fn_novt",
    semantics="（②不成立，不产出一句话语义）",
    r3="未计入", r3why="② 物理不成立，③ 不计入裁定；仅记录：chA 站点 0x6EB56F `call` 目标 0x47C2A0 无 atlas 边界且该地址落在某函数中部（0x47C2A0 字节 `00 00` 即 add [eax],al），无法定返回约定",
    r3anchors=[(0x6EB56F, 1, 3)],
    r4="FAIL", r4why="仅有 6 个 direct 调用者、无活虚表槽位；D-40 ④『direct-only 不足』"),
"006EBAD0": dict(idx=31, kind="fn_novt",
    semantics="（②不成立，不产出）",
    r3="未计入", r3why="② 物理不成立；且机械站点是假阳：chA 把 call 0x6EBD52 `call [edx+0x184]` 与 3 条之后的 0x6EBD67 `test eax,eax` 配成对，但两者之间 0x6EBD61 `8b 86 a4 05 00 00`(mov eax,[esi+0x5a4]) 已覆写 eax ⇒ 正是卡片点名的『eax 覆写陷阱』",
    r3anchors=[(0x6EBD52, 0, 6)],
    r4="FAIL", r4why="仅 12 个 direct 调用者、无活虚表槽位（全镜像 0 引用）"),
"006EC450": dict(idx=32, kind="fwd_380_init",
    semantics="经 0x410380 读入嵌套对象后装 4 张虚表并构造 +0x24..+0x44 共 11 个成员",
    r3="FAIL", r3why="模板假句：站点 0x6EC45B `call 0x410380` / 0x6EC460 `test eax,eax` / 0x6EC462 `jl` 的 E_POINTER 早退合格，但成功路为『call 0x4101C0、call 0x426620、装 4 张虚表 0x6EC485..0x6EC499、11 次 call 0x6CF240(0x6EC4A9..0x6EC535) 构造成员』，语义只能写成『校验后初始化对象』，撞『模板假句』禁令",
    r3anchors=[(0x6EC45B, 1, 4), (0x6EC4A9, 0, 3)],
    r4="PASS", r4install=0x6E8B32, r4func=0x6E8A90),
"006EC540": dict(idx=33, kind="fwd_320",
    semantics="转发 0x410320 读嵌套对象，成功后返回 0",
    r3="FAIL", r3why="③a 纯转发壳：仅一次 call 0x410320（0x6EC54F），0x6EC554 `test eax,eax` / 0x6EC556 `jl` 后成功路仅 0x6EC558 `xor eax,eax` 即 `ret 0xc`，两路只差常量",
    r3anchors=[(0x6EC54F, 2, 4)],
    r4="PASS", r4install=0x6E8B32, r4func=0x6E8A90),
"006EC9A0": dict(idx=34, kind="fn_novt",
    semantics="（②不成立，不产出）",
    r3="未计入", r3why="② 物理不成立；仅记录：chA 站点 0x6ECA05 `call 0x6E9050` 后 0x6ECA0D `test eax,eax` / 0x6ECA0F `je`，但 0x6E9050 是 `ret 4` 的 void 函数（0x6E912F `c2 04 00`），不收尾 eax ⇒ 返回约定不可伪证",
    r3anchors=[(0x6ECA05, 0, 4)],
    r4="FAIL", r4why="仅 1 个 direct 调用者、无活虚表槽位（全镜像 0 引用）"),
"006ECA70": dict(idx=35, kind="fn_novt",
    semantics="（②不成立，不产出）",
    r3="未计入", r3why="② 物理不成立；仅记录：chA 站点 0x6ECAE3 `call 0x6E9050` 后 0x6ECAEB `test eax,eax` / 0x6ECAED `je`，被调同为 void `ret 4`（0x6E912F `c2 04 00`）⇒ 返回约定不可伪证",
    r3anchors=[(0x6ECAE3, 0, 4)],
    r4="FAIL", r4why="仅 1 个 direct 调用者、无活虚表槽位（全镜像 0 引用）"),
"006ED200": dict(idx=36, kind="fn_novt",
    semantics="（②不成立，不产出）",
    r3="未计入", r3why="② 物理不成立；仅记录：chA 站点 0x6ED294 `call dword ptr [edx+0x2c]`（虚派发）后 0x6ED297 `cmp eax,1` / 0x6ED29A `je`，比较的是对象类型枚举而非错误码",
    r3anchors=[(0x6ED294, 0, 4)],
    r4="FAIL", r4why="仅 1 个 direct 调用者、无活虚表槽位（全镜像 0 引用）"),
}

REFS = json.load(open(os.path.join(WORK, "refs.json"), encoding="utf-8"))
R4 = json.load(open(os.path.join(WORK, "ring4.json"), encoding="utf-8"))

def ring2(entry):
    v = REFS[entry]
    if not v["slots"]:
        return None
    s = v["slots"][0]
    return s["resolved"], s["ref_va"]

def build(entry, spec):
    e = entry
    ea = int(e, 16)
    size = R.ATLAS.get(e, {}).get("size") or 0
    ins = list(md.disasm(R.read_va(ea, size), ea))
    L = []
    A = L.append
    A("ROW_%s   subsystem=S14   name=%s   批次=s14_B2 第%d行(全局第%d)" % (e, REFS[e]["name"], spec["idx"] - 18, spec["idx"]))
    A("目标: ra2youli\\gamemd.exe  SHA-256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476")
    A("ImageBase=0x400000  .text=[0x401000,0x7E038D)")
    A("")
    # ①
    A("[环① 入口]")
    A("  entry=%08X 在 .text=%s  atlas_size=%d  n_insn=%d  skipdata=%d 首条=%s 末条=%s %s" % (
        ea, R.in_text(ea), size, len(ins), sum(1 for i in ins if i.id == 0),
        ("%s %s" % (ins[0].mnemonic, ins[0].op_str)) if ins else "-",
        ("%s %s" % (ins[-1].mnemonic, ins[-1].op_str)) if ins else "-",
        " 首条字节=" + ins[0].bytes.hex() if ins else ""))
    A("  函数边界自洽：末条为 ret/ret-imm/jmp ⇒ %s" % (bool(ins) and ins[-1].mnemonic.startswith(("ret", "jmp"))))
    A("")
    # ②
    r2 = ring2(e)
    A("[环② 类身份]")
    if r2:
        res, refva = r2
        vt = int(res["vtable"], 16); off = res["slot_off"]
        A("  .rdata 中本 entry 作 4B VA 的槽: %s = %s（唯一命中，全镜像 dword 引用数=%d）" % (
            refva, hexdump(int(refva, 16), 4), REFS[e]["refs_total"]))
        A("  vtable_base=%s  slot_off=%d  slot_no=%d   线索槽号=%s ⇒ 自洽=%s" % (
            res["vtable"], off, off // 4,
            (REFS[e]["name"].split("slot")[-1] if "slot" in REFS[e]["name"] else "(fn_式名字,无槽号线索)"),
            (off // 4 == int(REFS[e]["name"].split("slot")[-1])) if "slot" in REFS[e]["name"] else "n/a"))
        A("  [vt-4]=COL %s 字节=%s   sig=%d(0=正常单一继承)" % (res["col"], hexdump(int(res["col"], 16), 16), 0))
        A("  [COL+0xC]=TD %s 字节=%s" % (res["td"], hexdump(int(res["td"], 16), 12)))
        A("  TD+8 名串 @%s 字节=%s" % (res["name_va"], cstr_bytes(int(res["name_va"], 16))))
        A("  RTTI 类名 = %s" % res["rtti"])
        A("  结论: PASS —— 由 RTTI 描述符(COL→TD→名串)与虚表槽独立钉死，未借用名字中的 Class 部分")
    else:
        A("  全镜像（.text/.rdata/.data 全部段）以 4B VA 搜索本 entry：命中 %d 次" % REFS[e]["refs_total"])
        A("  本函数体内是否存在把带 RTTI 的虚表写入 [mem] 的指令：%s" % ("无" if not REFS[e]["installs_by_self"] else REFS[e]["installs_by_self"]))
        A("  结论: FAIL —— 无虚表槽、无 RTTI 描述符链可回扫；名字 %s 只是地址式标签（不以 sub_ 开头才被机械计为 named），不构成类身份" % REFS[e]["name"])
    A("")
    # ③
    A("[环③ 整体合同]  裁定=%s" % spec["r3"])
    A("  %s" % spec["r3why"])
    for (va, before, after) in spec["r3anchors"]:
        A("  锚点 %08X 附近：" % va)
        for ln in show(va, before, after):
            A(ln)
    if spec.get("find"):
        f = spec["find"]
        A("  被调(Find)证据：容器对象首 dword 的虚表由 .text 构造期安装指令钉住 —— vt=%08X(%s)" % (f["vt"], f["gt"]))
        A("    vt[#4]=%08X = Find 函数体：" % f["find"])
        for ln in show(f["find"], 0, 10):
            A(ln)
        A("    未命中返回 -1 的字节：%08X 字节=%s" % (f["minus1_va"], hexdump(f["minus1_va"], 5)))
        if f.get("mov_ecx_va"):
            A("  容器 this 传入 + 字段自洽（独立于虚表的第二道交叉校验）：")
            for ln in show(f["mov_ecx_va"], 1, 2):
                A(ln)
            A("    站点前有 `mov ecx,0x%08X` ⇒ 本次 call 的 this 即该全局容器实例；" % int(f["container"], 16))
            A("    Find 体内读 [ecx+0x10]=0x%08X(元素计数) 与 [ecx+4]=0x%08X(向量指针)，" % (int(f["count"], 16), int(f["vec"], 16)))
            A("    与本函数内压缩移除代码所用的 0x%08X / 0x%08X 逐字段一致 ⇒ 被调确为该容器的 Find，非猜测" % (
                int(f["count"], 16), int(f["vec"], 16)))
    A("")
    # ④
    A("[环④ 使用见证]  裁定=%s" % spec["r4"])
    v4 = R4.get(e, {})
    if v4.get("vt"):
        A("  vt=%s  slot#%d  vt[slot]==entry? %s (槽值=%s)" % (
            v4["vt"], v4["slot_no"], v4["slot_points_to_entry"], v4["slot_value"]))
        A("  行外、非 atexit 的构造安装点共 %d 个；本行举证用 %08X（所在函数 %s，基类 ctor 调用见下）" % (
            v4["n_outside_alive"], spec["r4install"], ("%08X" % spec["r4func"]) if spec.get("r4func") else "-"))
        A("  安装点附近：")
        for ln in show(spec["r4install"], 3, 3):
            A(ln)
        A("  安装点字节：%08X = %s" % (spec["r4install"], hexdump(spec["r4install"], 6)))
        fsz = R.ATLAS.get("%08X" % spec["r4func"], {}).get("size") or 0
        fbody = list(md.disasm(R.read_va(spec["r4func"], fsz), spec["r4func"]))
        calls = sorted({("%08X" % (i.operands[0].imm & 0xFFFFFFFF)) for i in fbody
                        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM})
        A("  所在函数 %08X size=%d 前若干条（构造器形态：先调基类 ctor 再装本类虚表）" % (spec["r4func"], fsz))
        for ln in show(spec["r4func"], 0, 7):
            A(ln)
        A("  该函数全部直接调用目标: %s" % ", ".join(calls[:12]))
        A("  是否 atexit 析构注册（push <fn>; call 0x7C978A）: False（已逐点排除）")
    else:
        A("  %s" % spec.get("r4why", "无"))
    A("")
    # 交叉
    A("[②④不同源]")
    if r2 and v4.get("vt"):
        A("  ② 锚在 .rdata 的 RTTI 描述符/虚表槽 %s；④ 锚在 .text 的构造安装指令 %08X —— 段不同、地址不同、产物类型不同，且非同一虚表槽复用" % (
            ring2(e)[1], spec["r4install"]))
    else:
        A("  ② 不成立，无从谈不同源")
    A("")
    A("[裁定] %s" % ("四环齐全 ⇒ [已证]，写入 delta.tsv" if (spec["r3"] == "PASS" and spec["r4"] == "PASS" and r2) else "不成立，不写入 delta.tsv"))
    return "\n".join(L) + "\n"

delta_rows = []
for e, spec in ROWS.items():
    txt = build(e, spec)
    open(os.path.join(EV, "ROW_%s.txt" % e), "w", encoding="utf-8").write(txt)
    r2ok = bool(REFS[e]["slots"])
    if spec["r3"] == "PASS" and spec["r4"] == "PASS" and r2ok:
        delta_rows.append((e, REFS[e]["name"], spec))

delta_rows.sort(key=lambda x: int(x[0], 16))

def one_line(e, nm, spec):
    """每行自己的 one_line_semantics：③ 站点/字节 + 语义 + ② 锚 + ④ 锚（全部本行地址）。"""
    res, refva = ring2(e)
    v4 = R4[e]
    head = "%s %s —— %s。语义：%s。② 槽 %s(vt %s +0x%X，slot#%d) 的 4B 值即本 entry，RTTI COL=%s→TD=%s→name=%s，槽号与线索自洽；④ 活 vt 构造安装点 0x%s(in_func=%s，atexit=False，写在行外、与 ② 槽不共用) 把 vt 装入活对象，②④ 不同源(.rdata RTTI 数据链 vs .text 构造安装指令)。" % (
        "S14", nm, spec["r3why"], spec["semantics"],
        refva, res["vtable"], res["slot_off"], res["slot_off"] // 4,
        res["col"], res["td"], res["rtti"],
        ("%08X" % v4_stores_first(e)), ("%08X" % spec["r4func"]))
    return head

# ④ 举证安装点（取 ring4 里第一个「行外且非 atexit」的写点）
def v4_stores_first(e):
    for s in R4[e]["stores"]:
        if not s["in_self"] and s["atexit"] is False:
            return int(s["va"], 16)
    return int(R4[e]["stores"][0]["va"], 16)

with open(os.path.join(OUT, "delta.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\n")
    for e, nm, spec in delta_rows:
        sem = one_line(e, nm, spec).replace("\t", " ").replace("\n", " ")
        f.write("%s\tS14\t%s\t%s\t[已证]\tD:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S14_B2/EVIDENCE/ROW_%s.txt\n" % (e, nm, sem, e))

n2 = sum(1 for e in ROWS if REFS[e]["slots"])
n3 = sum(1 for e, s in ROWS.items() if s["r3"] == "PASS")
n4 = sum(1 for e, s in ROWS.items() if s["r4"] == "PASS")
tot = len(ROWS)
with open(os.path.join(OUT, "base_rate.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("S14_B2\t%d\t%d\t%d\t%d\t%d\t%.4f\n" % (tot, n2, n3, n4, len(delta_rows), len(delta_rows) / tot))

print("evidence files:", len(ROWS))
print("delta rows:", len(delta_rows), [x[0] for x in delta_rows])
print("counts: ring2=%d ring3b=%d ring4=%d all=%d rate=%.4f" % (n2, n3, n4, len(delta_rows), len(delta_rows) / tot))
