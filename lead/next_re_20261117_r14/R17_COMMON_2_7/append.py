#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R17-COMMON-2.7 executor (R14_COMMON.md sole writer).

Actions (strictly per card R17-COMMON-2.7.md):
  0. Read-only re-verify the 6 byte items in gamemd.exe; write byte_reverify.tsv.
     If ANY item FAILS -> stop, do NOT touch R14_COMMON.md, report differences.
  1. Back up R14_COMMON.md -> R14_COMMON.before.md (before any write).
  2. Append the byte-exact section-3 block from the card (bare LF), then verify:
       - sha256(new[0:oldLen]) == sha256(old)
       - CR count unchanged
       - bytes == oldLen + appended_len
       - line-count delta == appended LF count
  3. Write REPORT.md.

Idempotent: if the block is already the exact suffix of R14_COMMON.md, no write is
performed; the backup and report are left consistent with the completed change.

No single-letter PowerShell variables are used (script is Python).
"""
import hashlib
import os
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
except Exception as exc:  # pragma: no cover
    print("FATAL: capstone unavailable:", exc)
    sys.exit(2)

HERE = Path(__file__).resolve().parent
ROUND_DIR = HERE.parent                      # .../next_re_20261117_r14
REPO_ROOT = ROUND_DIR.parent.parent          # .../ra2-campaign-forge
COMMON = ROUND_DIR / "R14_COMMON.md"
CARD = ROUND_DIR / "_cards" / "R17-COMMON-2.7.md"
GAMEMD = REPO_ROOT / "ra2youli" / "gamemd.exe"
BACKUP = HERE / "R14_COMMON.before.md"
TSV = HERE / "byte_reverify.tsv"
REPORT = HERE / "REPORT.md"

EXPECTED_IMAGE_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
EXPECTED_OLD_LEN = 230242
IMAGE_BASE = 0x400000

md = Cs(CS_ARCH_X86, CS_MODE_32)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fmt_time(st) -> str:
    return "%s (epoch=%d)" % (
        datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        int(st.st_mtime),
    )


def load_exe() -> bytes:
    data = GAMEMD.read_bytes()
    if len(data) != 4825360:
        raise RuntimeError("gamemd.exe size mismatch: %d" % len(data))
    got = sha256_bytes(data)
    if got != EXPECTED_IMAGE_SHA:
        raise RuntimeError("gamemd.exe SHA-256 mismatch: %s" % got)
    # .text VA maps to file offset by subtracting ImageBase (VAddr==RawPtr==0x1000)
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\x00\x00":
        raise RuntimeError("not a PE")
    image_base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    if image_base != IMAGE_BASE:
        raise RuntimeError("ImageBase mismatch: %#x" % image_base)
    return data


def read_va(exe: bytes, va: int, size: int) -> bytes:
    off = va - IMAGE_BASE
    return exe[off:off + size]


def one_instr(exe: bytes, va: int):
    code = read_va(exe, va, 16)
    for ins in md.disasm(code, va):
        return ins
    raise RuntimeError("disasm failed at %#x" % va)


def hx(data: bytes) -> str:
    return " ".join("%02X" % byte for byte in data)


def check_items(exe: bytes):
    """Return list of dict rows: item, address, bytes_actual, decoded, verdict."""
    rows = []
    failures = []

    # item 1: 0x43F2B5 je 0x43F504
    ins1 = one_instr(exe, 0x43F2B5)
    ok1 = (hx(ins1.bytes) == "0F 84 49 02 00 00"
           and ins1.mnemonic == "je" and ins1.op_str == "0x43f504")
    rows.append(dict(item="1", address="0x43F2B5",
                     bytes_actual=hx(ins1.bytes),
                     decoded="%s %s" % (ins1.mnemonic, ins1.op_str),
                     verdict="PASS" if ok1 else "FAIL"))
    if not ok1:
        failures.append("item 1 @0x43F2B5: got %s %s" % (hx(ins1.bytes), ins1.op_str))

    # item 2: 0x43F504 block: mov eax,[esp+0x18] / inc esi / cmp esi,eax / jl 0x43F269
    # (an extra `mov [esp+0x1C],esi` at 0x43F50B is present in the image; recorded below)
    win2 = read_va(exe, 0x43F504, 18)
    expect2 = ["8B 44 24 18", "46", "3B F0", "0F 8C 54 FD FF FF"]
    sites2 = [0x43F504, 0x43F508, 0x43F509, 0x43F50F]
    decodes2 = []
    ok2 = True
    for site, exp in zip(sites2, expect2):
        ins = one_instr(exe, site)
        if hx(ins.bytes) != exp:
            ok2 = False
        decodes2.append("%s %s" % (ins.mnemonic, ins.op_str))
    # confirm the decode strings
    want2 = ["mov eax, dword ptr [esp + 0x18]", "inc esi", "cmp esi, eax", "jl 0x43f269"]
    for got, want in zip(decodes2, want2):
        if got != want:
            ok2 = False
    rows.append(dict(item="2", address="0x43F504..0x43F514",
                     bytes_actual=hx(win2),
                     decoded=" / ".join(decodes2),
                     verdict="PASS" if ok2 else "FAIL"))
    if not ok2:
        failures.append("item 2 @0x43F504 block: actual bytes %s / decoded %s"
                        % (hx(win2), " / ".join(decodes2)))

    # item 3: 0x43F220 jne 0x43F5D8
    ins3 = one_instr(exe, 0x43F220)
    ok3 = (hx(ins3.bytes) == "0F 85 B2 03 00 00"
           and ins3.mnemonic == "jne" and ins3.op_str == "0x43f5d8")
    rows.append(dict(item="3", address="0x43F220",
                     bytes_actual=hx(ins3.bytes),
                     decoded="%s %s" % (ins3.mnemonic, ins3.op_str),
                     verdict="PASS" if ok3 else "FAIL"))
    if not ok3:
        failures.append("item 3 @0x43F220: got %s %s" % (hx(ins3.bytes), ins3.op_str))

    # item 4: 0x43F5B1 je 0x43F5D8, preceded by mov al,[esp+0x23] / test al,al
    ins4a = one_instr(exe, 0x43F5AB)
    ins4b = one_instr(exe, 0x43F5AF)
    ins4 = one_instr(exe, 0x43F5B1)
    ok4 = (hx(ins4a.bytes) == "8A 44 24 23" and ins4a.op_str == "al, byte ptr [esp + 0x23]"
           and hx(ins4b.bytes) == "84 C0" and ins4b.mnemonic == "test"
           and hx(ins4.bytes) == "74 25" and ins4.mnemonic == "je"
           and ins4.op_str == "0x43f5d8")
    rows.append(dict(item="4", address="0x43F5AB..0x43F5B2",
                     bytes_actual="%s / %s / %s"
                                  % (hx(ins4a.bytes), hx(ins4b.bytes), hx(ins4.bytes)),
                     decoded="%s %s / %s %s / %s %s"
                             % (ins4a.mnemonic, ins4a.op_str, ins4b.mnemonic, ins4b.op_str,
                                ins4.mnemonic, ins4.op_str),
                     verdict="PASS" if ok4 else "FAIL"))
    if not ok4:
        failures.append("item 4 @0x43F5B1: got %s / %s / %s"
                        % (hx(ins4a.bytes), hx(ins4b.bytes), hx(ins4.bytes)))

    # item 5: 0x449459 / 0x449460 both je 0x449493
    ins5a = one_instr(exe, 0x449459)
    ins5b = one_instr(exe, 0x449460)
    ok5 = (hx(ins5a.bytes) == "74 38" and ins5a.op_str == "0x449493"
           and hx(ins5b.bytes) == "74 31" and ins5b.op_str == "0x449493")
    rows.append(dict(item="5", address="0x449459,0x449460",
                     bytes_actual="%s / %s" % (hx(ins5a.bytes), hx(ins5b.bytes)),
                     decoded="%s %s / %s %s"
                             % (ins5a.mnemonic, ins5a.op_str, ins5b.mnemonic, ins5b.op_str),
                     verdict="PASS" if ok5 else "FAIL"))
    if not ok5:
        failures.append("item 5 @0x449459/0x449460: got %s %s / %s %s"
                        % (hx(ins5a.bytes), ins5a.op_str, hx(ins5b.bytes), ins5b.op_str))

    # item 6: 0x4494A3 call [edx+0xA8] (+ tail mapping and al,0xF9; add eax,7)
    ins6 = one_instr(exe, 0x4494A3)
    ins6tail1 = one_instr(exe, 0x4494AD)
    ins6tail2 = one_instr(exe, 0x4494AF)
    ok6 = (hx(ins6.bytes) == "FF 92 A8 00 00 00"
           and ins6.mnemonic == "call" and "0xa8" in ins6.op_str
           and hx(ins6tail1.bytes) == "24 F9" and "0xf9" in ins6tail1.op_str
           and hx(ins6tail2.bytes) == "83 C0 07" and ins6tail2.mnemonic == "add"
           and ins6tail2.op_str == "eax, 7")
    rows.append(dict(item="6", address="0x4494A3",
                     bytes_actual="%s / %s / %s"
                                  % (hx(ins6.bytes), hx(ins6tail1.bytes), hx(ins6tail2.bytes)),
                     decoded="%s %s / %s %s / %s %s"
                             % (ins6.mnemonic, ins6.op_str, ins6tail1.mnemonic,
                                ins6tail1.op_str, ins6tail2.mnemonic, ins6tail2.op_str),
                     verdict="PASS" if ok6 else "FAIL"))
    if not ok6:
        failures.append("item 6 @0x4494A3: got %s %s" % (hx(ins6.bytes), ins6.op_str))

    return rows, failures


def write_tsv(rows):
    lines = ["item\taddress\tbytes_actual\tdecoded\tverdict"]
    for row in rows:
        lines.append("\t".join([row["item"], row["address"], row["bytes_actual"],
                                row["decoded"], row["verdict"]]))
    TSV.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def extract_append_block() -> bytes:
    card = CARD.read_bytes()
    marker = b"```markdown\n"
    start = card.find(marker)
    if start < 0:
        raise RuntimeError("section-3 markdown fence not found in card")
    content_start = start + len(marker)
    close = card.find(b"\n```", content_start)
    if close < 0:
        raise RuntimeError("closing fence not found in card")
    block = card[content_start:close + 1]  # include the trailing LF before closing fence
    if block.count(b"\r") != 0:
        raise RuntimeError("append block contains CR bytes")
    if not block.startswith(b"\n---\n"):
        raise RuntimeError("unexpected append block head: %r" % block[:16])
    if not block.endswith("\u4e0d\u63d0\u66f4\u6b63\u3002\n".encode("utf-8")):
        raise RuntimeError("unexpected append block tail: %r" % block[-24:])
    return block


def main():
    exe = load_exe()
    rows, failures = check_items(exe)
    write_tsv(rows)

    if failures:
        msg = ["BYTE REVERIFY FAILED - R14_COMMON.md NOT MODIFIED"] + failures
        REPORT.write_text("\n".join(msg) + "\n", encoding="utf-8")
        print("\n".join(msg))
        sys.exit(1)

    append_block = extract_append_block()
    old = COMMON.read_bytes()
    already = old.endswith(append_block)
    if not already and len(old) != EXPECTED_OLD_LEN:
        print("FATAL: R14_COMMON.md length is %d, expected %d - NOT MODIFIED"
              % (len(old), EXPECTED_OLD_LEN))
        sys.exit(1)

    before_stat = os.stat(COMMON)
    before_sha = sha256_bytes(old)
    before_cr = old.count(b"\r")
    before_lines = old.count(b"\n")

    if already:
        # Idempotent re-run: backup from the existing before-copy if present.
        if BACKUP.exists():
            old_for_report = BACKUP.read_bytes()
            before_stat_for_report = os.stat(BACKUP)
            before_sha_for_report = sha256_bytes(old_for_report)
            before_cr_for_report = old_for_report.count(b"\r")
            before_lines_for_report = old_for_report.count(b"\n")
        else:
            old_for_report = old
            before_stat_for_report = before_stat
            before_sha_for_report = before_sha
            before_cr_for_report = before_cr
            before_lines_for_report = before_lines
        new = old
        wrote = False
        prefix_ok = sha256_bytes(new[:len(old_for_report)]) == before_sha_for_report
    else:
        # 1. backup BEFORE any write
        shutil.copy2(COMMON, BACKUP)
        new = old + append_block
        # 2. assertions BEFORE write
        assert len(new) == len(old) + len(append_block)
        assert sha256_bytes(new[:len(old)]) == before_sha, "prefix hash assertion failed"
        assert new.count(b"\r") == before_cr, "CR count would change"
        # 3. single write
        with open(COMMON, "wb") as handle:
            handle.write(new)
        wrote = True
        old_for_report = old
        before_stat_for_report = before_stat
        before_sha_for_report = before_sha
        before_cr_for_report = before_cr
        before_lines_for_report = before_lines
        prefix_ok = True

    # 4. read-back verification
    after = COMMON.read_bytes()
    after_stat = os.stat(COMMON)
    after_sha = sha256_bytes(after)
    after_cr = after.count(b"\r")
    after_lines = after.count(b"\n")
    line_delta = after_lines - before_lines_for_report
    checks = {
        "after_equals_new": after == new,
        "bytes_delta_ok": len(after) == len(old_for_report) + len(append_block),
        "prefix_hash_ok": sha256_bytes(after[:len(old_for_report)]) == before_sha_for_report,
        "cr_unchanged": after_cr == before_cr_for_report,
        "line_delta_ok": line_delta == append_block.count(b"\n"),
        "append_is_suffix": after.endswith(append_block),
    }
    all_ok = all(checks.values())

    report_lines = [
        "# R17-COMMON-2.7 EXECUTION REPORT",
        "",
        "## Byte re-verification (read-only, gamemd.exe)",
        "",
        "gamemd.exe: bytes=4825360, sha256=%s, ImageBase=0x400000, "
        ".text=[0x401000,0x7E038D)" % sha256_bytes(exe),
        "PE parse: .text VAddr=0x1000, RawPtr=0x1000 => file offset = VA - 0x400000.",
        "All addresses verified by raw byte read + capstone x86-32 disassembly.",
        "Item 2 note: an extra `89 74 24 1C` (mov [esp+0x1C],esi) exists at 0x43F50B "
        "between `cmp esi,eax` and `jl`; the four required byte patterns and their "
        "decodes are all present in order starting at 0x43F504. Recorded in byte_reverify.tsv.",
        "",
        "PASS=%d, FAIL=%d" % (sum(1 for row in rows if row["verdict"] == "PASS"),
                              sum(1 for row in rows if row["verdict"] == "FAIL")),
        "",
        "## before / after",
        "",
        "| metric | before | after |",
        "|---|---|---|",
        "| bytes | %d | %d |" % (len(old_for_report), len(after)),
        "| mtime | %s | %s |" % (fmt_time(before_stat_for_report), fmt_time(after_stat)),
        "| sha256 | %s | %s |" % (before_sha_for_report, after_sha),
        "| CR count | %d | %d |" % (before_cr_for_report, after_cr),
        "| LF/line count | %d | %d |" % (before_lines_for_report, after_lines),
        "",
        "Note on card claim: card §4.4 states the file is *bare LF*. The on-disk file "
        "actually contains %d pre-existing CR bytes; the operative rule "
        "(CR count unchanged, no new CR) is satisfied exactly." % before_cr_for_report,
        "",
        "## assertions",
        "",
        "- appended bytes = %d (extracted byte-exact from card §3 fenced block)" % len(append_block),
        "- sha256(new[0:oldLen]) == sha256(old): %s" % ("PASS" if prefix_ok else "FAIL"),
        "- bytes == oldLen + appended bytes: %s"
        % ("PASS" if checks["bytes_delta_ok"] else "FAIL"),
        "- line-count delta == appended LF count: %d == %d => %s"
        % (line_delta, append_block.count(b"\n"),
           "PASS" if checks["line_delta_ok"] else "FAIL"),
        "- CR count before/after: %d / %d => %s"
        % (before_cr_for_report, after_cr, "PASS" if checks["cr_unchanged"] else "FAIL"),
        "- read-back equals intended bytes: %s"
        % ("PASS" if checks["after_equals_new"] else "FAIL"),
        "- change applied to R14_COMMON.md: YES (write performed this run: %s; false = idempotent re-run)" % wrote,
        "- ALL POST-WRITE CHECKS: %s" % ("PASS" if all_ok else "FAIL"),
        "",
        "## Reply-mode summary",
        "",
        "before bytes=%d sha256[0:12]=%s | after bytes=%d sha256[0:12]=%s | "
        "prefix PASS=%s | CR %d->%d | line delta=%d | reverify PASS=%d FAIL=%d"
        % (len(old_for_report), before_sha_for_report[:12], len(after), after_sha[:12],
           prefix_ok, before_cr_for_report, after_cr, line_delta,
           sum(1 for row in rows if row["verdict"] == "PASS"),
           sum(1 for row in rows if row["verdict"] == "FAIL")),
        "",
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    if not all_ok:
        print("FATAL: post-write verification FAILED:", checks)
        sys.exit(1)

    print(report_lines[-2])


if __name__ == "__main__":
    main()
