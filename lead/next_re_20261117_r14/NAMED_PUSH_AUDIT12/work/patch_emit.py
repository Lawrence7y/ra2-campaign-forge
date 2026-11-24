import io

p = "emit.py"
s = open(p, encoding="utf-8").read()

sec_block = '''SEC_VT = {
 "006C5210":[(0x007E88B4,0x004C9920,"+4"),(0x007E88AC,0x004C9926,"+8"),(0x007E88A4,0x004C992D,"+0xC")],
 "006C5390":[(0x007F6B14,0x0075D0C1,"+4"),(0x007F6B0C,0x0075D0C7,"+8"),(0x007F6B04,0x0075D0CE,"+0xC")],
 "006C5510":[(0x007F739C,0x00771E7D,"+4"),(0x007F7394,0x00771E83,"+8"),(0x007F738C,0x00771E8A,"+0xC")],
 "006C5690":[(0x007EF938,0x0062BC50,"+4"),(0x007EF930,0x0062BC57,"+8"),(0x007EF928,0x0062BC5E,"+0xC")],
 "006C5810":[(0x007F016C,0x00644CFA,"+4"),(0x007F0164,0x00644D01,"+8"),(0x007F015C,0x00644D08,"+0xC")],
 "006C5990":[(0x007EFB80,0x0062DFAC,"+4"),(0x007EFB78,0x0062DFB3,"+8"),(0x007EFB70,0x0062DFBA,"+0xC")],
 "006C5B10":[(0x007F008C,0x006441A2,"+4"),(0x007F0084,0x006441A8,"+8"),(0x007F007C,0x006441AF,"+0xC")],
 "006C5C90":[(0x007E2A34,0x0041E407,"+4"),(0x007E2A2C,0x0041E40E,"+8"),(0x007E2A24,0x0041E415,"+0xC")],
 "006C5E10":[(0x007E3DD4,0x0043A37B,"+4"),(0x007E3DCC,0x0043A382,"+8"),(0x007E3DC4,0x0043A389,"+0xC")],
 "006C5F90":[(0x007E8B1C,0x004D090F,"+4"),(0x007E8B14,0x004D0916,"+8"),(0x007E8B0C,0x004D091D,"+0xC")],
 "006C6110":[(0x007E3288,0x00420B16,"+4"),(0x007E3280,0x00420B1D,"+8"),(0x007E3278,0x00420B24,"+0xC")],
}
SECTION_NAME = {'''

assert 'SECTION_NAME = {' in s
s = s.replace('SECTION_NAME = {', sec_block, 1)

a1 = '"006C5690":"主表 `007EF954` 只有 1 张表（无 +4 副表），第 4 列未声称为多表对象，无冲突",'
b1 = '"006C5690":"同类 4 表（+0/+4/+8/+0xC），主表写点 `0062BC4A`；第 4 列只写主表，未混入副表",'
assert a1 in s
s = s.replace(a1, b1, 1)

a2 = '"006C5E10":"NeuronClass 体最小（new 0x38、ctor 仅 4 条写表），第 4 列「分配构造」措辞与字节一致",'
b2 = '"006C5E10":"NeuronClass 实为 4 表对象（写点 `0043A375`–`0043A389`），非「单表小类」；第 4 列只引主表，无冲突",'
assert a2 in s
s = s.replace(a2, b2, 1)

anchor = '    lines.append(f"| ④ 使用见证 |'
assert anchor in s
insert = ('    sec = "；".join(f"{d_} `{v:08X}`@`{a:08X}` slot0=`{im.u32(v):08X}`" for v, a, d_ in SEC_VT[e])\n'
          '    lines.append(f"| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `{pvt:08X}`（slot0=`{im.u32(pvt):08X}`）；副表 {sec} ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |")\n'
          + anchor)
s = s.replace(anchor, insert, 1)

open(p, "w", encoding="utf-8").write(s)
print("patched ok")
