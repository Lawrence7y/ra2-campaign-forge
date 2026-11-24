#!/usr/bin/env python3
"""W131i: aggregate the field census into per-class / per-subsystem layouts.

Outputs
  field_layout_classes.tsv      class, offset, reads, writes, width
  field_layout_subsystems.tsv   subsystem, offset, reads, writes, width
  FIELD_LAYOUT.md               human-readable top fields per entity, with the
                                evidence (how many methods touch each offset)
The point of milestone (4): a subsystem's "关键结构条目" should be the offsets the
code actually touches, ranked by how many independent methods touch them -- not a
guess from names.
"""
import collections
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    rows = []
    pat = re.compile(r"FieldLayout\.java> ([^\t]+)\t(0x[0-9a-f]+)\t(\d+)\t(\d+)\t(\S+)")
    for ln in io.open(os.path.join(HERE, "fieldlayout.raw.log"), encoding="utf-8",
                      errors="replace").read().splitlines():
        m = pat.search(ln)
        if not m:
            continue
        rows.append((m.group(1), int(m.group(2), 16), int(m.group(3)),
                     int(m.group(4)), m.group(5)))
    print("field rows: %d" % len(rows))

    by_ent = collections.defaultdict(list)
    for ent, off, r, w, wd in rows:
        by_ent[ent].append((off, r, w, wd))

    def dump(prefix, path):
        ents = sorted(e for e in by_ent if e.startswith(prefix))
        with io.open(path, "w", encoding="utf-8") as f:
            f.write("entity\toffset\treads\twrites\ttouch\twidth\n")
            for e in ents:
                for off, r, w, wd in sorted(by_ent[e]):
                    f.write("%s\t0x%X\t%d\t%d\t%d\t%s\n"
                            % (e, off, r, w, r + w, wd))
        return ents

    cls = dump(".?AV", os.path.join(HERE, "field_layout_classes.tsv"))
    subs = dump("SUB:", os.path.join(HERE, "field_layout_subsystems.tsv"))
    print("classes: %d   subsystems: %d" % (len(cls), len(subs)))

    # ---------- human-readable ----------
    md = ["# 关键结构条目（milestone 4）", "",
          "每个对象的字段按\"被多少个方法触碰\"排序（touch = reads + writes）。",
          "来源：反编译后统计 `this` 相对偏移的访问；read/write 由赋值方向判定。",
          "**这不是猜测的字段名，而是代码真实访问过的偏移。**", ""]

    def section(entity, title, cap=14):
        lst = by_ent.get(entity)
        if not lst:
            return
        tot = sum(x[1] + x[2] for x in lst)
        offs = len(lst)
        md.append("## %s" % title)
        md.append("")
        md.append("偏移数 **%d**，总访问 **%d** 次。最常被触碰的 %d 个：" % (offs, tot, min(cap, offs)))
        md.append("")
        md.append("| 偏移 | 读 | 写 | 触碰 | 宽度 |")
        md.append("|---|---:|---:|---:|---|")
        for off, r, w, wd in sorted(lst, key=lambda x: -(x[1] + x[2]))[:cap]:
            md.append("| `+0x%X` | %d | %d | **%d** | %s |" % (off, r, w, r + w, wd))
        md.append("")

    md.append("# 一、按类")
    md.append("")
    for c in [".?AVTechnoClass@@", ".?AVObjectClass@@", ".?AVBuildingClass@@",
              ".?AVAbstractClass@@", ".?AVHouseClass@@", ".?AVCellClass@@",
              ".?AVMapClass@@", ".?AVLocomotionClass@@", ".?AVBSurface@@",
              ".?AVGadgetClass@@", ".?AVCCToolTip@@", ".?AVConnectionClass@@"]:
        section(c, "`%s`" % c)
    md.append("# 二、按子系统（该子系统最大函数所触碰的偏移）")
    md.append("")
    for s in ["SUB:GameObj_Logic", "SUB:UI_Gadget_Dialog", "SUB:Ini_Rules_DB",
              "SUB:Net_Transport", "SUB:Scenario_Map", "SUB:Movement_Locomotion",
              "SUB:Graphics_Blit_Shape", "SUB:File_Mix_FS", "SUB:AI_Team_Script",
              "SUB:SaveLoad", "SUB:Audio_Sound_Music", "SUB:Sidebar_Radar_HUD"]:
        section(s, "`%s`" % s.replace("SUB:", ""))

    open(os.path.join(HERE, "FIELD_LAYOUT.md"), "w", encoding="utf-8").write("\n".join(md))
    print("\nwrote field_layout_classes.tsv / field_layout_subsystems.tsv / FIELD_LAYOUT.md")

    # quick console digest: densest classes
    print("\n=== densest layouts (classes) ===")
    for c in cls:
        lst = by_ent[c]
        print("  %-28s offsets=%-4d accesses=%-6d"
              % (c, len(lst), sum(x[1] + x[2] for x in lst)))


if __name__ == "__main__":
    main()
