#!/usr/bin/env python3
"""Build the release folder: ROM, source zip (verified by rebuilding), complete zip."""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = os.path.join(ROOT, 'release')
ROMNAME = 'HOLLOW_MAN_II_THE_SECOND_SHADOW.gbc'


def sha1(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()


def main():
    os.makedirs(REL, exist_ok=True)
    rom = os.path.join(ROOT, 'build', ROMNAME)
    out_rom = os.path.join(REL, ROMNAME)
    shutil.copyfile(rom, out_rom)
    print('ROM', out_rom, sha1(out_rom))

    # source archive: every tracked file (git ls-files) + uncommitted tracked changes
    files = subprocess.check_output(['git', 'ls-files'], cwd=ROOT).decode().split('\n')
    files = [f for f in files if f and not f.startswith('release/')]
    src_zip = os.path.join(REL, 'HOLLOW_MAN_II_SOURCE.zip')
    with zipfile.ZipFile(src_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files:
            p = os.path.join(ROOT, f)
            if os.path.isfile(p):
                z.write(p, os.path.join('HOLLOW_MAN_II_SOURCE', f))
    print('source zip', src_zip, len(files), 'files')

    # verify: extract and rebuild from scratch, ROM must be byte-identical
    gbdk = os.environ.get('GBDK_HOME', '/opt/gbdk')
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(src_zip) as z:
            bad = z.testzip()
            assert bad is None, bad
            z.extractall(td)
        d = os.path.join(td, 'HOLLOW_MAN_II_SOURCE')
        r = subprocess.run(['make', 'GBDK_HOME=' + gbdk], cwd=d, capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-2000:], r.stderr[-2000:])
            sys.exit('rebuild from source zip FAILED')
        rebuilt = os.path.join(d, 'build', ROMNAME)
        same = sha1(rebuilt) == sha1(out_rom)
        print('rebuild from source zip:', 'IDENTICAL' if same else 'DIFFERENT')
        if not same:
            sys.exit('rebuilt ROM differs from release ROM')

    # complete release zip
    comp = os.path.join(REL, 'HOLLOW_MAN_II_COMPLETE.zip')
    with zipfile.ZipFile(comp, 'w', zipfile.ZIP_DEFLATED) as z:
        base = 'HOLLOW_MAN_II_THE_SECOND_SHADOW'
        z.write(out_rom, os.path.join(base, ROMNAME))
        for doc in ('MANUAL.md', 'CONTROLS.md', 'SOUNDTRACK.md', 'BUILD.md', 'TESTING.md'):
            p = os.path.join(ROOT, 'docs', doc)
            if os.path.exists(p):
                z.write(p, os.path.join(base, 'docs', doc))
        z.write(os.path.join(REL, 'RELEASE_NOTES.md'), os.path.join(base, 'RELEASE_NOTES.md'))
        shots = os.path.join(REL, 'screenshots')
        if os.path.isdir(shots):
            for f in sorted(os.listdir(shots)):
                z.write(os.path.join(shots, f), os.path.join(base, 'screenshots', f))
        z.write(src_zip, os.path.join(base, 'HOLLOW_MAN_II_SOURCE.zip'))
    with zipfile.ZipFile(comp) as z:
        assert z.testzip() is None
        names = z.namelist()
    print('complete zip', comp, len(names), 'entries')


if __name__ == '__main__':
    main()
