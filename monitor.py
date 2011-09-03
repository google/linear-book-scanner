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
import subprocess

window = None

def blue():
  return (128, 128, 255)

def render_text(screen, text, position):
  font = pygame.font.SysFont('Courier', 28, bold=True)
  text = font.render(text, 1, (255, 255, 255))
  background = pygame.Surface(text.get_size())
  background = background.convert()
  background.fill(blue())
  screen.blit(background, position)
  screen.blit(text, position)

def clearscreen(screen):
  background = pygame.Surface(screen.get_size())
  background = background.convert()
  background.fill(blue())
  screen.blit(background, (0,0))

def main(barcode):
  global window
  pygame.init()
  beep = pygame.mixer.Sound('beep.wav')
  h = pygame.display.Info().current_h
  w = pygame.display.Info().current_w
  fullscreen = True
  window = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
  current = ""
  while True:
    time.sleep(0.5)
    for event in pygame.event.get():
      if (event.type == pygame.KEYDOWN):
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_q: 
          pygame.quit()
          sys.exit()
        if fullscreen:
          window = pygame.display.set_mode((w, h))
          fullscreen = False
        else:
          window = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
          fullscreen = True
        current = ""
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
    files = sorted(glob.glob('/var/tmp/playground/%s/*.pnm' % barcode))
    if len(files) < 2:
      continue
    latest = files[-1]
    if latest != current:
      basename_a, dummy = os.path.splitext(os.path.basename(files[-2]))
      basename_b, dummy = os.path.splitext(os.path.basename(files[-1]))
      if int(basename_b) % 2 == 1:
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
      screen = pygame.display.get_surface()
      clearscreen(screen)
      epsilon = w // 100
      screen.blit(surface_a, (w / 2 - w_prime - epsilon, 0))
      screen.blit(surface_b, (w / 2 + epsilon, 0))
      render_text(screen, basename_a, (0, 0))
      render_text(screen, basename_b, (w - 110, 0))
      pygame.display.update()
      beep.play()
      current = latest

if __name__ == "__main__":
  main(sys.argv[1])
