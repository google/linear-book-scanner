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

import collections
import pygame
import sys
import os
import numpy
from pnm import pnm_header
from detect import detect_stripes
from phase import find_phase

def init_graphics():
  pygame.init()
  window = pygame.display.set_mode((640, 100)) 
  pygame.display.set_caption('Cheese meter')
  screen = pygame.display.get_surface()
  ball_surface = pygame.image.load('ball.png')
  bg_surface = pygame.image.load('ball_bg.png')
  return screen, ball_surface, bg_surface

def process():
  linewidth, linecount, channels = pnm_header()
  linesize = linewidth * channels
  phase = 0
  n = 0
  offscreen = -100
  pos = offscreen
  screen, ball_surface, bg_surface = init_graphics()
  while True:
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      break
    sys.stdout.write(scanline)
    if detect_stripes(scanline, channels):
      prev_phase = phase
      phase, period = find_phase(scanline, channels)
      speed = phase - prev_phase
      if phase < prev_phase:
        speed += period
      pos = min(300 * speed, 600)
      screen.blit(ball_surface, (pos, 30))
    elif pos > 0:
      pos = offscreen
      screen.blit(bg_surface, (0,0))
    if n % (70 // channels) == 0:
      pygame.display.update()
      screen.blit(bg_surface, (0,0))
    n += 1


if __name__=='__main__':
  process()
