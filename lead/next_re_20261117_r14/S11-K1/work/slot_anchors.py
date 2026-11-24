"""
S11-K1: dump ILocomotion (col_offset=4) vtable slots and disassemble key anchor callsites.
Byte-level (no atlas for discovery). capstone skipdata=True via pehelp.
"""
from pehelp import IMAGE_BASE, rd, u32, disasm, fmt, is_code, section_of

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K1\EVIDENCE\slot_anchors.txt'
lines=[]
def P(s=''):
    lines.append(str(s)); print(s)

VT = {
 'LocomotionClass(base)':0x7EADF4,
 'Drive':0x7E7EB0,
 'Walk':0x7F69F8,
 'Fly':0x7E89F4,
 'Hover':0x7EACFC,
 'Ship':0x7F2D8C,
 'Mech':0x7EDB6C,
 'Rocket':0x7F0B1C,
 'Tunnel':0x7F5A24,
 'Jumpjet':0x7ECD68,
 'Teleport':0x7F5000,
 'DropPod':0x7E8278,
}
names = ['QueryInterface','AddRef','Release','Link_To_Object','Is_Moving','Destination',
 'Head_To_Coord','Can_Enter_Cell','Is_To_Have_Shadow','Draw_Matrix','Shadow_Matrix',
 'Draw_Point','Shadow_Point','Visual_Character','Z_Adjust','Z_Gradient','Process',
 'Move_To','Stop_Moving','Do_Turn','Unlimbo','Tilt_Pitch_AI','Power_On','Power_Off',
 'Is_Powered','Is_Ion_Sensitive','Push','Shove','Force_Track','In_Which_Layer',
 'Force_Immediate_Destination','Force_New_Slope','Is_Moving_Now','Apparent_Speed',
 'Drawing_Code','Can_Fire','Get_Status','Acquire_Hunter_Seeker_Target','Is_Surfacing',
 'Mark_All_Occupation_Bits','Is_Moving_Here','Will_Jump_Tracks','Is_Really_Moving_Now',
 'Stop_Movement_Animation','Lock','Unlock','ILocomotion_B8','Get_Track_Number',
 'Get_Track_Index','Get_Speed_Accum']

P('===== ILocomotion (col_off=4) vtable slots 0..49 =====')
P('slot name                          '+ ' '.join('%-10s'%k[:10] for k in VT))
for i in range(50):
    row='%2d   %-32s' % (i, names[i] if i<len(names) else '?')
    for k,vt in VT.items():
        v=u32(vt+4*i)
        row+=' %08X'%v
    P(row)

P('')
P('===== derived override matrix (slot: value if != base basevalue) =====')
base=[u32(0x7EADF4+4*i) for i in range(50)]
for k,vt in VT.items():
    if k.startswith('Locomotion'): continue
    diffs=[]
    for i in range(50):
        v=u32(vt+4*i)
        if v!=base[i]:
            diffs.append((i,names[i] if i<len(names) else '?',v))
    P('%s: %d overrides' % (k,len(diffs)))
    for i,n,v in diffs:
        if i<32 or n in ('Get_Track_Number','Get_Track_Index','Get_Speed_Accum'):
            P('   slot %2d %-32s %08X' % (i,n,v))

# key anchor callsites
anchors = [
 (0x4DA877, 0x40, '0x4DA877 per-frame dispatch'),
 (0x4D55F0, 0x44, 'FootClass::MoveTo -> Move_To slot17'),
 (0x4D55C0, 0x48, 'FootClass::StopMoving -> Stop_Moving slot18'),
 (0x4D9C10, 0x1C, 'FootClass::Can_Enter_Cell -> slot7'),
]
P('')
P('===== anchor callsite disasm =====')
for a, disp, label in anchors:
    P('--- %s @ %08X (call [reg+%02X]) ---' % (label,a,disp))
    for ins in disasm(a-0x20, 0x60):
        P(fmt(ins))
    P('')

with open(OUT,'w',encoding='utf-8') as f:
    f.write('\n'.join(lines)+'\n')
print('WROTE',OUT)
