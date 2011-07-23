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

Vit = None

def calculate_prony_matrix(period,t):
  ## Angular frequency
  w_1 = 2*numpy.pi/period
  ## How many partials fit in the frequency space for this given frequency.
  ## i.e. how many are below Nyquist freq.
  lastpartial = numpy.floor(period / 2)
  ## Harmonic "indices" k. Skip the evens ones because it's a square wave...
  k = numpy.mgrid[1:lastpartial+1:2]
  ## The component frequencies.
  w_k=w_1*numpy.array([k])
  V = numpy.exp(numpy.dot(t.T, 1j * numpy.c_[w_k, 0, -w_k]))
  Vit = numpy.linalg.pinv(V)
  return Vit

def find_phase(scanline, channels):
  '''Estimates wave phase using Prony's method. Vit is the
  pseudo-inverse of the Van der Monde matrix that contains the
  component waves, complex-exponential harmonics.'''
  ## The length of our signal.
  scanwidth = len(scanline) // channels
  length = extent_of_stripes(scanwidth)
  ## Time variable (sample index).
  t = numpy.mgrid[:length,]
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
  w_1 = 2 *numpy.pi / period
  global Vit
  if Vit == None:
    Vit = calculate_prony_matrix(period, t)
  x = numpy.dot(Vit, d)
  phi1 = numpy.arctan2(numpy.real(x[0]), numpy.imag(x[0]))
  phi = phi1
  delta = phi * period / (2 * numpy.pi)
  return delta, period

if __name__ == "__main__":
  linewidth, linecount, channels = pnm_header()
  linesize = linewidth * channels
  while True:
    scanline = sys.stdin.read(linesize)
    scanlinearr = numpy.fromstring(scanline, dtype=numpy.uint8)
    if len(scanline) != linesize:
      break
    length = 60
    phase, per = find_phase(scanline, channels)
    phase_i = int(phase) + length
    ## Paint the detected edges red if we can
    if channels == 3:
      scanlinearr[phase_i * 3:phase_i * 3 + 3] = [255, 0, 0]
    sys.stdout.write(scanlinearr)
