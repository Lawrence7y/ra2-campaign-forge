import sys
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
for s in sys.argv[1:]:
 a=int(s,16)
 print(hex(a),'cov',cov.get(f'{a:08X}'),'atl',atl.get(f'{a:08X}'.lower()),'class',common.class_at_slot(a))
