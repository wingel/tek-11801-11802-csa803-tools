# Tektronix 11801, 11802 and CSA803 tools

This is a collection of random useful tools for the Tektronix 11801,
11802 and CSA803 sampling oscilloscopes.

There are also multiple revisions of the scopes, for example the 11801
can be found in 11801A, 11801B and 11801C variants.  The 11801 was the
first model and is quite different from all the other ones.

The first model of this scope was made in 1988 and many units are
getting a bit long in the tooth.  They can break due to old age or
just bad luck.  For example the batteries for the non volatile
memories (NVRAMs) are running out.  The EEPROMs in the sampling heads
are known to break when plugging them in and out.  And old EPROMs
sometimes just suffer from bit rot and lose their contents.

Since the NVRAMs in the mainframe and the EEPROMs on the sampling
heads contain calibration constants and serial numbers it's a very
good idea to make a backup so that they can be restored if they break.

This repository contains some Python 3 script to use the RS232 on a
mainframe to make a backup of these memories.  It also contains some
scripts to work with these images.

# Quick start

Warning: I have only tested this script on my 11801B, it ought to work
on a 11801A and 11801C without changes.  The CSA803 models should only
differ in the number of acquisition modules and should require fairly
minor modications to work.  The original non-letter 11801/11802 are
very different and the program will most probably need major changes
to the program to work.

The backup program has only been tested on a Linux machine, but might
work on Windows too.

If you make any modifications to these scripts please tell me and I'll
try to include those in my version.  Or just tell me if you found
these useful.

## Prerequisites

An installation of Python 3 is required.

Check out this repository and change to top level directory.

Install some Python 3 packages which are needed with:

```
pip3 install -r requirements.txt
```

## Making a backup

Connect the RS232 port on the scope to a serial port on your PC.  Find
out what the name of the serial port is.  This example assumes that it
is connected to /dev/ttyUSB0 on a Linux machine.

Run the backup script in a ANSI compatible terminal Window:

```
python3 backup.py /dev/ttyUSB0
```

This command will redirect screen output from the scope over RS232.
It will then simulate keypresses over RS232 which tells the scope to
extract data from the different memories and print it to the screen,
that is RS232, and parse the results and dump it to file.

The extraction process is slow and will take about 12 hours to finish.
Be patient

When the process is finished a directory wit EPROM and NVRAM images
for the mainframe will have been created.  The name of the directory
will contain the mainframe model and version.  In the directory there
will be files for each IC with names showing the board name, IC
identifier, which subsystem it belongs to and the version.  The
version information is extracted from the "ID?" string.

For example a directory called "TEK-11801B-V81_1-B012345" with the
following contents:

| Filename                     | Address | Size | Description              |
| :--------------------------- | ------: | ---: | :----------------------- |
| A5-U300-TBC-4_03.bin         |   C0000 |  64k | Time Base                |
| A5-U310-TBC-4_03.bin         |   C0001 |  64k | Time Base                |
| A5-U400-TBC-4_03.bin         |   E0000 |  64k | Time Base                |
| A5-U410-TBC-4_03.bin         |   E0001 |  64k | Time Base                |
| A15-U140-DSY-4_00.bin        |   E0000 |  64k | Display                  |
| A15-U150-DSY-4_00.bin        |   E0001 |  64k | Display                  |
| A18-U800-EXP-4_04.bin        |  FC0000 | 128k | Executive                |
| A18-U900-EXP-4_04.bin        |  FC0001 | 128k | Executive                |
| A18-U810-EXP-4_04.bin        |  F80000 | 128k | Executive                |
| A18-U810-EXP-4_04.bin        |  F80001 | 128k | Executive                |
| A18-U820-EXP-4_04.bin        |  F40000 | 128k | Executive                |
| A18-U820-EXP-4_04.bin        |  F40001 | 128k | Executive                |
| A18-U830-EXP-4_04.bin        |  F00000 | 128k | Executive                |
| A18-U930-EXP-4_04.bin        |  F00001 | 128k | Executive                |
| A28-U611-ACQ1-9_02-UPPER.bin |    8000 |  32k | Acquisition (incomplete) |

Note that the acquisition image is incomplete and only contains the
upper 32kBytes from the 64kByte EPROM.

Also note that if the backup is stopped the program will resume from
where it left off when restarted.  If you want to do a clean backup
from scratch, delete the files you want to redo a backup of.  Also
remove any temporary files called "mem-*" in the directory since the
backup can resume from those files too.

And a directory "MODULES-date-time" with a file per sampling module
with a name containing the model, serial number and when the file was
created.  The reason for having the date is that the module contents
can change over time when new calibration constants are written to the
module.

For example a directory named "MODULES-20220328-2215" with the
following contents

| Filename                        |      Size |
| :------------------------------ | --------: |
| SD-26-B022222.bin | 128 bytes |
| SD-24-B023333.bin | 128 bytes |

## Sharing your images

This is optional, but I would very much appreciate if you can make a
zip file of the "TEK-*" firmware directory and the "MODULE-*" sampling
module directory and mail it to me at [Christer Weinigel
&lt;christer@weinigel.se&gt;](mailto:christer@weinigel.se).  I am very
interesting in collecting as many firmwares as possible for
11801/11802/CSA830 scopes.  On reason is that I'm just curious about
which firmware versions there are out there.  I'd also like to upload
them to the TekWiki so that other people can fix their scopes.

## Replacing the sampling module EEPROMs

The original EPROM in the sampling modules seems to be a National
Semiconductor NMC9346N.  If you manage to break it you can replace it
with just about any compatible serial EEPROM such as an AT93C46E in in
the same 8 pin PDIP package.

If you have forgotten to make a backup of you sampling modules, just
as I did, not all is lot.  You can take an EEPROM image from another
module of the same kind, change the serial number as described below,
and use that image instead.  This repository currently contains images
for a SD-24 and SD-26 in the EXAMPLE-MODULES directory.  It seems to
work well enough, after calibrating the module it seems to work quite
well.

### EEPROM programmers

I have used a Mini Pro TL866 USB Universal Progammer to program a new
EEPROM.  Since I don't have a Windows machine in my lab I couldn't use
the Windows software that came with the programmer, but there is an
open source program available for controlling it from Linux:

* https://gitlab.com/DavidGriffith/minipro/

The Windows software should work too, but I have not tried it
personally.

### Programming the image using Mini Pro

First convert the image from the big endian format used by backup.py
to little endian format which is required by the minipro tool.  For
example, if the EEPROM is called SD-24-B0200024.bin convert it from
big endian forma to little endian format with:

```
./moduletool.py -I big -i SD-24-B020024.bin -O little SD-24-B020024.little
```

I'm not sure if the Windows tool requires this conversion or if it can
work with big endian files.

Connect the Mini Pro to a USB port, and then tell the minipro program
what kind of EEPROM you have with "-p" and that it should write "-w"
the image to the EEPROM:

```
sudo ./minipro -p 'AT93C46(x16)' -w SD-24-B023105.little
```

On the original EEPROM that I desoldered the narrow parts of the pins
had been cut off, but I decided to just bend the pins of the new
EEPROM so that they were fairly flat against the bottom of the package
before soldering it in place.  After replacing the EEPROM my sampling
modules started working again.

### Converting an EEPROM image from the hex dump text format

If you have made a backup of the EEPROM by hand and have a hex dump of
the contents you can also convert the text format to the binary
format.  The default for moduletool is to use the big endian binary
format, specify "-O little" if you want the little endian format.

```
./moduletool.py -I text -i SD-24-B020024.txt SD-24-B020024.little
```

### Changing the serial number in an EEPROM image

This command will read a image, change the serial number, recalculate
the checksum, and write the modified image to a file:

```
./moduletool.py -i SD-24-B020024.bin -s B023456 -o SD-24-B023456.bin
```

# Behind the scenes

Below are a lot of details on the ideas behind the backup script.
This could be useful if you want to make these scripts work on other
models.

## RS232 serial port

The 25 pin DB25 connector on the back is a normal RS232 DCE seriala
port.  Only the TD, RD and GND pins are used.  An old An old DB9 to
DB25 modem cable can be used to connect an USB-RS232 adapter to the
scope.

| Name | Description      | DB25 pin | DB 9 pin |
| ---- | ---------------- | -------: | -------: |
| TD   | Transmitted Data |        2 |        3 |
| RD   | Received Data    |        3 |        2 |
| GND  | Signal Ground    |        7 |        5 |

The default parameters are 9600 bps, 1 stop bit, no parity and no flow
control.

## Normal GPIB mode

The default baudrate in this mode is 9600 bps but can be set as high
as 19200 bps in the menu of the scope.  This setting is stored in
NVWAM and survives a power cycle of the scope.  All commands and
responses are followed by a newline.  Both CR (\r) and LF (\n) are
understood in commands.  Responses are terminated by CR+LF (\r\n).

An example of a command is the identification query (followed by a
newline):

```
ID?
```

With a reponse which looks something like this:

```
ID TEK/11801B,V81.1,TBC/4.03,DSY/4.00,EXP/4.04,ACQM1/9.02,ACQM2/9.02
```

V81.1 probably a version number the whole system.  TBC is time base
controller, DSY is display, EXP is the main executive processor, and
finally ACQM1 and ACQM2 are the acquisition modules.

To show the serial numbers of the mainframe and the sampling heads use:

```
UID?
```

response:

```
UID MAIN:"B021111",M1:"B022222",M3:"B023333",M5:"B024444"
```

For our purposes the most important command is the one used to enter
the Extended Diagnostics.  It can be entered using the touch screen
(Utility->Enhanced Accuracy->Utility2->Extended Diagnostics) or by
sending the following command over the serial port (followed by a
newline):

```
TEST MAN
```

This command will sometimes give an "OK" response, but not always.

For more documentation of the supported commands, see the Programmer
Manual on the respective models page on TekWiki.

## Extended Diagnostics

The commands available in this mode are documented in the service
manuals and diagnostics manual found on TekWiki.

The Extended Diagnostics are normally perfomed using the physival
buttons and touch screen soft buttons on the unit.  Commands sent over
the RS232 port can simulate button presses.  Most available commands
are shown on the screen in parenthesis.  Note that the commands are
case sensitive.  Some "Non-Displayed Commands" are documented on
service manuals.  The "Enter" soft button corresponds to sending CR
(\r) over the RS232 port, LF (\n) will sometimes not work.

The Extended Diagnostics baudrate defaults to 9600 bps, so the
baudrate of your terminal will have to be changed to this after
issuing "TEST MAN".  Note, this baudrate is set Diagnostic Options
jumpers on the Input/Output Board, so it might not be 9600 bps on your
device.

"B&lt;baud rate&gt;" followed by &lt;CR&gt;
: Change baud rate.  Supported baud rates are 9600, 19200 and 38400
bps.  The baudrate change takes effect immediately.

"T"
: Toggle the output between the touch screen and ANSI escape codes
over the RS232 port.

"K"
: Toggle the output between the touch screen and Tektronix 4105 or
4205 escape codes over the RS232 port.

"L"
: Toggle the output between the touch screen and Tektronix 5107, 4109,
4207, or 4208 escape codes over the RS232 port.

"H"
: Produce a hardcopy of the current diagnostic display.

"O"
: Equivalent to the Touch Panel On/Off button.

"W"
: Equivalent to the Waveform button.

"Q"
: Equivalent to the Acquisition Run/Stop button.

The Low-Level Debugging command is disabled by default.  To enable it,
press the Waveform button five times followed by the Touch Panel
On/Off button.  This can also be performed by sending "WWWWWO" over
the RS232 port.

## Extended diagnostics over RS232 port

To switch the output over to the RS232 port, wait until the menu has
been drawn on the touch screen and then send "T" over the RS232 port.

Any commands sent over RS232 will be ignored until the menu has been
drawn a first time.  If you can't see the screen, it takes about 5
seconds from issuing the "TEST MAN" command until the menu has been
drawn and the device will recognize "T" sent over the RS232 port.

If you happen to have a Tektronix 4000 series terminal you could use
the "L" or "K" commands, but such terminals are rare nowdays and as
far as I know there is no terminal emulator available for them either.

To speed up dumping memory it's recommended to switch to the highest
baudrate supported by the scope.  Send "B38400" followed by &lt;CR&gt; and
then configure your terminal program to 38400 bps.

## Backing up the EEPROM contents of a sampling module

The sampling module in slots 1 and 2 are head number 1 and 2 on Acq 1.
The sampling module in slots 3 and 4 are head number 1 and 2 on Acq 2.

* Make sure the bottom right soft button says "(r) Run" and "Stopped".
If not, select "(q) Quit" to stop any running tests.

* Select "(1) Subsystem" and "d) Main Acq"

* Select "(2) Block" and "a) Acq 1 or "b) Acq 2"

* Select "(3) Area" and "g) Excercisers"

* Select "(4) Routine" and "e) Registers"

* Select "(r) Run" to start the test.

* At the "Select function" prompt enter "2" followed by &lt;CR&gt; for
  "Display sampling head eeprom contents"

* At the "Enter head number" prompt enter "1" or "2" followed by &lt;CR&gt;

The contents of the EEPROM of the sampling module will be shown as
eight lines with eight 16-bit hexadecimal words.  Copy those lines to
a file.

* Select "(X) Exit" to exit the test.  Repeat the processes for the
sampling modules in other slots.

### Sampling head EEPROM format

The contents of the sampling head EEPROMs are 128 bytes.

| Addr (hex) | Addr (dec)  | Description                 |
| ---------: | ----------: | --------------------------- |
| 0x00..0x6d |      0..109 | Unknown                     |
| 0x6e..0x75 |    110..117 | Model, e.g. SD-24           |
| 0x76..0x7d |    118..125 | Serial number. e.g. B020024 |
| 0x7e..0x7f |    126..127 | Checksum                    |

Strings such as the model and serial number are padded on the right
with spaces (ASCII 32).

To verify the checksum, convert the image into 64 big endian 16 bit
words and sum all words.  If the checksum is correct the low 16 bits
of the sum should be 0.  To update the checksum, calculate the sum of
the first 63 words, and negate it and take the low 16 bits and place
them in the last word.  Convert the words back to bytes.

TODO Try to collect multiple modules and compare the contents and
see if we can figure out the meaning of the unknown data.

## Mainframe memories (EPROM and NVRAM)

There are multiple subsystems in the oscilloscope with multiple memory
ICs.  Most of the models seem to have the same names for the EPROMs,
except for the original 11801 which has a totally different set of
EPROMs.  The main difference seems to be that the 11801 uses two pairs
of two 27C512 EPROMs spread out over two boards for the Executive
firmware while the other models use 27C1000 EPROMs on just one board.

It is possible to discover where the EPROMs are mapped into the
memory space of each subsystem using the extended diagnostics and the
"ROM Checksum" test.

### Executive subsystem EPROM

The main "Executive" subsystem uses an Intel 80286 processor with 24
bits or 16MBytes of address space.  To find the memory locations of
the eight EPROMs associated with it make the following menu choices:

* "(1) Subystem" and "a) Executive"
* "(2) Block" and "a) Exec Control"
* "(3) Area" and "b) ROM Checksum"
* "(4) Routine"
* Make sure "(x) All" is set "On"
* Press "(r) Run" to run the test

The top row of buttons should look like the first line below.  Above
that there should be a list of tests that have passed.  On my 11801B
with a version V4.04 EPROM it looks like this:

```
Executive  Exec Control   ROM Checksum       U800

    ROUTINE      INDEX  FAULTS  ADDRES  EXPECT  ACTUAL

a) U800           pass          FC0000    2521    2521
b) U900           pass          FC0001    2C5D    2C5D
c) U810           pass          F80000    E6D3    E6D3
d) U910           pass          F80001    6938    6938
e) U820           pass          F40000    18EE    18EE
f) U920           pass          F40001    B895    B895
g) U830           pass          F00000    8B29    8B29
h) U930           pass          F00001    ECCF    ECCF
```

ROUTINE is the name of the EPROM on the board. ADDRESS is where each
EPROM is mapped into the memory space.  EXPECT is the checksum which
is stored in the first two bytes of each EPROM.  ACTUAL is the
checksum that has been calculated from the data.

The EPROMs on the A18 board are 27C1000 with 1024kbits or 128kBytes
each.  The EPROMs on the other boards are 27C512 with 512kbits or
64kBytes each.

Each pair of EPROMs are interleaved.  For eample U800 contains even
bytes and U900 contains odd bytes.  This means that U800/U900 together
make upp 256kBytes of memory mapped from address FC0000 to FDFFFF.

The data from these addresses can be read out using the Low-Level
Hardware Debugger described below.

### Executive NVRAM

There is a test for the executive NVRAM which looks like this:

```
Executive  Exec Control       NVRAM      Address/Data

    ROUTINE      INDEX  FAULTS  ADDRES  EXPECT  ACTUAL

a) Battery        pass          3E0002    2152    2152
b) Data Lines     pass          3E0000    8000    8000
c) Address/Data   pass          43FFFE    AAAA    AAAA
```

There is some kind of memory at address 3E000 which contains the
mainframe serial number and also seems to have a log of messages.  I'm
assuming that this is the NVRAM and that there is 256kBytes of it
mapped from address 3E0000 to 3FFFFF.

```
003e0000  ad de 52 21 ad de 52 21  34 2e 30 34 00 a2 00 00  |..R!..R!4.04....|
003e0010  80 40 40 00 01 00 c0 18  42 30 32 33 34 35 36 00  |.@@.....B023456.|
003e0020  00 00 00 00 00 01 00 80  94 02 ae 41 01 00 76 24  |...........A..v$|
003e0030  00 00 39 08 20 20 20 34  33 20 30 32 2f 32 35 2f  |..9.   43 02/25/|
003e0040  39 37 20 31 30 3a 35 33  3a 31 33 20 20 33 38 36  |97 10:53:13  386|
003e0050  20 4d 69 6e 6f 72 20 74  69 6d 65 20 62 61 73 65  | Minor time base|
003e0060  20 63 61 6c 69 62 72 61  74 69 6f 6e 20 70 72 6f  | calibration pro|
003e0070  62 6c 65 6d 3a 20 31 36  00 20 20 31 33 31 20 30  |blem: 16.  131 0|
```

TODO Find out what physical chips on A18 actually store the NVRAM data

### Display subsystem EPROM

The "Display" subsystem uses an Intel 80186 processor with 20 bits or
1Mbyte of address space.

```
 Display    Dsy Control   ROM Checksum       U140

    ROUTINE      INDEX  FAULTS  ADDRES  EXPECT  ACTUAL

a) U140           pass          0E0000    4875    4875
b) U150           pass          0E0001    9989    9989
```

It has one pair of 27C512 EPROMs: U140/U150 which gives 128kBytes that
are mapped att address E0000 to FFFFF.

### Time Base subsystem EPROM

The "Time Base" subsystem also uses an Intel 80186 processor.

```
    ROUTINE      INDEX  FAULTS  ADDRES  EXPECT  ACTUAL

a) U300           pass          0C0000    4C1F    4C1F
b) U310           pass          0C0001    6877    6877
c) U400           pass          0E0000    10D1    10D1
d) U410           pass          0E0001    AB0E    AB0E
```

It has two pairs of 27C512 EPROMs which are mapped at C0000 to CFFFF
and E0000 to EFFFF.

### Time base NVRAM

The time base board has four 128kbit / 32kByte SRAMs chips.  Two of
them, U500 and U511, sit in a battery powered socket.  The unpowered
ones are probably mapped to address 00000 to 0ffff.  The battery
powered ones are reportedly mapped to address 10000 to 1ffff.

This memory contains some kind of serial number and calibration for
the time base controller.  There are reports of the time base becoming
wildly out of spec if the contents if this NVRAM are lost.

### Acquisition subsystem EPROM

Each acquisition board (one on the 11802 and CSA devices, two on the
11801 models) has a Motorola 6809 processor with 16 bits of address
space.  The two boards should have identical contents.

```
     ROUTINE      INDEX  FAULTS  ADDRES  EXPECT  ACTUAL

a) ROM Loc        pass          428800    00F0    00F0
b) ROM Check      pass          008000    F622    F622
c) RAM Data       pass          004001    0000    0000
d) RAM Address    pass          006000    00AA    00AA
```

The name of this EPROM is not shown in the self test, but it is called
U611 in the service manual.  This is actually a 64kByte EPROM but the
address space from 8000 to FFFF is only 32kBytes.  There must be some
kind of bank switching going on and I'm not sure it it is possible to
read out the whole EPROM using software.

## Dumping memory using Low-Level Debugger

To dump memory one has to use the Low-Level Hardware Debugger.  This can be
dangerous since the debugging mode can also write to memory.  Be
careful.

If the debugger is normally disabled (not highlighted) and can't be
selected, send "WWWWWO" to enable it.

* Use "(1) Subsystem" and choose which subsystem the memory is
connected to.

* Use "(D) Debugger" to enter the debugging mode.

* Make sure that "(o) Operation is set to "Read"

* Make sure that "(m) Memory/IO" is set to "Memory"

* Make sure "x" (8/16 bit) is set to "16".  For dumping normal memory
8 bit mode will work too, but 16 bit mode is faster since the output
is slightly more compact.  For most EPROMs the words are little
endian, for the acquisition EPROM the words are big endian.

Enable logging in your terminal program so that the output is saved to
a file.  Send "T" (Test) to start the test and the dump memory.  This
file can then be parsed to extract the memory contents.

## Setting serial numbers

According to the service manual it should be possible to change the
serial number of a unit using the RS232 port.

> Locate the manufacturing jumper, J860, on the A5 Time
> Base/Controller board (see Figure 6-10), and install the terminal
> connector link.
>
> After the instrument is powered on, to establish communication
> from the terminal or controller, enter the following commands
> (&lt;CR> is the return key):
>
> e&lt;CR>
> v&lt;CR>
>
> Verify that the serial number on the instrument's front panel matches
> the mainframe ID number in the pop-up menu in the UTILITY major menu.
> If the numbers do not match, then enter the command:
>
> ```
> uid main:"BXXXXXX"&lt;CR>
> ```
>
> where corresponds to the serial number digits found on the front
> panel serial number marker.

If the UID command in the manufacturing mode uses the same naming for
the sampling heads, it may be possible to change the serial number of
a sampling heads by using "uid m1" for the head in slot 1, "uid m3"
for slot 2, "uid m5" for slot 3 and "uid m7" for slot 4.  All of this
is speculation though.

# Random stuff

## Differences between models

The original 11801 is quite different from the later models.  It has a
different set of boards.  The EPROMS are different and have different
names.  The acquisition boards are totally different.  All later
versions seem to have a lot more hardware in common.

My guess is that when the 11801 became popular Tektronix optimised the
design a bit for the 11801A by simplifying the design slightly and
reducing the number of boards.  All later models share the same basic
design with only small changes.

With regards to functionality the models called 11801 have four slots
for sampling modules.  The 11802 models replaced the two leftmost
slots with two delay lines.  The CSA803 was originally called 11803 it
was then branded as a "Communications Signal Analyzer" and added some
functionality in the firmware to verify signal masks.  The the two
leftmost slots on the CSA803 only provide power and can't be used for
sampling.  The trigger inputs on the CSA830 also differ.

Based on the service manuals found on the TekWiki these are the
differences between the different models (original 11801 not included
since it is so different anyway):

|       | 11801B      | 11801C      | CSA803      | CSA803A     | CSA803C     | Description                                  |
| :---- | :---------- | :---------- | :---------- | :---------- | :---------- | :------------------------------------------- |
| A5    | 671-2931-00 | 672-0386-00 |             |             |             | Time Base/Controller (Standard)              |
| A5    | 671-2929-00 | 672-0385-00 |             |             |             | Time Base/Controller (w/Option 1M)           |
| A5    |             |             | 671-1479-00 | 671-2813-01 | 672-0383-00 | Time Base/Controller w/ Prescaler (Standard) |
| A5    |             |             | 671-1479-50 | 671-2813-51 | 672-0384-00 | Time Base/Controller w/o Prescaler (Opt. 10) |
| A6    |             | 671-4471-00 | 657-0058-00 |             | 671-4471-00 | 671-4471-00  Calibrator                      |
| No A# |             | 657-0081-01 |             |             |             | Trigger Prescaler Hybrid                     |
| A9    | 614-0916-00 | 614-0940-00 | 614-0864-00 |             |             | Touch Panel Assembly                         |
| A14   | 670-8854-02 | 670-8854-04 | 670-8854-04 | 670-8854-04 | 670-8854-04 | Input/Output                                 |
| A15   | 671-1023-02 | 671-1023-02 | 671-1023-50 | 671-1023-02 | 671-1023-02 | MMU                                          |
| A17   | 671-2888-00 | 671-2888-00 | 671-1024-50 | 671-2888-00 | 671-2888-00 | Executive Processor                          |
| A18   | 671-1890-00 | 671-1890-00 | 671-1575-00 | 671-1890-00 | 671-1890-00 | Memory                                       |
| No A# |             |             | 657-0074-00 | 657-0089-00 | 657-0089-00 | Acquisition Module                           |
| A24   | 671-9364-04 | 670-9364-05 |             |             |             | Acquisition Analog (P/O 657-)                |
| A27   | 671-9364-04 | 670-9364-05 | 670-9364-00 | 670-9364-05 | 670-9364-05 | Acquisition Analog (P/O 657-)                |

Only hardware Hardware which differs between models is listed above.
This means that boards such as the motherboard (671-1192-00) and
Acquisition MPU are identical between all models (670-9363-01).

Unfortunately I have been unable to find a service manual for the
11801A.

Reportedly a 11801A can run the 11801B firmware, and a 11801B can run
the 11801C firmware if some unspecified hardware is upgraded.

# Resources

## TekScopes group

* https://groups.io/g/TekScopes

How to do these backups was inspired by this post:

* https://groups.io/g/TekScopes/topic/38764672

About firmware compatibility between different models:

* https://groups.io/g/TekScopes/message/161104

## TekWiki

TekWiki contains a lot of information about Tektronix equipment in
general.

* https://w140.com/tekwiki/wiki/11801
* https://w140.com/tekwiki/wiki/11802
* https://w140.com/tekwiki/wiki/CSA803

There are also ROM dumps from a lot of Tektronix devices:

* https://w140.com/tekwiki/wiki/ROM_images
