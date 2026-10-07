"""Exercise flash-plan rejection using disposable copies of the actual build.

Run after ./build-t-display-s3.sh. This never opens a serial port.
"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'muse-gadget-sdk/esp32/build-t-display-s3-audited'
spec = importlib.util.spec_from_file_location('board_verify', ROOT / 'tools/verify-t-display-s3.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class FlashPlanTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.build = Path(self.temp.name)
        plan = json.loads((BUILD / 'flasher_args.json').read_text())
        files = set(plan['flash_files'].values()) | {
            'sdkconfig', 'config/sdkconfig.json', 'compile_commands.json',
            'flasher_args.json', 'audited-manifest.json',
        }
        for name in files:
            dest = self.build / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BUILD / name, dest)

    def verify(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return checker.verify(self.build)

    def change_config(self, key, value):
        path = self.build / 'sdkconfig'
        lines = [s for s in path.read_text().splitlines()
                 if not s.startswith(key + '=') and s != '# ' + key + ' is not set']
        lines.append(key + '=' + value)
        path.write_text('\n'.join(lines) + '\n')

    def change_plan(self, change):
        path = self.build / 'flasher_args.json'
        plan = json.loads(path.read_text())
        change(plan)
        path.write_text(json.dumps(plan))

    def test_valid_build(self):
        self.assertEqual(self.verify()['app']['offset'], '0x20000')

    def test_absent_octal_memory_is_rejected(self):
        self.change_config('CONFIG_SPIRAM_MODE_OCT', 'n')
        with self.assertRaisesRegex(ValueError, 'CONFIG_SPIRAM_MODE_OCT'):
            self.verify()

    def test_duplicate_display_backend_is_rejected(self):
        self.change_config('CONFIG_HOMEHUB_LED_BACKEND_IDEASPARK', 'y')
        with self.assertRaisesRegex(ValueError, 'Conflicting status backends'):
            self.verify()

    def test_security_provisioning_is_rejected(self):
        self.change_config('CONFIG_HOMEHUB_PAIRING_EFUSE_AUTH', 'y')
        with self.assertRaisesRegex(ValueError, 'CONFIG_HOMEHUB_PAIRING_EFUSE_AUTH'):
            self.verify()

    def test_wrong_chip_is_rejected(self):
        self.change_plan(lambda p: p['extra_esptool_args'].update(chip='esp32'))
        with self.assertRaisesRegex(ValueError, 'Wrong chip'):
            self.verify()

    def test_wrong_app_offset_is_rejected(self):
        self.change_plan(lambda p: p['app'].update(offset='0x10000'))
        with self.assertRaisesRegex(ValueError, 'App flash offset'):
            self.verify()

    def test_extra_write_into_nvs_is_rejected(self):
        self.change_plan(lambda p: p['flash_files'].update({'0x11000': p['bootloader']['file']}))
        with self.assertRaisesRegex(ValueError, 'erase NVS'):
            self.verify()

    def test_changed_binary_is_rejected(self):
        plan = json.loads((self.build / 'flasher_args.json').read_text())
        path = self.build / plan['app']['file']
        data = bytearray(path.read_bytes())
        data[100] ^= 1
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'changed after the audited build'):
            self.verify()

    def test_changed_partition_geometry_is_rejected(self):
        self.verify()  # loads the IDF partition parser
        from gen_esp32part import PartitionTable
        plan = json.loads((self.build / 'flasher_args.json').read_text())
        path = self.build / plan['partition-table']['file']
        table = PartitionTable.from_binary(path.read_bytes())
        next(p for p in table if p.name == 'nvs').offset = 0x10000
        path.write_bytes(table.to_binary())
        with self.assertRaisesRegex(ValueError, 'preserve the existing NVS'):
            self.verify()


if __name__ == '__main__':
    unittest.main()
