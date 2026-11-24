#!/usr/bin/env python3
"""W125: same-length text editor for an entry inside an encrypted-header MIX.

Why "same-length": the engine rejects any expandmd01.mix whose total size changed
(4 variants tested, all BLOCKED). Same-length edits are accepted (4 variants, all VALID).
So this tool only performs in-place, equal-length replacements.

Read-only by default; --apply writes. Always verifies by re-reading.

Usage:
  python w125_mixedit.py <mix> --list
  python w125_mixedit.py <mix> --show 0x8218F9F4 --find "[105mm]"
  python w125_mixedit.py <mix> --show 0x8218F9F4 --replace "ROF=60" "ROF=99" --apply
"""
import argparse, struct, sys, os, shutil, hashlib

sys.path.insert(0, r"D:\Project\ra2-campaign-forge")
from ra2forge import mixlib


def read_header(raw):
    if not (struct.unpack_from("<H", raw, 2)[0] & 2):
        raise SystemExit("not an encrypted-header MIX (flags&2 == 0); this tool targets those")
    key = mixlib.westwood_decrypt_key_block(raw[4:84])
    fish = mixlib.Blowfish(key)
    pt8 = fish.decrypt(raw[84:92])
    n = struct.unpack_from("<H", pt8, 0)[0]
    blocks = (13 + n * 12) // 8
    pt = fish.decrypt(raw[84:84 + blocks * 8])
    size_field = struct.unpack_from("<I", pt, 2)[0]
    ents = [list(struct.unpack_from("<III", pt, 6 + i * 12)) for i in range(n)]
    data_start = 84 + blocks * 8
    return dict(n=n, size_field=size_field, ents=ents, data_start=data_start, blocks=blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mix")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--show", help="entry id in hex, e.g. 0x8218F9F4")
    ap.add_argument("--find", help="text to locate (optional context marker)")
    ap.add_argument("--replace", nargs=2, metavar=("OLD", "NEW"))
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    raw = bytearray(open(a.mix, "rb").read())
    h = read_header(bytes(raw))
    print("entries=%d  data_start=%d  size_field=%d  filesize=%d"
          % (h["n"], h["data_start"], h["size_field"], len(raw)))
    maxend = max(o + s for _, o, s in h["ents"])
    print("check size_field == max(offset+size)+9 : %s (%d vs %d)"
          % (h["size_field"] == maxend + 9, h["size_field"], maxend + 9))

    if a.list:
        for hid, off, size in sorted(h["ents"], key=lambda e: e[1]):
            print("  id=0x%08X  offset=%-9d size=%-8d align4=%s" % (hid, off, size, off % 4 == 0))
        return 0

    if not a.show or not a.replace:
        if a.show:
            hid = int(a.show, 16)
            ent = next((e for e in h["ents"] if e[0] == hid), None)
            if not ent:
                raise SystemExit("id not found")
            st = h["data_start"] + ent[1]
            body = bytes(raw[st:st + ent[2]])
            if a.find:
                k = body.find(a.find.encode("latin1"))
                print("anchor at %d; context: %r" % (k, body[max(0, k - 30):k + 60]))
            else:
                print("size=%d head=%r" % (len(body), body[:80]))
        return 0

    hid = int(a.show, 16)
    old, new = a.replace[0].encode("latin1"), a.replace[1].encode("latin1")
    if len(old) != len(new):
        raise SystemExit("REFUSED: replacement must be SAME LENGTH (%d vs %d bytes). "
                         "Size changes break the archive." % (len(old), len(new)))
    ent = next((e for e in h["ents"] if e[0] == hid), None)
    if not ent:
        raise SystemExit("id not found")
    st = h["data_start"] + ent[1]
    body = bytes(raw[st:st + ent[2]])
    if a.find:
        base = body.find(a.find.encode("latin1"))
        if base < 0:
            raise SystemExit("--find anchor not present")
    else:
        base = 0
    k = body.find(old, base)
    if k < 0:
        raise SystemExit("OLD text not found after anchor")
    if body.find(old, k + 1) >= 0:
        print("WARN: OLD occurs more than once; patching the first occurrence at %d" % k)
    newbody = body[:k] + new + body[k + len(old):]
    assert len(newbody) == len(body)
    nb = bytearray(raw)
    nb[st:st + ent[2]] = newbody
    assert len(nb) == len(raw), "size changed - aborting"

    print("patched id=0x%08X at body offset %d : %r -> %r" % (hid, k, old, new))
    print("file size unchanged: %s" % (len(nb) == len(raw)))
    # verify by re-reading through mixlib
    tmp = a.mix + ".w125tmp"
    open(tmp, "wb").write(bytes(nb))
    A, B = mixlib.MixFile(a.mix), mixlib.MixFile(tmp)
    ida = {e.id: e for e in A.entries}
    idb = {e.id: e for e in B.entries}
    assert set(ida) == set(idb), "id set changed"
    diff = [x for x in ida if A.read_entry(ida[x]) != B.read_entry(idb[x])]
    print("entries differing: %s (expect exactly one)" % [hex(x) for x in diff])
    A.close(); B.close()
    if len(diff) != 1:
        os.remove(tmp)
        raise SystemExit("verification failed - not applied")
    if not a.apply:
        os.remove(tmp)
        print("dry-run OK (use --apply to write)")
        return 0
    bak = a.mix + ".bak_w125"
    if not os.path.exists(bak):
        shutil.copy2(a.mix, bak)
        print("backup: %s" % bak)
    shutil.move(tmp, a.mix)
    print("APPLIED. restore with: copy '%s' '%s'" % (bak, a.mix))
    print("sha256 now: %s" % hashlib.sha256(open(a.mix, "rb").read()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())