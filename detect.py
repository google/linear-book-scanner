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
from ppm_header import ppm_header

def extent_of_stripes(scanline):
  w = len(scanline) // 3
  kFractionOfSensor = .04 # portion containing strip   
  n = int(w * kFractionOfSensor) * 3
  return n

def detect_stripes(scanline):
  """Are we on the barber stripe or not?"""
  n = extent_of_stripes(scanline)
  roi = scanline[:n]
  kDarkThreshold = 80
  kLightThreshold = 100
  a = numpy.fromstring(roi, dtype=numpy.uint8)
  black = len(numpy.where(a < kDarkThreshold)[0])
  white = len(numpy.where(a > kLightThreshold)[0])
  balance = abs(black - white) / float(len(roi))
  coverage = (black + white) / float(len(roi))
  if balance < 0.35:
    if coverage > 0.7:
      return True
  return False

if __name__ == "__main__":
  linesize, linecount = ppm_header()
  page_number = 0
  scanline = sys.stdin.read(linesize)
  prev_scanline = scanline
  while True:
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      break
    if detect_stripes(scanline):
      sys.stdout.write(scanline)
