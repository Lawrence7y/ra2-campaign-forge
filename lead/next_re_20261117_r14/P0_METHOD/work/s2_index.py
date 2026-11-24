"""S2 · 全 .text 线性反汇编索引（capstone 5.0.7, skipdata=True）。

产出 work/index.pkl：
  insn_starts  : 全部指令起始 VA（升序，array 'i'）
  insn_sizes   : 对应长度（array 'B'）
  insn_kind    : 0=普通 1=E8 call rel32 2=E9 jmp rel32 3=jcc(7x/0F8x) 4=skipdata/undecodable
  call_targets : 指令边界上的 E8 rel32 目标（只收落在 .text 内的）
  jmp_targets  : 指令边界上的 E9 rel32 目标
  jcc_targets  : 指令边界上的 jcc 目标（仅作"体内标签"负向辅证，不是四通道之一）
报告口径（错源 ㉖）：必须给"覆盖 .text 的百分比"，且所有交付站点落在自报覆盖范围内。
"""
import json
import os
import pickle
import sys
from array import array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import EVIDENCE, HERE, Image, new_md

img = Image()
md = new_md()

code = img.read(img.text_start, img.text["raw_size"])
assert code is not None
start = img.text_start
limit = img.text_end

starts, sizes, kinds = array("i"), array("B"), array("B")
call_t, jmp_t, jcc_t = set(), set(), set()
n_data = 0
n_insn = 0
gaps = []
cursor = start
max_end = start

for insn in md.disasm(code, start):
    if insn.address >= limit:
        break
    if insn.address != cursor:
        gaps.append((hex(cursor), hex(insn.address)))
        cursor = insn.address
    st = insn.address
    sz = insn.size
    kind = 0
    if insn.id == 0:  # skipdata 伪指令
        n_data += 1
        kind = 4
    else:
        n_insn += 1
        mn = insn.mnemonic
        ops = insn.operands
        if mn == "call" and len(ops) == 1 and ops[0].type == 2 and sz == 5:  # X86_OP_IMM
            kind = 1
            t = ops[0].imm & 0xFFFFFFFF
            if img.in_text(t):
                call_t.add(t)
        elif mn == "jmp" and len(ops) == 1 and ops[0].type == 2 and sz == 5:
            kind = 2
            t = ops[0].imm & 0xFFFFFFFF
            if img.in_text(t):
                jmp_t.add(t)
        elif mn.startswith("j") and mn != "jmp" and len(ops) == 1 and ops[0].type == 2:
            kind = 3
            t = ops[0].imm & 0xFFFFFFFF
            if img.in_text(t):
                jcc_t.add(t)
    starts.append(st)
    sizes.append(sz if sz < 256 else 0)
    kinds.append(kind)
    cursor = st + sz
    max_end = cursor

text_bytes = img.text_end - img.text_start
decoded = max_end - start
cov_pct = 100.0 * decoded / text_bytes

stats = dict(
    text_start=hex(start),
    text_end=hex(limit),
    text_bytes=text_bytes,
    raw_bytes_used=len(code),
    decoded_bytes=decoded,
    covered_pct_of_text=round(cov_pct, 4),
    max_decoded_addr=hex(max_end),
    instructions=n_insn,
    skipdata_pseudo=n_data,
    jumps_in_stream=len(gaps),
    call_rel32_sites=sum(1 for k in kinds if k == 1),
    jmp_rel32_sites=sum(1 for k in kinds if k == 2),
    jcc_sites=sum(1 for k in kinds if k == 3),
    distinct_call_targets_in_text=len(call_t),
    distinct_jmp_targets_in_text=len(jmp_t),
    distinct_jcc_targets_in_text=len(jcc_t),
    all_sites_within_coverage=(max(t for t in jmp_t) < max_end and max(t for t in call_t) < max_end),
    max_site_addr=hex(max(max(jmp_t), max(call_t))),
)
with open(os.path.join(HERE, "index.pkl"), "wb") as f:
    pickle.dump(dict(starts=starts, sizes=sizes, kinds=kinds,
                     call_targets=call_t, jmp_targets=jmp_t, jcc_targets=jcc_t), f)
with open(os.path.join(EVIDENCE, "s2_disasm.json"), "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)
print(json.dumps(stats, ensure_ascii=False, indent=2))
