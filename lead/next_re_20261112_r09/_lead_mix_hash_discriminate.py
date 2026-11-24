#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 关键判别：引擎查找 MIX 条目时用的到底是哪一种哈希？

两个互相矛盾的既有说法：
  (i)  `ra2forge/mixlib.py:309` 注释称 "MixFileClass lookups are pure CRC32 hits (0x5B44D5)"
  (ii) Lead 亲算的 count-pad CRC 能 5/5 复现零售 id（含 ARTMD.INI → 0x5B47D8D5）

若 (ii) 成立而 ra2forge 用 `crc32` 写条目 id，则引擎应找不到 ra2forge 写的地图 —— 但真机
加载成功。**两者不能同时为真。** 本脚本用 ra2forge 自己生成的包做判别实验。

判别逻辑：
  · 取 `expandmd98.mix`（ra2forge 生成）与地图名 `RA2F_M1.MAP`
  · 算 crc32(UPPER) 与 count-pad 两种 id
  · 看 MIX 索引里实际存在的是哪一个
  · 结论：
      - 若索引里是 crc32 id 而引擎仍能找到 ⇒ 引擎用的是 crc32（或另有名称数据库）
      - 若索引里是 count-pad id ⇒ ra2forge 已用了正确哈希（与 mixlib.py 读到的源码不符）
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
sys.path.insert(0, str(ROOT / "ra2forge"))

CANDIDATE_MIXES = [
    ROOT / "lead" / "next_re_20261112_r08" / "W98_clean" / "out" / "sandbox_game" / "expandmd98.mix",
    ROOT / "ra2youli" / "expandmd98.mix",
]
NAMES = ["RA2F_M1.MAP", "ECH01.MAP", "ECH02.MAP", "ECH03.MAP", "ARTMD.INI", "RULESMD.INI"]


def crc_upper(name: str) -> int:
    return zlib.crc32(name.upper().encode("ascii")) & 0xFFFFFFFF


def engine_hash(name: str) -> int:
    b = name.encode("ascii")
    n = len(b)
    full = (n // 4) * 4
    pre, left = b[:full], b[full:]
    k = len(left)
    if k == 0:
        return zlib.crc32(pre) & 0xFFFFFFFF
    return zlib.crc32(pre + left + bytes([k]) + left[0:1] * (3 - k)) & 0xFFFFFFFF


def read_mix_ids(path: Path):
    """读 MIX 头 + 索引，返回 (flags, count, [ids], 加密?, size)。

    RA2/YR MIX 头是**一个 DWORD**：低 16 位 = flags，**高 16 位 = 文件数**。
    （我第一版把它当成 `<HI` 两段读，得到 count=196608 这种荒谬值 —— 已修正。）
    索引项 = 12 字节 (id, offset, size)。
    """
    data = path.read_bytes()
    if len(data) < 6:
        raise ValueError("too small")
    dw = struct.unpack_from("<I", data, 0)[0]
    flags = dw & 0xFFFF
    count = (dw >> 16) & 0xFFFF
    if count == 0 and len(data) >= 4:
        # 少数变体：额外 2 字节 count
        count = struct.unpack_from("<H", data, 2)[0]
        hdr = 4
    else:
        hdr = 4
    # 高 16 位 flags 有置位 => 索引加密，跳过 80 字节 key block
    enc = (flags & 0x0002) != 0 or (dw & 0x00010000) != 0 and False
    # 实测：加密标志在 flags 的 bit1（值 0x0002），加密时 key block 80 字节
    enc = bool(flags & 0x0002)
    if enc:
        hdr += 80
    ids = []
    for i in range(count):
        off = hdr + i * 12
        if off + 12 > len(data):
            break
        fid = struct.unpack_from("<I", data, off)[0]
        ids.append(fid)
    return flags, count, ids, enc, len(data)


def main():
    print("=" * 96)
    print("判别：引擎 MIX 查找用的是 crc32 还是 count-pad CRC？")
    print("=" * 96)
    for nm in NAMES:
        print(f"  {nm:<14} crc_upper={crc_upper(nm):08X}   count_pad={engine_hash(nm):08X}   "
              f"{'相同' if crc_upper(nm) == engine_hash(nm) else '不同'}")

    for mix in CANDIDATE_MIXES:
        print()
        print("=" * 96)
        print(f"MIX: {mix}")
        print("=" * 96)
        if not mix.is_file():
            print("  （不存在，跳过）")
            continue
        try:
            flags, count, ids, enc, size = read_mix_ids(mix)
        except Exception as e:
            print(f"  读取失败: {e}")
            continue
        print(f"  size={size}  flags=0x{flags:04X}  count={count}  索引加密={enc}")
        idset = set(ids)
        print(f"  {'name':<14}{'crc_upper':>12}{'count_pad':>12}   实际在索引里的是")
        for nm in NAMES:
            a, b = crc_upper(nm), engine_hash(nm)
            found = []
            if a in idset:
                found.append("crc_upper")
            if b in idset:
                found.append("count_pad")
            print(f"  {nm:<14}{a:>12X}{b:>12X}   {found if found else '（无）'}")
        print(f"  索引前 8 个 id: " + " ".join(f"{i:08X}" for i in ids[:8]))


if __name__ == "__main__":
    main()
