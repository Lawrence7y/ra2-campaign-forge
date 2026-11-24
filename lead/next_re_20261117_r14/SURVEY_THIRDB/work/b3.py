"""SURVEY-THIRDB ③b detector. Byte-only. Self-written CFG extent (no atlas entry+size).

③b 判据（R14_COMMON §8.6 条 3 / §8.7 判据 6）的机械操作化：
 ③b① 跳表 / switch 多路分支，且「每路可核（各分支后续动作确实不同）」
      ①-jt   : jmp dword ptr [reg*4+tab] 且 tab 至少 3 个相异 .text 目标
      ①-chain: 同一判别寄存器上的线性 cmp/test→jcc 链（≥3 闸）
      两式都必须：≥3 条「独立作用集非空」的臂，且其中 ≥3 个作用签名两两相异。
      作用签名 = (直接 call 目标集, 间接 call 槽/导入集, 非栈内存写 (目标,值) 集, 终止形态)
      **寄存器身份不计入签名**（否则「仅源寄存器不同」的三闸会被误判为相异）。
      臂的作用只在「该臂独占」的块上取（汇入共享桩/共享 call 块的臂，独占集为空 ⇒ 不计）。
 ③b② 可证伪的错误码 / 返回约定：call 结果寄存器被 cmp/test（≤3 条内）且在失败路径上
      `mov eax,K` 后返回，K ∈ 错误码集；被比较操作数必须是寄存器（内存字段 ⇒ 字段哨兵，不算）。
 ③b③ 内存形状断言：成员 ctor 数 ≥2（被调首块内 `mov [reg], vt` 且 vt 经 RTTI 可解）
      + 函数体内装 ≥2 张 RTTI 可解 vt + 对象大小断言（call 前 ≤3 条 push/mov 传入 ≥0x40 的立即数）。
 ③b④ 完整循环 I/O：真回边，且循环体内同时具备 读 + 判 + 写(非栈) + 推进 + 边界检查(出环 jcc)。
 其余 = ③a。
"""
import sys, json, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

# ---------------- register helpers ----------------
def mem_desc(op):
    """('g',addr) | ('f',disp) | ('i',disp) | ('stk',disp)"""
    b, i, d = op.mem.base, op.mem.index, op.mem.disp
    if b == 0 and i == 0:
        return ('g', int(d) & 0xffffffff)
    if b != 0 and i == 0:
        if b in (C.X86_REG_ESP, C.X86_REG_EBP):
            return ('stk', int(d))
        return ('f', int(d))
    return ('i', int(d))

def is_stack(op):
    d = mem_desc(op)
    return d[0] == 'stk'

# ---------------- CFG ----------------
class Fn:
    def __init__(self, entry):
        self.entry = entry
        lo, hi, addrs, blocks = C.extent(entry)
        self.lo, self.hi, self.addrs, self._runs = lo, hi, addrs, blocks
        self.ins = C.decode_fn(blocks)
        self.byaddr = {i.address: i for i in self.ins}
        self._build()

    def _build(self):
        ins = self.ins
        if not ins: self.blocks = []; self.order = {}; return
        idx = {i.address: k for k, i in enumerate(ins)}
        leaders = {ins[0].address}
        for k, i in enumerate(ins):
            t = term_of(i)
            if t is not None:
                if k+1 < len(ins) and ins[k+1].address == i.address + i.size:
                    leaders.add(ins[k+1].address)
                for tg in t[1]:
                    if tg in idx: leaders.add(tg)
        leaders = sorted(leaders)
        self.blocks = []
        cur = []
        lead = set(leaders)
        for i in ins:
            cur.append(i)
            if i.address in lead and len(cur) > 1 and i.address != cur[0].address:
                cur.pop(); self.blocks.append(cur); cur = [i]
            if term_of(i) is not None:
                self.blocks.append(cur); cur = []
        if cur: self.blocks.append(cur)
        self.order = {b[0].address: n for n, b in enumerate(self.blocks)}
        self.succ = {}
        for n, b in enumerate(self.blocks):
            t = term_of(b[-1])
            s = []
            if t is None:
                if n+1 < len(self.blocks): s.append(n+1)
            else:
                for tg in t[1]:
                    if tg in self.order: s.append(self.order[tg])
                if t[0] == 'jcc' and n+1 < len(self.blocks):
                    s.append(n+1)
            self.succ[n] = sorted(set(s))
        # reachability
        self.reach = {}
        for n in range(len(self.blocks)):
            seen = {n}; stack = [n]
            while stack:
                x = stack.pop()
                for y in self.succ.get(x, []):
                    if y not in seen: seen.add(y); stack.append(y)
            self.reach[n] = seen

def term_of(i):
    """('ret',[]) | ('jcc',[tgt]) | ('jmp',[tgt]) | ('ijmp',[tgt,...]) | None"""
    mn = i.mnemonic
    if mn.startswith('ret'): return ('ret', [])
    if mn in ('jmp',):
        if len(i.operands) == 1 and i.operands[0].type == X86_OP_IMM:
            return ('jmp', [int(i.operands[0].imm) & 0xffffffff])
        tg = C.TGT_JT.get(i.address - C.TVA)
        if tg: return ('ijmp', list(tg))
        return ('jmp', [])
    if mn in C.JCCS and len(i.operands) == 1 and i.operands[0].type == X86_OP_IMM:
        return ('jcc', [int(i.operands[0].imm) & 0xffffffff])
    return None

def direct_call_target(i):
    if i.mnemonic == 'call' and i.size == 5 and i.bytes[0] == 0xE8:
        return (i.address + 5 + int.from_bytes(i.bytes[1:5], 'little', signed=True)) & 0xffffffff
    if i.mnemonic == 'call' and len(i.operands) == 1 and i.operands[0].type == X86_OP_IMM:
        return int(i.operands[0].imm) & 0xffffffff
    return None

# 真正会「写内存」的助记符集合（test / cmp 只读并置标志位，**不是**写）
WRITE_MNEMS = {'mov','movzx','movsx','add','sub','and','or','xor','inc','dec',
               'shl','shr','sar','sal','rol','ror','stos','stosb','stosd',
               'movs','movsb','movsd','movd','movq','xchg','xadd','setne','sete',
               'seta','setb','setg','setl','not', 'neg','bts','btr','adc','sbb'}

def is_mem_write(i):
    if i.mnemonic not in WRITE_MNEMS: return None
    if not i.operands: return None
    if i.operands[0].type != X86_OP_MEM: return None
    return i.operands[0]

# ---------------- effects ----------------
def block_effect(blk):
    calls = set(); slots = set(); writes = set()
    for i in blk:
        t = direct_call_target(i)
        if t is not None:
            calls.add(t); continue
        if i.mnemonic == 'call' and i.operands and i.operands[0].type == X86_OP_MEM:
            d = mem_desc(i.operands[0])
            if d[0] == 'g':
                nm = C.import_of(d[1])
                slots.add(('iat', nm or hex(d[1])))
            elif d[0] == 'f':
                slots.add(('slot', d[1]))
            else:
                slots.add(('islot', d[1]))
            continue
        mo = is_mem_write(i)
        if mo is not None:
            d = mem_desc(mo)
            if d[0] == 'stk':
                continue
            if len(i.operands) > 1 and i.operands[1].type == X86_OP_IMM:
                val = ('imm', int(i.operands[1].imm) & 0xffffffff)
            else:
                val = ('any',)
            writes.add((d, val))
    return calls, slots, writes

def term_shape(blk):
    last = blk[-1]
    t = term_of(last)
    if t is None: return ('fall',)
    if t[0] == 'ret':
        for j in blk[-4:-1]:
            if j.mnemonic == 'mov' and j.operands and j.operands[0].type == X86_OP_REG \
               and j.operands[0].reg in (C.X86_REG_EAX,) and len(j.operands) > 1 \
               and j.operands[1].type == X86_OP_IMM:
                return ('ret', int(j.operands[1].imm) & 0xffffffff)
            if j.mnemonic == 'xor' and j.op_str.startswith('eax, eax'):
                return ('ret', 0)
        return ('ret',)
    if t[0] == 'jmp': return ('tail', t[1][0] if t[1] else None)
    return (t[0],)

def arm_region(fn, arm, all_arms):
    """Blocks owned by this arm: BFS from the arm entry, STOPPING at (and excluding)
    any other arm's entry. This keeps fall-through "staircase" cases separate
    instead of letting an earlier arm's reach swallow the later ones."""
    barriers = set(all_arms) - {arm}
    seen = set(); stack = [arm]
    while stack:
        n = stack.pop()
        if n in seen or n in barriers: continue
        seen.add(n)
        for y in fn.succ.get(n, []):
            if y not in seen and y not in barriers: stack.append(y)
    return seen

def sig_of(fn, region):
    calls = set(); slots = set(); writes = set(); reads = set(); terms = set()
    for n in sorted(region):
        b = fn.blocks[n]
        c, s, w = block_effect(b)
        calls |= c; slots |= s; writes |= w
        for i in b:
            for o in i.operands[1:]:
                if o.type == X86_OP_MEM:
                    d = mem_desc(o)
                    if d[0] != 'stk': reads.add(d)
        terms.add(term_shape(b))
    nonempty = bool(calls or slots or writes or reads)
    substant = bool(calls or slots or writes or reads)
    return dict(calls=frozenset(calls), slots=frozenset(slots), writes=frozenset(writes),
                reads=frozenset(reads), terms=frozenset(terms),
                nonempty=nonempty, substant=substant,
                has_call_or_write=bool(calls or slots or writes))

def multiway(fn, arm_entries, level='strict'):
    """level='strict': arms must differ in their ACTION set (call targets / call slots /
    non-stack writes / terminal); a differing memory read or immediate alone does NOT count,
    per §8.6 条3 「只有参数不同则不算」.
    level='loose': arms only need their own non-empty region with some substantive access
    (this is the level the project's SEMFIX_SLOTS2/KPROVED3 precedents were accepted at)."""
    regions = {a: arm_region(fn, a, arm_entries) for a in arm_entries}
    sigs = []; raw = []
    for a in arm_entries:
        sg = sig_of(fn, regions[a]); raw.append((a, sg, len(regions[a])))
        if level == 'strict':
            ok = sg['has_call_or_write']
            key = (sg['calls'], sg['slots'], sg['writes'], sg['terms'])
        else:
            ok = sg['substant']
            key = (sg['calls'], sg['slots'], sg['writes'], sg['reads'], sg['terms'])
        if ok: sigs.append(key)
    return len(sigs), len(set(sigs)), raw

# ---------------- ③b① ----------------
def jt_arms(fn):
    out = []
    for i in fn.ins:
        if i.mnemonic != 'jmp' or not i.operands or i.operands[0].type != X86_OP_MEM:
            continue
        m = i.operands[0].mem
        if m.index == 0 or m.scale != 4 or m.base != 0 or m.disp <= 0:
            continue
        tg = C.TGT_JT.get(i.address - C.TVA)
        if not tg: continue
        tg = [t for t in tg if t in fn.order]
        if len(set(tg)) >= 3:
            out.append((i.address, sorted(set(tg))))
    return out

def chain_arms(fn):
    """linear switch chain: block ends b cmp/test R,imm -> jcc ; fallthrough block does same on R."""
    chains = []
    for n, b in enumerate(fn.blocks):
        last = b[-1]
        t = term_of(last)
        if not t or t[0] != 'jcc': continue
        reg, imm = cmp_reg_imm(b)
        if reg is None: continue
        arms = [t[1][0]]
        cur = n; depth = 1
        while depth < 64:
            nxt = cur + 1
            if nxt >= len(fn.blocks): break
            nb = fn.blocks[nxt]
            nt = term_of(nb[-1])
            if not nt or nt[0] != 'jcc': break
            r2, i2 = cmp_reg_imm(nb)
            if r2 != reg: break
            arms.append(nt[1][0]); cur = nxt; depth += 1
        if depth >= 3:
            arms.append(fn.blocks[cur][-1].address + fn.blocks[cur][-1].size)
            chains.append((b[0].address, [a for a in arms if a in fn.order]))
    return chains

def cmp_reg_imm(blk):
    for i in reversed(blk[-3:]):
        if i.mnemonic in ('cmp','test') and len(i.operands) >= 2:
            a, b = i.operands[0], i.operands[1]
            if a.type == X86_OP_REG and b.type in (X86_OP_IMM, X86_OP_REG):
                return a.reg, (int(b.imm) & 0xffffffff if b.type == X86_OP_IMM else None)
    return None, None

def b1(fn, level='strict'):
    """returns (hits, alt_hits) : hits at `level`, alt_hits at the other level."""
    other = 'loose' if level == 'strict' else 'strict'
    hits = []; alt = []
    for (site, targets) in jt_arms(fn):
        arms = [fn.order[t] for t in targets]
        nq, nd, _ = multiway(fn, arms, level)
        if nq >= 3 and nd >= 3: hits.append(('jt', site, len(targets), nq, nd))
        nq2, nd2, _ = multiway(fn, arms, other)
        if nq2 >= 3 and nd2 >= 3: alt.append(('jt', site, len(targets), nq2, nd2))
    for (site, targets) in chain_arms(fn):
        arms = [fn.order[t] for t in targets if t in fn.order]
        if len(arms) < 3: continue
        nq, nd, _ = multiway(fn, arms, level)
        if nq >= 3 and nd >= 3: hits.append(('chain', site, len(targets), nq, nd))
        nq2, nd2, _ = multiway(fn, arms, other)
        if nq2 >= 3 and nd2 >= 3: alt.append(('chain', site, len(targets), nq2, nd2))
    return hits, alt

# ---------------- ③b② ----------------
ERRCODES = {0xffffffff, 0x80004001, 0x80004002, 0x80004005, 0x80070057, 0x8007000e,
            0x80070005, 0x8000000a, 0x8876086c}
def is_errcode(v):
    v &= 0xffffffff
    if v in ERRCODES: return True
    if 0x80000000 <= v <= 0x8004ffff: return True
    if 0x80070000 <= v <= 0x8007ffff: return True
    return False

def b2(fn):
    """两个通道，均要求被比较操作数是「调用的返回值寄存器」，而不是内存字段（字段哨兵）。
    ②-ret: call 结果被 cmp/test（≤3 条内），且失败路径上 `mov eax,K` 后返回，K ∈ 错误码集。
    ②-hr : call 结果被 cmp 到具名 HRESULT 常量（0x8000xxxx/0x8007xxxx），其后跟着不同的
           分支动作（错误上报 call / 跳过）。"""
    ins = fn.ins
    ret_hits = []; hr_hits = []
    for k, i in enumerate(ins):
        is_call = direct_call_target(i) is not None or (
            i.mnemonic == 'call' and i.operands and i.operands[0].type == X86_OP_MEM)
        if not is_call: continue
        for j in range(k+1, min(k+4, len(ins))):
            c = ins[j]
            if c.mnemonic not in ('cmp','test'): continue
            if not c.operands: continue
            o0 = c.operands[0]
            if o0.type != X86_OP_REG or o0.reg not in (C.X86_REG_EAX, C.X86_REG_AX, C.X86_REG_AL):
                continue
            if len(c.operands) > 1 and c.operands[1].type == X86_OP_MEM: continue  # 字段哨兵
            lim = None
            if len(c.operands) > 1 and c.operands[1].type == X86_OP_IMM:
                lim = int(c.operands[1].imm) & 0xffffffff
            # ②-hr : 具名 HRESULT 常量（真错误码）
            # ②-hr-sent : 仅 cmp eax,-1 —— 是「被调返回 −1」的哨兵式判等，不是「本函数返回错误码」，
            #             卡片示例（GetLastError → 返回 −1）不覆盖此形 ⇒ **不计入主口径**，只作余量单列。
            if lim is not None and is_errcode(lim):
                tag = '②hr-sent' if lim == 0xffffffff else '②hr'
                hr_hits.append((tag, ins[k].address, c.address, lim))
            # ②-ret : 失败路径返回错误码
            for m in ins[j+1: j+40]:
                if m.mnemonic == 'mov' and m.operands and m.operands[0].type == X86_OP_REG \
                   and m.operands[0].reg == C.X86_REG_EAX and len(m.operands) > 1 \
                   and m.operands[1].type == X86_OP_IMM and is_errcode(int(m.operands[1].imm)):
                    ret_hits.append((ins[k].address, c.address, int(m.operands[1].imm) & 0xffffffff))
                    break
        if len(ret_hits) + len(hr_hits) > 2: break
    hits = [('②ret',) + h for h in ret_hits[:2]] + [
        (t, a, c, v) for (t, a, c, v) in hr_hits[:2]]
    return hits

# ---------------- ③b③ ----------------
_ctor_cache = {}
def ctor_vts(callee, depth=1):
    """does callee install a RTTI-resolvable vtable at [reg] near its entry?"""
    if callee in _ctor_cache: return _ctor_cache[callee]
    vts = set()
    if C.in_text(callee):
        lo, hi, addrs, blocks = C.extent(callee, cap=120)
        for i in C.decode_fn(blocks)[:14]:
            if i.mnemonic == 'mov' and len(i.operands) == 2 \
               and i.operands[0].type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM:
                d = mem_desc(i.operands[0])
                if d[0] in ('f', 'g') and d[1] == 0:
                    v = int(i.operands[1].imm) & 0xffffffff
                    if C.rtti_class_of_vt(v): vts.add(v)
    _ctor_cache[callee] = vts
    return vts

def b3(fn):
    """③b③ 内存形状断言 = 成员 ctor 数 + vt + 对象大小，三者齐备。
    - 成员 ctor 数：被调函数首块内 `mov [reg], <RTTI 可解 vt>`（即装 vtable 的 ctor）个数 ≥2
    - vt        ：函数体内装 RTTI 可解 vtable 的相异张数 ≥2
    - 对象大小  ：① call 前 ≤3 条 push 传入 ≥0x40 的立即数（显式 size 实参），或
                  ② 体内非栈成员位移最大值 ≥0x80（对象形状跨过 128B，等价于对该对象的体量断言）
    """
    vt_inst = set(); ctor_calls = set(); size_args = set(); max_disp = 0
    ins = fn.ins
    for i in ins:
        if i.mnemonic == 'mov' and len(i.operands) == 2 \
           and i.operands[0].type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM:
            d = mem_desc(i.operands[0])
            if d[0] in ('f', 'g'):
                v = int(i.operands[1].imm) & 0xffffffff
                if C.rtti_class_of_vt(v): vt_inst.add(v)
        for o in i.operands:
            if o.type == X86_OP_MEM:
                d = mem_desc(o)
                if d[0] in ('f', 'i') and d[1] > max_disp: max_disp = d[1]
    for k, i in enumerate(ins):
        t = direct_call_target(i)
        if t is None: continue
        if ctor_vts(t): ctor_calls.add(t)
        for j in range(max(0, k-3), k):
            p = ins[j]
            if p.mnemonic == 'push' and p.operands and p.operands[0].type == X86_OP_IMM:
                v = int(p.operands[0].imm) & 0xffffffff
                if 0x40 <= v <= 0x100000: size_args.add(v)
    size_ok = bool(size_args) or max_disp >= 0x80
    ok = (len(ctor_calls) >= 2 and len(vt_inst) >= 2 and size_ok)
    return dict(ok=ok, n_ctor=len(ctor_calls), n_vt=len(vt_inst),
                size=sorted(size_args)[:4], max_disp=max_disp, size_ok=size_ok,
                ctor=sorted(ctor_calls)[:6], vt=[hex(v) for v in sorted(vt_inst)[:6]])

# ---------------- ③b④ ----------------
ADV = {'inc','dec','add','sub','lea'}
def b4(fn):
    """③b④ 完整循环 I/O：真回边，且循环体内同时具备
       读（非栈内存读）+ 判（cmp/test）+ 写（非栈内存写）+ 推进（归纳寄存器自增/自减）
       + 边界检查（对同一归纳寄存器的有界比较 cmp/test 紧跟 jcc）。
    口径（明写）：
      - 「写」只认**非栈**内存写；栈累加槽（[esp..]/[ebp..]）不计，单列 `stackacc` 供核对。
      - 边界检查认「计数式」（cmp R,imm; jcc）与「指针式」（cmp R,limit_reg; jcc）两种；
        jcc 可以是继续边（回跳表头）也可以是出环边。
    """
    ins = fn.ins
    best = None
    for k, i in enumerate(ins):
        t = term_of(i)
        if not t or t[0] != 'jcc' or not t[1]: continue
        tgt = t[1][0]
        if not (fn.lo <= tgt < i.address): continue
        body = [y for y in ins if tgt <= y.address <= i.address]
        if len(body) < 6: continue
        read = False; write = False; write_stk = False; testc = False; adv = set()
        for y in body:
            mo = is_mem_write(y)
            if mo is not None:
                if mem_desc(mo)[0] == 'stk': write_stk = True
                else: write = True
            for o in y.operands[1:]:
                if o.type == X86_OP_MEM and not is_stack(o): read = True
            if y.mnemonic in ('cmp','test'): testc = True
            if y.mnemonic in ADV and y.operands and y.operands[0].type == X86_OP_REG:
                adv.add(y.operands[0].reg)
        # 归纳寄存器 = 被推进 且 被比较
        ind = set(adv)
        bounds = False; indhit = None
        for n2, y in enumerate(body):
            if y.mnemonic not in ('cmp','test') or not y.operands: continue
            r0 = y.operands[0].reg if y.operands[0].type == X86_OP_REG else None
            r1 = y.operands[1].reg if len(y.operands) > 1 and y.operands[1].type == X86_OP_REG else None
            if (r0 in ind) or (r1 in ind):
                # 有界比较：另一侧是立即数或另一寄存器
                lim = False
                if len(y.operands) > 1 and y.operands[1].type == X86_OP_IMM: lim = True
                if r0 in ind and r1 is not None: lim = True
                if r1 in ind and r0 is not None: lim = True
                if not lim: continue
                nxt = ins.index(y)
                for z in ins[nxt+1: nxt+3]:
                    tt = term_of(z)
                    if tt and tt[0] == 'jcc':
                        bounds = True; indhit = (y.address, z.mnemonic); break
            if bounds: break
        progress = bool(ind)
        ok = read and testc and write and progress and bounds
        if ok:
            return dict(ok=True, head=tgt, back=i.address, n=len(body), ind=sorted(ind)[:6],
                        bound=indhit, why='read+test+write+advance+bounds')
        if best is None:
            best = dict(ok=False, head=tgt, back=i.address, n=len(body), read=read, test=testc,
                        write=write, write_stk=write_stk, progress=progress, bounds=bounds,
                        ind=sorted(ind)[:4])
    return best or dict(ok=False, why='no_backedge')

# ---------------- orchestrator ----------------
def classify(entry, level='strict'):
    fn = Fn(entry)
    out = dict(entry=entry, lo=fn.lo, hi=fn.hi, n_ins=len(fn.ins), n_blk=len(fn.blocks))
    h1, h1alt = b1(fn, level) if fn.ins else ([], [])
    out['b1'] = h1
    out['b1_alt'] = h1alt
    out['b2'] = b2(fn) if fn.ins else []
    out['b3'] = b3(fn) if fn.ins else dict(ok=False, n_ctor=0, n_vt=0, size=[], ctor=[], vt=[])
    out['b4'] = b4(fn) if fn.ins else dict(ok=False)
    # 主口径 ②：只认 ②ret（返回错误码）与 ②hr（具名 HRESULT）；②hr-sent 单列
    b2_main = [h for h in out['b2'] if h[0] != '②hr-sent']
    b2_sent = [h for h in out['b2'] if h[0] == '②hr-sent']
    out['b2_main'] = b2_main
    out['b2_sent'] = b2_sent
    def mk(h1x, b2x):
        return [c for c, f in (('③b①', bool(h1x)), ('③b②', bool(b2x)),
                               ('③b③', bool(out['b3'].get('ok'))),
                               ('③b④', bool(out['b4'].get('ok')))) if f]
    out['cats'] = mk(h1, b2_main)                 # 主口径
    out['cats_alt'] = mk(h1alt, out['b2'])        # 敏感档 B：① 放宽到「目标档」+ ② 收全部
    out['cats_sent'] = mk(h1, out['b2'])          # 敏感档 A：② 含 cmp eax,-1
    out['verdict'] = '③b' if out['cats'] else '③a'
    out['verdict_alt'] = '③b' if out['cats_alt'] else '③a'
    out['verdict_sent'] = '③b' if out['cats_sent'] else '③a'
    return out

if __name__ == '__main__':
    C.build_jt()
    for e, name in [(0x0053AF40, 'POS 0053AF40'), (0x0069DEB0, 'NEG 0069DEB0'),
                    (0x00704350, 'NEG 00704350'), (0x004DDDE0, 'NEG 004DDDE0')]:
        r = classify(e)
        print('%-14s strict=%s %s | loose=%s %s  nins=%d nblk=%d' % (
            name, r['verdict'], r['cats'], r['verdict_alt'], r['cats_alt'],
            r['n_ins'], r['n_blk']))
        print('    b1        =%s' % (r['b1'],))
        print('    b1(loose) =%s' % (r['b1_alt'],))
        if r['b2']: print('    b2=%s' % (r['b2'],))
        if r['b3'].get('ok'): print('    b3=%s' % (r['b3'],))
        if r['b4'].get('ok'): print('    b4=%s' % (r['b4'],))
