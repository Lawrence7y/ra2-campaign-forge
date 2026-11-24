"""Self-check: consolidate 4-ring status for the 8 card rows from the self-written EVIDENCE.
Produces EVIDENCE/final8.json and prints a summary. Read-only on exe.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))

HERE = os.path.dirname(__file__)
EV = os.path.join(HERE, "..", "EVIDENCE")
rtti = json.load(open(os.path.join(EV,"rtti_all_tables.json"),encoding="utf-8"))
sites = json.load(open(os.path.join(EV,"direct_sites_card8.json"),encoding="utf-8"))["targets"]

# decision table (from THREE_B_DETERMINATION.md, manually adjudicated)
DEC = {
 "00431F70": {"name":"BufferIOFileClass::vslot7","ring2":"BufferIOFileClass (single vt 7E3A2C/slot7)",
              "ring3":"3b1","ring4":"direct","four":True,"disp":"delta"},
 "00432050": {"name":"BufferIOFileClass::vslot12","ring2":"base BufferIOFileClass (2 tables slot12: 7E1668/CDFile + 7E3A2C/BufferIO)",
              "ring3":"3b4","ring4":"direct","four":True,"disp":"delta"},
 "004322A0": {"name":"BufferIOFileClass::vslot9","ring2":"base BufferIOFileClass (2 tables slot9: 7E1668/CDFile + 7E3A2C/BufferIO)",
              "ring3":"3b4","ring4":"direct","four":True,"disp":"delta"},
 "0047AE10": {"name":"CDFileClass::slot2","ring2":"CDFileClass (single vt 7E1668/slot2)",
              "ring3":"3b4","ring4":"direct","four":True,"disp":"delta"},
 "0065CDD0": {"name":"RawFileClass::slot12","ring2":"RawFileClass (single vt 7F0904/slot12)",
              "ring3":"3b2+3b1","ring4":"direct","four":True,"disp":"delta"},
 "0065D0D0": {"name":"RawFileClass::slot11","ring2":"RawFileClass (single vt 7F0904/slot11)",
              "ring3":"3b2","ring4":"direct","four":True,"disp":"delta"},
 "0065D190": {"name":"RawFileClass::slot4","ring2":"base RawFileClass (4 tables slot4: 7E1668/CD + 7E16B0/CC + 7E3A2C/BIO + 7F0904/Raw)",
              "ring3":"3b1+3b2","ring4":"direct","four":True,"disp":"delta"},
 "0065D240": {"name":"RawFileClass::slot15","ring2":"base RawFileClass (3 tables slot15: 7E1668/CD + 7E3A2C/BIO + 7F0904/Raw)",
              "ring3":"3a (3 gates converge to same ret)","ring4":"direct","four":False,"disp":"UNKNOWNS U1"},
}
out = {}
for e,d in DEC.items():
    r = rtti[e]; s = sites[e]
    out[e] = dict(d,
        n_rtti_occ=r["n_occ"], n_rtti_pairs=len(r["pairs"]), rtti_slots=r["slots"],
        rtti_classes=r["classes"], multi_same_slot=r["multi_table_same_slot"],
        ring4_n=s["n"], ring4_agree=s["agree"], ring4_sites=s["kept_A"])
    print("%s %-24s 2:%d pairs 4:%d sites agree=%s four=%s %s" % (
        e,d["name"],len(r["pairs"]),s["n"],s["agree"],d["four"],d["disp"]))

n_four = sum(1 for d in DEC.values() if d["four"])
n_delta = sum(1 for d in DEC.values() if d["disp"]=="delta")
print("four-ring count =", n_four, " delta rows =", n_delta,
      " consistent =", (n_four==n_delta))
json.dump({"rows":out,"four_ring_count":n_four,"delta_rows":n_delta},
          open(os.path.join(EV,"final8.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
print("wrote EVIDENCE/final8.json")
