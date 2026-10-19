import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\tools")
from re_gap_spysat_deep import read_bytes

for a in [0x81a98c, 0x81a978, 0x81a960, 0x81a94c, 0x82ad48]:
    s = read_bytes(a, 32).split(b'\0')[0].decode('ascii', 'ignore')
    print(f"0x{a:08X}: \"{s}\"")
