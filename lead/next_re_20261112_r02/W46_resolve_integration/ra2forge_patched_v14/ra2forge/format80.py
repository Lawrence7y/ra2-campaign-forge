"""Format80 (a.k.a. Format5 / WSA codec) — used by TS/RA2 [OverlayPack] and
[OverlayDataPack]. Encoder/decoder ported from WorldAlteringEditor's
Format80.cs (itself from OpenRA), plus a matching decoder for validation.
"""

from __future__ import annotations


def decode(src: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(src)
    while i < n:
        code = src[i]
        i += 1
        if code & 0x80 == 0:
            # command 0 (0cccpppp p): relative copy
            count = (code >> 4) + 3
            back = ((code & 0xF) << 8) + src[i]
            i += 1
            start = len(out) - back
            for k in range(count):
                out.append(out[start + k])
        else:
            count = code & 0x3F
            if code & 0x40 == 0:
                if count == 0:
                    break  # end of stream
                # command 1 (10cccccc): verbatim copy
                out += src[i:i + count]
                i += count
            else:
                if count < 0x3E:
                    # command 2 (11cccccc p p): absolute-position copy
                    count += 3
                    pos = src[i] | (src[i + 1] << 8)
                    i += 2
                    for k in range(count):
                        out.append(out[pos + k])
                elif count == 0x3E:
                    # command 3 (11111110 c c v): fill
                    count = src[i] | (src[i + 1] << 8)
                    i += 2
                    value = src[i]
                    i += 1
                    out += bytes([value]) * count
                else:
                    # command 4 (11111111 c c p p): long copy
                    count = src[i] | (src[i + 1] << 8)
                    i += 2
                    pos = src[i] | (src[i + 1] << 8)
                    i += 2
                    for k in range(count):
                        out.append(out[pos + k])
    return bytes(out)


def _count_same(src: bytes, offset: int, max_count: int) -> int:
    max_count = min(len(src) - offset, max_count)
    if max_count <= 0:
        return 0
    first = src[offset]
    count = 1
    while count < max_count and src[offset + count] == first:
        count += 1
    return count


def _write_copy_blocks(out: bytearray, src: bytes, offset: int, count: int):
    while count > 0:
        write_now = min(count, 0x3F)
        out.append(0x80 | write_now)
        out += src[offset:offset + write_now]
        count -= write_now
        offset += write_now


def encode(src: bytes) -> bytes:
    """Quick-and-dirty Format80 encoder (raw copy + RLE), as in WAE."""
    out = bytearray()
    offset = 0
    length = len(src)
    block_start = 0
    while offset < length:
        repeat = _count_same(src, offset, 0xFFFF)
        if repeat >= 4:
            _write_copy_blocks(out, src, block_start, offset - block_start)
            # command 3: fill
            out.append(0xFE)
            out.append(repeat & 0xFF)
            out.append(repeat >> 8)
            out.append(src[offset])
            offset += repeat
            block_start = offset
        else:
            offset += 1
    _write_copy_blocks(out, src, block_start, offset - block_start)
    out.append(0x80)  # terminator
    return bytes(out)
