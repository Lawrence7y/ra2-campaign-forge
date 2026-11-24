from pathlib import Path
import hashlib
import re

base = Path('D:/Project/ra2-campaign-forge/lead/direction_ruling_20261108')
old = (base / '_dr_RULING.md').read_bytes()
doc = (base / 'RULING_DIRECTION.md').read_bytes()
text = doc.decode('utf-8')
expected = 'c6fa7a0a3315cdc95bd71916c40c4b565f5066ee2c51ad239d01db5977330316'
checks = {
    'old_fingerprint_match': hashlib.sha256(old).hexdigest() == expected and len(old) == 20942,
    'six_sections': re.findall(r'^## ([1-6])(?: |$)', text, re.M) == list('123456'),
    'required_terms': all(t in text for t in ['Q1','Q2','Q3','Q4','Q5','Q6','裁定','依据','下一步','待裁']),
    'forbidden_literals_absent': all(t not in text.lower() for t in ['game' + 'md.exe', 'ra2' + 'loader', 'task' + 'kill']),
    'partial_unconfirmed_recorded': 'partial' in text and 'unconfirmed' in text,
}
lines = ['COMMAND: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/direction_ruling_20261108/_delivery_check.py']
for name, data in [('_dr_RULING.md', old), ('RULING_DIRECTION.md', doc)]:
    lines += [name, f'被核对象 SHA256 = {hashlib.sha256(data).hexdigest()}，字节数 = {len(data)}']
lines += [f'{key} = {value}' for key, value in checks.items()]
lines += ['SCOPE: delivery structure and fingerprint only; upstream checks NOT RUN.', f'EXIT={0 if all(checks.values()) else 1}']
output = '\n'.join(lines) + '\n'
(base / '_delivery_check_stdout.txt').write_text(output, encoding='utf-8')
print(output, end='')
raise SystemExit(0 if all(checks.values()) else 1)
