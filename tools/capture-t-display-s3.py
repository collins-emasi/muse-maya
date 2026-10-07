#!/usr/bin/env python3
"""Capture redacted logs passively, or explicitly reset to capture one full boot."""
import argparse,os,re,termios,time,pathlib
ap=argparse.ArgumentParser();ap.add_argument('port');ap.add_argument('--seconds',type=float,default=10);ap.add_argument('--out',type=pathlib.Path,required=True)
ap.add_argument('--reset',action='store_true',help='Reset through native USB before capturing boot')
a=ap.parse_args()
serial_port=None
if a.reset:
 import serial
 serial_port=serial.Serial(a.port,115200,timeout=.02)
 fd=serial_port.fileno()
else:fd=os.open(a.port,os.O_RDONLY|os.O_NOCTTY|os.O_NONBLOCK)
t=termios.tcgetattr(fd);t[2]&=~termios.HUPCL;termios.tcsetattr(fd,termios.TCSANOW,t)
if serial_port:
 serial_port.dtr=False;serial_port.rts=True;time.sleep(.1);serial_port.rts=False
end=time.monotonic()+a.seconds;data=bytearray()
try:
 while time.monotonic()<end:
  try:
   b=serial_port.read(4096) if serial_port else os.read(fd,4096)
   if b:data.extend(b)
  except BlockingIOError:pass
  time.sleep(.02)
finally:
 if serial_port:serial_port.close()
 else:os.close(fd)
s=data.decode(errors='replace');s=re.sub(r'mgst_[A-Za-z0-9_-]+','<sdk-token-redacted>',s)
s=re.sub(r'(?i)(token|password|ssid)([=: ]+)([^\r\n]+)',r'\1\2<redacted>',s)
a.out.write_text(s)
for l in s.splitlines():
 if re.search(r'panic|Backtrace|failed|HEAP|psram|PSRAM|board:|UI up|ready:|Rebooting|starting|ST7789|t.display|BLE advertising',l):print(l)
print(f'{len(data)} serial bytes captured; redacted log saved to {a.out}')
