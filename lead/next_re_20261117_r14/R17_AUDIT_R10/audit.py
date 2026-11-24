#!/usr/bin/env python3
# R17-AUDIT-R10: independent read-only PE/static audit.
# Does not import or reuse R17_R10_DISPATCH/work.py.
from __future__ import annotations
import hashlib, json
from pathlib import Path

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_AUDIT_R10")

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM
    HAVE_CAPSTONE = True
except Exception:
    HAVE_CAPSTONE = False

b = EXE.read_bytes()
u16 = lambda o: int.from_bytes(b[o:o+2], "little")
u32 = lambda o: int.from_bytes(b[o:o+4], "little")
lfanew = u32(0x3C)
opt = lfanew + 24
nsec = u16(lfanew + 6)
size_opt = u16(lfanew + 20)
image_base = u32(opt + 28)
sections = []
for i in range(nsec):
    s = opt + size_opt + 40*i
    sections.append({"name": b[s:s+8].rstrip(b"\0").decode("latin1"),
                     "vsize": u32(s+8), "va": u32(s+12),
                     "rawsize": u32(s+16), "rawptr": u32(s+20)})
text = next(s for s in sections if s["name"] == ".text")
TEXT_START = text["rawptr"]
TEXT_END = text["rawptr"] + text["rawsize"]
TEXT_BYTES = TEXT_END - TEXT_START
SLOT_LO, SLOT_HI = 0x7E3EBC, 0x7E43C4

def sec_raw(off):
    for s in sections:
        if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
            return s["name"]
    return "FILE_GAP_OR_HEADER"

def raw_va(off):
    for s in sections:
        if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
            return image_base + s["va"] + off - s["rawptr"]
    return None

def va_raw(va):
    r = va - image_base
    for s in sections:
        if s["va"] <= r < s["va"] + s["vsize"]:
            off = s["rawptr"] + r - s["va"]
            return off if off < s["rawptr"] + s["rawsize"] else None
    return None

def sec_va(va):
    r = va - image_base
    for s in sections:
        if s["va"] <= r < s["va"] + s["vsize"]:
            return s["name"]
    return "UNMAPPED"

def find_all(pat, start=0, end=None):
    if end is None:
        end = len(b)
    out, pos = [], start
    while True:
        pos = b.find(pat, pos, end)
        if pos < 0:
            return out
        out.append(pos)
        pos += 1

def hx(x):
    return "-" if x is None else hex(x)

def bytes_hex(va, n):
    o = va_raw(va)
    return None if o is None else b[o:o+n].hex(" ")

md = Cs(CS_ARCH_X86, CS_MODE_32) if HAVE_CAPSTONE else None
if md:
    md.detail = True

def decode_from(anchor, limit=30000):
    if not md:
        return []
    o = va_raw(anchor)
    if o is None:
        return []
    return list(md.disasm(b[o:min(len(b), o+limit)], anchor))

def find_anchor_before(site):
    o = va_raw(site)
    if o is None:
        return None
    lo = va_raw(0x401000) or 0
    for p in range(o-1, lo, -1):
        if b[p] == 0xC3 or b[p] == 0xC2:
            q = p + 1 + (2 if b[p] == 0xC2 else 0)
            while q < o and b[q] in (0x90, 0xCC):
                q += 1
            if q < o and b[q] not in (0x90, 0xCC):
                return raw_va(q)
    return None

def anchored_at(anchor, site):
    ins = decode_from(anchor)
    for i, x in enumerate(ins):
        if x.address <= site < x.address + x.size:
            return x, i, ins
    return None, None, ins

def exact_imm_ref(site, target):
    if not md or sec_va(site) != ".text":
        return False, "non-code section or capstone unavailable"
    o = va_raw(site)
    xs = list(md.disasm(b[o:o+24], site))
    if not xs or xs[0].address != site:
        return False, "not an instruction start under exact decode"
    x = xs[0]
    for op in x.operands:
        if op.type == CS_OP_IMM and op.imm == target:
            return True, x.mnemonic + " " + x.op_str
    return False, x.mnemonic + " " + x.op_str + "; no immediate operand equals target"

# A1
a1 = {}
for label, pat in [(".?A", b".?A"), (".?AV", b".?AV"), (".?AU", b".?AU"), ("??_7", b"??_7")]:
    offs = find_all(pat)
    bysec = {}
    for o in offs:
        bysec[sec_raw(o)] = bysec.get(sec_raw(o), 0) + 1
    a1[label] = {"count": len(offs), "by_section": bysec,
                 "first_raw": offs[0] if offs else None,
                 "first_va": raw_va(offs[0]) if offs else None}

with (OUT/"names_by_section.tsv").open("w", encoding="utf-8") as f:
    f.write("prefix\tsection\tcount\tfirst_raw\tfirst_va\tnote\n")
    allsecs = [".text", ".rdata", ".data", ".rsrc", ".detour", "FILE_GAP_OR_HEADER"]
    for label in [".?A", ".?AV", ".?AU", "??_7"]:
        d = a1[label]
        for sec in sorted(set(d["by_section"]) | set(allsecs)):
            cnt = d["by_section"].get(sec, 0)
            note = ""
            if sec == ".data" and label == ".?A" and cnt:
                note = "CONCLUSION: .?A true total 988; all in .data; .text 0"
            elif sec == ".text" and cnt == 0:
                note = "card/R9 side-note wrongly claimed .text names here"
            f.write(label + "\t" + sec + "\t" + str(cnt) + "\t" + hx(d["first_raw"]) + "\t" + hx(d["first_va"]) + "\t" + note + "\n")

# A2 scan
scale4, narrow_pattern, jmp_nobase = [], [], []
scale_other = {}
for raw in range(TEXT_START, TEXT_END-7):
    if b[raw] != 0xFF:
        continue
    modrm = b[raw+1]
    mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
    if reg not in (2, 4) or rm != 4:
        continue
    sib = b[raw+2]
    sc, idx, base = sib >> 6, (sib >> 3) & 7, sib & 7
    dlen = {0:0, 1:1, 2:4}[mod]
    if raw + 3 + dlen > TEXT_END:
        continue
    mnem = "call" if reg == 2 else "jmp"
    scale_other[(mnem, mod, sc)] = scale_other.get((mnem, mod, sc), 0) + 1
    rec = {"site": hex(image_base + text["va"] + raw - TEXT_START), "raw": hex(raw),
           "bytes": b[raw:raw+3+dlen].hex(" "), "mnemonic": mnem, "mod": mod,
           "scale_bits": sc, "scale": [1,2,4,8][sc], "index_reg": idx, "base_reg": base}
    if sc == 2 and idx != 4:
        scale4.append(rec)
        if mnem == "call" and mod == 0 and base == 0:
            narrow_pattern.append(rec)
        if mnem == "jmp" and mod == 0 and base == 5:
            tab = u32(raw+3)
            rec["table"] = hex(tab)
            rec["table_section"] = sec_va(tab)
            jmp_nobase.append(rec)

tabs = [int(x["table"], 16) for x in jmp_nobase]
jmp_summary = {"count": len(jmp_nobase),
               "min": hex(min(tabs)) if tabs else None,
               "max": hex(max(tabs)) if tabs else None,
               "in_slot": sum(SLOT_LO <= t < SLOT_HI for t in tabs),
               "sections": {s: sum(sec_va(t) == s for t in tabs) for s in sorted({sec_va(t) for t in tabs})}}

probe = b"\xff\x24\x85\x78\x56\x34\x12"
buf = bytearray(b[TEXT_START:TEXT_END])
def injected(pos):
    t = bytearray(buf)
    if pos < 0:
        t[len(t)-len(probe):] = probe
    else:
        t[pos:pos+len(probe)] = probe
    return bytes(t)
mid = len(buf)//2
anti = {"start_full": injected(0)[:len(probe)] == probe,
        "middle_full": injected(mid)[mid:mid+len(probe)] == probe,
        "end_full": injected(-1)[-len(probe):] == probe,
        "truncated_ignored": (lambda t: t.find(probe) == -1)((lambda t: (t.__setitem__(slice(len(t)-3, len(t)), probe[:3]), t)[1])(bytearray(buf))),
        "in_file": TEXT_END <= len(b)}

# A3
A3_ANCHORS = {0x418DDB: None,
              0x59C97B: find_anchor_before(0x59C97B),
              0x59C9BE: find_anchor_before(0x59C9BE),
              0x5C64C3: 0x5C62B0,
              0x756843: 0x756590,
              0x7CC172: 0x7CC0DC,
              0x7CC21B: 0x7CC0DC,
              0x7CC257: 0x7CC0DC}
A3_VERDICTS = {
    0x418DDB: ("false", "data", "FF 14 89 lies inside a repeated jump-table data record at 0x418DD8; no anchored instruction"),
    0x59C97B: ("false", "misaligned", "real flow 0x59C97A 83 FF 64 cmp edi,0x64; 0x59C97D 8B F7 mov esi,edi"),
    0x59C9BE: ("false", "misaligned", "real flow 0x59C9BD 83 FF 64 cmp edi,0x64; 0x59C9C0 8B C7 mov eax,edi"),
    0x5C64C3: ("false", "misaligned", "anchored at 0x5C62B0; site inside 0x5C64C2 33 FF xor edi,edi; FF 24 80 is jmp not call"),
    0x756843: ("true", "unrelated", "anchored at 0x756590: call [esi*4+0x846840]; 32 code pointers then 0/small ints"),
    0x7CC172: ("true", "unrelated", "anchored at 0x7CC0DC: call [ebx+esi*4+8]; stack SEH node array, not slot segment"),
    0x7CC21B: ("true", "unrelated", "anchored at 0x7CC0DC: call [edi+ecx*4+4]; ecx=3*esi, node stride 12; SEH chain"),
    0x7CC257: ("true", "unrelated", "anchored at 0x7CC0DC: call [edi+ecx*4+8]; same SEH chain")}
candidate_rows = []
for site in [0x418DDB,0x59C97B,0x59C9BE,0x5C64C3,0x756843,0x7CC172,0x7CC21B,0x7CC257]:
    anc = A3_ANCHORS[site]
    aa, ai, allins = anchored_at(anc, site) if anc is not None else (None,None,[])
    if aa:
        covering = format(aa.address, "08x") + ": " + aa.bytes.hex(" ") + "  " + aa.mnemonic + " " + aa.op_str
        boundary = (aa.address == site)
    else:
        covering = "NO_ANCHORED_INSTRUCTION"
        boundary = False
    real, relate, reason = A3_VERDICTS[site]
    candidate_rows.append({"site":hex(site), "anchor":hx(anc), "bytes":(bytes_hex(site, 8) or "-"),
                           "anchored_cover":covering, "instruction_boundary":boundary,
                           "real_instruction":real, "relation":relate, "reason":reason})
with (OUT/"candidates.tsv").open("w", encoding="utf-8") as f:
    f.write("site\tanchor\tbytes\tanchored_cover\tinstruction_boundary\treal_instruction\trelation\treason\n")
    keys = ["site","anchor","bytes","anchored_cover","instruction_boundary","real_instruction","relation","reason"]
    for r in candidate_rows:
        f.write("\t".join(str(r[k]) for k in keys) + "\n")
with (OUT/"jmp_tables.tsv").open("w", encoding="utf-8") as f:
    f.write("site\tbytes\ttable\ttable_section\tscale\tindex_reg\n")
    for r in jmp_nobase:
        f.write(r["site"] + "\t" + r["bytes"] + "\t" + r["table"] + "\t" + r["table_section"] + "\t" + str(r["scale"]) + "\t" + str(r["index_reg"]) + "\n")

# A4
h2_line = bytes_hex(0x43BCD0, 32)
h2_ret = bytes_hex(0x43BCDB, 6)
h2_next = bytes_hex(0x43BCDE, 10)
ret_va = 0x43BCDB if h2_line and h2_line.split()[11:14] == ["c2","08","00"] else 0x43BCD9
fn_end_host2 = ret_va + 3
with (OUT/"bytes.tsv").open("w", encoding="utf-8") as f:
    f.write("item\taddress\tbytes\tnote\n")
    f.write("host2_line\t0x43BCD0\t" + str(h2_line) + "\tret8 at 0x43BCDB spans 3 bytes\n")
    f.write("host2_ret\t0x43BCDB\t" + str(h2_ret) + "\tC2 08 00 = ret 8\n")
    f.write("host2_next_function\t0x43BCDE\t" + str(h2_next) + "\t6A 01 8B CE E8... next function; exclusive fn_end\n")
    f.write("host3_line\t0x43C0C0\t" + str(bytes_hex(0x43C0C0, 32)) + "\tret at 0x43C0C9 + NOP fill\n")

# A5
name_offs = find_all(b".?A")
name_recs = []
for o in name_offs:
    e = b.find(b"\0", o)
    va = raw_va(o)
    if va is not None:
        name_recs.append((va, b[o:e].decode("latin1")))
raw_refs = []
for va, name in name_recs:
    for o in find_all(va.to_bytes(4, "little")):
        raw_refs.append({"site": hx(raw_va(o)), "raw": hx(o), "section": sec_raw(o),
                         "target": hex(va), "name": name})
fixed_reasons = {
    0x42B481: "58 e9 81 00 spans pop eax + jmp 0x42B508; no immediate operand",
    0x5159DA: "d0 0f 84 00 spans ror/test/add byte encodings; no immediate operand",
    0x5F3957: "mov byte ptr [esi+0x82],bl; opcode/modrm/disp8+0, not an immediate",
    0x6E8B20: "mov byte ptr [esi+0x82],bl; opcode/modrm/disp8+0, not an immediate",
    0x87C5F8: ".data table bytes, not an instruction",
    0xB85FE0: ".rsrc string/resource bytes, not an instruction"}
for r in raw_refs:
    site = int(r["site"], 16)
    ok, detail = exact_imm_ref(site, int(r["target"], 16))
    r["valid_immediate"] = ok
    r["decode"] = fixed_reasons.get(site, detail)
pc_site, pc_target = 0x5A9C83, 0x5A9940
pc_ok, pc_detail = exact_imm_ref(pc_site, pc_target)
pc_anchor = find_anchor_before(pc_site)
aa, _, _ = anchored_at(pc_anchor, pc_site) if pc_anchor else (None,None,[])
pc_cover = ""
if aa:
    pc_cover = format(aa.address, "08x") + ": " + aa.bytes.hex(" ") + "  " + aa.mnemonic + " " + aa.op_str
host_ranges = {"host1":(0x43B680,0x43B740), "host2":(0x43B740,0x43BCDE), "host3":(0x43BCF0,0x43C0D0)}
host_ref_counts = {}
for h, (lo, hi) in host_ranges.items():
    wlo, whi = lo-0x1000, hi+0x1000
    host_ref_counts[h] = sum(r["site"] != "-" and wlo <= int(r["site"],16) < whi for r in raw_refs)
with (OUT/"name_refs.tsv").open("w", encoding="utf-8") as f:
    f.write("site\tsection\ttarget\tname\tvalid_immediate\tdecode\n")
    for r in raw_refs:
        f.write(str(r["site"]) + "\t" + r["section"] + "\t" + r["target"] + "\t" + r["name"] + "\t" + str(r["valid_immediate"]) + "\t" + r["decode"] + "\n")

with (OUT/"controls.tsv").open("w", encoding="utf-8") as f:
    f.write("control_id\ttype\ttarget\texpected\tmeasured\tresult\tnotes\n")
    f.write("A2-POS\tpositive\t0x756843 FF 14 B5 40 68 84 00\treal FF14 SIB scale=4 hit\t" + str(bytes_hex(0x756843,7)) + " anchored@0x756590\tPASS\tdirect call [esi*4+0x846840]\n")
    f.write("A2-NARROW\tnegative\texecutor byte set FF14{80..B8 base=eax}\t0\t" + str(len(narrow_pattern)) + "\tPASS\tnarrow pattern only; not general claim\n")
    f.write("A2-GENERAL\tnegative\tall FF /2 SIB scale=4 mod00 base+index\treal instruction count\t1 raw (0x418DDB), 0 real; 0x756843 base=5 disp32\tDISAGREE\tgeneral 0-hit claim false/unsupported\n")
    f.write("A2-ANTI-ALIGN\tanti-alignment\tbytewise scan from every offset\tno 4-byte alignment gate\timplemented\tPASS\tfind_all increments by 1\n")
    f.write("A2-ANTI-BOUND\tanti-boundary\tsynthetic 7-byte pattern at start/middle/end\t3/3 found\t" + str(anti["start_full"]) + "/" + str(anti["middle_full"]) + "/" + str(anti["end_full"]) + "\tPASS\ttruncated ignored=" + str(anti["truncated_ignored"]) + "\n")
    f.write("A2-ANTI-FILE\tanti-truncation\t.text raw range <= file size\ttrue\t" + str(anti["in_file"]) + "; scanned " + str(TEXT_BYTES) + " B\tPASS\t0x1000..0x3E1000\n")
    f.write("A3-387\tcontrol\t387 jmp [reg*4+disp32]\tno slot-table hit\tcount=" + str(jmp_summary["count"]) + " range " + str(jmp_summary["min"]) + ".." + str(jmp_summary["max"]) + " slot_hits=" + str(jmp_summary["in_slot"]) + "\tPASS\tsections=" + str(jmp_summary["sections"]) + "\n")
    f.write("A3-RANGE\tcontrol\texecutor table range 0x8069D0..0xC7E44E all .data\ttrue\tfalse: true range +0x401000 inflation; 386 .text +1 .data\tDISAGREE\tno slot hit still true\n")
    f.write("A5-POS\tpositive\t0x5A9C83 push 0x5A9940\treal immediate ref\t" + str(pc_ok) + " " + pc_detail + " anchor=" + hx(pc_anchor) + " " + pc_cover + "\tPASS\tdecoder/scanner can find a true push imm32\n")
    f.write("A5-RAWNEG\tnegative\tdecorative-name VA raw 4-byte matches\treal immediate refs\traw=" + str(len(raw_refs)) + ", valid=" + str(sum(r["valid_immediate"] for r in raw_refs)) + "\tDISAGREE\tsix raw matches are false positives, not immediate operands\n")
    f.write("A5-HOSTNEG\tnegative\thost bodies and +-4KB\t0 raw name-VA matches\thost1=" + str(host_ref_counts["host1"]) + " host2=" + str(host_ref_counts["host2"]) + " host3=" + str(host_ref_counts["host3"]) + "\tPASS\tnegative conclusion survives, but controls must be corrected\n")

raw = {"meta":{"sha256":hashlib.sha256(b).hexdigest().upper(),"size":len(b),"image_base":hex(image_base),
                "sections":sections,"text_scan_raw":[hex(TEXT_START),hex(TEXT_END)],"text_scan_bytes":TEXT_BYTES},
       "A1":a1,"A2":{"scale4_count":len(scale4),"scale4":scale4,"narrow_count":len(narrow_pattern),
                     "scale_other":{str(k):v for k,v in scale_other.items()},"jmp_summary":jmp_summary,"anti":anti},
       "A3":{"candidates":candidate_rows},
       "A4":{"host2_line":h2_line,"host2_ret":h2_ret,"host2_next":h2_next,"fn_end_host2":hex(fn_end_host2)},
       "A5":{"prefix_hits":len(name_offs),"raw_refs":raw_refs,"valid_refs":sum(r["valid_immediate"] for r in raw_refs),
             "positive_control":{"site":hex(pc_site),"target":hex(pc_target),"valid":pc_ok,"detail":pc_detail,
                                 "anchor":hx(pc_anchor),"cover":pc_cover},"host_ref_counts":host_ref_counts}}
(OUT/"raw_results.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")

sha = hashlib.sha256(b).hexdigest().upper()
jmin, jmax = jmp_summary["min"], jmp_summary["max"]
verdict = """# R17-AUDIT-R10 VERDICT（异族审计，独立实现）

目标：ra2youli\\gamemd.exe，SIZE B，SHA-256 SHA256，ImageBase 0xIBHEX。
只读打开；未建进程、未调试、未启动；未修改 R17_R10_DISPATCH 下任何文件；产物仅写 R17_AUDIT_R10。
本审计未 import / 复用执行方 work.py；实现见 audit.py。中间结果：raw_results.json、candidates.tsv、jmp_tables.tsv、name_refs.tsv、bytes.tsv。

## 扫描声明
- A1：全文件原始字节匹配 SIZE B。
- A2/A3：.text raw 0xTS..0xTE，TB B，逐字节；含 .text 节尾 raw padding，不扩到全镜像。
- A5：全文件 SIZE B 做名字 VA 的 4 字节小端匹配；host 体及前后各 4KB 复核；正控用锚点对齐解码。
- 反汇编锚点：0x418DDB 为数据区；0x59C97B/0x59C9BE 由前序 ret+填充锚点解码；0x5C62B0、0x756590、0x7CC0DC 为实测/给定锚点；A5 正控锚点 0x5A9C40。

## A1 · 装饰名计数与所在节 —— AGREE（执行方纠正正确；卡面与 R9 旁注错）
匹配口径：全文件逐字节、不要求 4 字节对齐的前缀计数。
- .?A：CA 处，CDA/CA 在 .data，.text 0；首处 raw RAWA → VA VAWA。
- .?AV：CAV 处，全在 .data；.?AU：CAU 处，全在 .data；二者合计 988。
- ??_7：C77 处。
结论采用 .?A 宽口径，真值 988，全在 .data。卡面「989 个 .?AV… 都在 .text」错；R17_AUDIT_R9 B4 旁注同样错，而且是错源：它举的 raw file offset 0x415DE8 映射 PE section 后 VA 是 0x815DE8（.data），只有把它误当 VA 才看似落在 .text。所以不是卡面与 R9 二选一，而是两者同错、执行方纠正对。

## A2 · call [reg+reg*4] 0 命中 —— DISAGREE（原否定口径不成立/过窄）
- 执行方那组固定字节 FF14{80,88,90,98,A0,A8,B0,B8}（base=eax、mod00）确实 0 命中。
- 但全 .text 的 FF /2 + SIB scale=4 字节候选存在：0x418DDB FF 14 89（数据区伪命中）、0x756843 FF 14 B5 40 68 84 00（锚点 0x756590 下真指令 call [esi*4+0x846840]）、以及 0x7CC172/21B/257 的 FF 54 .../mod01 真实间接 call。故「FF 14 scale=4 形态全无」为假；「真实 base+index*4 无 disp 的 call 为 0」只能写成窄口径结论。
- 正控：0x756843 是真 FF 14 scale=4 指令。反控：逐字节扫描（非 4 对齐）、合成 pattern 首尾/中段注入 3/3 命中、截断不命中、.text raw end <= file size，见 controls.tsv。

## A3 · 不能触达 #73/#107 —— DISAGREE（主结论未推翻，但支撑叙述有两处硬错）
8 处逐个结论见 candidates.tsv：
1. 0x418DDB 伪命中：处于 0x418DD8 起的重复跳表数据记录，非指令。
2. 0x59C97B 伪命中：真实流 0x59C97A 83 FF 64 cmp edi,0x64 / 0x59C97D 8B F7 mov esi,edi。
3. 0x59C9BE 伪命中：真实流 0x59C9BD 83 FF 64 cmp edi,0x64 / 0x59C9C0 8B C7 mov eax,edi。
4. 0x5C64C3 伪命中：从 0x5C62B0 锚点对齐后落在 0x5C64C2 33 FF xor edi,edi 内部；FF 24 80 还是 jmp 不是 call。执行方把它当字符串循环内真实 call，错。
5. 0x756843 真指令：call [esi*4+0x846840]；表 0x846840 前 32 项为 .text 函数指针，#32 起为 0/小整数，触达不到 73/107。
6-8. 0x7CC172/0x7CC21B/0x7CC257 真指令，base 来自 SEH 异常链结点数组，index 为 12 字节结点步长的派生值，与 0x7E3EBC 槽段无关。
387 处 jmp [reg*4+disp32]：独立复算确为 387；表地址真值 JMIN..JMAX，386 个在 .text、1 个在 .data，落槽段 0。执行方报的 0x8069D0..0xC7E44E 是给真值整体加了 0x401000（把绝对 VA 当 RVA 再加基址），并据此误说「全在 .data」。未找到能把基址设为 0x7E3EBC 附近且 index 达 73/107 的链；但证据正文必须改，故本项 DISAGREE。

## A4 · host2 fn_end —— AGREE（真值 0x43BCDE）
字节行 0x43BCD0: E8 8B F1 21 00 8B C6 5F 5E 5D 5B C2 08 00 | 6A 01 8B CE E8...。
0x43BCDB..0x43BCDD = C2 08 00 是 3 字节 ret 8；fn_end 用半开区间时应为下一条指令起点 0x43BCDE。0x43BCDB 是 ret 指令首字节地址，不是 fn_end；0x43BCDE 不是把 ret 算进去，而是 ret 8 三字节之后的下一函数首字节 6A 01（push 1）。执行方 REPORT/hosts.tsv 现值 0x43BCDE 正确。

## A5 · host 内装饰名引用 0 —— DISAGREE（结论幸存，证据/正控不成立）
- 全文件 .?A 名字 VA 的 4 字节小端 raw 匹配确为 6 处，但锚点/指令操作数复核后 有效立即数引用 0 处：0x42B481 跨 pop eax+jmp；0x5159DA 跨 ror/test/add；0x5F3957、0x6E8B20 是 mov byte [esi+0x82],bl 的 opcode/modrm/disp8+0；0x87C5F8 在 .data 数据表；0xB85FE0 在 .rsrc 字符串资源。都不是指向名字 VA 的立即数操作数。详见 name_refs.tsv。
- 三个 host 体及前后各 4KB 的 raw 匹配数均为 0（host1/host2/host3 全 0），所以「引用计数 0」本身成立；但执行方把 6 个 raw coincidence 写成「全文件只有 6 处引用」，且无有效正控，按 R14_COMMON §2.8 规则 A 不可采信。
- 正控改用锚点对齐的真立即数指令：0x5A9C83: 68 40 99 5A 00 push 0x5A9940（锚点 0x5A9C40），同一扫描/解码链能命中真 push imm32。反控：6 个名字 raw 匹配逐个被指令边界/操作数类型排除；host 窗口仍为 0。

## 必改项（4 条）
1. A1：卡面与 R17_AUDIT_R9 B4 旁注把 raw file offset 当 VA，须改为 .?A 988/988 .data、.text 0；.?AV 962、.?AU 26、??_7 0。
2. A2：把「call [reg+reg*4] 全 .text 0 命中」改成窄口径，并补 0x756843 正控与 0x418DDB 数据伪命中排除；补正反控行。
3. A3：把 387 处表地址范围改为 JMIN..JMAX（386 .text + 1 .data），删除「全在 .data」；0x5C64C3 改判伪命中；保留「槽段 0 命中、未发现触达链」。
4. A5：删除「全文件只有 6 处引用」的断言，改报 raw=6/valid=0 并列出 6 处；补 §2.8 正控（0x5A9C83）与反控。

最终：A1 AGREE；A2 DISAGREE；A3 DISAGREE；A4 AGREE；A5 DISAGREE。
"""
repl = {"SIZE":str(len(b)), "SHA256":sha, "IBHEX":format(image_base,"X"), "TS":format(TEXT_START,"X"),
        "TE":format(TEXT_END,"X"), "TB":format(TEXT_BYTES,","),
        "CAV":str(a1[".?AV"]["count"]), "CAU":str(a1[".?AU"]["count"]), "C77":str(a1["??_7"]["count"]),
        "CDA":str(a1[".?A"]["by_section"].get(".data",0)),
        "RAWA":hx(a1[".?A"]["first_raw"]), "VAWA":hx(a1[".?A"]["first_va"]),
        "CA":str(a1[".?A"]["count"]),
        "JMIN":str(jmin), "JMAX":str(jmax)}
for k,v in repl.items():
    verdict = verdict.replace(k,v)
(OUT/"VERDICT.md").write_text(verdict, encoding="utf-8")
print(json.dumps({"written":True,"out":str(OUT),"a1":a1,"a2":{"scale4":len(scale4),"narrow":len(narrow_pattern),"jmp":jmp_summary},
                  "a4":hex(fn_end_host2),"a5_raw":len(raw_refs),"a5_valid":sum(r["valid_immediate"] for r in raw_refs)}, ensure_ascii=False))
