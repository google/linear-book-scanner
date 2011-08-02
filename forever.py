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

import subprocess
import sys
import pnm
import os

def pass_just_the_pixels(fp):
  magic_number, comment, dimensions, max_value = pnm.read_pnm_header(fp)
  pass_the_whole_file(fp)

def pass_the_whole_file(fp):
  chunksize = 10000
  while True:
    data = fp.read(chunksize)
    sys.stdout.write(data)
    sys.stdout.flush()
    if len(data) != chunksize:
      break

def scan():
  cmd = sys.argv[1:]
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  return p.stdout

if __name__ == "__main__":
  # Invoke scanning forever, concatenating all data into a single stream
  # Works around hardware limitations that otherwise limit the number 
  # of scanlines.
  fp = scan()
  pass_the_whole_file(fp)
  fp.close()
  while True:
    fp = scan()
    pass_just_the_pixels(fp)
    fp.close()
