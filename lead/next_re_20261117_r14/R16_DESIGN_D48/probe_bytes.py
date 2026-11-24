"""探针：确认 0x7C978A（atexit 注册）、活表/死表的字节形态，以及 vtable 安装点扫描规模。
只读。输出到 stdout。"""
import sys, collections
sys.dont_write_bytecode = True
import pefile, capstone
from capstone import x86 as X

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs.append((nm, BASE + s.VirtualAddress, max(s.Misc_VirtualSize, s.SizeOfRawData), s.get_data()))
buf = bytearray(max(va + n for _, va, n, _ in secs) - BASE + 16)
for nm, va, n, d in secs:
    buf[va - BASE:va - BASE + len(d)] = d

def u32(va):
    o = va - BASE
    return int.from_bytes(buf[o:o + 4], 'little') if 0 <= o <= len(buf) - 4 else None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

text = [s for s in secs if s[0] == '.text'][0]
code = text[3]

# 1) 0x7C978A 附近
print('=== around 0x7C978A ===')
for insn in md.disasm(code[0x7C9760 - TEXT_LO:0x7C97C0 - TEXT_LO], 0x7C9760):
    print('  %08X  %-28s %s %s' % (insn.address, insn.bytes.hex(), insn.mnemonic, insn.op_str))

# 2) 谁 call 0x7C978A，前面 push 了什么
cnt_call = 0
pushed = collections.Counter()
prev = []
for insn in md.disasm(code, TEXT_LO):
    if insn.id == 0:
        prev = []
        continue
    if insn.mnemonic == 'call' and insn.operands and insn.operands[0].type == X.X86_OP_IMM:
        tgt = insn.operands[0].imm & 0xFFFFFFFF
        if tgt == 0x7C978A:
            cnt_call += 1
            # 最近的 push imm32
            got = None
            for p in reversed(prev):
                if p.mnemonic == 'push' and p.operands and p.operands[0].type == X.X86_OP_IMM:
                    got = p.operands[0].imm & 0xFFFFFFFF
                    break
            pushed[got] += 1
    prev.append(insn)
    if len(prev) > 6:
        prev.pop(0)
print('\n=== call 0x7C978A ===')
print('count', cnt_call, 'distinct pushed imm', len(pushed))
print('top', pushed.most_common(5))
intext = [k for k in pushed if k is not None and TEXT_LO <= k < TEXT_HI]
print('pushed targets inside .text:', len(intext))

# 3) mov [mem], imm32 == vt 的规模
cand = 0
imm_targets = collections.Counter()
for insn in md.disasm(code, TEXT_LO):
    if insn.id == 0:
        continue
    if insn.mnemonic == 'mov' and len(insn.operands) == 2:
        a, b = insn.operands
        if a.type == X.X86_OP_MEM and b.type == X.X86_OP_IMM:
            imm = b.imm & 0xFFFFFFFF
            if 0x7E1000 <= imm < 0x812000:      # .rdata
                cand += 1
                imm_targets[imm] += 1
print('\n=== mov [mem], imm32 pointing into .rdata ===')
print('sites', cand, 'distinct imm', len(imm_targets))

# 4) 该 imm 是否正好是 vt（vt-4 处是 COL 指针且 COL.sig==0, TD 名 .?A）
def col_of(vt):
    col = u32(vt - 4)
    if not col or not (BASE <= col < BASE + 0x800000):
        return None
    if u32(col) != 0:
        return None
    td = u32(col + 12)
    if not td or not (BASE <= td < BASE + 0x800000):
        return None
    o = td + 8 - BASE
    e = buf.find(b'\x00', o, o + 256)
    if e < 0:
        return None
    try:
        nm = bytes(buf[o:e]).decode('latin-1')
    except Exception:
        return None
    return nm if nm.startswith('.?A') else None

ok = [imm for imm in imm_targets if col_of(imm)]
print('of those distinct imm, RTTI-vt:', len(ok))
