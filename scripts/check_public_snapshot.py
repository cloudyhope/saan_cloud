"""Fail closed on obvious secrets and local data in a public Git snapshot.

This checks Git objects from a commit, not an untracked working directory. Run a
dedicated secret scanner as well before publication; this is a second guard.
"""

import io
import re
import subprocess
import sys
import zipfile


revision = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'


def git(*args):
    return subprocess.run(['git', *args], check=True, stdout=subprocess.PIPE).stdout


forbidden_path = re.compile(
    r'(^|/)(?:data|local_media|local_static|output|outputs|tmp)/|'
    r'\.(?:sqlite|sqlite3|db|pem|p12|pfx|key|dump|bak)$', re.I,
)
patterns = {
    'credentialed URL': re.compile(rb'https?://[^\s/@]+:[^\s/@]+@'),
    'private key': re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    'embedded RSA private key': re.compile(rb'rsa\.key\.PrivateKey\s*\(\s*\d'),
    'GitHub token': re.compile(rb'gh[pousr]_[A-Za-z0-9_]{20,}'),
    'GitLab token': re.compile(rb'glpat-[A-Za-z0-9_-]{20,}'),
    'AWS access key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'literal credential': re.compile(
        rb'(?im)^\s*(?:secret|password|api_?key|access_?token)\s*=\s*b?[\'\"][^\'\"\r\n]{8,}[\'\"]'
    ),
    'JWT literal': re.compile(rb'eyJ[A-Za-z0-9_-]{30,}\.eyJ[A-Za-z0-9_-]{20,}\.'),
}

problems = []
tree = git('ls-tree', '-r', '-z', '--name-only', revision)
paths = [path.decode('utf-8') for path in tree.split(b'\0') if path]
for path in paths:
    if forbidden_path.search(path):
        problems.append(f'{path}: forbidden path')
        continue
    blob = git('show', f'{revision}:{path}')
    if zipfile.is_zipfile(io.BytesIO(blob)):
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            for name in archive.namelist():
                if not name.endswith(('.xml', '.rels', '.txt')):
                    continue
                content = archive.read(name)
                for label, pattern in patterns.items():
                    if pattern.search(content):
                        problems.append(f'{path}!{name}: {label}')
                if re.search(rb'(?<!\d)09\d{9}(?!\d)', content):
                    problems.append(f'{path}!{name}: phone-like value')
        continue
    if b'\0' in blob[:4096]:
        continue
    for label, pattern in patterns.items():
        if pattern.search(blob):
            problems.append(f'{path}: {label}')

if problems:
    print('Public snapshot audit failed:')
    for problem in problems:
        print(f'  {problem}')
    sys.exit(1)
print(f'Public snapshot audit passed for {len(paths)} tracked paths.')
