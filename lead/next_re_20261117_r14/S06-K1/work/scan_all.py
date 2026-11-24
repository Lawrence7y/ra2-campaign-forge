from pehelp import *
for nm in [b'.?AVCellClass@@', b'.?AVMapClass@@', b'CellClass', b'MapClass']:
    print(f"=== search {nm} whole file ===")
    data = pe.__data__
    idx = data.find(nm)
    cnt = 0
    while idx != -1 and cnt < 20:
        print(f"  fileoff {idx:#x}")
        idx = data.find(nm, idx+1); cnt += 1
    print("  count:", cnt)
