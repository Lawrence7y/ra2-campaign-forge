"""Verify all required FIX-round corrections landed in coverage_delta.tsv."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..')); TAB=chr(9)
lines=open(os.path.join(BASE,'coverage_delta.tsv'),encoding='utf-8').read().splitlines()[1:]
d={}
for ln in lines:
    p=ln.split(TAB); d[p[0].lower()]=p
exp_names={
 '004011c0':'AudioIDXData::Create','00401580':'AudioIDXData::~AudioIDXData',
 '004015c0':'AudioIDXData::FindSampleIndex','00401640':'AudioIDXData::GetSampleInformation',
 '00401910':'AudioIDXData::ClearCurrentSample',
 '00405c00':'AudioController::~AudioController','00405d40':'AudioController::DTOR_1',
 '00405fd0':'AudioController::DTOR_2','00406060':'AudioController::ShutUp',
 '00407b60':'AudioStream::PlayWAV','00408610':'Audio::ReadWAVFile',
 '0040e320':'GenericNode::GenericNode',
 '0042e6f0':'BaseClass::BaseClass','0042f380':'BaseClass::FailedToPlaceNode',
 '004385d0':'BombClass::BombClass',
 '00438bf0':'BombListClass::Update','00438e70':'BombListClass::Plant',
 '00439080':'BombListClass::AddDetector','004390d0':'BombListClass::RemoveDetector',
 '00439150':'BombListClass::PointerGotInvalid',
 '004397e0':'BounceClass::Initialize','004399a0':'BounceClass::GetCoords',
 '004399e0':'BounceClass::GetDrawingMatrix','00439b00':'BounceClass::Update',
}
exp_down={'004060f0','00406130','00406170','004061d0','00406270','00406310'}
ok=bad=0
for a,e in sorted(exp_names.items()):
    got=d.get(a,['','',''])[2]
    hit=(got==e)
    print('%s exp=%-38s got=%-38s %s'%(a,e,got,'OK' if hit else 'MISMATCH'))
    ok+=hit; bad+=(not hit)
print('\nname fixes: %d/%d OK'%(ok,len(exp_names)))
print('\n=== 6 downgrades ===')
for a in sorted(exp_down):
    p=d.get(a,[]); print('%s name=%-38s grade=%s'%(a,p[2] if p else '-',p[4] if p else '-'))
print('\n=== [已证] count ===', sum(1 for p in d.values() if p[4]=='[已证]'))
