#!/usr/bin/env python3
"""Validate the generated LilyGO profile and flash plan, reject stale artifacts."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
SDK = ROOT / 'muse-gadget-sdk/esp32'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def config(path):
    result = {}
    for line in path.read_text().splitlines():
        if line.startswith('CONFIG_') and '=' in line:
            k, v = line.split('=', 1)
            result[k] = v
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):
            result[line[2:-11]] = 'n'
    return result

def verify(build, record=False):
    build = pathlib.Path(build).resolve()
    cfg = config(build / 'sdkconfig')
    expected = {
        'CONFIG_IDF_TARGET': '"esp32s3"',
        'CONFIG_MUSE_BOARD_ID': '"lilygo_t_display_s3"',
        'CONFIG_MUSE_ENABLED': 'y', 'CONFIG_HOMEHUB_LED_BACKEND_MUSE': 'y',
        'CONFIG_SPIRAM': 'y', 'CONFIG_SPIRAM_MODE_OCT': 'y',
        'CONFIG_SPIRAM_IGNORE_NOTFOUND': 'n', 'CONFIG_SPIRAM_MEMTEST': 'y',
        'CONFIG_ESPTOOLPY_FLASHSIZE': '"16MB"',
        'CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG': 'y',
        'CONFIG_HOMEHUB_BUTTON_GPIO': '0',
        'CONFIG_LV_OS_FREERTOS': 'y', 'CONFIG_LV_USE_CUSTOM_MALLOC': 'y',
        'CONFIG_LV_COLOR_DEPTH': '16', 'CONFIG_FREERTOS_HZ': '1000',
        'CONFIG_CJSON_NESTING_LIMIT': '16',
        'CONFIG_LWIP_TCP_SND_BUF_DEFAULT': '16384',
        'CONFIG_LWIP_TCP_WND_DEFAULT': '16384',
        'CONFIG_SECURE_BOOT': 'n', 'CONFIG_SECURE_FLASH_ENC_ENABLED': 'n',
        'CONFIG_HOMEHUB_PAIRING_EFUSE_AUTH': 'n', 'CONFIG_HOMEHUB_OTA_ENABLED': 'n',
    }
    for key, value in expected.items():
        actual = cfg.get(key, 'n')
        if actual != value:
            raise ValueError(f'{key}: expected {value}, got {actual}; rebuild in a fresh directory')
    backends = [k for k,v in cfg.items() if k.startswith('CONFIG_HOMEHUB_LED_BACKEND_') and v == 'y']
    if backends != ['CONFIG_HOMEHUB_LED_BACKEND_MUSE']:
        raise ValueError(f'Conflicting status backends: {backends}')
    generated = json.loads((build / 'config/sdkconfig.json').read_text())
    for key, value in expected.items():
        desired = {'y': True, 'n': False}.get(value, value.strip('"'))
        if value.isdigit(): desired = int(value)
        if generated.get(key[7:], False) != desired:
            raise ValueError(f'Generated config/sdkconfig.json disagrees with sdkconfig: {key}')
    # Verify every request in the board and UI overlays after last-overlay wins.
    requested = {}
    for overlay in [SDK/'devices/sdkconfig.muse', SDK/'devices/sdkconfig.muse-lilygo-t-display-s3', ROOT/'build-config/t-display-s3/sdkconfig.lilygo-t-display-s3']:
        requested.update(config(overlay))
    for key, value in requested.items():
        if cfg.get(key, 'n') != value:
            raise ValueError(f'Board/UI overlay setting did not apply: {key} (expected {value}, got {cfg.get(key, "n")})')
    manifest = json.loads((build / 'flasher_args.json').read_text())
    if manifest['extra_esptool_args']['chip'] != 'esp32s3': raise ValueError('Wrong chip in flash plan')
    if int(manifest['partition-table']['offset'],16) != int(cfg['CONFIG_PARTITION_TABLE_OFFSET'],16):
        raise ValueError('Partition table offset does not match generated bootloader config')
    # Inspect the actual compiled partition binary, not an unbuilt CSV.
    sys.path.insert(0, str(pathlib.Path(__import__('os').environ.get('IDF_PATH', str(pathlib.Path.home()/'esp/esp-idf'))) / 'components/partition_table'))
    from gen_esp32part import PartitionTable
    table = PartitionTable.from_binary((build / manifest['partition-table']['file']).read_bytes())
    parts = {p.name: p for p in table}
    app_offset = int(manifest['app']['offset'],16)
    app = parts.get('ota_0')
    if not app or app.offset != app_offset: raise ValueError('App flash offset disagrees with ota_0')
    if parts['nvs'].offset != 0x11000 or parts['nvs'].size != 0x6000:
        raise ValueError('Project compatibility layout must preserve the existing NVS partition')
    if parts['otadata'].offset != int(manifest['otadata']['offset'],16): raise ValueError('otadata mismatch')
    entries = sorted((int(offset,16), build/name) for offset,name in manifest['flash_files'].items())
    artifacts = {}
    for offset, path in entries:
        size = path.stat().st_size
        if offset + size > 16*1024*1024: raise ValueError(f'Flash overflow: {path.name}')
        erase_start = offset // 4096 * 4096
        erase_end = (offset + size + 4095) // 4096 * 4096
        nvs = parts['nvs']
        if erase_start < nvs.offset+nvs.size and erase_end > nvs.offset:
            raise ValueError(f'Write would erase NVS: {path.name}')
        artifacts[str(path.relative_to(build))] = sha(path)
    if entries[0][0] != 0 or entries[0][1].stat().st_size > int(cfg['CONFIG_PARTITION_TABLE_OFFSET'],16):
        raise ValueError('Bootloader overlaps partition table')
    app_size = (build / manifest['app']['file']).stat().st_size
    if app_size > app.size: raise ValueError('App exceeds OTA slot')
    if app_size > app.size * .9: raise ValueError('Less than 10% OTA slot headroom; review layout before flashing')
    cmds = json.loads((build/'compile_commands.json').read_text())
    boards = {pathlib.Path(c['file']).name for c in cmds if '/muse/boards/board_' in c['file']}
    if boards != {'board_lilygo_t_display_s3.c'}: raise ValueError(f'Wrong board sources compiled: {boards}')
    sources = {}
    for path in SDK.rglob('*'):
        rel = path.relative_to(SDK)
        if any(s.startswith(('build','managed_components','test-build','test-docker')) for s in rel.parts): continue
        if path.is_file() and (path.suffix in {'.c','.cpp','.h','.cmake','.yml'} or path.name in {'Kconfig','Kconfig.projbuild','sdkconfig.defaults','CMakeLists.txt'} or path.name.startswith('sdkconfig.muse')):
            sources[str(rel)] = sha(path)
    data = {'board': 'LilyGO T-Display-S3', 'artifacts': artifacts, 'sources': sources,
            'config_sha256': sha(build/'sdkconfig'), 'flasher_args_sha256': sha(build/'flasher_args.json'),
            'app_bytes': app_size, 'slot_bytes': app.size}
    audit_path = build/'audited-manifest.json'
    if record:
        audit_path.write_text(json.dumps(data,indent=2)+'\n')
    elif not audit_path.exists() or json.loads(audit_path.read_text()) != data:
        raise ValueError('Source/config/binary changed after the audited build; run ./build-t-display-s3.sh')
    print(f'Validated standard T-Display-S3: octal PSRAM, one display backend, native USB, no security eFuse provisioning.')
    print(f'App: {app_size} / {app.size} bytes ({(app.size-app_size)/app.size:.1%} free). NVS sectors excluded from all writes.')
    for offset,path in entries: print(f'  {offset:#08x} {path.name} ({path.stat().st_size} bytes)')
    return manifest

if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build', type=pathlib.Path);ap.add_argument('--record',action='store_true')
    args=ap.parse_args()
    try: verify(args.build,args.record)
    except (ValueError,KeyError,FileNotFoundError) as e: sys.exit(f'Validation failed: {e}')
