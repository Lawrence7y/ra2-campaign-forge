# -*- coding: utf-8 -*-
"""
scan_evidence.py — gamemd.exe 逐函数证据采集（只读二进制）
产出: evidence.json  { entry: {imports, callees, callers, vclasses, module} }
纪律:
  - mm[VA - 0x400000] 索引
  - .data raw 字节只到 0x0087E000 (VA 0x812000 + RawSize 0x6C000)
  - 代码指针判据: .text = 0x00401000..0x007E038D (VA inclusive of end-1)
"""
import json, time, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_CALL, CS_GRP_JUMP

BASE = 0x400000
ATLAS_DIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas"
OUT_DIR   = ATLAS_DIR + r"\glm_seg"
EXE       = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D
DATA_RAW_END_VA  = 0x0087E000   # .data 文件字节上限(BSS 之后)

t0 = time.time()
pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories(directories=[
    pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
mm = pe.get_memory_mapped_image()

# ---- IAT 映射 ----
iat = {}          # slot VA -> "dll!api"
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll = e.dll.decode()
    for imp in e.imports:
        name = imp.name.decode() if imp.name else ("ord%d" % imp.ordinal)
        iat[imp.address] = dll + "!" + name
iat_lo, iat_hi = min(iat), max(iat)
print("IAT slots: %d  range %08X..%08X" % (len(iat), iat_lo, iat_hi))

# ---- 函数表 ----
funcs = []        # (entry_int, size, ...)
fset = set()
with open(ATLAS_DIR + r"\function_atlas.tsv", encoding="utf-8") as f:
    hdr = f.readline()
    for line in f:
        c = line.rstrip("\n").split("\t")
        if len(c) < 8:
            continue
        entry = int(c[0], 16)
        funcs.append({"entry": entry, "size": int(c[1]), "n_instr": int(c[2]),
                      "n_callers": int(c[3]), "n_callees": int(c[4]),
                      "is_fnptr": int(c[5]), "first_import": c[6],
                      "n_strings": int(c[7]),
                      "strings": c[8] if len(c) > 8 else ""})
        fset.add(entry)
funcs.sort(key=lambda d: d["entry"])
print("functions: %d" % len(funcs))

# ---- module attribution ----
mod = {}
with open(ATLAS_DIR + r"\module_attribution.tsv", encoding="utf-8") as f:
    next(f)
    for line in f:
        c = line.rstrip("\n").split("\t")
        if len(c) >= 4 and c[0].startswith("004"):
            mod[int(c[0], 16)] = c[3].replace("D:\\ra2mdpost\\", "")
print("module-attributed: %d" % len(mod))

# ---- vtable 槽重建: vt 地址 -> 连续 .text 指针 ----
vtj = json.load(open(ATLAS_DIR + r"\vtables_canonical.json", encoding="utf-8"))
fn_vclasses = {}    # entry -> set(class names)
vt_stats = []
for rec in vtj["vtables"]:
    vt = rec["vt"]; cls = rec["class"]; sec = rec.get("section", "")
    # 校验该 vt 区域是否有文件字节
    if sec == ".rdata" and not (0x007E1000 <= vt < 0x007E1000 + 0x30074):
        vt_stats.append((vt, "rdata-out")); continue
    if sec == ".data" and vt >= DATA_RAW_END_VA:
        vt_stats.append((vt, "bss")); continue
    idx = vt - BASE
    slots = []
    for i in range(1024):   # 上限保护
        off = idx + 4 * i
        if off + 4 > len(mm):
            break
        val = int.from_bytes(mm[off:off + 4], "little")
        if TEXT_LO <= val < TEXT_HI and val in fset:
            slots.append(val)
        else:
            break
    if slots:
        vt_stats.append((vt, "%d slots" % len(slots)))
        for s in slots:
            fn_vclasses.setdefault(s, set()).add(cls)
print("vtables scanned: %d, bad: %s" % (len(vtj["vtables"]),
      sum(1 for _, r in vt_stats if "slots" not in r)))
print("functions in vtables: %d" % len(fn_vclasses))

# ---- capstone 全量扫描 ----
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True          # 纪律 2
md.detail = True

ev = {}
n_imp_fn = n_edge = 0
for i, fn in enumerate(funcs):
    va, size = fn["entry"], fn["size"]
    start = va - BASE
    data = mm[start:start + size]
    imports, callees = set(), set()
    try:
        for ins in md.disasm(data, va):
            grp = ins.groups
            for op in ins.operands:
                if op.type == 3 and iat_lo <= op.mem.disp <= iat_hi:   # CS_OP_MEM
                    if op.mem.disp in iat:
                        imports.add(iat[op.mem.disp])
                if op.type == 2:                                       # CS_OP_IMM
                    t = op.imm & 0xFFFFFFFF
                    if ins.mnemonic == "call" and (CS_GRP_CALL in grp) and t in fset:
                        callees.add(t)
                    elif ins.mnemonic == "jmp" and (CS_GRP_JUMP in grp) and t in fset:
                        callees.add(t)   # 尾调用也算边
    except Exception as ex:
        print("disasm err @%08X: %s" % (va, ex))
    if imports: n_imp_fn += 1
    n_edge += len(callees)
    d = {"imports": sorted(imports), "callees": sorted(callees)}
    if va in mod: d["module"] = mod[va]
    if va in fn_vclasses: d["vclasses"] = sorted(fn_vclasses[va])
    ev[va] = d
    if i % 1000 == 0:
        print("  %d/%d  %.1fs" % (i, len(funcs), time.time() - t0), flush=True)

print("functions w/ imports: %d ; static edges: %d ; %.1fs"
      % (n_imp_fn, n_edge, time.time() - t0))

json.dump(ev, open(OUT_DIR + r"\evidence.json", "w"), indent=0)
print("saved evidence.json")
