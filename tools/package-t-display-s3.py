#!/usr/bin/env python3
"""Prepare/release a credential-free SDK source contribution from an explicit file list."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, shutil, subprocess, tempfile, zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
SDK=ROOT/'muse-gadget-sdk'
TEMPLATES=ROOT/'support/t-display-s3'
BASE='b139b45064b4dcecf7bfe97e75bc7f99c10c28b6'
VERSION='0.1.0'
NAME=f't-display-s3-sdk-support-v{VERSION}'
PACKAGE=ROOT/'dist'/NAME
STATE=ROOT/'dist/t-display-s3-package-work.json'

BOARD_FILES=[
 'esp32/AGENTS.md','esp32/README.md','esp32/cmake/validate_config.cmake',
 'esp32/components/muse/CMakeLists.txt','esp32/components/muse/Kconfig',
 'esp32/components/muse/boards/board_lilygo_t_display_s3.c',
 'esp32/components/muse/boards/NOTICE.lilygo-t-display-s3',
 'esp32/components/muse/idf_component.yml','esp32/devices/AGENTS.md',
 'esp32/devices/README.md','esp32/devices/sdkconfig.muse',
 'esp32/devices/sdkconfig.muse-lilygo-t-display-s3','esp32/tests/test_t_display_s3.py',
 'esp32/devices/lilygo-t-display-s3.md',
 'esp32/tools/muse/avatar.py','esp32/tools/muse/board.sh','esp32/tools/muse/ports.py',
]
HARDEN_FILES=[
 'esp32/components/muse/muse_app.c','esp32/components/muse/muse_ui.c',
 'esp32/main/app.c','esp32/main/ble_server.c','esp32/main/wifi_mgr.c',
 'esp32/tests/test_ble_start_failures.py','esp32/tests/test_link_ble_lifecycle_contract.py',
]

def run(*args,cwd=None):
    return subprocess.run(args,cwd=cwd,check=True,capture_output=True).stdout

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def clone_base(dest):
    run('git','clone','--no-hardlinks','--no-checkout',str(SDK),str(dest))
    run('git','checkout','--detach',BASE,cwd=dest)

def write(dest,text):
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)

def copy_templates():
    for name in ['README.md','install.sh','NOTICE','licenses/LilyGO-MIT.txt']:
        path=TEMPLATES/name;dest=PACKAGE/name
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)

def prepare():
    if PACKAGE.exists():raise ValueError(f'Package already exists: {PACKAGE}; use --finalize after validation')
    PACKAGE.mkdir(parents=True)
    copy_templates()
    snapshot=pathlib.Path(tempfile.mkdtemp(prefix='maya-sdk-package-source-'))/'sdk'
    clone_base(snapshot)
    for name in BOARD_FILES:
        dest=snapshot/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SDK/name,dest)

    # Omit this enclosing project's optional compatibility bridge from the SDK contribution.
    board_sh=snapshot/'esp32/tools/muse/board.sh'
    s=board_sh.read_text()
    start=s.index('# This enclosing project\'s board already has a different storage geometry.')
    end=s.index('baud=${baud:-460800}',start)
    board_sh.write_text(s[:start]+s[end:])

    # SDK documentation is portable; local project migration details stay in the audit.
    section='''### Standard LilyGO T-Display-S3\n\nStandard 1.9-inch ST7789V LCD model, ESP32-S3R8, 16 MB flash, 8 MB octal\nPSRAM; 320x170 I80 landscape, GPIO0/14 buttons, native USB, no audio/touch.\nBuild: `tools/muse/board.sh build t-display-s3`. See\n[board guide](devices/lilygo-t-display-s3.md) for pins, provisioning,\nvalidation and storage compatibility before flashing an existing installation.\n'''
    for name in ['esp32/AGENTS.md','esp32/README.md']:
        p=snapshot/name;s=p.read_text().split('### Standard LilyGO T-Display-S3 custom port')[0]
        p.write_text(s.rstrip()+'\n\n'+section)
    p=snapshot/'esp32/devices/README.md'
    s=p.read_text().split('## LilyGO T-Display-S3 custom port')[0]
    p.write_text(s.rstrip()+'''\n\n## LilyGO T-Display-S3\n\nStandard 1.9-inch ST7789V LCD model, ESP32-S3R8, 16 MB flash and 8 MB octal\nPSRAM. Muse UI over 8-bit I80 in 320x170 landscape; GPIO0/14 buttons and\nnative USB; no audio or touch. Overlay: `sdkconfig.muse-lilygo-t-display-s3`\nafter `sdkconfig.muse`. Helper alias: `t-display-s3`.\n\nSee [the board guide](lilygo-t-display-s3.md) for hardware references,\nconfiguration, controls and existing-storage compatibility.\n''')
    for name in ['esp32/AGENTS.md','esp32/devices/README.md']:
        p=snapshot/name;s=p.read_text()
        needle='| AIPI Lite |'
        rows=s.splitlines();idx=next(i for i,l in enumerate(rows) if l.startswith(needle))
        row=('| LilyGO T-Display-S3 (standard LCD) | `esp32s3` | `devices/sdkconfig.muse;devices/sdkconfig.muse-lilygo-t-display-s3` | `tools/muse/board.sh build t-display-s3` |'
             if name.endswith('AGENTS.md') else
             '| LilyGO T-Display-S3 | ESP32-S3 | 1.9-inch ST7789V I80, 320x170 | No | No | [Board guide](lilygo-t-display-s3.md) |')
        # Device README tables differ: keep its dedicated section unless columns match.
        if name.endswith('AGENTS.md'):rows.insert(idx+1,row);p.write_text('\n'.join(rows)+'\n')

    board_paths=BOARD_FILES
    run('git','add','--',*board_paths,cwd=snapshot)
    patches=PACKAGE/'patches';patches.mkdir()
    run('git','-c','user.name=SDK Port Package','-c','user.email=package@localhost',
        '-c','commit.gpgsign=false','commit','-m','Add standard T-Display-S3 board support',cwd=snapshot)
    for name in HARDEN_FILES:
        dest=snapshot/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SDK/name,dest)
    run('git','add','--',*HARDEN_FILES,cwd=snapshot)
    (patches/'t-display-s3-sdk-support.patch').write_bytes(run('git','diff','--binary',BASE,cwd=snapshot))
    changed=run('git','diff','--name-only',BASE,cwd=snapshot).decode().splitlines()
    if set(changed)!=set(board_paths+HARDEN_FILES):raise ValueError('Unexpected file set in contribution')
    shutil.copy2(SDK/'LICENSE',PACKAGE/'LICENSE')
    # A second clean checkout exercises the actual recipient installer.
    check=pathlib.Path(tempfile.mkdtemp(prefix='maya-sdk-package-check-'))/'sdk'
    clone_base(check)
    run(str(PACKAGE/'install.sh'),str(check))
    for name in changed:
        if sha(check/name)!=sha(snapshot/name):raise ValueError(f'Patch/source mismatch: {name}')
    STATE.write_text(json.dumps({'base':BASE,'package':str(PACKAGE),'check_sdk':str(check),'files':changed,'source_sha256':{n:sha(snapshot/n) for n in changed},'patch_sha256':sha(patches/'t-display-s3-sdk-support.patch')},indent=2)+'\n')
    print(json.dumps({'package':str(PACKAGE),'clean_applied_sdk':str(check),'changed_files':len(changed)},indent=2))

def finalize():
    state=json.loads(STATE.read_text())
    results=json.loads((TEMPLATES/'validation-results.json').read_text())
    if results.get('status')!='passed':raise ValueError('Clean package validation is incomplete')
    check=pathlib.Path(state['check_sdk'])
    if state['source_sha256'] != results.get('validated_sdk_files'):
        raise ValueError('Release source differs from the validated source; repeat validation')
    for name,digest in state['source_sha256'].items():
        if sha(check/name)!=digest:raise ValueError(f'Validated source changed: {name}')
    if sha(PACKAGE/'patches/t-display-s3-sdk-support.patch') != state['patch_sha256']:
        raise ValueError('Validated patch changed')
    copy_templates()
    private_values=[]
    private=ROOT/'build-config/t-display-s3/sdkconfig.private'
    if private.exists():
        for line in private.read_text().splitlines():
            if '=' in line:
                value=line.split('=',1)[1].strip().strip('"')
                if len(value)>=8:private_values.append(value)
    # Include only explicit release payload; no binaries, generated configs or personal data.
    for path in PACKAGE.rglob('*'):
        if path.is_file():
            if path.suffix in {'.bin','.elf','.bak','.pem'} or '.git' in path.parts or path.name in {'sdkconfig','sdkconfig.private'}:
                raise ValueError(f'Private/build material in package: {path.relative_to(PACKAGE)}')
            s=path.read_text(errors='replace')
            if '/Users/emasi/' in s or '24:58:7c:d3:96:30' in s:
                raise ValueError(f'Personal metadata in package: {path.relative_to(PACKAGE)}')
            if any(v in s for v in private_values) or re.search(r'mgst_[A-Za-z0-9_-]{24,}',s):
                raise ValueError(f'Credential-like literal in package: {path.relative_to(PACKAGE)}')
    manifest={
        'name':NAME,'version':VERSION,'sdk_repository':'https://github.com/facebookincubator/muse-gadget-sdk',
        'sdk_base_commit':BASE,'esp_idf':'v6.0.1','lvgl':'9.5.0','esp_lvgl_adapter':'0.6.4',
        'standard_board_only':True,'contains_firmware':False,'contains_credentials':False,
        'vendor_references':{'LilyGo-Display-IDF':'b1a1cc54994bf1b417e3bb30c437bbe1036bff7f','T-Display-S3':'ec889e789b3cf093412689a143f7f37b42b56af7'},
        'validation':results,
        'files':{str(p.relative_to(PACKAGE)):sha(p) for p in sorted(PACKAGE.rglob('*')) if p.is_file() and p.name not in {'PACKAGE_MANIFEST.json','SHA256SUMS'}},
    }
    write(PACKAGE/'PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    sums=''.join(f'{sha(p)}  {p.relative_to(PACKAGE)}\n' for p in sorted(PACKAGE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS')
    write(PACKAGE/'SHA256SUMS',sums)
    archive=PACKAGE.parent/(NAME+'.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(PACKAGE.rglob('*')):
            if p.is_file():z.write(p,str(pathlib.Path(NAME)/p.relative_to(PACKAGE)))
    archive.with_suffix('.zip.sha256').write_text(f'{sha(archive)}  {archive.name}\n')
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive)},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--finalize',action='store_true')
    args=ap.parse_args()
    finalize() if args.finalize else prepare()
