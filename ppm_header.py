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

def ppm_header():
  """ Read the image header from stdin, parse, and pass to stdout.
  Returns size of a scanline in bytes, and the number of rows. """
  magic_number = sys.stdin.readline()
  if magic_number != "P6\n":
    raise Exception("I only work with ppm")
  comment = sys.stdin.readline()
  if comment[0] == "#":
    dimensions = sys.stdin.readline()
  else:
    dimensions = comment
    comment = "# Cheesegrater\n"
  max_value = sys.stdin.readline()
  if max_value != "255\n":
    raise Exception("I only work with 8 bits per color channel")
  linesize = int(dimensions.split(" ")[0]) * 3
  linecount = int(dimensions.split(" ")[1])
  sys.stdout.write(magic_number)
  sys.stdout.write(comment)
  sys.stdout.write(dimensions)
  sys.stdout.write(max_value)
  return linesize, linecount
