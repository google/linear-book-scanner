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

import os
import sys
from ppm import ppm_header

def insert_pagefeed(linesize):
  """Add a page feed to the image stream."""
  sys.stdout.write("Pagefeed")
  for i in range(linesize - 8):
    sys.stdout.write(" ")

def detect_pagefeed(scanline):
  """Notice a page feed in the image stream."""
  if scanline[0:8] == "Pagefeed":
    return True
  else:
    return False

def write_ppm(page_number, scanlines):
  """Write out a single page image to the playground."""
  w = len(scanlines[0]) / 3
  h = len(scanlines)
  if h < w:
    return False
  kDir = "/tmp/playground"
  if not os.path.exists(kDir):
    os.mkdir(kDir)
  filename = os.path.join(kDir, "page-%d.ppm" % page_number)
  f = open(filename, "wb")
  f.write("P6\n%d %d\n255\n" % (w, h))
  for i in range(h):
    f.write(scanlines[i])
  f.close()
  return True

def process(page_number):
  """Split up the image stream into separate pages, and store them."""
  linesize, linecount = ppm_header()
  scanlines = []
  while True:
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      break
    if detect_pagefeed(scanline):
      if write_ppm(page_number, scanlines):
        page_number += 2
      scanlines = []
    scanlines.append(scanline)

if __name__ == "__main__":
  page_number = 0
  if len(sys.argv) == 2:
    page_number = int(sys.argv[1])
  process(page_number)
