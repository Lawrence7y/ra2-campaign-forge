# -*- coding: utf-8 -*-
"""r134d_arg3_and_indirect.py -- R134：把 else 臂可达性的边界钉死到它能被证的程度。

分两步，两步都只做字节事实：
  第一步（F 组）：15 个直接调用点的 arg3 是否全为 7。
      方法：disasm_lite 一次线性扫描（skipdata=True）建 addr -> (size, mnem, op) 表；
      从站点向后走，要求 addr+size == next_addr（严连续），遇控制转移或断开即停；
      收集这段尾巴里的 push；cdecl 右到左，最近的三个 push 里最早的那个是 arg3。
  第二步（G 组）：是否存在**间接**入路 —— 即 call/jmp 的目标来自寄存器或内存。
      若某个 call reg 的目标在静态上不可定，则「else 臂任意输入不可达」不能由本脚本关闭，
      必须如实降级为「在可静态定址的 15 个入路上不可达」。

内存纪律：全段扫描只用 disasm_lite（不建 detail 对象）；push 的解码只对站址附近
<= 96 字节窗口开 detail=True。
"""
import io, os, json, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

BIN = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUTP = '/home/t628/projects/ra2-campaign-forge/_r134/r134d_arg3_and_indirect.json'
ENTRIES = [0x6bedb0, 0x41c250]
SITES = [0x6bc364, 0x6bc3aa, 0x416bc2, 0x44e02c, 0x4db8cc, 0x4df85c, 0x51b064,
         0x521fc2, 0x5230dc, 0x65f092, 0x6cc999, 0x710213, 0x7354f2, 0x742699, 0x742a94]
res = []


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-58s %s' % ('PASS' if cond else 'FAIL', name, detail))


data = open(BIN, 'rb').read()
pe = struct.unpack_from('<I', data, 0x3c)[0]
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
base = struct.unpack_from('<I', data, pe + 24 + 28)[0]
secs = []
off = pe + 24 + optsz
for i in range(nsec):
    nm = data[off:off + 8].rstrip(b'\0').decode('latin1')
    vsize, vaddr, rawsz, rawptr = struct.unpack_from('<IIII', data, off + 8)
    secs.append((nm, base + vaddr, vsize, rawsz, rawptr))
    off += 40
text = [s for s in secs if s[0] == '.text'][0]
tnm, tva, tvsize, trawsz, trawptr = text
tblob = data[trawptr:trawptr + trawsz]
print('.text VA %#x vsize %#x raw %d' % (tva, tvsize, trawsz))

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
insn = {}
endmap = {}          # addr+size -> addr, so the backward walk is O(1) per step
n = 0
for a, sz, mn, op in md.disasm_lite(tblob, tva):
    insn[a] = (sz, mn, op)
    endmap[a + sz] = a
    n += 1
print('linear sweep %d instructions, last VA %#x' % (n, max(insn)))
chk('F0a sweep covered the tail of .text (last insn > 0x7e0000)',
    max(insn) > 0x7e0000, 'last=%#x' % max(insn))
chk('F0b sweep did not silently stop early (count > 1_000_000)', n > 1000000, 'n=%d' % n)

CTRL = ('ret', 'jmp', 'call', 'jz', 'je', 'jnz', 'jne', 'jl', 'jle', 'jg', 'jge',
        'jb', 'jbe', 'ja', 'jae', 'js', 'jns', 'jo', 'jno', 'jp', 'jnp', 'jecxz',
        'loop', 'loope', 'loopne', 'int3', 'hlt', 'iret')


def tail_pushes(site, max_insn=24):
    """walk back enforcing strict contiguity; return instructions nearest-first, stop at 3 pushes"""
    cur = site
    seq = []
    for _ in range(max_insn):
        a = endmap.get(cur)
        if a is None:
            break
        sz, mn, op = insn[a]
        if mn in CTRL:
            break
        seq.append((a, mn, op))
        cur = a
        if mn.startswith('push') and sum(1 for x in seq if x[1].startswith('push')) >= 3:
            break
    return seq


def push_imm(addr, sz):
    """decode one push instruction in a <=16B window WITH detail, return imm or None"""
    win = tblob[addr - tva: addr - tva + sz]
    d2 = Cs(CS_ARCH_X86, CS_MODE_32)
    d2.detail = True                     # bounded window only (R134: never on whole .text)
    for i in d2.disasm(win, addr):
        if i.mnemonic == 'push' and i.operands and i.operands[0].type == 2:   # X86_OP_IMM
            return i.operands[0].imm
        if i.mnemonic == 'push' and i.op_str:
            try:
                return int(i.op_str, 0)
            except ValueError:
                return None
    return None


args = []
for site in SITES:
    seq = tail_pushes(site)
    pushes = [x for x in seq if x[1].startswith('push')][:3]
    if len(pushes) < 3:
        args.append((site, None, 'pushes=%d' % len(pushes)))
        continue
    a3, mn3, op3 = pushes[2]      # earliest of nearest three = third arg (cdecl)
    imm = push_imm(a3, insn[a3][0])
    args.append((site, imm, op3))
for site, imm, op in args:
    print('  site %#x arg3=%s (%s)' % (site, imm, op))
nums = [a[1] for a in args]
chk('F1 all 15 sites resolved to an immediate arg3', all(x is not None for x in nums),
    'resolved=%d/15' % sum(1 for x in nums if x is not None))
chk('F2 arg3 == 7 at all 15 sites', all(x == 7 for x in nums), 'values=%s' % (sorted(set(x for x in nums)),))
chk('F3 7 & 0x14 != 0 hence je NOT taken (control falls into if arm)',
    all((x & 0x14) != 0 for x in nums if x is not None),
    '7&0x14=%#x' % (7 & 0x14))

# ---- G 组：间接入路 ----
indirect = []
for a, (sz, mn, op) in insn.items():
    if mn not in ('call', 'jmp'):
        continue
    if not op:
        continue
    t = op.strip()
    if t.startswith('0x') or t.startswith('dword ptr') or t.startswith('qword ptr'):
        continue
    indirect.append((a, mn, t))
reg_ind = [x for x in indirect if not x[2].startswith('dword')]
print('\nindirect call/jmp total %d, register-form %d' % (len(indirect), len(reg_ind)))
chk('G1 indirect register-form call/jmp exists in .text (static target unknowable)',
    len(reg_ind) > 0, 'count=%d e.g. %s' % (len(reg_ind), [(hex(a), m, t) for a, m, t in reg_ind[:5]]))

# 能否静态排除这些间接目标落到两个入口？只测了两件事：入口地址作为 imm32 全库 0 次、
# .detour 内 0 次。这两条**不足以**排除运行期计算出来的地址，故不作断言，只作范围声明。
print('\nSTATIC SCOPE, not a proof: entry VA appears as imm32 0 times and in .detour 0 times,')
print('and 15 rel32 sites land exactly on the entries (r134c). There are %d indirect' % len(reg_ind))
print('register-form call/jmp sites whose targets cannot be resolved statically, so the')
print('claim that the else arm is unreachable FOR ARBITRARY INPUTS stays open. What is')
print('established is narrower: unreachable at every statically addressable entry, and')
print('arg3 == 7 at all 15 of those, so 7 & 0x14 != 0 and the je is not taken there.')

n_ = sum(1 for _, ok, _ in res if ok)
print('\n%d/%d PASS' % (n_, len(res)))
json.dump({'pass': n_, 'total': len(res), 'sweep_insns': n, 'last_va': hex(max(insn)),
           'args': [[hex(s), v, o] for s, v, o in args],
           'indirect_reg_count': len(reg_ind),
           'indirect_reg_sample': [[hex(a), m, t] for a, m, t in reg_ind[:20]],
           'results': [{'name': a, 'ok': b, 'detail': c} for a, b, c in res]},
          io.open(OUTP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
raise SystemExit(0 if n_ == len(res) else 1)
