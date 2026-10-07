#!/usr/bin/env python3
"""Inspect, back up and flash only validated standard T-Display-S3 artifacts."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, pathlib, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('board_verify', ROOT/'tools/verify-t-display-s3.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port',required=True)
    ap.add_argument('--expected-mac',required=True,help='Verified board USB serial/MAC, e.g. 24:58:7c:d3:96:30')
    ap.add_argument('--build',type=pathlib.Path,default=ROOT/'muse-gadget-sdk/esp32/build-t-display-s3-audited')
    ap.add_argument('--backup-only',action='store_true')
    ap.add_argument('--dry-run',action='store_true',help='Validate files and print offsets; do not open hardware')
    args=ap.parse_args();build=args.build.resolve()
    plan=checker.verify(build)
    if args.dry_run:return
    import esptool
    from serial.tools import list_ports
    devices=[p for p in list_ports.comports() if p.device==args.port]
    if len(devices)!=1 or (devices[0].vid,devices[0].pid)!=(0x303a,0x1001):
        raise ValueError('Specified port is not Espressif native USB Serial/JTAG')
    expected=args.expected_mac.lower()
    if (devices[0].serial_number or '').lower()!=expected:
        raise ValueError('USB serial does not match the verified physical board')
    esp=esptool.connect_esp(port=args.port,chip='auto')
    try:
        if esp.CHIP_NAME!='ESP32-S3':raise ValueError(f'Wrong chip: {esp.CHIP_NAME}')
        features=esp.get_chip_features()
        if not any('Embedded PSRAM 8MB' in feature for feature in features):
            raise ValueError(f'Chip does not identify the standard S3R8 memory package: {features}')
        mac=':'.join(f'{v:02x}' for v in esp.read_mac())
        if mac!=expected:raise ValueError('Chip MAC differs from expected board')
        info=esp.get_security_info()
        if info['parsed_flags']['SECURE_BOOT_EN'] or bin(info['flash_crypt_cnt']).count('1')%2:
            raise ValueError('Hardware security is already enabled; stop for a device-specific recovery plan')
        esp=esptool.run_stub(esp)
        esptool.attach_flash(esp)
        size=esptool.cmds.detect_flash_size(esp)
        if size!='16MB':raise ValueError(f'Wrong flash capacity: {size}')
        print(f'Connected {esp.get_chip_description()}, MAC {mac}, 16 MB flash; Secure Boot and flash encryption disabled.')
        print(f'Chip features: {features}')
        directory=ROOT/'audit-evidence';directory.mkdir(exist_ok=True)
        stamp=time.strftime('%Y%m%d-%H%M%S',time.gmtime())
        backup=directory/f'flash-before-{mac.replace(":", "")}-{stamp}.bin'
        backup.touch(mode=0o600,exist_ok=False)
        esptool.read_flash(esp,0,16*1024*1024,str(backup),no_progress=True)
        backup.chmod(0o600)
        metadata={'mac':mac,'bytes':backup.stat().st_size,'sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'security_flags':info['flags']}
        if metadata['bytes']!=16*1024*1024:raise ValueError('Incomplete backup; aborting before writing')
        # Compare the real on-device table to the new layout before any write.
        from gen_esp32part import PartitionTable
        old=PartitionTable.from_binary(backup.read_bytes()[0x8000:0x9000])
        new=PartitionTable.from_binary((build/plan['partition-table']['file']).read_bytes())
        old_geometry={p.name:(p.type,p.subtype,p.offset,p.size) for p in old}
        new_geometry={p.name:(p.type,p.subtype,p.offset,p.size) for p in new}
        if old_geometry!=new_geometry:raise ValueError('Partition geometry differs from the board backup; no flash writes performed')
        metadata_path=backup.with_suffix('.json')
        metadata_path.touch(mode=0o600,exist_ok=False)
        metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')
        print(f'Complete private backup: {backup}; existing partition geometry matches.')
        if args.backup_only:return
        checker.verify(build)  # reject edits made while the full backup was reading
        entries=sorted((int(offset,16),str(build/name)) for offset,name in plan['flash_files'].items())
        # Preserve compiled image headers (also preserves signed app bytes),
        # use build-generated offsets, never force or erase-all.
        esptool.write_flash(esp,entries,flash_mode='keep',flash_freq='keep',flash_size='keep',no_progress=True)
        esptool.verify_flash(esp,entries,flash_mode='keep',flash_freq='keep',flash_size='keep')
        print('Every flashed file verified against the build. NVS was not erased.')
    finally:
        esp.hard_reset()
        esp._port.close()

if __name__=='__main__':
    try:main()
    except Exception as exc:sys.exit(f'Flash aborted: {exc}')
