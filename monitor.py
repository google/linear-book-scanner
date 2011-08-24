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

import os
import glob
import time
import pygame
import sys
import os.path

def main(barcode):
  w = 1400
  h = 800
  window = pygame.display.set_mode((w, h))
  screen = pygame.display.get_surface()
  current = ""
  while True:
    time.sleep(0.5)
    files = sorted(glob.glob('/var/tmp/playground/%s/*.ppm' % barcode))
    if len(files) < 2:
      continue
    latest = files[-1]
    if latest != current:
      print files
      pygame.display.set_caption("Barcode: %s [ %s %s ]" %
                                 (barcode,
                                  os.path.basename(files[-1]),
                                  os.path.basename(files[-2])))
      image_a = pygame.image.load(files[-1])
      image_b = pygame.image.load(files[-2])
      surface_a = pygame.transform.smoothscale(image_a, (w / 2, h))
      surface_b = pygame.transform.smoothscale(image_b, (w / 2, h))
      screen.blit(surface_a, (0, 0))
      screen.blit(surface_b, (w / 2, 0))
      pygame.display.update()
      current = latest

main(sys.argv[1])
