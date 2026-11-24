"""LZO1X-1 compression/decompression — faithful port of minilzo 2.06
(via WorldAlteringEditor's MiniLZO.cs, itself a port by zzattack).

Used by Tiberian Sun / Red Alert 2 / Yuri's Revenge for [IsoMapPack5] and
[PreviewPack]. The compressor is byte-compatible with lzo1x_1_compress; the
decompressor implements the standard lzo1x stream format and is validated
against real game data.
"""

from __future__ import annotations


def _ctz32(v: int) -> int:
    return (v & -v).bit_length() - 1


def _u32(buf, i: int) -> int:
    return buf[i] | (buf[i + 1] << 8) | (buf[i + 2] << 16) | (buf[i + 3] << 24)


def _lzo1x_1_compress_core(inb, base: int, ll: int, out: bytearray, ti: int) -> int:
    """Compress inb[base:base+ll] appending to out. Returns the tail count."""
    ip_end = base + ll - 20
    ii = base
    ip = base + (4 - ti if ti < 4 else 0)
    dict_ = [0] * (1 << 14)

    while True:
        # literal:
        ip += 1 + ((ip - ii) >> 5)
        # next:
        done = False
        while True:
            if ip >= ip_end:
                done = True
                break
            dv = _u32(inb, ip)
            dindex = ((0x1824429D * dv) >> 18) & 0x3FFF
            m_pos = dict_[dindex]
            dict_[dindex] = ip - base
            if dv == _u32(inb, m_pos):
                break
            ip += 1 + ((ip - ii) >> 5)  # goto literal
        if done:
            break

        # match found at ip, candidate at m_pos
        ii -= ti
        ti = 0
        t = ip - ii
        if t != 0:
            if t <= 3:
                out[-2] |= t
                out += inb[ii:ii + t]
            elif t <= 18:
                out.append(t - 3)
                out += inb[ii:ii + t]
            else:
                tt = t - 18
                out.append(0)
                while tt > 255:
                    tt -= 255
                    out.append(0)
                out.append(tt)
                out += inb[ii:ii + t]

        # match length
        m_len = 4
        v = _u32(inb, ip + m_len) ^ _u32(inb, m_pos + m_len)
        if v == 0:
            while True:
                m_len += 4
                if ip + m_len >= ip_end:
                    break
                v = _u32(inb, ip + m_len) ^ _u32(inb, m_pos + m_len)
                if v != 0:
                    m_len += _ctz32(v) // 8
                    break
        else:
            m_len += _ctz32(v) // 8

        m_off = ip - m_pos
        ip += m_len
        ii = ip
        if m_len <= 8 and m_off <= 0x0800:
            m_off -= 1
            out.append(((m_len - 1) << 5) | ((m_off & 7) << 2))
            out.append(m_off >> 3)
        elif m_off <= 0x4000:
            m_off -= 1
            if m_len <= 33:
                out.append(32 | (m_len - 2))
            else:
                m_len -= 33
                out.append(32)
                while m_len > 255:
                    m_len -= 255
                    out.append(0)
                out.append(m_len)
            out.append((m_off << 2) & 0xFF)
            out.append((m_off >> 6) & 0xFF)
        else:
            m_off -= 0x4000
            if m_len <= 9:
                out.append(16 | ((m_off >> 11) & 8) | (m_len - 2))
            else:
                m_len -= 9
                out.append(16 | ((m_off >> 11) & 8))
                while m_len > 255:
                    m_len -= 255
                    out.append(0)
                out.append(m_len)
            out.append((m_off << 2) & 0xFF)
            out.append((m_off >> 6) & 0xFF)

    return (base + ll) - (ii - ti)


def lzo1x_1_compress(data: bytes) -> bytes:
    """lzo1x_1_compress — byte-compatible compressor."""
    out = bytearray()
    in_len = len(data)
    ip = 0
    l = in_len
    t = 0
    while l > 20:
        ll = min(l, 49152)
        # minilzo overflow-check idiom: break to tail when (t+ll) < 32
        if ((t + ll) >> 5) == 0:
            break
        t = _lzo1x_1_compress_core(data, ip, ll, out, t)
        ip += ll
        l -= ll
    t += l
    if t > 0:
        ii = in_len - t
        if len(out) == 0 and t <= 238:
            out.append(17 + t)
        elif t <= 3:
            out[-2] |= t
        elif t <= 18:
            out.append(t - 3)
        else:
            tt = t - 18
            out.append(0)
            while tt > 255:
                tt -= 255
                out.append(0)
            out.append(tt)
        out += data[ii:ii + t]
    out += bytes((16 | 1, 0, 0))
    return bytes(out)


def lzo1x_decompress(data: bytes) -> bytes:
    """Standard lzo1x decompressor; returns the decompressed bytes."""
    out = bytearray()
    n = len(data)
    ip = 0

    def copy_match(m_pos: int, count: int):
        """Copy `count` bytes from out[m_pos] (byte-by-byte: overlap-safe)."""
        src = m_pos
        for _ in range(count):
            out.append(out[src])
            src += 1

    # preamble
    if data[0] > 17:
        t = data[0] - 17
        ip = 1
        if t < 4:
            out += data[ip:ip + t]
            ip += t
            t = data[ip]
            ip += 1
            # goto match
            match_t = t
            first_literal = False
        else:
            out += data[ip:ip + t]
            ip += t
            match_t = None
            first_literal = True
    else:
        match_t = None
        first_literal = False

    while True:
        if not first_literal and match_t is None:
            t = data[ip]
            ip += 1
            if t >= 16:
                match_t = t
            else:
                if t == 0:
                    while data[ip] == 0:
                        t += 255
                        ip += 1
                    t += 15 + data[ip]
                    ip += 1
                run = t + 3
                out += data[ip:ip + run]
                ip += run
                first_literal = True
                continue
        elif first_literal:
            first_literal = False
            t = data[ip]
            ip += 1
            if t < 16:
                # M1 with 0x800 base: 3-byte copy
                m_pos = len(out) - (1 + 0x0800) - (t >> 2) - (data[ip] << 2)
                ip += 1
                copy_match(m_pos, 3)
                # match_done
                t = data[ip - 2] & 3
                if t == 0:
                    continue
                out += data[ip:ip + t]
                ip += t
                match_t = data[ip]
                ip += 1
                # fall through to match loop
            else:
                match_t = t

        # match do-while
        while True:
            t = match_t
            if t >= 64:
                m_pos = len(out) - 1 - ((t >> 2) & 7) - (data[ip] << 3)
                ip += 1
                length = (t >> 5) - 1 + 2
                copy_match(m_pos, length)
            elif t >= 32:
                tt = t & 31
                if tt == 0:
                    while data[ip] == 0:
                        tt += 255
                        ip += 1
                    tt += 31 + data[ip]
                    ip += 1
                m_pos = len(out) - 1 - ((data[ip] | (data[ip + 1] << 8)) >> 2)
                ip += 2
                copy_match(m_pos, tt + 2)
            elif t >= 16:
                tt = t & 7
                m_pos = len(out) - ((t & 8) << 11)
                if tt == 0:
                    while data[ip] == 0:
                        tt += 255
                        ip += 1
                    tt += 7 + data[ip]
                    ip += 1
                m_pos -= (data[ip] | (data[ip + 1] << 8)) >> 2
                ip += 2
                if m_pos == len(out):
                    return bytes(out)  # EOF marker
                m_pos -= 0x4000
                copy_match(m_pos, tt + 2)
            else:
                m_pos = len(out) - 1 - (t >> 2) - (data[ip] << 2)
                ip += 1
                copy_match(m_pos, 2)

            # match_done: literal count packed in discarded low bits
            t = data[ip - 2] & 3
            if t == 0:
                match_t = None
                break
            out += data[ip:ip + t]
            ip += t
            match_t = data[ip]
            ip += 1
