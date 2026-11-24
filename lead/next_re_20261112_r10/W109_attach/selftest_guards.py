# -*- coding: utf-8 -*-
"""W109 防环/防崩守卫的独立实检（不依赖 Mem/proc，纯 fake mem）。写入 EVIDENCE/guards.txt。

覆盖：自环 / 二元环 / 节点上限 / 垃圾 next（超范围、0、低址）/ 读失败 / 目标中途退出。
每个用例都断言 scan_chain **返回**而不是抛异常，且 stop 原因符合预期。
"""
import sys

import cell_sentinel as cs

fails = []


def ck(name, ok, got):
    print("  [%s] %s (got %r)" % ("PASS" if ok else "FAIL", name, got))
    if not ok:
        fails.append(name)


HEAD = 0x00100000
VT = 0x00120000
THUNK = 0x00130000


class F(object):
    """最小 fake mem：只实现 scan_chain 用到的两个方法，未命中一律 -> None。"""

    def __init__(self, table):
        self.table = dict(table)
        self.st = cs.ReadStats()

    def read_bytes(self, va, n):
        if va in self.table:
            v = self.table[va]
            return v if isinstance(v, bytes) else int(v).to_bytes(4, "little")
        return None

    def readable(self, va, n):
        return self.read_bytes(va, 4) is not None


def chain_map(nodes, nxt_of, vptr_of):
    """建一个 fake 内存映射。注意：vptr 目标必须**整段可读**才能走到 WhatAmI 判定
    （scan_chain 会先检查 vptr..vptr+0x30 可读），所以每种 vptr 用例都要单独铺目标页。"""
    m = {HEAD: nodes[0] if nodes else 0,
         VT + 0x2C: THUNK,
         THUNK: b"\xb8\x06\x00\x00\x00\xc3"}
    # scan_chain 会读 w+1 起的 4 字节取 WhatAmI 立即数；F.read_bytes 按 va 精确查表，
    # 所以 THUNK+1 必须单独登记，否则会被误判成 whatami_out_of_range。
    m[THUNK + 1] = b"\x06\x00\x00\x00"
    for n in nodes:
        m[n] = vptr_of(n)
        m[n + 0x30] = nxt_of(n)
    return m


def readable_span(m, base, size):
    """把 base..base+size 逐 dword 铺成 0，使其"可读"。"""
    for off in range(0, size, 4):
        m.setdefault(base + off, 0)


print("=== W109 guard tests (fake mem; no process, no file writes) ===")

# 1) 自环
A = 0x00140000
m = chain_map([A], lambda n: n, lambda n: VT)
r = cs.scan_chain(F(m), HEAD, max_nodes=64)
ck("自环 -> stop=cycle 且不抛", r["stop"] == "cycle", r["stop"])
ck("自环 -> 节点数=1（不重复计数）", len(r["nodes"]) == 1, len(r["nodes"]))

# 2) 二元环
B1, B2 = 0x00150000, 0x00160000
m = chain_map([B1, B2],
              lambda n: B2 if n == B1 else B1,
              lambda n: VT)
r = cs.scan_chain(F(m), HEAD, max_nodes=64)
ck("二元环 -> stop=cycle 且不抛", r["stop"] == "cycle", r["stop"])
ck("二元环 -> 节点数=2", len(r["nodes"]) == 2, len(r["nodes"]))

# 3) 节点上限：长无环链
C = 0x00170000
long_nodes = [C + i * 0x100 for i in range(40)]
idx = dict((n, i) for i, n in enumerate(long_nodes))
m = chain_map(long_nodes,
              lambda n: long_nodes[idx[n] + 1] if idx[n] + 1 < len(long_nodes) else 0,
              lambda n: VT)
for cap in (1, 8, 39):
    r = cs.scan_chain(F(m), HEAD, max_nodes=cap)
    ck("节点上限 max_nodes=%d -> stop=max_nodes，节点数<=%d" % (cap, cap),
       r["stop"] == "max_nodes" and len(r["nodes"]) <= cap,
       (r["stop"], len(r["nodes"])))
# 链只有 40 节：上限大于链长时应自然走到 NULL
r = cs.scan_chain(F(m), HEAD, max_nodes=64)
ck("max_nodes=64 > 链长 40 -> stop=null（不误报）", r["stop"] == "null", r["stop"])

# 4) 垃圾 next：超范围 / 低址 / 0
for nxt, want in ((0xFFFFFFF0, "illegal"), (0x00000010, "illegal"), (0, "null")):
    m = chain_map([A], lambda n, v=nxt: v, lambda n: VT)
    r = cs.scan_chain(F(m), HEAD)
    ck("next=0x%08X -> stop=%s" % (nxt, want), r["stop"] == want, r["stop"])

# 5) 链头不可读 / 节点页不可读 / next 槽不可读
r = cs.scan_chain(F({}), HEAD)
ck("head 不可读 -> stop=unreadable 且 head_unreadable",
   r["stop"] == "unreadable" and any(f["kind"] == "head_unreadable" for f in r["findings"]),
   r["stop"])
m = {HEAD: A, A + 0x30: 0}
r = cs.scan_chain(F(m), HEAD)
ck("节点不可读 -> unreadable_node 且不抛",
   any(f["kind"] == "unreadable_node" for f in r["findings"]), r["stop"])

# 6) vptr 三态：小整数 / 堆指针 / 合法 thunk
CASE_HEAP = 0x00180000     # <0x100000 -> "vptr_small_int" 分支；>=0x400000 才叫 heap_ptr
CASE_HEAP2 = 0x00600000    # >=0x400000 且页可读、+0x2C 不是 thunk -> "vptr_heap_ptr"
for vp, want, note in ((0x00000A08, "vptr_small_int", "小整数，解引用不到 +0x2C"),
                       (CASE_HEAP2, "vptr_heap_ptr", ">=0x400000，页可读但 +0x2C 非 thunk"),
                       (CASE_HEAP, "vptr_fake_table", "<0x400000，页可读但 +0x2C 非 thunk"),
                       (VT, None, "合法 vtable（+0x2C = thunk）")):
    m = chain_map([A], lambda n: 0, lambda n: vp)
    if vp in (CASE_HEAP, CASE_HEAP2):
        readable_span(m, vp, 0x100)
        m[vp + 0x2C] = 0x00000014        # 与 W104 S3 同形态：+0x2C 不是 thunk
    if vp == VT:
        readable_span(m, VT, 0x100)
        m[VT + 0x2C] = THUNK
    r = cs.scan_chain(F(m), HEAD)
    kinds = [f["kind"] for f in r["findings"]]
    ok = (want is None and kinds == []) or (want in kinds)
    ck("vptr=0x%08X -> %s（%s）" % (vp, want or "无 finding", note), ok, kinds)

# 7) 判定函数：不在镜像范围内 -> suspect；非法 -> suspect
tpl = bytes(0x1000)
for vp in (0x99999999, 0x00001234, 0xFFFFFFFF):
    v, d = cs.judge_vptr(F({}), tpl, 0x00400000, vp)
    ck("judge_vptr(0x%08X) -> suspect（不抛）" % vp, v == "suspect", (v, d))

print("\n=== summary: %d failure(s) ===" % len(fails))
print("RESULT: %s" % ("GREEN" if not fails else "RED"))
for f in fails:
    print("  FAILED: " + f)
sys.exit(0 if not fails else 1)


