# -*- coding: utf-8 -*-
"""R16-FIX-B2-1ROW : executable HOST-IDENTITY VERIFICATION RULE (G0-G5).

Reuses the G1-G5 structure of R16_FIX_B1_2ROWS/host_rule.py with two card-driven
adaptations, both documented in REPORT.md:

  * G4 ("call <alloc>") accepts a direct call in [host, site) to a KNOWN base
    ctor ({0x431B20, 0x47AA30}) OR to any target that itself installs a vptr
    from ecx and returns that register (ctor-like).  CCFileClass's direct base
    is CDFileClass whose ctor is 0x47AA30 (it in turn calls 0x431B20); a rule
    hardcoded to 0x431B20 alone would wrongly reject the audit-recommended
    host 0x473A80.
  * G2 ("this target") additionally rejects a this-carrier register that is
    RE-WRITTEN between `mov reg, ecx` and the store (e.g. `add esi,4` in the
    destructor at 0x759510), so [reg+0] is really [this+0].

All inputs are read-only.  Nothing is written by this module.
"""
import bisect, io, json, os, sys
sys.dont_write_bytecode = True
import pefile, capstone

IB = 0x400000
BASE_CTOR = 0x431B20          # AbstractClass/FileClass base ctor
CD_CTOR = 0x47AA30            # CDFileClass base ctor (proved in R16_FIX_B1_2ROWS)
KNOWN_BASE_CTORS = (BASE_CTOR, CD_CTOR)
BASE_DTOR = 0x431B80          # base destructor (vptr re-install + operator delete)
OP_DELETE = 0x7C8B3D
GPRS = ("eax", "ebx", "ecx", "edx", "esi", "edi")


class Image(object):
    def __init__(self, exe_path):
        with open(exe_path, "rb") as fh:
            fh.read(1)                       # prove read-only open
        self.pe = pefile.PE(exe_path, fast_load=True)
        self.secs = []
        for s in self.pe.sections:
            self.secs.append((IB + s.VirtualAddress, s.Misc_VirtualSize,
                              s.SizeOfRawData, s.get_data(),
                              s.Name.rstrip(b"\x00").decode("latin-1")))
        end = max(va + max(vs, rs) for va, vs, rs, _d, _n in self.secs)
        self.buf = bytearray(end - IB + 16)
        self.sec_of = {}
        for va, vs, rs, d, nm in self.secs:
            self.buf[va - IB:va - IB + len(d)] = d
            for o in range(va - IB, va - IB + len(d)):
                self.sec_of[o] = nm
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.md.detail = True
        self.md.skipdata = True

    def u32(self, va):
        o = va - IB
        return int.from_bytes(self.buf[o:o + 4], "little") if 0 <= o <= len(self.buf) - 4 else None

    def cstr(self, va, n=256):
        o = va - IB
        if o < 0 or o >= len(self.buf):
            return None
        e = self.buf.find(b"\x00", o, min(o + n, len(self.buf)))
        return bytes(self.buf[o:e]).decode("latin-1", "replace") if e > 0 else None

    def dis(self, va, n):
        return list(self.md.disasm(bytes(self.buf[va - IB:va - IB + n]), va))

    def decode_store(self, va, vt, max_back=16):
        """Decode the unique `mov [mem], imm32` whose imm==vt and whose END is
        immediately after the imm bytes, starting exactly at `va`."""
        pat = (vt & 0xFFFFFFFF).to_bytes(4, "little")
        lo = max(0, va - IB - max_back)
        hi = min(len(self.buf) - 4, va - IB + 8)
        for o in range(lo, hi + 1):
            if self.buf[o:o + 4] != pat:
                continue
            vend = IB + o + 4
            for back in range(0, max_back + 1):
                s = IB + o - back
                if s < IB:
                    continue
                r = list(self.md.disasm(bytes(self.buf[s - IB:s - IB + 24]), s, count=1))
                if not r:
                    continue
                ins = r[0]
                if ins.address + ins.size != vend or ins.mnemonic != "mov":
                    continue
                op = ins.operands
                if len(op) != 2 or op[0].type != capstone.x86.X86_OP_MEM \
                        or op[1].type != capstone.x86.X86_OP_IMM:
                    continue
                if (op[1].imm & 0xFFFFFFFF) != (vt & 0xFFFFFFFF):
                    continue
                if s == va:
                    return ins
        return None

    def ctor_like(self, target):
        """True iff the target function installs a vptr from a this-carrier and
        returns that register -- a plausible base ctor for G4."""
        if target in KNOWN_BASE_CTORS:
            return True
        if target < IB or target - IB >= len(self.buf):
            return False
        body = self.dis(target, 0x80)
        reg = None
        installed = False
        for x in body[:16]:
            if x.mnemonic == "mov" and len(x.operands) == 2 \
                    and x.operands[0].type == capstone.x86.X86_OP_REG \
                    and x.operands[1].type == capstone.x86.X86_OP_REG \
                    and self.md.reg_name(x.operands[1].reg) == "ecx":
                reg = self.md.reg_name(x.operands[0].reg)
            if x.mnemonic == "mov" and len(x.operands) == 2 \
                    and x.operands[0].type == capstone.x86.X86_OP_MEM \
                    and x.operands[1].type == capstone.x86.X86_OP_IMM:
                mo = x.operands[0].mem
                if (mo.base and self.md.reg_name(mo.base) == reg and (mo.disp & 0xffffffff) == 0
                        and 0x400000 <= (x.operands[1].imm & 0xffffffff) < 0x900000):
                    installed = True
        if not installed:
            return False
        idxs = [i for i, x in enumerate(body) if x.mnemonic in ("ret", "retf")]
        for i in idxs:
            if any(x.mnemonic == "mov" and x.op_str == ("eax, %s" % reg)
                   for x in body[max(0, i - 6):i]):
                return True
        return False


class HostRule(object):
    def __init__(self, image):
        self.im = image

    def body(self, host, site, cap=0x2000):
        """Linear decode from host, stopping at the first ret *after* site.
        Returns (insns, site_in_body)."""
        if host < IB or host - IB >= len(self.im.buf):
            return [], False
        out = []
        for x in self.im.md.disasm(bytes(self.im.buf[host - IB:host - IB + cap]), host):
            out.append(x)
            if x.mnemonic in ("ret", "retf") and x.address > site:
                break
        return out, any(x.address == site for x in out)

    def _writes_reg(self, x, reg):
        op = x.operands[0] if x.operands else None
        if op is None or op.type != capstone.x86.X86_OP_REG:
            return False
        if self.im.md.reg_name(op.reg) != reg:
            return False
        return x.mnemonic not in ("cmp", "test", "push")

    def classify(self, site, vt, host):
        im = self.im
        ins = im.decode_store(site, vt)
        if ins is None:
            return dict(site="%08X" % site, ins="未取得", ins_bytes="", target="未取得",
                        target_base="?", target_disp=None, target_is_stack="未取得",
                        target_is_abs="未取得", this_from_ecx="未取得", base_reg_changed="未取得",
                        base_ctor_before="未取得", dtor_call_after="未取得", sdd_sig="未取得",
                        returns_this="未取得", host_is_ctor="未取得",
                        host_is_canonical_ctor="未取得", host_is_dtor="未取得",
                        verdict="SKIP", failed_gates="未取得", site_in_body="否",
                        ctor_call_targets="")
        mo = ins.operands[0].mem
        base = im.md.reg_name(mo.base) if mo.base else ""
        disp = mo.disp & 0xFFFFFFFF
        target = ins.op_str.split(",")[0].strip()
        target_is_stack = base in ("esp", "ebp")
        target_is_abs = (base == "")

        body, site_in_body = self.body(host, site)
        by_addr = {x.address: i for i, x in enumerate(body)}
        idx_site = by_addr.get(site)

        # G2: `mov base, ecx` in prologue AND base not rewritten before the store
        def_idx = None
        for i, x in enumerate(body[:16]):
            if x.mnemonic == "mov" and x.op_str == ("%s, ecx" % base):
                def_idx = i
                break
        base_changed = False
        if def_idx is not None and idx_site is not None:
            for x in body[def_idx + 1:idx_site]:
                if self._writes_reg(x, base):
                    base_changed = True
                    break
        this_from_ecx = (def_idx is not None and not base_changed)

        ctor_targets = []
        base_ctor_before = False
        dtor_call_after = False
        delete_sig = False
        for x in body:
            if x.mnemonic not in ("call", "jmp"):
                continue
            imm = None
            for op in x.operands:
                if op.type == capstone.x86.X86_OP_IMM:
                    imm = op.imm & 0xFFFFFFFF
            if imm is None:
                continue
            if x.mnemonic == "call" and imm in KNOWN_BASE_CTORS and x.address < site:
                base_ctor_before = True
                ctor_targets.append("%08X(known)" % imm)
            elif x.mnemonic == "call" and x.address < site and im.ctor_like(imm):
                base_ctor_before = True
                ctor_targets.append("%08X(ctor_like)" % imm)
            if imm == BASE_DTOR and x.address > site:
                dtor_call_after = True
            if imm == OP_DELETE:
                delete_sig = True
        txt = ["%s %s" % (x.mnemonic, x.op_str) for x in body]
        has_test_flag = any(t.startswith("test") and "[esp" in t and t.rstrip().endswith(", 1") for t in txt)
        has_ret_imm = any(t.startswith("ret 0x") for t in txt)
        sdd_sig = has_test_flag and delete_sig and has_ret_imm

        returns_this = False
        if base == "eax" and this_from_ecx:
            returns_this = True
        else:
            idxs = [i for i, x in enumerate(body) if x.mnemonic in ("ret", "retf")]
            for i in idxs:
                for x in body[max(0, i - 6):i]:
                    if x.mnemonic == "mov" and x.op_str == ("eax, %s" % base):
                        returns_this = True
                        break
                if returns_this:
                    break

        host_is_dtor = bool(dtor_call_after or sdd_sig)
        gates = dict(
            G1_nonstack=not target_is_stack and not target_is_abs,
            G2_this_object=(base in GPRS) and (disp == 0) and this_from_ecx,
            G3_not_dtor=(not dtor_call_after) and (not sdd_sig),
            G4_base_ctor_before=base_ctor_before,
            G5_returns_this=returns_this,
        )
        core = gates["G1_nonstack"] and gates["G2_this_object"] and gates["G3_not_dtor"]
        canonical = core and gates["G4_base_ctor_before"] and gates["G5_returns_this"]
        verdict = "OK" if core else "SUSPECT"
        fail = [k for k, v in gates.items() if not v]
        return dict(
            site="%08X" % site, ins="%s %s" % (ins.mnemonic, ins.op_str),
            ins_bytes=ins.bytes.hex(), target=target, target_base=base,
            target_disp=disp, target_is_stack="是" if target_is_stack else "否",
            target_is_abs="是" if target_is_abs else "否",
            this_from_ecx="是" if this_from_ecx else "否",
            base_reg_changed="是" if base_changed else "否",
            base_ctor_before="是" if base_ctor_before else "否",
            dtor_call_after="是" if dtor_call_after else "否",
            delete_sig="是" if delete_sig else "否",
            sdd_sig="是" if sdd_sig else "否",
            returns_this="是" if returns_this else "否",
            host_is_ctor="是" if core else "否",
            host_is_canonical_ctor="是" if canonical else "否",
            host_is_dtor="是" if host_is_dtor else "否",
            verdict=verdict, failed_gates=",".join(fail) if fail else "-",
            site_in_body="是" if site_in_body else "否",
            ctor_call_targets=",".join(ctor_targets),
        )
