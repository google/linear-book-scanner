August 16, 2012
Jeff Breidenbach

This software supports the linear book scanner. It has been tested on
MacOS and Ubuntu 12.04. Instructions for Ubuntu follow. If you have
complete and working hardware, you may begin scanning by running the
top level script.

$ ./scan

=== top level directory ===

The top level directory contains everything needed for scanning.
Besides the run script, it contains a graphical user interface for
display, manipulation, and export of scanned images. The viewer lives
may be run independently of the hardware, and performs best on systems
with solid state storage.

$ sudo apt-get install python-pygame     # required for viewer
$ sudo apt-get install python-reportlab  # required for PDF output
$ sudo apt-get install tesseract-ocr     # required for searchable PDF output
$ ./viewer.py testdata                   # self test, no hardware required

=== motor subdirectory ===

This directory contains software for an mDrive microcontroller. This
assembly language program controls image synchronization, integration
with the break beam sensor, and motor control.  The majority of the
files are for debug purposes only, for example manual motor movement
commands, or a sensor diagnosis program to help aim the break beam
sensor during hardware construction. For programming reference,
consult your favorite internet search engine for "Programming and
Software Reference for: MCode". To program the motors, run the
following command.

$ ./program_motors

=== sane subdirectory ===

This directory contains patches to SANE (Scanner Access Now Easy).
The patch is required to allow the off the shelf scanning hardware to
run in a modified state; for example disabling paper sensors or
changing calibration routines. You must retrieve the SANE source code,
apply these patches, and install them on the computer attached to the
hardware. These example commands are beyond the scope of this
document; consult a local Linux expert as needed.

$ sudo apt-get install pbuilder
$ apt-get source sane-backends
$ patch -p0 < sane-canon-dr.diff
$ sudo pbuilder create
$ sudo pbuilder build sane-backends*.dsc
$ sudo dpkg -i /var/cache/pbuilder/result/libsane-common*.deb
$ sudo dpkg -i /var/cache/pbuilder/result/libsane_*.deb
$ sudo dpkg -i /var/cache/pbuilder/result/sane-utils*.deb

=== testdata subdirectory ===

This directory contains a limited number of sample images. Their sole
purpose is to help test and verify the viewer program, even in the
complete absence of working hardware.
