from pehelp import *
# CellClass vtable xref sites (clean alignment) and constructor region
print("=== 0x47bb40..0x47bd90 (ctor/dtor region around vtable xrefs) ===")
for ins in disasm(0x47bb40, 0x260, count=160):
    print("   ", fmt(ins))
