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
import pygame
from pnm import pnm_header

def marker_string():
  """This marker should survive reversal of scanline"""
  return "PPPaaagggeeefffeeeeeeddd"

def insert_pagefeed(linesize):
  """Add a page feed to the image stream."""
  marker = marker_string()
  reverse_marker = marker[::-1]
  sys.stdout.write(marker)
  for i in range(linesize - 2 * len(marker)):
    sys.stdout.write(" ")
  sys.stdout.write(reverse_marker)
  sys.stdout.flush()

def detect_pagefeed(scanline):
  """Notice a page feed in the image stream."""
  marker = marker_string()
  n = len(marker)
  if scanline[0:n] == marker:
    return True
  else:
    return False

def write_pnm(page_number, scanlines, channels):
  """Write out a single page image to the playground. Ignore
  any images that are smaller than the caddy. Use audio alerts
  to indicate what is happening."""
  pygame.mixer.init()
  beep = pygame.mixer.Sound('beep.wav')
  boop = pygame.mixer.Sound('boop.wav')
  w = len(scanlines[0]) // channels
  h = len(scanlines)
  kCaddyAspectRatio = 0.8
  kNoiseThreshold = 3
  if h < kNoiseThreshold:
    return False
  if h < w / kCaddyAspectRatio:
    boop.play()
    return False
  kDir = "/tmp/playground"
  if not os.path.exists(kDir):
    os.mkdir(kDir)
  if channels == 3:
    magic_number = "P6"
    extension = "ppm"
  elif channels == 1:
    magic_number = "P5"
    extension = "pgm"
  else:
    raise ValueError("Unsupported channel count: %d" % channels)
  header = "%s\n%d %d\n255\n" % (magic_number, w, h)
  filename = os.path.join(kDir, "page-%d.%s" % (page_number, extension))
  f = open(filename, "wb")
  f.write(header)
  for i in range(h):
    f.write(scanlines[i])
  f.close()
  beep.play()
  return True

def process(page_number):
  """Split up the image stream into separate pages, and store them.
  Take care of mirror image effect while we are at it."""
  linewidth, linecount, channels = pnm_header()
  linesize = linewidth * channels
  scanlines = []
  while True:
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      break
    if page_number % 2 == 1:
      scanline = scanline[::-1]
    sys.stdout.write(scanline)
    sys.stdout.flush()
    if detect_pagefeed(scanline):
      if write_pnm(page_number, scanlines, channels):
        page_number += 2
      scanlines = []
    scanlines.append(scanline)

if __name__ == "__main__":
  page_number = 0
  if len(sys.argv) == 2:
    page_number = int(sys.argv[1])
  process(page_number)
