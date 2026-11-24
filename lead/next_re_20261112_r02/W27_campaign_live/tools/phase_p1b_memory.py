#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · P1b read-only engine battle-list memory dump (one serial instance).

Locates the ASCII "RA2F1" address via a bounded read-only memory scan, then
dumps a few KB around it (hex+ASCII) plus the neighbourhood of every
"MISSING:" UTF-16LE string. Goal: establish whether the appended campaign is
in the engine's parsed battle list, and what its resolved Description is.
No writes of any kind; closes own instance and restores configs at end.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402


def dump(hproc, addr, size, sink, label):
    b = L.rpm_partial(hproc, addr, size)
    if not b:
        sink.step("dump_failed", label=label, addr=hex(addr))
        return None
    lines = []
    for off in range(0, len(b), 16):
        chunk = b[off:off + 16]
        hx = " ".join("%02x" % x for x in chunk)
        asc = "".join(chr(x) if 32 <= x < 127 else "." for x in chunk)
        u16 = "".join(chr(chunk[i]) if 32 <= chunk[i] < 127 else "."
                      for i in range(0, 16, 2))
        lines.append("%08x  %-47s  %-16s %s" % (addr + off, hx, asc, u16))
    sink.step("memory_dump", label=label, addr=hex(addr), size=size,
              lines=lines)
    return b


def main():
    sink = L.Sink("p1b_memory")
    pid = hwnd = hproc = None
    try:
        pre = L.list_gamemd()
        sink.step("pre_launch_guard", gamemd_processes=pre, n=len(pre))
        if pre:
            raise RuntimeError("residual gamemd before launch; STOP per card")
        launcher = L.launch_game(sink)
        pid = L.wait_for_pid(launcher, sink)
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            hwnd = L.game_hwnd(pid)
            if hwnd:
                break
            time.sleep(1.0)
        hproc = L.open_proc(pid)
        # wait for main menu
        t0 = time.monotonic()
        while time.monotonic() - t0 < 120:
            if L.find_btn(pid, "GUI:SinglePlayer"):
                break
            time.sleep(2.0)
        sink.step("main_menu", controls=[c["text"] for c in L.controls(pid)
                                         if c["visible"] and c["text"]])

        r = L.memory_search(hproc, ["RA2F1", "W27LIVE", "MISSING:",
                                    "DESC:ALL1", "DESC:SOV1", "ECH01.MAP"],
                            sink, "locate")

        # ---- engine global Battle table (documented in
        # docs/re/fs_mix_load_chain_deep.md §2.3): base 0xA83CF8,
        # Count 0xA83D08, elements 0x3A0 bytes, name at +0x24 ----
        dump(hproc, 0x00A83CF8, 64, sink, "battle_table_header")
        cb = L.rpm(hproc, 0x00A83D08, 4)
        count = int.from_bytes(cb, "little") if cb else None
        sink.step("battle_table_count", count=count, addr="0xA83D08")
        hb = L.rpm_partial(hproc, 0x00A83CF8, 16)
        if hb:
            ptr = int.from_bytes(hb[:8], "little")
            sink.step("battle_table_pointer", ptr=hex(ptr),
                      plausible=bool(0x10000 < ptr < 0x7FFFFFFF))
            if 0x10000 < ptr < 0x7FFFFFFF and count and count < 100:
                for stride in (4, 8, 0x3A0):
                    rows = []
                    for i in range(min(count, 40)):
                        a = ptr + i * stride
                        e = L.rpm_partial(hproc, a, 0x60)
                        if not e:
                            rows.append({"i": i, "addr": hex(a), "read": False})
                            continue
                        s = "".join(chr(x) if 32 <= x < 127 else "."
                                    for x in e)
                        rows.append({"i": i, "addr": hex(a),
                                     "hex": e[:0x40].hex(),
                                     "ascii": s})
                    sink.step("battle_table_try", stride=stride, rows=rows)
        # find first RA2F1 ascii hit address
        samples = r["hits"]["RA2F1|ascii"]["samples"]
        if samples:
            a = int(samples[0]["addr"], 16)
            dump(hproc, a - 512, 2048, sink, "around_RA2F1")
        ms = r["hits"]["MISSING:|utf16le"]["samples"]
        for i, s in enumerate(ms[:6]):
            a = int(s["addr"], 16)
            dump(hproc, a - 64, 256, sink, "missing_%d" % i)
        # also dump around our W27LIVE utf16 hit
        ws = r["hits"]["W27LIVE|utf16le"]["samples"]
        for i, s in enumerate(ws[:2]):
            a = int(s["addr"], 16)
            dump(hproc, a - 96, 320, sink, "w27live_%d" % i)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-4000:])
    finally:
        try:
            if hproc:
                L.k32.CloseHandle(hproc)
        except Exception:
            pass
        try:
            L.close_game(pid, hwnd, sink)
        except Exception as e:
            sink.step("close_error", error=repr(e))
        try:
            L.restore_configs(sink)
        except Exception as e:
            sink.step("restore_error", error=repr(e))
        try:
            sink.step("p1b_done", gamemd_residual=L.list_gamemd())
        except Exception:
            pass
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
