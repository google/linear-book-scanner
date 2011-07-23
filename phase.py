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
from PIL import Image
from pnm import pnm_header
from detect import extent_of_stripes

carrier = None

def calculate_windowed_complex_exponential(period, N):
  t = numpy.mgrid[0:N] - .5 * (N - 1)
  # window = 0.54 + 0.46 * numpy.cos(2 * numpy.pi * (t / N )) # Hamming window
  window = numpy.sinc(t / (N / 2 + N % 2)) # Lanczos window
  omega = 2 * numpy.pi / period
  return window * numpy.exp(-1j * omega * t)

def find_phase(scanline, channels):
  '''Estimates wave phase by de-modulating the input square wave with a
  windowed complex exponential of the same frequency.'''
  ## The length of our signal.
  scanwidth = len(scanline) // channels
  length = extent_of_stripes(scanwidth)
  ## Convert to numpy
  b = numpy.fromstring(scanline, dtype=numpy.uint8)
  ## Work with green pixel
  if channels == 1:
    d = b[0:length]
  elif channels == 3:
    d = b[1:1 + 3 * length:3]
  else:
    raise("BUG")
  kScanbarPixels = 2524   # When run at 300 ppi
  period = 24.0 * scanwidth / kScanbarPixels
  global carrier
  if carrier == None:
    carrier = calculate_windowed_complex_exponential(period, length)
  coeff = numpy.dot(carrier,d)
  phi = numpy.arctan2(numpy.real(coeff), numpy.imag(coeff)) 
  delta = phi * period / (2 * numpy.pi)
  return delta, period

if __name__ == "__main__":
  linewidth, linecount, channels = pnm_header()
  linesize = linewidth * channels
  while True:
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      break
    phase, period = find_phase(scanline, channels)
    ## Paint the detected edges red if we can
    if channels == 3:
      scanlinearr = numpy.fromstring(scanline, dtype=numpy.uint8)
      length = 60
      phase_i = int(phase) + length
      scanlinearr[phase_i * 3:phase_i * 3 + 3] = [255, 0, 0]
      sys.stdout.write(scanlinearr)
    else:
      sys.stdout.write(scanline)
