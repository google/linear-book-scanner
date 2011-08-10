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
import pygame
from pnm import pnm_header
from split import detect_pagefeed

def walk_through_lines(linesize, ratio):
  """Throw out several scan lines for each one that we keep."""
  for unused in range(ratio):
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      return None
    sys.stdout.write(scanline)
    sys.stdout.flush()
    if detect_pagefeed(scanline):
      return "Pagefeed"
  return scanline

def process(ratio):
  """View an image as it passes from stdin to stdout. Downsize by ratio
  so that it can fit on a computer screen."""
  n = 0
  y = 0
  h = 800
  linewidth, linecount, channels = pnm_header()
  linesize = linewidth * channels
  w = linewidth // ratio
  if channels == 1:
    image_type = "P"
    palette = tuple([(i, i, i) for i in range(256)])
  elif channels == 3:
    image_type = "RGB"
  window = pygame.display.set_mode((w, h))
  screen = pygame.display.get_surface()
  pygame.display.set_caption('Pass Through Viewer')
  while True:
    if y % h == 0:
      pygame.display.set_caption('Pass Through Viewer - %d' % n)
    scanline = walk_through_lines(linesize, ratio)
    n += ratio
    if scanline == None:
      break
    if scanline == "Pagefeed":
      y = 0
    else:
      image_line = pygame.image.frombuffer(scanline, (linewidth, 1), image_type)
      if channels == 1:
        image_line.set_palette(palette)
      scaled_line = pygame.transform.scale(image_line, (w, 1))
      screen.blit(scaled_line, (0, y % h))
    y += 1
    if y % 40 == 0 or scanline == "Pagefeed":
      pygame.draw.line(screen, (0, 255, 0), (0, y % h), (w, y % h))
      pygame.display.update()

if __name__ == "__main__":
  ratio = 5
  if len(sys.argv) == 2:
    ratio = int(sys.argv[1])
  process(ratio)
