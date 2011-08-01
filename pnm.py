#!/usr/bin/python2.6
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import stat
import tempfile

def pnm_header():
  """Pass through the pnm header. Returns size of scanline in bytes, and
  the number of rows."""
  magic_number, comment, dimensions, max_value = read_pnm_header(sys.stdin)
  if magic_number == "P6\n":
    channels = 3
  elif magic_number == "P5\n":
    channels = 1
  else:
    raise ValueError("Unsupported format %s" % magic_number)
  linewidth = int(dimensions.split(" ")[0])
  linecount = int(dimensions.split(" ")[1])
  sys.stdout.write(magic_number)
  sys.stdout.write(comment)
  sys.stdout.write(dimensions)
  sys.stdout.write(max_value)
  return linewidth, linecount, channels

def read_pnm_header(fp):
  """ Read the image header from stdin and parse it."""
  magic_number = fp.readline()
  if len(magic_number) != 3 or magic_number[0] != "P":
    raise TypeError("Hey! This is not image data.")
  comment = fp.readline()
  if comment[0] == "#":
    dimensions = fp.readline()
  else:
    dimensions = comment
    comment = "# Cheesegrater\n"
  max_value = fp.readline()
  if max_value != "255\n":
    raise ValueError("I only work with 8 bits per color channel")
  return (magic_number, comment, dimensions, max_value)

def fix_pnm_file(filename):
  """ Fix the number of rows in the header. Useful if someone
  has truncated a pnm image, but you still want to open it with
  a standard viewer."""
  filesize = os.stat(filename)[stat.ST_SIZE]
  src = open(filename)
  magic_number, comment, dimensions, max_value = read_pnm_header(src)
  w = int(dimensions.split(" ")[0])
  linesize = w
  if magic_number == "P6":
    linesize *= 3
  h = filesize // linesize
  tmpfile, tmpfilename = tempfile.mkstemp()
  os.write(tmpfile, magic_number)
  os.write(tmpfile, comment)
  os.write(tmpfile, "%d %d\n" % (w, h))
  os.write(tmpfile, max_value)
  while True:
    scanline = src.read(linesize)
    if len(scanline) != linesize:
      break
    os.write(tmpfile, scanline)
  os.close(tmpfile)
  src.close()
  os.rename(tmpfilename, filename)

if __name__ == "__main__":
  fix_pnm_file(sys.argv[1])
