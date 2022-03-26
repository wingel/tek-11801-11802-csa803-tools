#! /usr/bin/python3
import sys
import os
import struct
import time
import re
import serial
import pexpect
import pexpect_serial
import datetime

from romtool import *

# Order to try baudrates for main console
MAIN_BAUDRATES = [ 9600 ] # , 19200 ]

# Order to try baudrates for test mode
TEST_BAUDRATES = [ 9600, 38400 ]

HOME_PAT = '\033\\[2K'

class FriendlyException(Exception):
    pass

screen_dirty = False

def screen_cleanup():
    global screen_dirty
    if screen_dirty:
        print('\033[0m\033[24;0H', flush = True)
    screen_dirty = False

def sanitize_fn(s):
    return re.sub('[^-_A-Za-z0-9]', '-', s)

class Printer():
    def __init__(self, f):
        self.f = f
        self.current_level = 2
        self.last = ''

    def write(self, s):
        if self.current_level < 1000:
            sys.stdout.write(s)
            sys.stdout.flush()

        s = self.last + s
        r = re.compile('\033\\[2K|\n')
        i = 0
        while 1:
            match = r.search(s, i)
            if not match:
                break

            if match.group() == '\r\n':
                e = match.start()
            else:
                e = match.end()
            self.f.write(s[i:e])
            self.f.write('\n')
            i = match.end()

        self.f.flush()
        self.last = s[i:]

    def flush(self):
        if self.current_level < 1000:
            sys.stdout.flush()

        self.f.flush()

    def level(self, level):
        last_level = self.current_level
        self.current_level = level
        return last_level

class Tek():
    def __init__(self, ser):
        self.ser = ser
        self.debug = 10
        self.keep_tmp = True

        ser.inter_byte_timeout = 0.1

        self.spawn = pexpect_serial.SerialSpawn(
            ser, encoding = 'ASCII', codec_errors = 'replace',
            timeout = 5)

        logf = open('log','w')
        self.printer = Printer(logf)
        self.printer.level(2)

        self.spawn.logfile_read = self.printer

        self.main_baudrate = None
        self.test_baudrate = None

        self.after = ''
        self.saved = ''

    def set_baudrate(self, baudrate):
        print("Baudrate %u bps" % baudrate, file = sys.stderr)
        self.ser.baudrate = baudrate

    def reset_input_buffer(self):
        self.ser.reset_input_buffer()

    def send(self, buf, *args, **kwargs):
        return self.spawn.send(buf, *args, **kwargs)

    def send_delay(self, buf, delay, *args, **kwargs):
        for b in buf:
            self.spawn.send(b, *args, **kwargs)
            time.sleep(delay)

    def sendline(self, *args, **kwargs):
        return self.spawn.sendline(*args, **kwargs)

    def expect(self, *args, save = False, **kwargs):
        idx = self.spawn.expect(*args, **kwargs)
        self.after = self.spawn.after
        if save:
            self.saved = self.after
        return idx

    def get_dev_id(self):
        self.sendline('ID?')
        try:
            self.expect('ID .*\r\n', timeout = 1)
        except pexpect.exceptions.TIMEOUT:
            return None

        s = self.after

        return s[3:].strip()

    def get_dev_uid(self):
        self.sendline('UID?')
        try:
            self.expect('UID .*\r\n', timeout = 1)
        except pexpect.exceptions.TIMEOUT:
            return None

        s = self.after

        return s[4:].strip()

    def exit_test_mode(self):
        self.send('XEE')

    def hard_exit_test_mode(self):
        # Try to exit test modea
        if self.debug >= 1:
            print("Trying to exit test modes", file = sys.stderr)

        last_level = self.printer.level(1000)
        for b in TEST_BAUDRATES:
            self.set_baudrate(b)
            self.exit_test_mode()
            time.sleep(0.5)

        self.printer.level(last_level)

    def try_connect(self):
        for b in MAIN_BAUDRATES:
            if self.debug >= 1:
                print("Trying to connect at %u bps" % b, file = sys.stderr)
            self.set_baudrate(b)
            self.sendline('')
            time.sleep(0.1)
            self.reset_input_buffer()

            dev_id = self.get_dev_id()
            if not dev_id:
                continue

            self.main_baudrate = b

            return dev_id

    def connect(self):
        dev_id = self.try_connect()
        if not dev_id:
            for retry in range(10):
                self.hard_exit_test_mode()
                time.sleep(1)
                self.reset_input_buffer()

                dev_id = self.try_connect()
                if dev_id:
                    break

        if not dev_id:
            raise FriendlyException("Failed to connect")

        if self.debug >= 1:
            print("Connected to %s" % repr(dev_id),
                  file = sys.stderr)

        parts = dev_id.split(',')

        self.device = parts[0]

        self.main = parts[0].replace('/', '-') + ' ' + parts[1]

        self.subsystems = {}
        for part in parts[2:]:
            k, v = part.split('/')
            self.subsystems[k] = v

        dev_uid = self.get_dev_uid()
        print(dev_uid)

        parts = dev_uid.split(',')
        for p in parts:
            if p.startswith('MAIN:"') and p.endswith('"'):
                self.main += '-' + p[6:-1]
                break

        self.rom_dir = sanitize_fn(self.main)

        now = datetime.datetime.now().strftime('%Y%m%d-%H%M')
        self.module_dir = 'MODULES-%s' % now


    def dump_module(self, unit):
        os.makedirs(self.module_dir, exist_ok = True)

        acq = (unit - 1) // 2
        acq_key = 'ab'[acq]
        num = (unit - 1) % 2 + 1

        if ' Stopped ' not in self.saved:
            self.send('q')

        self.send('1')
        if ' Main Acq ' not in self.saved:
            self.send('d')
            self.expect(' Main Acq .*' + HOME_PAT)

        s = ' Acq %u ' % (acq + 1)
        if s not in self.saved:
            time.sleep(1)
            self.send('2')
            self.expect(HOME_PAT)
            self.send(acq_key)
            self.expect(s + '.*' + HOME_PAT)

        if ' Exercisers ' not in self.saved:
            time.sleep(1)
            self.send('3')
            self.expect(HOME_PAT)
            self.send('g')
            self.expect(' Exercisers .*' + HOME_PAT)

        if ' Registers ' not in self.saved:
            self.send('4')
            self.expect(HOME_PAT)
            self.send('e')
            self.expect(' Registers .*' + HOME_PAT)

        time.sleep(1)
        self.send('r')

        self.expect('Select function.*' + HOME_PAT)
        time.sleep(1)
        self.send('2')
        self.expect(' Enter.*' + HOME_PAT)
        time.sleep(1)
        self.send('\r')

        self.expect('Enter head number.*' + HOME_PAT)
        self.send('%u' % num)
        time.sleep(1)
        self.expect(' Enter.*' + HOME_PAT)
        time.sleep(1)
        self.send('\r')

        # Wait until done and use everyting after "Enter head number" as the data
        values = []
        while 1:
            idx = self.expect([
                'Select ENTER to continue.*' + HOME_PAT,
                ('[0-9A-F]' * 4 + ' ') * 8,
                'Enter head number',
            ])
            if idx == 0:
                break
            elif idx == 1:
                values.append(self.spawn.after.strip())
            elif idx == 2:
                values.clear()

        words = [ int(_, 16) for _ in ' '.join(values).strip().split() ]

        octets = bytearray(struct.pack('>64H', *words))
        if octets == b'\xff' * 128:
            print("no module in slot %u" % unit)

        else:
            desc = ' '.join(octets[0x6e:0x7d].decode('ASCII', errors = 'replace').strip().split())
            fn = sanitize_fn(desc) + '.bin'
            with open(os.path.join(self.module_dir, fn), 'wb') as f:
                f.write(octets)

        time.sleep(1)
        self.send('\r')

        self.expect('Select function.*' + HOME_PAT)
        time.sleep(1)
        self.send('X')

        self.expect(' Stopped .*' + HOME_PAT)

        time.sleep(1)
        self.send('1')
        time.sleep(1)
        self.send('T')
        time.sleep(1)
        self.send('T')
        self.expect('EXTENDED DIAGNOSTICS', save = True)

    def dump_mem(self, subsystem, start, count, *filenames,
                 byte_order = '<'):
        """Dump memory from subsystem.

        Dump count bytes of memory at address start from a subystem to
        files.  If there are multiple filenames the file will be split
        so that the files contain even/odd bytes.
        """

        # Speed up when testing logic
        if 0 and count > 0x40:
            count = 0x40

        keep_tmp = self.keep_tmp

        if len(filenames) == 0:
            keep_tmp = True

        os.makedirs(self.rom_dir, exist_ok = True)

        tmp_fn = os.path.join(self.rom_dir, 'mem-%s-%08x.bin' % (
            subsystem, start))

        # Check if all files already exist
        if filenames:
            for fn in filenames:
                path = os.path.join(self.rom_dir, fn)
                if not os.path.exists(path) or os.path.getsize(path) < count:
                    break
            else:
                print("files exist: skipping dump")
                return

        # Resume if temporary file already exists
        if os.path.exists(tmp_fn):
            n = os.path.getsize(tmp_fn)
            start += n
            count -= n

        # Start download if we have something to read
        if count > 0:
            f = open(tmp_fn, 'ab')

            self.send('1')
            self.send(subsystem)

            try:
                self.send('D')
                time.sleep(1)

                self.expect('Low-Level Hardware Debugger')

                i = self.expect([
                    ' 8/16 .* 8 .*' + HOME_PAT,
                    ' 8/16 .* 16 .*' + HOME_PAT,
                ])
                if i == 0:
                    self.send('x')
                    self.expect(' 16 .*' + HOME_PAT)

                self.send('s')
                time.sleep(1)
                self.send_delay('%x' % start, 0.1)
                time.sleep(1)
                self.send('\r')
                self.send('l')
                time.sleep(1)
                self.send_delay('%x' % (count//2), 0.1)
                time.sleep(1)
                self.send('\r')

                self.expect(pexpect.TIMEOUT)

                time.sleep(1)
                self.send('T')

                pat = 'RM +[0-9A-F]+( +[0-9A-F]+)+'
                r = re.compile(pat)
                next = start
                while count > 0:
                    idx = self.expect([
                        pexpect.TIMEOUT,
                        pat + ' +.*\033',
                    ])
                    if idx == 0:
                        break
                    else:
                        match = r.match(self.spawn.after)
                        parts = match.group().split()
                        addr = int(parts[1], 16)
                        words = [ int(_, 16) for _ in parts[2:] ]
                        data = struct.pack('%s%uH' % (byte_order, len(words)), *words)
                        if addr == next:
                            f.write(data)
                            f.flush()
                            n = len(data)
                            next = addr + n
                            count -= n
                        elif addr > next:
                            raise ValueError('lost address sync')

            finally:
                self.send('X')

            f.close()

        # Split into parts
        if filenames:
            arrays = split_file(tmp_fn, *[
                os.path.join(self.rom_dir, _) for _ in filenames
            ])

        # Remove temporary file
        if not keep_tmp:
            os.remove(tmp_fn)

    def enable_debugger(self):
        DEBUGGER_ENABLED = '\033\\[0;4;7m.* Debugger .*\033\\[0m'
        if not re.search(DEBUGGER_ENABLED, self.saved):
            print("Enabling debugger", file = sys.stderr)
            self.send('WWWWWO')
            self.expect(DEBUGGER_ENABLED + '.*' + HOME_PAT, timeout = 10)

    def run(self):
        self.connect()

        self.sendline('TEST MAN')

        self.printer.level(2)

        try:
            time.sleep(5)

            for b in TEST_BAUDRATES:
                if self.debug >= 1:
                    print("Trying test mode %u bps" % b, file = sys.stderr)

                self.set_baudrate(b)
                self.send('T')
                self.expect('SUBSYSTEM')
                if self.debug >= 2:
                    print("Seen \"SUBSYSTEM\"", file = sys.stderr)

                self.test_baudrate = b

                break

            global screen_dirty
            screen_dirty = True

            self.expect('EXTENDED DIAGNOSTICS', save = True)
            if self.debug >= 2:
                print("Seen \"EXTENDED DIAGNOSTICS\"", file = sys.stderr)

            self.expect(HOME_PAT)
            if self.debug >= 2:
                print("Seen HOME_PAT", file = sys.stderr)

            print("Baudrate %u bps" % b, file = sys.stderr)

            if b != 38400:
                print("Switching to 38400 bps\n", file = sys.stderr)
                self.sendline('B38400')
                time.sleep(0.1)
                self.set_baudrate(38400)
                self.send('TT')
                self.expect('EXTENDED DIAGNOSTICS', save = True)
                if self.debug >= 2:
                    print("Seen EXTENDED DIAGNOSTICS", file = sys.stderr)

            self.enable_debugger()

            if 1:
                for i in range(4):
                    self.dump_module(i+1)

            if 0:
                # Dump the first bit of each 64k section to see if we
                # can find anything interesting
                for i in range(0x100):
                    self.dump_mem('a', i * 0x10000, 0x100)

            ver = sanitize_fn(self.subsystems.get('ACQM1') or self.subsystems.get('ACQM2') or 'unknown')
            self.dump_mem('d', 0x8000, 0x8000, 'A28_U611_ACQ_%s_UPPER.bin' % ver, byte_order = '>')

            ver = sanitize_fn(self.subsystems.get('DSY') or 'unknown')
            self.dump_mem('b', 0xe0000, 0x20000, 'A15_U140_DSY_%s.bin' % ver, 'A15_U150_DSY_%s.bin' % ver)

            ver = sanitize_fn(self.subsystems.get('TBC') or 'unknown')
            self.dump_mem('c', 0xc0000, 0x20000, 'A5_U300_TBC_%s.bin' % ver, 'A5_U400_TBC_%s.bin' % ver)
            self.dump_mem('c', 0xe0000, 0x20000, 'A5_U310_TBC_%s.bin' % ver, 'A5_U410_TBC_%s.bin' % ver)
            self.dump_mem('c', 0x10000, 0x10000, 'A5_U500_TBC_%s.bin' % ver, 'A5_U511_TBC_%s.bin' % ver)

            ver = sanitize_fn(self.subsystems.get('EXP') or 'unknown')
            self.dump_mem('a', 0xfc0000, 0x00040000, 'A18_U800_EXP_%s.bin' % ver, 'A18_U900_EXP_%s.bin' % ver)
            self.dump_mem('a', 0xf80000, 0x00040000, 'A18_U810_EXP_%s.bin' % ver, 'A18_U910_EXP_%s.bin' % ver)
            self.dump_mem('a', 0xf40000, 0x00040000, 'A18_U820_EXP_%s.bin' % ver, 'A18_U920_EXP_%s.bin' % ver)
            self.dump_mem('a', 0xf00000, 0x00040000, 'A18_U830_EXP_%s.bin' % ver, 'A18_U930_EXP_%s.bin' % ver)
            self.dump_mem('a', 0x3e0000, 0x00020000, 'A18_NVRAM_EXP_%s.bin' % ver)

            # self.dump_mem('a', 0x400000, 0x10000)
            # self.dump_mem('a', 0x410000, 0x10000)
            # self.dump_mem('a', 0x420000, 0x10000)
            # self.dump_mem('a', 0x430000, 0x10000)

            print("Success")

        finally:
            time.sleep(1)
            self.exit_test_mode()
            pass

def main():
    device = sys.argv[1]

    with serial.Serial(device, timeout = 0) as ser:
        try:
            tek = Tek(ser)
            tek.run()

        except FriendlyException as e:
            screen_cleanup()
            print(e, file = sys.stderr)
            sys.exit(1)

        finally:
            screen_cleanup()

if __name__ == '__main__':
    # Test for when run from within emacs
    if not sys.argv[0]:
        print()
        sys.argv = [ '',
                     '/dev/serial/by-id/usb-FTDI_Chipi-X_FT2HLN37-if00-port0',
                     ]

    main()
