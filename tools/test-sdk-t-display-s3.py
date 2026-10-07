"""Verify SDK/avatar routing without building firmware or touching hardware."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class SDKRoutingTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for name in ['tools/sdk-t-display-s3.sh','muse-gadget-sdk/esp32/tools/muse/board.sh','muse-gadget-sdk/esp32/tools/muse/ports.py']:
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
        for name in ['build-t-display-s3.sh','flash-t-display-s3.sh']:
            p=self.root/name;p.write_text('#!/bin/bash\nprintf "%s\\n" "'+name+'" "$@"\n');p.chmod(0o755)
        p=self.root/'build-config/t-display-s3/partitions.csv';p.parent.mkdir(parents=True);p.touch()
        p=self.root/'serial/tools';p.mkdir(parents=True)
        (p.parent/'__init__.py').touch();(p/'__init__.py').touch()
        (p/'list_ports.py').write_text('from types import SimpleNamespace\ndef comports():\n return [SimpleNamespace(device="/dev/fake-t-display",vid=0x303a,pid=0x1001,serial_number="24:58:7c:d3:96:30")]\n')
        self.env={**os.environ,'PYTHONPATH':str(self.root)};self.env.pop('MUSE_BENCH',None)

    def run_helper(self,*args):
        return subprocess.run([str(self.root/'muse-gadget-sdk/esp32/tools/muse/board.sh'),*args],env=self.env,capture_output=True,text=True)

    def test_build_delegates_to_compatibility_wrapper(self):
        r=self.run_helper('build','t-display-s3');self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(r.stdout.strip(),'build-t-display-s3.sh')

    def test_flash_uses_selected_port_and_usb_identity(self):
        r=self.run_helper('flash','t-display-s3','24:58:7c:d3:96:30');self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(r.stdout.splitlines(),['flash-t-display-s3.sh','/dev/fake-t-display','24:58:7c:d3:96:30'])

    def test_unmatched_identity_never_flashes(self):
        r=self.run_helper('flash','t-display-s3','wrong-board');self.assertNotEqual(r.returncode,0)
        self.assertNotIn('flash-t-display-s3.sh',r.stdout)

    def test_build_error_is_logged_and_propagated(self):
        p=self.root/'build-t-display-s3.sh'
        p.write_text('#!/bin/bash\necho "avatar/muse_pixel.c: error: fixture failure" >&2\nexit 7\n')
        r=self.run_helper('build','t-display-s3');self.assertEqual(r.returncode,7)
        self.assertIn('fixture failure',Path('/tmp/muse_build_t-display-s3.log').read_text())

    def test_bench_cannot_silently_use_another_layout(self):
        self.env['MUSE_BENCH']='1'
        r=self.run_helper('build','t-display-s3');self.assertNotEqual(r.returncode,0)
        self.assertIn('bench profile is not configured',r.stderr)

if __name__=='__main__':unittest.main()
