# -*- coding: utf-8 -*-
"""RC-4 触发归因：把 30 个崩溃站点映射到宿主函数。

目的：判定每个宿主是否有 E8 调用者 / 是否在虚表 / 是否有立即数引用。
若某个宿主三者皆无，则它只能经运行期计算的间接分发到达 ⇒
「尾部窗口内再命中一次」取决于运行期状态，不是每帧必发 —— 这是 18% 的结构性来源。

只读磁盘，零真机。

口径注意（本件踩过的坑）：
  - SectionHeader.VirtualAddress 是 RVA，必须加镜像基数才是真实 VA。
  - 函数头检测要取「离站点最近的终结指令之后」，不能取最远的
    （否则窗口会跨到上一个函数）。
  - 有些函数（如 0x4A8960）没有标准 ret 收尾，用本法会返回 None，
    这类站点归入「?」，不影响「三无」判定。
"""
import io
import struct
import sys

import capstone

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

SITES = [
    0x004A8B75, 0x00640427, 0x00654413, 0x00654469, 0x006AC00B, 0x006AC03E,
    0x006AC0ED, 0x006AC140, 0x006AC193, 0x006AC1E6, 0x006D059B, 0x006D0619,
    0x006D0634, 0x006D0664, 0x006D089D, 0x006D08B3, 0x006D0940, 0x006D09FA,
    0x006D1293, 0x006D1308, 0x006D137E, 0x006D13F3, 0x006D1541, 0x006D155C,
    0x006D15CB, 0x006D1605, 0x006D1632, 0x006D16C2, 0x006D16DD, 0x006D1744,
]

# 文档记载的宿主函数与站点数（raw/06_sites_chain.txt L38）
DOC_HOSTS = {
    0x006ABD30: 6, 0x006D1200: 6, 0x006D04F0: 4, 0x006D0680: 3,
    0x006D1660: 3, 0x00654320: 2,
}


def load():
    data = io.open(GAMEMD, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 0x34)[0]
    sec_off = pe + 24 + opt_size
    secs = []
    for i in range(nsec):
        o = sec_off + i * 40
        name = data[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
        vsize, va, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        secs.append({"name": name, "vsize": vsize, "va": base + va,
                     "rsize": rsize, "roff": roff})
    return data, base, secs


def read_slice(data, secs, va, n):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
            off = s["roff"] + (va - s["va"])
            return data[off:off + n]
    return None


def find_func_start(data, secs, site, max_back=0x600):
    """找离 site 最近的终结指令（ret/int3）之后的第一条非填充指令。"""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    start_limit = site - max_back
    chunk = read_slice(data, secs, start_limit, max_back)
    if chunk is None:
        return None
    insns = list(md.disasm(chunk, start_limit))
    if not insns:
        return None
    last_term_idx = None
    for i, ins in enumerate(insns):
        if ins.address >= site:
            break
        if ins.mnemonic in ("ret", "retf", "int3"):
            last_term_idx = i
    if last_term_idx is None:
        return None
    for ins in insns[last_term_idx + 1:]:
        if ins.mnemonic in ("nop", "int3"):
            continue
        if ins.address >= site:
            return None
        return ins.address
    return None


def disasm_at(data, secs, va, n=64):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    chunk = read_slice(data, secs, va, n)
    if not chunk:
        return []
    return list(md.disasm(chunk, va))


def e8_callers(data, secs, target):
    text = next(s for s in secs if s["name"] == ".text")
    tb = data[text["roff"]:text["roff"] + text["rsize"]]
    tva = text["va"]
    out = []
    i = 0
    while True:
        j = tb.find(b"\xe8", i)
        if j < 0 or j + 5 > len(tb):
            break
        rel = struct.unpack_from("<i", tb, j + 1)[0]
        if (tva + j + 5 + rel) & 0xFFFFFFFF == target:
            out.append(tva + j)
        i = j + 1
    return out


def imm_refs(data, secs, target, base):
    """全镜像找该地址的立即数引用，VA 与 RVA 两种编码都查。"""
    hits = []
    for s in secs:
        buf = data[s["roff"]:s["roff"] + s["rsize"]]
        for kind, val in (("VA", target), ("RVA", target - base)):
            pat = struct.pack("<I", val)
            i = 0
            while True:
                j = buf.find(pat, i)
                if j < 0:
                    break
                if j % 4 == 0:
                    hits.append((kind, s["name"], s["va"] + j))
                i = j + 1
    return hits


def main():
    data, base, secs = load()
    print("镜像基数 0x%08X" % base)
    print()
    print("%-12s %-12s %s" % ("站点 VA", "宿主函数", "宿主首条指令"))
    print("-" * 72)

    hosts = {}
    for site in SITES:
        host = find_func_start(data, secs, site)
        hosts.setdefault(host, []).append(site)
        head = disasm_at(data, secs, host, 8) if host else []
        head_s = " ; ".join("%s %s" % (i.mnemonic, i.op_str) for i in head[:2])
        print("%-12s %-12s %s"
              % ("0x%08X" % site,
                 ("0x%08X" % host) if host else "? (无标准 ret 边界)",
                 head_s[:44]))

    print()
    print("=== 宿主函数汇总（三无判定）===")
    print("%-12s %-8s %-8s %-8s %-8s %s"
          % ("宿主", "站点数", "E8调用", "立即数", "文档", "结论"))
    orphan_sites = 0
    orphan_hosts = 0
    for h, sites in sorted(hosts.items(), key=lambda kv: (kv[0] or 0)):
        if h is None:
            print("  %-12s %-8d %-8s %-8s %-8s %s"
                  % ("?", len(sites), "-", "-", "-", "未判定（边界法失效）"))
            continue
        n_e8 = len(e8_callers(data, secs, h))
        n_imm = len(imm_refs(data, secs, h, base))
        doc = DOC_HOSTS.get(h)
        if n_e8 == 0 and n_imm == 0:
            verdict = "★ 三无 ⇒ 只能间接分发"
            orphan_hosts += 1
            orphan_sites += len(sites)
        else:
            verdict = ""
        print("  %-12s %-8d %-8d %-8d %-8s %s"
              % ("0x%08X" % h, len(sites), n_e8, n_imm,
                 ("%d" % doc) if doc else "-", verdict))

    print()
    print("站点总数 = %d，宿主数 = %d"
          % (sum(len(v) for v in hosts.values()), len(hosts)))
    print("★ 三无宿主 = %d 个，覆盖站点 %d 个（%.1f%%）"
          % (orphan_hosts, orphan_sites, orphan_sites * 100.0 / len(SITES)))


if __name__ == "__main__":
    sys.exit(main())
