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
  w = 1280
  h = 800
  window = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
  screen = pygame.display.get_surface()
  current = ""
  while True:
    time.sleep(0.5)
    for event in pygame.event.get():
      if (event.type == pygame.KEYUP) or (event.type == pygame.KEYDOWN):
        window = pygame.display.set_mode((w, h))
        sys.exit()
    files = sorted(glob.glob('/var/tmp/playground/%s/*.pnm' % barcode))
    if len(files) < 2:
      continue
    latest = files[-1]
    if latest != current:
      basename, extension = os.path.splitext(os.path.basename(latest))
      if int(basename) % 2 == 1:
        continue
      pygame.display.set_caption("Barcode: %s [ %s %s ]" %
                                 (barcode,
                                  os.path.basename(files[-2]),
                                  os.path.basename(files[-1])))
      image_a = pygame.image.load(files[-2])
      image_b = pygame.image.load(files[-1])
      w_prime = image_a.get_width() * h / image_a.get_height()
      surface_a = pygame.transform.smoothscale(image_a, (w_prime, h))
      surface_b = pygame.transform.smoothscale(image_b, (w_prime, h))
      surface_a = pygame.transform.flip(surface_a, True, False)
      screen.blit(surface_a, (w / 2 - w_prime, 0))
      screen.blit(surface_b, (w / 2, 0))
      pygame.display.update()
      current = latest

main(sys.argv[1])
