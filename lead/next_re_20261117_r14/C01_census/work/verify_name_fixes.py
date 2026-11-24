"""Verify the 24 name corrections against the audit's expected values."""
import os, json
HERE=os.path.dirname(os.path.abspath(__file__))
yrpp=json.load(open(os.path.join(HERE,'yrpp_names.json'),encoding='utf-8'))
y={int(k):v for k,v in yrpp.items()}
# expected from audit s3_out.txt (verified by reading YRpp headers above)
exp={
 0x4011C0:'AudioIDXData::Create',0x401580:'AudioIDXData::~AudioIDXData',
 0x4015C0:'AudioIDXData::FindSampleIndex',0x401640:'AudioIDXData::GetSampleInformation',
 0x401910:'AudioIDXData::ClearCurrentSample',
 0x405C00:'AudioController::~AudioController',0x405D40:'AudioController::DTOR_1',
 0x405FD0:'AudioController::DTOR_2',0x406060:'AudioController::ShutUp',
 0x4060F0:'AudioController::sub_4060F0',0x406130:'AudioController::sub_406130',
 0x406170:'AudioController::sub_406170',0x4061D0:'AudioController::sub_4061D0',
 0x406270:'AudioController::sub_406270',0x406310:'AudioController::sub_406310',
 0x407B60:'AudioStream::PlayWAV',0x408610:'Audio::ReadWAVFile',
 0x40E320:'GenericNode::GenericNode',
 0x42E6F0:'BaseClass::BaseClass',0x42F380:'BaseClass::FailedToPlaceNode',
 0x4385D0:'BombClass::BombClass',
 0x438BF0:'BombListClass::Update',0x438E70:'BombListClass::Plant',
 0x439080:'BombListClass::AddDetector',0x4390D0:'BombListClass::RemoveDetector',
 0x439150:'BombListClass::PointerGotInvalid',
 0x4397E0:'BounceClass::Initialize',0x4399A0:'BounceClass::GetCoords',
 0x4399E0:'BounceClass::GetDrawingMatrix',0x439B00:'BounceClass::Update',
}
ok=0; bad=[]
for a,e in sorted(exp.items()):
    got=[r['full'] for r in y.get(a,[])]
    hit = e in got
    print('%08X expect=%-38s got=%s %s'%(a,e,got[:2],'OK' if hit else 'MISMATCH'))
    if hit: ok+=1
    else: bad.append((a,e,got))
print('\nMATCH %d/%d'%(ok,len(exp)))
if bad:
    print('MISMATCHES:')
    for a,e,g in bad: print('  %08X exp=%s got=%s'%(a,e,g))
