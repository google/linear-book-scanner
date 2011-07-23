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
import numpy
from pnm import pnm_header

def extent_of_stripes(scanwidth):
  """Stripe should cover at least this many pixels."""
  kFractionOfSensor = .025
  return int(scanwidth * kFractionOfSensor)

def detect_stripes(scanline, channels):
  """Are we on the fiducial stripe or not?"""
  scanwidth = len(scanline) // channels
  n = extent_of_stripes(scanwidth) * channels
  roi = scanline[:n]
  kThreshold = 15
  a = numpy.fromstring(roi, dtype=numpy.uint8)
  avg = numpy.average(a)
  black = len(numpy.where(a < avg - kThreshold)[0])
  white = len(numpy.where(a > avg + kThreshold)[0])
  balance = abs(black - white) / float(n)
  coverage = (black + white) / float(n)
  if balance < 0.35:
    if coverage > 0.7:
      return True
  return False

if __name__ == "__main__":
  linewidth, linecount, channels = pnm_header()
  linesize = linewidth * channels
  page_number = 0
  scanline = sys.stdin.read(linesize)
  prev_scanline = scanline
  while True:
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      break
    if detect_stripes(scanline, channels):
      sys.stdout.write(scanline)
