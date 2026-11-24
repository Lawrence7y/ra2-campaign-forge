# _vev_fp.py — 独立复核员自算 11 件指纹（只读，hashlib）
import hashlib, os

BASE = r"D:\Project\ra2-campaign-forge"
ITEMS = [
    ("lead/s604_script_hunt_20261109/S604_SCRIPT_HUNT.md",
     "f607b404c3b39f758d6f4c9bf54ed361d38d4d36bfae587748f5a112ec1a192c", 27347),
    ("lead/s604_script_hunt_20261109/_sh_generator_512655.txt",
     "6dd66437b63700b2e780ed5d4c9e53e7939a0a11f904936b97a6b855892122fa", 13188),
    ("lead/s604_script_hunt_20261109/_sh_gen512655_out.txt",
     "cf74264071463777e55a10111b6768ff528328bb43d203da001886be6fda9256", 1247),
    ("lead/s604_script_hunt_20261109/_sh_gen512655_payload.py",
     "a6ad4afe73494ac5510a73cfefeded36070c4b56f1a851e13d6b52148f611b9d", 1641),
    ("lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md",
     "823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c", 30536),
    ("lead/s604_attribution_20261108/S604_ATTRIBUTION.md",
     "8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182),
    ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
     "593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740", 20271),
    ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
     "724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719),
    ("lead/slowframe_r3_20261108/S604_GAP_RECHECK.md",
     "5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726", 19291),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

n_match = 0
for rel, esha, ebytes in ITEMS:
    p = os.path.join(BASE, rel)
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
            n += len(c)
    gsha, gbytes = h.hexdigest(), n
    ok = "MATCH" if (gsha == esha and gbytes == ebytes) else "MISMATCH"
    if ok == "MATCH":
        n_match += 1
    print(ok + "\t" + rel)
    print("  got=" + gsha + "/" + str(gbytes))
    print("  exp=" + esha + "/" + str(ebytes))
print("SUMMARY: " + str(n_match) + "/" + str(len(ITEMS)) + " MATCH")
print("DONE")
