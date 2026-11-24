import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R

# TD address = name_addr - 8
TD_TARGETS = {
  0x81B2C8: "CampaignScoreClass",
  0x81B488: "CampaignEndScoreClass",
  0x81B7A8: "CarryoverClass",
  0x83E2D8-8: "ScorePrintClass",
  0x83E2F8-8: "ScoreTimeClass",
}
# scan all image dwords for value == TD target (COL+0xC) -> COL = addr-0xC
data=R.BIN.pe.__data__
def va2off(va):
    for s in R.BIN.sections:
        if s["va"]<=va<s["va"]+s["rawsize"]:
            return s["raw"]+(va-s["va"])
    return None

def va_of_off(off):
    for s in R.BIN.sections:
        if s["raw"]<=off<s["raw"]+s["rawsize"]:
            return s["va"]+(off-s["raw"])
    return None

for td, name in TD_TARGETS.items():
    print(f"\n=== {name} TD={td:08X} ===")
    needle=struct.pack("<I",td)
    start=0
    cols=[]
    while True:
        i=data.find(needle,start)
        if i<0: break
        va=va_of_off(i)
        if va is not None:
            cols.append(va-0xC)  # potential COL
        start=i+1
    for col in cols:
        try:
            sig=R.u32(col); off=R.u32(col+4); cd=R.u32(col+8); tdv=R.u32(col+0xC)
            print(f"  COL {col:08X}: sig={sig:08X} off={off:08X} cd={cd:08X} td={tdv:08X}")
        except Exception as e:
            print(f"  COL {col:08X}: ERR {e}")
