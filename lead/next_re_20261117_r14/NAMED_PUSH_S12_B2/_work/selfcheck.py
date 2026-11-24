# -*- coding: utf-8 -*-
"""产物自校验：把 REPORT/delta/EVIDENCE 的每个可自动核对的断言回到二进制复算。"""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
rows = json.load(open(os.path.join(HERE, "rows_b2.json"), encoding="utf-8"))
summ = json.load(open(os.path.join(HERE, "final_summary.json"), encoding="utf-8"))

FAILS = []


def ck(cond, msg):
    if not cond:
        FAILS.append(msg)
        print("  [X] %s" % msg)


def ins(va):
    d = disasm(va, 15)
    return d[0] if d else None


def writes_eax_between(va, nbytes):
    d = disasm(va, nbytes)
    for i in d:
        try:
            _, w = i.regs_access()
        except Exception:
            w = []
        if X86_REG_EAX in w:
            return i
    return None


MAIN = {
    "BuildingClass": (0x007E3EBC, 322, ".?AVBuildingClass@@"),
    "BuildingTypeClass": (0x007E4570, 49, ".?AVBuildingTypeClass@@"),
    "CaptureManagerClass": (0x007E4B40, 24, ".?AVCaptureManagerClass@@"),
    "FactoryClass": (0x007E88D0, 24, ".?AVFactoryClass@@"),
}

print("== 1) 15 行 ① ② 复算 ==")
for r in rows:
    e = r["entry"]
    ev = int(e, 16)
    cls = r["name"].split("::")[0]
    slot = int(r["name"].split("::")[1].replace("vslot", "").replace("slot", ""))
    vt, n, rtti = MAIN[cls]
    ck(in_text(ev), "%s 不在 .text" % e)
    ck(hx(ev) in ATLAS, "%s 不在 atlas" % e)
    ck(slot < n, "%s 槽号 %d >= 表槽数 %d" % (e, slot, n))
    ck(u32(vt + 4 * slot) == ev, "%s 槽 %08X 值 != entry" % (e, vt + 4 * slot))
    col = u32(vt - 4)
    ci = parse_col(col)
    ck(ci and ci["sig"] == 0, "%s COL 签名非 0" % e)
    td = parse_td(ci["td"])
    ck(td and td["name"] == rtti, "%s RTTI 名 %s != %s" % (e, td and td["name"], rtti))
    ck(u32(vt) == 0x410260, "%s 主表 slot0 != 00410260" % e)
    # 陷阱③：确认 entry 不在任何小表里
    for sva in (0x7E3E90, 0x7E3E98, 0x7E3EA0, 0x7E4544, 0x7E454C, 0x7E4554,
                0x7E4B14, 0x7E4B1C, 0x7E4B24, 0x7E88A4, 0x7E88AC, 0x7E88B4):
        for k in range(6):
            ck(u32(sva + 4 * k) != ev, "%s 误落小表 %08X slot%d" % (e, sva, k))
print("   done")

print("\n== 2) ④ 构造安装点复算（含 atexit / 析构器排除）==")
CTOR = {
    "BuildingClass": [(0x0043B71F, 0x0043B680), (0x0043B9FA, 0x0043B740)],
    "BuildingTypeClass": [(0x0045E2CD, 0x0045DD90), (0x0045E558, 0x0045E520)],
    "CaptureManagerClass": [(0x00471807, 0x004717D0), (0x004718BC, 0x00471890)],
    "FactoryClass": [(0x004C991A, 0x004C98B0), (0x004CA2C7, 0x004CA270)],
}
for cls, lst in CTOR.items():
    vt = MAIN[cls][0]
    for w, fn in lst:
        got = u32(w + 2)
        ck(got == vt, "%s 安装点 %08X 立即数 %s != vt" % (cls, w, got and hex(got)))
        i = ins(w)
        ck(i and i.mnemonic == "mov" and "dword ptr" in i.op_str,
           "%s 安装点 %08X 非 mov dword" % (cls, w))
        ck(is_atexit_registered(fn) == [], "%s 安装点函数 %08X 出现在 atexit 表" % (cls, fn))
        # 构造器特征：不出现 test byte [esp+N],1 的删除式析构签名
        info = ATLAS.get(hx(fn))
        body = disasm(fn, info["size"])
        has_del = any(x.id == X86_INS_TEST and len(x.operands) == 2
                      and x.operands[1].type == X86_OP_IMM and x.operands[1].imm == 1
                      and x.operands[0].type == X86_OP_MEM for x in body)
        ck(not has_del, "%s 安装点函数 %08X 带删除式析构签名" % (cls, fn))
print("   done")

print("\n== 3) 6 个成立行的 ③b② 站点复算 ==")
# --- 00453E20 ---
i = ins(0x453EB8); ck(i and i.mnemonic == "cmp" and i.op_str == "eax, ebx", "00453E20 cmp 形态")
ck(ins(0x453E46).mnemonic == "xor" and ins(0x453E46).op_str == "ebx, ebx", "00453E20 ebx 未置 0")
j = ins(0x453EBE)
ck(j and j.mnemonic.startswith("j") and (j.operands[0].imm & 0xFFFFFFFF) == 0x45417E, "00453E20 jcc 目标")
ck(writes_eax_between(0x45417E, 6) is None, "00453E20 失败落点写了 eax")
i = ins(0x70C246); ck(i and i.mnemonic == "mov" and i.op_str == "eax, ebx", "0x70C246 成功返 0 形态")
ck(ins(0x70BF61).op_str == "ebx, ebx", "0x70BF61 ebx 未置 0")
ck(writes_eax_between(0x70C249, 8) is None, "0x70C249 失败落点写了 eax")
# --- 00465300 ---
i = ins(0x465318); ck(i and i.mnemonic == "test" and i.op_str == "eax, eax", "00465300 test 形态")
j = ins(0x46531A)
ck(j and j.mnemonic == "jl" and (j.operands[0].imm & 0xFFFFFFFF) == 0x46536A, "00465300 jl 目标")
i = ins(0x465368); ck(i and i.mnemonic == "xor" and i.op_str == "eax, eax", "00465300 成功 xor eax,eax")
ck(writes_eax_between(0x46536A, 8) is None, "00465300 失败落点写了 eax")
ck(writes_eax_between(0x717094, 8) is None, "0x717094 失败落点写了 eax")
i = ins(0x717091); ck(i and i.mnemonic == "xor" and i.op_str == "eax, eax", "0x717091 成功返 0")
# --- 004728E0 ---
i = ins(0x4728F3); ck(i and i.mnemonic == "call" and i.op_str == "0x410320", "004728E0 call 形态")
ck(ins(0x4728F8).op_str == "edi, eax", "004728E0 mov edi,eax")
ck(ins(0x4728FA).op_str == "edi, edi", "004728E0 test edi,edi")
j = ins(0x472900); ck(j and j.mnemonic == "jl" and (j.operands[0].imm & 0xFFFFFFFF) == 0x472956, "004728E0 jl 目标")
i = ins(0x41032B); ck(i and i.mnemonic == "mov" and i.op_str == "eax, 0x80004003", "0x41032B E_POINTER 常量")
# --- 004CA3C0 ---
i = ins(0x4CA3D2); ck(i and i.mnemonic == "call" and i.op_str == "0x410320", "004CA3C0 call 形态")
j = ins(0x4CA3D9); ck(j and j.mnemonic == "jl" and (j.operands[0].imm & 0xFFFFFFFF) == 0x4CA41F, "004CA3C0 jl 目标")
ck(writes_eax_between(0x4CA41F, 6) is None, "004CA3C0 失败落点写了 eax")
i = ins(0x4CA41D); ck(i and i.mnemonic == "xor" and i.op_str == "eax, eax", "004CA3C0 成功 xor eax,eax")
# --- 004729C0 ---
i = ins(0x4729F3); ck(i and i.mnemonic == "call" and "[edx + 0x10]" in i.op_str, "004729C0 call 形态")
CMPM1 = ("eax, -1", "eax, 0xffffffff")

i = ins(0x4729F6); ck(i and i.mnemonic == "cmp" and i.op_str in CMPM1, "004729C0 cmp -1")
j = ins(0x4729F9); ck(j and j.mnemonic == "je" and (j.operands[0].imm & 0xFFFFFFFF) == 0x472A28, "004729C0 je 目标")
# 全局容器静态初始化 + 类名 + Find
needle = struct.pack("<I", 0x89E0F0)
p = TEXT_DATA.find(b"\xc7\x05" + needle)
ck(p >= 0, "0x89E0F0 找不到静态初始化点")
gvt = struct.unpack_from("<I", TEXT_DATA, p + 6)[0]
ck(gvt == 0x7E4AD4, "0x89E0F0 初始化值 %s != 0x7E4AD4" % hex(gvt))
ci = parse_col(u32(gvt - 4)); td = parse_td(ci["td"])
ck(td["name"] == ".?AV?$DynamicVectorClass@PAVCaptureManagerClass@@@@", "容器 RTTI 名不符: %s" % td["name"])
find = u32(gvt + 0x10)
ck(find == 0x472FD0, "容器 slot4 %s != 0x472FD0" % hex(find))
fb = disasm(find, ATLAS.get(hx(find))["size"])
ck(any(x.mnemonic == "or" and x.op_str == "eax, 0xffffffff" for x in fb), "Find 无 or eax,-1")
ck(any(x.mnemonic.startswith("ret") and x.op_str == "4" for x in fb), "Find 非 ret 4")
# --- 004CA770 ---
i = ins(0x4CA7AA); ck(i and i.mnemonic == "call" and "[edx + 0x10]" in i.op_str, "004CA770 站点一")
i = ins(0x4CA7AD); ck(i and i.mnemonic == "cmp" and i.op_str in CMPM1, "004CA770 cmp -1 一")
i = ins(0x4CA803); ck(i and i.mnemonic == "call" and "[edx + 0x10]" in i.op_str, "004CA770 站点二")
i = ins(0x4CA806); ck(i and i.mnemonic == "cmp" and i.op_str in CMPM1, "004CA770 cmp -1 二")
for g, exp_vt, exp_find, exp_name in (
        (0xA83E30, 0x7E9FA4, 0x4EC2D0, ".?AV?$DynamicVectorClass@PAVFactoryClass@@@@"),
        (0xB0F720, 0x7E91EC, 0x4E0550, ".?AV?$DynamicVectorClass@PAVAbstractClass@@@@")):
    p = TEXT_DATA.find(b"\xc7\x05" + struct.pack("<I", g))
    ck(p >= 0, "%08X 找不到静态初始化点" % g)
    gv = struct.unpack_from("<I", TEXT_DATA, p + 6)[0]
    ck(gv == exp_vt, "%08X 初始化值 %s != %s" % (g, hex(gv), hex(exp_vt)))
    ci = parse_col(u32(gv - 4)); td = parse_td(ci["td"])
    ck(td["name"] == exp_name, "%08X 容器 RTTI 名不符: %s" % (g, td["name"]))
    f = u32(gv + 0x10)
    ck(f == exp_find, "%08X 容器 slot4 %s != %s" % (g, hex(f), hex(exp_find)))
    fb = disasm(f, ATLAS.get(hx(f))["size"])
    ck(any(x.mnemonic == "or" and x.op_str == "eax, 0xffffffff" for x in fb), "%s Find 无 or eax,-1" % hex(f))
print("   done")

print("\n== 4) 产物一致性 ==")
for s in summ:
    p = os.path.join(ROOT, "EVIDENCE", "ROW_%s.txt" % s["entry"])
    ck(os.path.exists(p), "缺证据文件 %s" % p)
    if os.path.exists(p):
        t = open(p, encoding="utf-8").read()
        ck(s["entry"] in t, "%s 证据文件未含 entry" % s["entry"])
        for k in ("①", "②", "③", "④"):
            ck(k in t, "%s 证据缺 %s" % (s["entry"], k))

dl = list(csv.reader(open(os.path.join(ROOT, "delta.tsv"), encoding="utf-8"), delimiter="\t"))
ck(dl[0] == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"], "delta 表头")
proved = [s["entry"] for s in summ if s["ok"]]
ck([r[0] for r in dl[1:]] == proved, "delta entry 集与裁定不一致")
for r in dl[1:]:
    ck(len(r) == 6, "delta 行列数 != 6: %s" % r[0])
    ck(r[0] == r[0].upper() and not r[0].startswith("0X") and len(r[0]) == 8, "delta entry 格式: %s" % r[0])
    ck(r[4] == "[已证]", "delta grade: %s" % r[4])
    ck(r[1] == "S12", "delta subsystem: %s" % r[1])
    nm = [x["name"] for x in rows if x["entry"] == r[0]][0]
    ck(r[2] == nm, "delta name 非原样: %s vs %s" % (r[2], nm))
    ck(os.path.exists(r[5].replace("/", "\\")), "delta evidence_path 不存在: %s" % r[5])
    ck("EVIDENCE/ROW_%s.txt" % r[0] in r[5], "delta evidence_path 指向错文件: %s" % r[5])
ck(len(set(r[3] for r in dl[1:])) == len(dl) - 1, "delta reason 有重复")

br = list(csv.reader(open(os.path.join(ROOT, "base_rate.tsv"), encoding="utf-8"), delimiter="\t"))
ck(br[0] == ["batch", "rows_checked", "ring2_ok", "ring3b_ok", "ring4_ok", "all_four", "rate"], "base_rate 表头")
v = br[1]
ck(v[0] == "S12_B2" and int(v[1]) == len(rows), "base_rate 批名/行数")
ck(int(v[2]) == sum(1 for s in summ if s["r2"] == "PASS"), "base_rate ring2")
ck(int(v[3]) == sum(1 for s in summ if s["r3"] == "PASS"), "base_rate ring3b")
ck(int(v[4]) == sum(1 for s in summ if s["r4"] == "PASS"), "base_rate ring4")
ck(int(v[5]) == len(proved), "base_rate all_four")
ck(abs(float(v[6]) - len(proved) / len(rows)) < 1e-4, "base_rate rate")
print("   done")

print("\n==== 结果：%s（%d 项失败）====" % ("全绿" if not FAILS else "有失败", len(FAILS)))
for f in FAILS:
    print("  -", f)
