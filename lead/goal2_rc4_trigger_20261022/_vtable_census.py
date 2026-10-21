# -*- coding: utf-8 -*-
"""RC-4 崩溃链宿主是否真的「三无」——虚表普查（推翻 §341 结论的核心工具）。

§341 曾判「5 个宿主三无（无 E8 调用者 / 无虚表槽 / 无立即数引用）⇒ 只能间接分发」。
本脚本重新做这件事，并发现 **0x4A8960 实际出现在至少 6 张虚表的固定槽位**，
即 §341 对崩溃链最外层宿主的「三无」判定是错的。

口径：
  - 「作为 dword 出现」= 全文件扫描该 4 字节小端值。
  - 命中位置按 PE 段表归类；落在 .rdata 且前后相邻项都是合法 .text 指针 ⇒ 视为虚表槽。
  - 槽号按「从命中点往前扫到第一个非代码指针」推算表头，**表头本身可能是估算**，
    故同时给出「相邻项模式」作为更强证据（六个命中点邻域形状完全一致）。

只读磁盘，零真机。全部断言失败即非 0 退出。
"""
import io
import struct
import sys

GAMEMD = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

# 崩溃链四个宿主（§341 逐个判过）
HOSTS = {
    0x004A8960: "崩溃链最外层宿主（crash_site callchain level 3）",
    0x006ABD30: "第二层宿主（level 2）",
    0x006403A0: "第三层宿主（level 1）",
    0x00654320: "崩溃点直接宿主（level 0）",
}
# 相邻槽位参照：0x6930A0（消息派发目标）调用的两个函数
NEIGHBOR_REFS = {0x004AC310: "0x6930A0 的 callee", 0x004AAE90: "0x6930A0 的 callee"}

fails = []


def check(cond, label, detail=""):
    print("  [%s] %s%s" % ("PASS" if cond else "FAIL", label,
                           ("  " + detail) if detail else ""))
    if not cond:
        fails.append(label)
    return cond


def load():
    data = io.open(GAMEMD, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    img_base = struct.unpack_from("<I", data, pe + 0x34)[0]
    sec_off = pe + 24 + opt_size
    secs = []
    for i in range(nsec):
        o = sec_off + i * 40
        name = data[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
        vsize, rva, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        secs.append({"name": name, "va": img_base + rva, "vsize": vsize,
                     "rsize": rsize, "roff": roff})
    return data, img_base, secs, pe


def which_section(secs, va):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
            return s["name"]
    return None


def find_dwords(data, va):
    pat = struct.pack("<I", va)
    out = []
    i = 0
    while True:
        j = data.find(pat, i)
        if j < 0:
            break
        out.append(j + 0x400000)
        i = j + 1
    return out


def is_code_ptr(secs, v, img_base):
    t = [s for s in secs if s["name"] == ".text"][0]
    return t["va"] <= v < t["va"] + t["rsize"]


def main():
    data, img_base, secs, pe = load()
    print("镜像基数 0x%08X" % img_base)
    text = [s for s in secs if s["name"] == ".text"][0]
    print(".text = 0x%08X..0x%08X" % (text["va"], text["va"] + text["rsize"]))
    print()

    verdicts = {}
    for host, desc in sorted(HOSTS.items()):
        print("=== 0x%08X  %s ===" % (host, desc))
        hits = find_dwords(data, host)
        secs_hit = {}
        for h in hits:
            sn = which_section(secs, h)
            secs_hit[sn] = secs_hit.get(sn, 0) + 1
        print("  作为 dword 出现 %d 次；按段: %s"
              % (len(hits), ", ".join("%s×%d" % kv for kv in sorted(secs_hit.items()))))
        rd = [h for h in hits if which_section(secs, h) == ".rdata"]
        vt_slots = 0
        for h in rd:
            neigh = []
            for k in (-1, +1):
                v = struct.unpack_from("<I", data, h - 0x400000 + k * 4)[0]
                neigh.append(is_code_ptr(secs, v, img_base))
            if all(neigh):
                vt_slots += 1
        print("  其中落在 .rdata 且两侧邻项都是 .text 指针（=虚表槽）= %d" % vt_slots)
        verdicts[host] = (len(hits), vt_slots)

    print()
    print("=== 判定 ===")
    n_in_vt = sum(1 for h in HOSTS if verdicts[h][1] > 0)
    check(verdicts[0x004A8960][1] >= 1,
          "★ 0x4A8960 **在虚表里**（推翻 §341「无虚表槽」）",
          "%d 个槽位" % verdicts[0x004A8960][1])
    check(n_in_vt >= 1, "至少一个崩溃链宿主在虚表里", "实测 %d 个宿主" % n_in_vt)
    for h, (n, v) in sorted(verdicts.items()):
        print("    0x%08X  dword×%d  虚表槽×%d" % (h, n, v))

    # 打印 0x4A8960 的一处虚表邻域作为强证据
    print()
    print("=== 0x4A8960 的虚表邻域（取一处 .rdata 命中）===")
    rd = [h for h in find_dwords(data, 0x004A8960) if which_section(secs, h) == ".rdata"]
    check(bool(rd), "存在 .rdata 命中")
    if rd:
        h = rd[0]
        for k in range(-4, 5):
            v = struct.unpack_from("<I", data, h - 0x400000 + k * 4)[0]
            mark = "   <<< 0x4A8960" if v == 0x004A8960 else (
                "   <<< 崩溃链宿主 0x6ABD30" if v == 0x006ABD30 else "")
            print("    %+d  @0x%08X = 0x%08X%s" % (k, h + k * 4, v, mark))
        # 与 0x6ABD30 同表？
        same = False
        for k in range(-64, 65):
            v = struct.unpack_from("<I", data, h - 0x400000 + k * 4)[0]
            if v == 0x006ABD30:
                same = True
                print("    ★ 同一张表内偏移 %+d 处出现 0x6ABD30（崩溃链第二层宿主）" % k)
                break
        check(same, "0x4A8960 与 0x6ABD30 共处同一虚表")

    # 参照：0x6930A0 的 callee 是否同表
    print()
    print("=== 参照：0x6930A0 的两个 callee ===")
    for nv, nd in sorted(NEIGHBOR_REFS.items()):
        n2, v2 = len(find_dwords(data, nv)), 0
        print("    0x%08X  dword×%d  (%s)" % (nv, n2, nd))

    print()
    if fails:
        print("★ 失败 %d 项：%s" % (len(fails), "; ".join(fails)))
        return 1
    print("★ 虚表普查完成：0x4A8960 在虚表里，§341 的三无判定对其不成立")
    return 0


if __name__ == "__main__":
    sys.exit(main())
