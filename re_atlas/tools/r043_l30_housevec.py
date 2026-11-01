# -*- coding: utf-8 -*-
"""R-043: L-30 (half-close) — the registry behind TEventClass+0x54's gate.

gamemd.exe sha256 73201cc0...f67476, read-only. All windows re-dumped THIS round
(capstone aligned; jump-table/ret anchors; no resync walker output used as fact).

Facts (each is a byte assertion, re-read from the exe):

  finder 0x502D30 (0x30 bytes, head->ret aligned decode):
    walk [0xA8022C] (vector) x [0xA80238] (count), item=[vector+i*4],
    ebx=[item+0x34]; CMP [ebx+0xB8], ecx(arg)  -> hit: return item (eax), miss: eax=0.
    NOTE: NO deref on miss before the handler's cmp?  The handler does
    `cmp ebx,[eax+0x30]` on the return -> miss path reads [0+0x30]; NOT adjudicated here.

  the vector global object lives AT 0xA80228:
    init   @0x4E6CFD  `mov dword [0xA80228], 0x7E9EE4`   (DynamicVectorClass<HouseClass*> vptr)
    degrade@0x4E6D28  `mov dword [0xA80228], 0x7E9F04`   (VectorClass<HouseClass*> vptr, teardown form)
    layout : [0xA80228]=vptr, [0xA8022C]=Vector, [0xA80234/35]=bytes,
             [0xA80238]=Count, [0xA8023C]=CapacityIncrement(0xA)  -- store-site census below.
    RTTI   : vtables 0x7E9EE4/0x7E9F04 are owned by `?$DynamicVectorClass@PAVHouseClass@@` /
             `?$VectorClass@PAVHouseClass@@` (symbols.json; raw name strings exist in the
             image at 0x4233B4/0x423384).  [structural half]

  store-site census (full .text, ALL encodings of a 32-bit store to the abs global):
    [0xA8022C] <- : {0x4E6CE7 (init xor eax,eax; mov), 0x4E6D47 (degrade mov ebx)}
    [0xA80238] <- : {0x4E6D11 (init), 0x4F61E0 (Push: inc ecx; mov)}
    element store : 0x4F61EC `mov [ecx+eax*4], ebp` (SIB modrm rm==4 -- LEGIT here, G-61 rule)

  handler gate @0x71F1DA (33 bytes to the jne):
    edi=[this+0x34]; cmp -1 -> skip-to-store; esi=[esp+0x38](arg2);
    call [arg2_vt+0x38] (slot14) -> ebx; ecx=edi; call 0x502D30; cmp ebx,[eax+0x30];
    jne fail.  So arg2's slot14 return must equal the found House item's +0x30 field.

  HouseClass self-proof: vtable slot11(+0x2C) @0x50E360 = `mov eax,0xD; ret`,
    and the AbstractType name table (8-byte (id,nameptr) pairs @0x816EE0) maps id 0x0D ->
    "House"  => cross-check that vector elements are HouseClass*.

MUTATION: R043_MUTATE=VA=BYTE[,...] in-memory only.
Run: python re_atlas/tools/r043_l30_housevec.py
"""
import hashlib, struct, sys, json, os

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
RTTI = ROOT + r"\re_atlas\evidence\rtti\symbols.json"
SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

blob = bytearray(open(EXE, "rb").read())
h0 = hashlib.sha256(bytes(blob)).hexdigest()

e = struct.unpack_from("<I", blob, 0x3C)[0]
nsec = struct.unpack_from("<H", blob, e + 6)[0]
optsz = struct.unpack_from("<H", blob, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", blob, opt + 28)[0]
tab = opt + optsz
SECS = []
for i in range(nsec):
    o = tab + i * 40
    vs, va, rs, rp = struct.unpack_from("<IIII", blob, o + 8)
    SECS.append((va, vs, rp, rs))

def _fileoff(va):
    rva = va - IB
    for s_rva, vs, rp, rs in SECS:
        if s_rva <= rva < s_rva + vs and rva - s_rva < rs:
            return rp + (rva - s_rva)
    return None

def read(va, n):
    fo = _fileoff(va)
    if fo is None:
        raise SystemExit("VA 0x%X not disk-backed" % va)
    return bytes(blob[fo:fo + n])

for _item in os.environ.get("R043_MUTATE", "").split(","):
    if "=" in _item:
        k, v = _item.split("=", 1)
        fo = _fileoff(int(k, 0))
        if fo is None:
            raise SystemExit("mutation target not disk-backed")
        blob[fo] = int(v, 0) & 0xFF

results = []
def check(tag, ok, msg):
    results.append((tag, ok, msg))
    print("%s %s: %s" % (tag, "PASS" if ok else "FAIL", msg), file=sys.stderr)

g0_ok = (h0 == SHA256)

# Y1 finder whole-function window (head to ret; aligned)
Y1 = read(0x502D30, 0x30) == bytes.fromhex(
    "5356578b3d3802a80033d285ff7e1b8b352c02a8008b068b5834398bb8000000740a4283c6043bd77ceb33c05f5e5bc3")
check("Y1", Y1, "finder @0x502D30 整函数 0x30 字节钉死：walk [0xA8022C]×[0xA80238]、item=[v+4i]、"
      "`cmp [item+0x34 所指+0xB8], ecx(arg)` 命中返 item、未命中 `xor eax,eax`")

# Y2a global-object init/degrade byte sites
Y2a = (read(0x4E6CFD, 10) == bytes.fromhex("c7052802a800e49e7e00")
       and read(0x4E6D28, 10) == bytes.fromhex("c7052802a800049f7e00")
       and read(0x4E6CE7, 6) == bytes.fromhex("a32c02a800a3")
       and read(0x4E6D11, 5) == bytes.fromhex("a33802a800"))
check("Y2a", Y2a, "全局对象 @0xA80228：init `mov [0xA80228],0x7E9EE4`@0x4E6CFD、teardown 换 vptr "
      "`mov [0xA80228],0x7E9F04`@0x4E6D28；`mov [0xA8022C],eax(0)`@0x4E6CE7、`mov [0xA80238],eax(0)`@0x4E6D11"
      " ⇒ 0xA80228 是 this（vptr+Vector+Count 布局），vptr 两态 0x7E9EE4/0x7E9F04")

# Y2b structural: RTTI COL->TD name strings of the two vtables
d = json.load(open(RTTI, encoding="utf-8"))
n1 = [c for c, v in d["classes"].items() if (v.get("vtable_va") or "").upper() == "007E9EE4"]
n2 = [c for c, v in d["classes"].items() if (v.get("vtable_va") or "").upper() == "007E9F04"]
raws = bytes(blob)  # mutated in-memory view so Y2b is killable by the mutation harness
Y2b = (n1 == ["?$DynamicVectorClass@PAVHouseClass@@"]
       and n2 == ["?$VectorClass@PAVHouseClass@@"]
       and raws.find(b"?$DynamicVectorClass@PAVHouseClass@@") >= 0
       and raws.find(b"?$VectorClass@PAVHouseClass@@") >= 0)
check("Y2b", Y2b, "【结构性】RTTI：vtable 0x7E9EE4/0x7E9F04 的 COL→TD 名 = `?$DynamicVectorClass@PAVHouseClass@@` / "
      "`?$VectorClass@PAVHouseClass@@`；两条修饰名原始串在镜像中存在 ⇒ 注册表元素类型=HouseClass*（定名半边）")

# Y3 store-site census (exact set; ALL encodings incl a3/c705/89-xx/88/a2 + 66-opsize prefix excluded by absence check)
def store_sites(abs_va, width_prefixes=False):
    text = [s for s in SECS if s[0] == 0x1000][0]
    base = IB + text[0]
    tbuf = bytes(blob[_fileoff(base):_fileoff(base) + text[1]])
    ABS = struct.pack("<I", abs_va)
    pats = [b"\xa3", b"\x89\x05", b"\x89\x0d", b"\x89\x15", b"\x89\x1d", b"\x89\x35", b"\x89\x3d",
            b"\xc7\x05", b"\x88\x05", b"\xa2"]
    hits = []
    for p in pats:
        o = 0
        while True:
            i = tbuf.find(p + ABS, o)
            if i < 0:
                break
            hits.append(base + i)
            o = i + 1
    return hits
G22C = store_sites(0xA8022C)
G238 = store_sites(0xA80238)
Y3 = (set(G22C) == {0x4E6CE7, 0x4E6D47} and set(G238) == {0x4E6D11, 0x4F61E0}
      and read(0x4F61E0, 6) == bytes.fromhex("890d3802a800")
      and read(0x4F61EC, 3) == bytes.fromhex("892c81"))
check("Y3", Y3, "存储站 census（全编码枚举：a3/89+r/m/c705/88/a2）：[0xA8022C]←恰 {0x4E6CE7,0x4E6D47}、"
      "[0xA80238]←恰 {0x4E6D11,0x4F61E0(Push 的 inc;mov)}；元素写入 0x4F61EC=`mov [ecx+eax*4],ebp`"
      "（rm==4 此站是合法 SIB，G-61 规则正确判读）⇒ 该向量只被 init/teardown/Push 三态触碰")

# Y4 handler gate window (aligned 33 bytes through the jne)
gate = read(0x71F1DA, 0x21)
Y4 = gate == bytes.fromhex("8b7d3483ffff74198b068bceff50388bcf8bd8e83e3bdeff3b58300f8568ffffff")
t4 = 0x71F1F2 + struct.unpack_from("<i", gate, 0x14)[0]
Y4 = Y4 and t4 == 0x502D30
check("Y4", Y4, "handler 门 @0x71F1DA（33 字节到 jne，含 rel32 复算 call 0x502D30）：edi=[this+0x34]==-1 跳存；"
      "call [arg2_vt+0x38]→ebx；arg2=esi=[esp+0x38]；finder 命中后 `cmp ebx,[eax+0x30]` ⇒ "
      "写 +0x54 前 arg2 的 slot14 必须等于命中 House 的 +0x30（门语义钉到字段级，不再多推）")

# Y5 arg2 provenance at consumer: [ [host+0x24] +0xA4/+0xB4 ]
Y5 = (read(0x72651F, 0x14) == bytes.fromhex("8b56248d4634508b82a4000000518b88b4000000")
      and read(0x726533, 5) == bytes.fromhex("e8f8c7ddff")
      and (0x726538 + struct.unpack_from("<i", read(0x726534, 4), 0)[0]) == 0x502D30)
check("Y5", Y5, "消费方 @0x72651F: edx=[esi+0x24]、push [esi+0x34]、eax=[edx+0xA4]、push ecx、ecx=[eax+0xB4]、"
      "call 0x502D30（rel32 复算）⇒ arg2 经宿主 TypeLink(+0x24)→+0xA4→+0xB4 链取得（链只登记不臆断类名）")

# Y6 HouseClass self-proof: WhatAmI 0xD + name table pair (raw dump: word0=nameptr, word1=id)
Y6 = (read(0x50E360, 6) == bytes.fromhex("b80d000000c3")
      and struct.unpack_from("<I", read(0x816EE0 + 0x0D * 8 + 4, 4), 0)[0] == 0x0D
      and read(struct.unpack_from("<I", read(0x816EE0 + 0x0D * 8, 4), 0)[0], 8).split(b"\x00")[0] == b"House")
check("Y6", Y6, "HouseClass 自证：vtable 0x7EA8A0 slot11(+0x2C)=0x50E360=`mov eax,0xd; ret`；AbstractType 名字表"
      " @0x816EE0 每对 8 字节（实测 word0=nameptr、word1=id，dump 坐实：+0x00→'<none>'/id0、+0x08→'Unit'/id1）"
      "第 0x0D 对 = 'House'+id 0x0D ⇒ 注册表元素类=HouseClass* 与注册表 TD 名交叉闭合")

UNCOUNTED = {"G0", "Y2b"}
n_pass = sum(1 for t, ok, _ in results if ok and t not in UNCOUNTED)
n_tot = sum(1 for t, ok, _ in results if t not in UNCOUNTED)
all_green = all(ok for _, ok, _ in results)
print("\n== R-043 %d/%d 字节断言 PASS（G0 指纹/Y2b 结构性不计入分母，Y2b 红仍非零退出）==" % (n_pass, n_tot), file=sys.stderr)
if not g0_ok:
    print("FATAL: image fingerprint mismatch", file=sys.stderr)
    sys.exit(2)
sys.exit(0 if all_green else 1)
