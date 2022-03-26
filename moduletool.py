#! /usr/bin/python3
from __future__ import division, print_function, unicode_literals

import sys
import struct
from optparse import OptionParser

def read_text(f):
    words = []
    for l in f:
        l = l.strip()
        if l.startswith('#'):
            continue
        t = [ int(_, 16) for _ in l.split() ]
        if len(t) != 8:
            print("error: each line of input must contain 8 words",
                  file = sys.stderr())
            sys.exit(1)
        words.extend(t)
    if len(words) != 64:
        print("error: input must contain 8 lines", file = sys.stderr)
        sys.exit(1)
    data = struct.pack('>64H', *words)
    return data

def read_bin(f):
    data = f.read()
    if len(data) != 128:
        print("error: input must be 128 bytes", file = sys.stderr())
        sys.exit(1)
    return data

def write_text(f, data):
    words = list(struct.unpack('>64H', data))
    for i in range(0, len(words), 8):
        print(' '.join('%04x' % _ for _ in words[i:i+8]), file = f)

def write_bin(f, data):
    f.write(data)

def byteswap(data):
    return struct.pack('>64H', *struct.unpack('<64H', data))

def main():
    parser = OptionParser()
    parser.add_option('-I', '--input-format', dest = 'infmt',
                      help = "input format: big (default), little, text",
                      metavar = "FMT")
    parser.add_option('-i', '--input', dest = 'infn',
                      help = "read input from FILE",
                      metavar = "FILE")
    parser.add_option('-O', '--output-format', dest = 'outfmt',
                      help = "output format: big (defalt), little, text",
                      metavar = "FMT")
    parser.add_option('-o', '--output', dest = 'outfn',
                      help = "write output to FILE",
                      metavar = "FILE")
    parser.add_option('-s', '--serial', dest = 'serial',
                      help = "change serial number to SERIAL",
                      metavar = "SERIAL")
    parser.add_option('-c', '--checksum', dest = 'checksum',
                      help = "calculate new checksum",
                      action = 'store_true')

    (options, args) = parser.parse_args()

    if len(args):
        print("%s: error: this program takes no arguments", file = sys.stderr)
        sys.exit(1)

    if options.infmt not in [ None, 'big', 'little', 'text' ]:
        print("error: invalid input format %s" % repr(options.infmt),
              file = sys.stderr)

    if options.outfmt not in [ None, 'big', 'little', 'text' ]:
        print("error: invalid output format %s" % repr(options.outfmt),
              file = sys.stderr)

    if options.infn is None or options.infn == '-':
        f = sys.stdin
        indesc = 'stdin'
    else:
        f = open(options.infn, 'r')
        indesc = repr(options.infn)

    if options.infmt == 'text':
        print("reading text data from %s" % indesc)
        data = read_text(f)
    else:
        if options.infmt == 'little':
            print("reading little endian data from %s" % indesc)
        else:
            print("reading big endian data from %s" % indesc)
        data = read_bin(f.buffer)
        if options.infmt == 'little':
            data = byteswap(data)

    if len(data) != 128:
        print("invalid file size, must be 128 bytes", file = sys.stderr)
        sys.exit(1)

    model = data[0x6e:0x76].decode('ASCII', errors = 'replace').strip()
    serial = data[0x76:0x7e].decode('ASCII', errors = 'replace').strip()
    print("model %s, serial %s" % (repr(model), repr(serial)))

    if options.serial:
        if len(options.serial) != 7:
            print("serial number must be 7 bytes", file = sys.stderr)
            sys.exit(1)

        print("setting serial number to %s" % repr(options.serial),
              file = sys.stderr)

        serial = options.serial

        data = data[:0x76] + b'%-08s' % serial.encode('ASCII') + data[0x7e:]

    words = list(struct.unpack('>64H', data))
    chk = -sum(words[:63]) & 0xffff
    if options.serial or options.checksum:
        print("setting checksum to 0x%04x" % chk, file = sys.stderr)
        words[63] = chk
    elif chk != words[63]:
        print("invalid checksum 0x%04x, calculated 0x%04x" % (words[-1], chk),
              file = sys.stderr)
        sys.exit(1)
    data = struct.pack('>64H', *words)

    if options.outfmt and options.outfn is None:
        options.outfn = '-'

    if options.outfn is not None:
        if options.outfn == '-':
            f = sys.stdout
            outdesc = 'stdout'
        else:
            f = open(options.outfn, 'w')
            outdesc = repr(options.outfn)

        if options.outfmt == 'text':
            print("writing text data to %s" % outdesc)
            print("# %s %s" % (model, serial), file = f)
            write_text(f, data)
        else:
            if options.outfmt == 'little':
                print("writing little endian data to %s" % outdesc)
                data = byteswap(data)
            else:
                print("writing big endian data from %s" % outdesc)
            write_bin(f.buffer, data)

if __name__ == '__main__':
    if not sys.argv[0]:
        sys.argv = [ '' ]

        if 1:
            sys.argv += [ '-s', 'B020024' ]

        if 1:
            sys.argv += [ '-I', 'text',
                          '-i', 'EXAMPLE-MODULES/SD-24-B020024.txt' ]
        elif 1:
            sys.argv += [ '-I', 'big',
                          '-i', 'EXAMPLE-MODULES/SD-24-B020024.bin' ]

        if 0:
            sys.argv += [ '-O', 'big',
                          '-o', 'SD-24-B020024.be' ]
        elif 0:
            sys.argv += [ '-O', 'little',
                          '-o', 'SD-24-B020024.le' ]
        elif 0:
            sys.argv += [ '-O', 'little',
                          '-o', 'SD-24-B020024.txt' ]
        elif 1:
            sys.argv += [ '-O', 'text' ]

    main()
