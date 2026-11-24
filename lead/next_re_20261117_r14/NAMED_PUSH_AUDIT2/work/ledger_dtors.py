"""量化：台账现有 [已证] 行里有多少是「标量删除析构器」形态、其中多少带 Find/-1 哨兵分支。
用于回答「析构语义此前是否被当作 ③b 入账过」。"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C, q

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
proved = []
with open(COV, encoding="utf-8") as f:
    next(f)
    for ln in f:
        p = ln.rstrip("\n").split("\t")
        if len(p) < 5:
            continue
        if p[4].strip() != "[已证]":
            continue
        try:
            e = int(p[0], 16)
        except ValueError:
            continue
        proved.append((e, p[1], p[2]))

print("total [已证] rows:", len(proved))

dtor_sig = []
find_sig = []
for e, sub, nm in proved:
    fa = C.fn_at(e)
    if not fa or fa[1] < 8 or fa[1] > 0x2000:
        continue
    ins = C.disasm(e, 10 ** 6, nbytes=fa[1])
    has_test_flag = False
    has_free = False
    has_find = False
    has_cmpm1 = False
    prev = []
    for i in ins:
        if i.mnemonic == "test" and "byte ptr [esp" in i.op_str and i.op_str.endswith(", 1"):
            has_test_flag = True
        if i.mnemonic == "call":
            t = q.callee_at(i.address)
            if t == 0x7C8B3D:
                has_free = True
        if i.mnemonic == "cmp" and i.op_str.replace(" ", "") == "eax,-1":
            has_cmpm1 = True
        if i.mnemonic == "call" and "[e" in i.op_str and "+0x10]" in i.op_str:
            has_find = True
    if has_test_flag and has_free:
        dtor_sig.append((e, sub, nm, has_find, has_cmpm1))
        if has_find and has_cmpm1:
            find_sig.append((e, sub, nm))

print("其中形似「标量删除析构器」(test byte[esp..],1 + call 0x7C8B3D):", len(dtor_sig))
print("其中再带 call [reg+0x10] + cmp eax,-1 容器哨兵分支:", len(find_sig))
for e, sub, nm in find_sig[:25]:
    print("   %08X %s %s" % (e, sub, nm))
