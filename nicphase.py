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
from PIL import Image
from ppm_header import ppm_header
import numpy as np

def find_phase(scanline):
  """ Not yet implemented. """
  qq = np.array(scanline[1::3],dtype=np.float)
  diff=qq[1:]-qq[:-1]
  edges = np.nonzero(diff > 100)[0]
  if edges!=[]:
    return edges[0] % 23
  else:
    return 0


if __name__ == "__main__":
  linesize, linecount = ppm_header()
  while True:
    scanline_string = sys.stdin.read(linesize)
    scanline = np.fromstring(scanline_string, dtype=np.uint8)
    if len(scanline) != linesize:
      break
    phase = find_phase(scanline)
    sys.stderr.write("%5.2f \n" % phase)

    if phase > 1 and phase < linesize/3-1:
      pt=phase*3
      scanline[pt:pt+3]=[255,0,0]
      scanline[pt-3:pt]=[ 32, 32, 32]

    sys.stdout.write(scanline)
