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

import pygame
import sys
import os
import numpy
from pnm import pnm_header
from detect import detect_stripes
from phase import find_phase
from phase import kScanbarPixels

def init():
  pygame.init()
  window = pygame.display.set_mode((640, 100)) 
  pygame.display.set_caption('Cheese meter')
  screen = pygame.display.get_surface()
  ball_surface = pygame.image.load('ball.png')
  bg_surface = pygame.image.load('ball_bg.png')
  return screen, ball_surface, bg_surface

def draw(screen, ball_surface, bg_surface, pos):
  screen.blit(bg_surface, (0,0))
  screen.blit(ball_surface, (pos, 30))
  pygame.display.update()

def process():
  screen, ball_surface, bg_surface = init()
  linewidth, linecount, channels = pnm_header()
  linesize = linewidth * channels
  phase = 0
  scale = 300 * linewidth / kScanbarPixels
  kSmoothingFactor = 20
  kGraphicalSmoothingFactor = 1
  values = range(kSmoothingFactor)
  n = 0
  while True:
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      break
    sys.stdout.write(scanline)
    n += 1
    if detect_stripes:
      prev_phase = phase
      phase, period = find_phase(scanline, channels)
      if phase > prev_phase:
        optical_dpi = scale / (phase - prev_phase)
        values[n % kSmoothingFactor] = optical_dpi
        pos = sum(values, 0.0) / len(values)
        if pos > 600:
          pos = 600  
    else:
      pos = -1000
    if n % kGraphicalSmoothingFactor == 0:
      draw(screen, ball_surface, bg_surface, pos)


if __name__=='__main__':
  process()
