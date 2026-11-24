# -*- coding: utf-8 -*-
"""§533 shared toolkit —— 逆向取证引擎（子代理复用；只读 gamemd.exe）。

口径纪律（与 re_atlas/tools/text_sweep.py、_crev_engine.py 同源）：
  * **必须用重同步线性解码**（逐址 +1 恢复），不许用 `for ins in MD.disasm(blob, va)`
    —— 后者在首个不可解码字节处**静默停止**（本仓 G-23 已登记，多次造成假零）。
  * 每条普查必须打印**覆盖率自证**（decoded bytes / .text size）。
  * 绝对地址访存判据 = capstone operand mem{base==0, index==0, disp==目标VA}，
    写/读由 operand.access & 2 判定。

用法：
    import sys; sys.path.insert(0, r"...\\swarm_20261104")
    from ra2tool import Engine
    eng = Engine()
    eng.disp_hits(0xA8ED84)          # [(va, 'W'|'R', mnem, op_str)]
    eng.disasm(0x55D360, 0x300)      # [(va, bytes_hex, mnem, op_str)]
    eng.rd(0x55D360, 16)             # raw bytes at VA
    eng.resolve_iat(0x7E11F0)        # (dll, func)
    eng.func_rets(0x55D360, 0x55DEE0)         # 出口枚举
    eng.reach_without(0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84)  # 绕开 INC 仍可达的 ret
"""
import hashlib
import struct
from collections import defaultdict

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

# 常用全局（台账在册）
G_GAMELOGIC = 0x00A8B230
G_GAMEMODE = 0x00A8B238
G_FOCUS = 0x00A8ED80     # 焦点/快进旗标；全镜像唯一写者 0x7778CE（WndProc WM_ACTIVATEAPP）
G_FRAME = 0x00A8ED84     # CurrentFrame；唯一 inc 0x55DE7E/0x55DE81
G_INGAME = 0x00A8E9A0    # 局内标志；=0 时 MainLogicFrame 直接早退 0x55DEDB
G_EXITSTATE = 0x00A8EDD8
G_HWND = 0x00B73550
G_PUMPCNT = 0x00AA0430
G_TICKTGT = 0x00887330   # LogicUpdate 目标间隔 ms
G_TICKLAST = 0x00887328

# MainLogicFrame 锚
MLF_HEAD = 0x55D360
MLF_INC_RD = 0x55DE73
MLF_INC_PT = 0x55DE7E
MLF_INC_WR = 0x55DE81
MLF_TAIL = 0x55DEE0      # 下一函数头（0x55DEE0 = 0x55DE... 另一个函数）


class Engine:
    def __init__(self, exe=EXE):
        self.raw = open(exe, "rb").read()
        self.sha = hashlib.sha256(self.raw).hexdigest()
        assert self.sha == EXPECT_SHA, "image drift: %s" % self.sha
        e = struct.unpack_from("<I", self.raw, 0x3C)[0]
        nsec = struct.unpack_from("<H", self.raw, e + 6)[0]
        optsz = struct.unpack_from("<H", self.raw, e + 20)[0]
        opt = e + 24
        self.IB = struct.unpack_from("<I", self.raw, opt + 28)[0]
        self.opt = opt
        tab = opt + optsz
        self.SEC = []
        for i in range(nsec):
            nm = self.raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
            vsz, va, rsz, rp = struct.unpack_from("<IIII", self.raw, tab + i * 40 + 8)
            self.SEC.append((nm, self.IB + va, vsz, rp, rsz))
        t = next(s for s in self.SEC if s[0] == ".text")
        self.TLO, self.THI, self.TB, self.TSZ = t[1], t[1] + t[4], t[3], t[4]
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True
        self._stream = None
        self._by = None

    # ---------- bytes ----------
    def fo(self, va):
        for nm, sva, vsz, rp, rsz in self.SEC:
            if sva <= va < sva + vsz:
                off = rp + (va - sva)
                return off if off < rp + rsz else None
        return None

    def rd(self, va, n):
        o = self.fo(va)
        return self.raw[o:o + n] if o is not None else b"\0" * n

    def u32(self, va):
        return struct.unpack_from("<I", self.rd(va, 4), 0)[0]

    # ---------- decode ----------
    @property
    def stream(self):
        if self._stream is not None:
            return self._stream
        out, cur, fails = [], self.TLO, 0
        tb = self.raw[self.TB: self.TB + self.TSZ]
        while cur < self.THI:
            got = list(self.md.disasm(tb[cur - self.TLO: cur - self.TLO + 15], cur))
            if not got:
                cur += 1
                fails += 1
                continue
            out.append(got[0])
            cur += got[0].size
        self._stream = out
        self._resync = fails
        self._by = {i.address: i for i in out}
        return out

    @property
    def coverage(self):
        s = self.stream
        return 100.0 * sum(i.size for i in s) / self.TSZ, len(s), self._resync

    def by(self):
        self.stream
        return self._by

    def disasm(self, va, n):
        o = self.fo(va)
        blob = self.raw[o:o + n]
        return [(i.address, i.bytes.hex(), i.mnemonic, i.op_str)
                for i in self.md.disasm(blob, va)]

    # ---------- 绝对全局访存普查 ----------
    def disp_hits(self, va):
        res = []
        for ins in self.stream:
            try:
                ops = ins.operands
            except Exception:
                continue
            for op in ops:
                if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 \
                        and op.mem.disp == va:
                    res.append((ins.address, "W" if (op.access & 2) else "R",
                                ins.mnemonic, ins.op_str))
                    break
        return res

    def disp_hits_field(self, disp):
        """任意基址的 [reg+disp] 家族。"""
        res = []
        for ins in self.stream:
            try:
                ops = ins.operands
            except Exception:
                continue
            for op in ops:
                if op.type == 3 and op.mem.disp == disp:
                    res.append((ins.address, "W" if (op.access & 2) else "R",
                                ins.mnemonic, ins.op_str))
                    break
        return res

    # ---------- IAT ----------
    def resolve_iat(self, va):
        dd = self.opt + 96
        imp_rva = struct.unpack_from("<I", self.raw, dd + 8)[0]
        if not imp_rva:
            return None
        o = self.fo(self.IB + imp_rva)
        k = 0
        while True:
            d = self.raw[o + k * 20: o + k * 20 + 20]
            if len(d) < 20 or d == b"\0" * 20:
                return None
            oft, _ts, _fc, name_rva, ft = struct.unpack_from("<IIIII", d, 0)
            no = self.fo(self.IB + name_rva)
            dll = self.raw[no:self.raw.index(b"\0", no)].decode("ascii", "replace")
            thunk = oft or ft
            j = 0
            while True:
                tv = struct.unpack_from("<I", self.raw, self.fo(self.IB + thunk) + j * 4)[0]
                if tv == 0:
                    break
                slot = self.IB + ft + j * 4
                if slot == va:
                    if tv & 0x80000000:
                        return (dll, "ord#%d" % (tv & 0xFFFF))
                    ho = self.fo(self.IB + tv + 2)
                    return (dll, self.raw[ho:self.raw.index(b"\0", ho)].decode("ascii", "replace"))
                j += 1
            k += 1

    # ---------- CFG ----------
    def _edges(self, lo, hi):
        succ = defaultdict(list)
        seq = [i for i in self.stream if lo <= i.address < hi]
        nxt = {seq[k].address: (seq[k + 1].address if k + 1 < len(seq) else None)
               for k in range(len(seq))}
        for ins in seq:
            a, mn = ins.address, ins.mnemonic
            tgt = None
            try:
                if ins.operands and ins.operands[0].type == 2:
                    tgt = ins.operands[0].imm
            except Exception:
                pass
            if mn.startswith("ret"):
                continue
            if mn == "jmp":
                if tgt is not None and lo <= tgt < hi:
                    succ[a].append(tgt)
                continue
            if mn.startswith("j"):
                if tgt is not None and lo <= tgt < hi:
                    succ[a].append(tgt)
                if nxt[a] is not None:
                    succ[a].append(nxt[a])
                continue
            if nxt[a] is not None:
                succ[a].append(nxt[a])
        return succ, seq

    def func_rets(self, lo, hi):
        succ, seq = self._edges(lo, hi)
        return [i for i in seq if i.mnemonic.startswith("ret")], succ

    def reach_without(self, head, hi, cut_lo, cut_hi):
        """从 head 出发、**不许穿过 [cut_lo,cut_hi) 直线块**时可达的全部地址。"""
        succ, seq = self._edges(head, hi)
        seen, work = set(), [head]
        while work:
            a = work.pop()
            if a in seen:
                continue
            seen.add(a)
            for s in succ.get(a, ()):
                if cut_lo <= s <= cut_hi:
                    continue
                if s not in seen:
                    work.append(s)
        return seen

    def loop_backedges(self, lo, hi):
        """[lo,hi) 内的全部回边（jcc/jmp 目标 < 自身地址）。"""
        out = []
        for ins in self.stream:
            if not (lo <= ins.address < hi):
                continue
            if not ins.mnemonic.startswith("j"):
                continue
            try:
                if not ins.operands or ins.operands[0].type != 2:
                    continue
                t = ins.operands[0].imm
            except Exception:
                continue
            if t < ins.address and lo <= t:
                out.append((ins.address, t, ins.mnemonic))
        return out
