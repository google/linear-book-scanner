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
fullscreen = True

def blue():
  return (128, 128, 255)

def render_text(screen, text, position):
  font = pygame.font.SysFont('Courier', 28, bold=True)
  text = font.render(text, 1, (255, 255, 255))
  background = pygame.Surface(text.get_size())
  background = background.convert()
  background.fill(blue())
  if position == "upperleft":
    pos = (0, 0)
    screen.blit(background, pos)
    screen.blit(text, pos)
  elif position == "upperright":
    pos = (screen.get_width() - text.get_width(), 0)
    screen.blit(background, pos)
    screen.blit(text, pos)

def clearscreen(screen):
  background = pygame.Surface(screen.get_size())
  background = background.convert()
  background.fill(blue())
  screen.blit(background, (0,0))

def process_images(h, filename_a, filename_b):
  kSaddleHeight = 3600
  kSensorOffsetA = 700
  kSensorOffsetB = 300
  image_a = pygame.image.load(filename_a)
  image_b = pygame.image.load(filename_b)
  crop_a = pygame.Surface((image_a.get_width(), kSaddleHeight))
  crop_b = pygame.Surface((image_b.get_width(), kSaddleHeight))
  crop_a.blit(image_a, (0, 0), (0,
                                kSensorOffsetA,
                                crop_a.get_width(),
                                crop_a.get_height()))
  crop_b.blit(image_b, (0, 0), (0, 
                                kSensorOffsetB,
                                crop_b.get_width(),
                                crop_b.get_height()))
  crop_a = pygame.transform.flip(crop_a, True, False)
  w_prime = image_a.get_width() * h / kSaddleHeight
  surface_a = pygame.transform.smoothscale(crop_a, (w_prime, h))
  surface_b = pygame.transform.smoothscale(crop_b, (w_prime, h))
  return surface_a, surface_b, crop_a, crop_b

def handle_user_input():
  h = pygame.display.Info().current_h
  w = pygame.display.Info().current_w
  for event in pygame.event.get():
    if event.type == pygame.MOUSEBUTTONDOWN:
      if event.button == 1:
        return event.pos
    if event.type == pygame.QUIT:
      pygame.quit()
      sys.exit()
    elif (event.type == pygame.KEYDOWN):
      if event.key == pygame.K_ESCAPE or event.key == pygame.K_q: 
        pygame.quit()
        sys.exit()
  return None

def get_labels(filename_a, filename_b):
  basename_a, dummy = os.path.splitext(os.path.basename(filename_a))
  basename_b, dummy = os.path.splitext(os.path.basename(filename_b))
  return int(basename_a), int(basename_b)

def mtime(filename):
  return os.stat(filename).st_mtime

def zoom(screen, click, epsilon, w, surface_a, surface_b, crop_a, crop_b):
  kZoomSize = w / 3
  zoombox_pos = (click[0] - kZoomSize, click[1] - kZoomSize)  
  if click[0] > w // 2:
    x = click[0] - (w // 2 + epsilon)
    x = x * crop_b.get_width() // surface_b.get_width()
    y = click[1] * crop_b.get_height() // surface_b.get_height()
    if x < 0 or x >= crop_b.get_width():
      return
    screen.blit(crop_b, zoombox_pos, 
                (x - kZoomSize, y - kZoomSize, 2 * kZoomSize, 2 * kZoomSize))
  else:
    x = click[0] - (w // 2 - epsilon - surface_a.get_width())
    x = x * crop_a.get_width() // surface_a.get_width()      
    y = click[1] * crop_a.get_height() // surface_a.get_height()
    if x < 0 or x >= crop_a.get_width():
      return
    screen.blit(crop_a, zoombox_pos,
                (x - kZoomSize, y - kZoomSize, 2 * kZoomSize, 2 * kZoomSize))

def draw(screen, basename_a, basename_b, surface_a, surface_b, w, epsilon):
  clearscreen(screen)
  render_text(screen, str(basename_a), "upperleft")
  render_text(screen, str(basename_b), "upperright")
  screen.blit(surface_a, (w // 2 - surface_a.get_width() - epsilon, 0))
  screen.blit(surface_b, (w // 2 + epsilon, 0))


def main(barcode):
  global window
  pygame.init()
  beep = pygame.mixer.Sound('beep.wav')
  h = pygame.display.Info().current_h
  w = pygame.display.Info().current_w
  window = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
  screen = pygame.display.get_surface()
  pygame.display.set_caption("Barcode: %s" % barcode)
  current = ""
  while True:
    time.sleep(0.5)
    click = handle_user_input()
    files = sorted(glob.glob('/var/tmp/playground/%s/*.pnm' % barcode),
                   key=mtime)
    if len(files) < 2:
      continue
    latest = files[-2]
    if latest != current:
      basename_a, basename_b = get_labels(files[-1], files[-2])
      if basename_b % 2 == 1:
        continue
      surface_a, surface_b, crop_a, crop_b = process_images(h, files[-1], 
                                                            files[-2])
      epsilon = w // 100
      draw(screen, basename_a, basename_b, surface_a, surface_b, w, epsilon)
      pygame.display.update()
      beep.play()
      current = latest
    if click:
      draw(screen, basename_a, basename_b, surface_a, surface_b, w, epsilon)
      zoom(screen, click, epsilon, w, surface_a, surface_b, crop_a, crop_b)
      pygame.display.update()

if __name__ == "__main__":
  main(sys.argv[1])
