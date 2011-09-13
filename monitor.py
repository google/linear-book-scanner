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

def blue():
  return (70, 120, 173)

def render_text(screen, text, position):
  font = pygame.font.SysFont('Courier', 28, bold=True)
  text = font.render(text, 1, (255, 255, 255))
  background = pygame.Surface(text.get_size())
  background = background.convert()
  background.fill(blue())
  if position == "upperleft":
    pos = (0, 0)
  elif position == "upperright":
    pos = (screen.get_width() - text.get_width(), 0)
  elif position == "center":
    pos = (screen.get_width() // 2 - text.get_width() // 2,
           screen.get_height() // 2)
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
  pos = None
  screen = None
  for event in pygame.event.get():
    if event.type == pygame.MOUSEBUTTONDOWN:
      if event.button == 1:
        pos = event.pos
    elif event.type == pygame.MOUSEBUTTONUP:
      if event.button == 1:
        pos = -1000, -1000
    elif event.type == pygame.QUIT:
      pygame.quit()
      sys.exit()
    elif (event.type == pygame.KEYDOWN):
      if event.key == pygame.K_ESCAPE or event.key == pygame.K_q: 
        pygame.quit()
        sys.exit()
      elif event.key == pygame.K_F11:
        h = pygame.display.Info().current_h
        w = pygame.display.Info().current_w
        window = pygame.display.set_mode((w, h))
        screen = pygame.display.get_surface()
  return pos, screen

def get_label(filename):
  basename, dummy = os.path.splitext(os.path.basename(filename))
  return int(basename)

def mtime(filename):
  return os.stat(filename).st_mtime

def zoombox(screen, click, surface, crop, surface_x0):
  w = pygame.display.Info().current_w
  kZoomSize = w / 3
  zoombox_pos = (click[0] - kZoomSize, click[1] - kZoomSize)  
  x = click[0] - surface_x0
  x = x * crop.get_width() // surface.get_width()
  y = click[1] * crop.get_height() // surface.get_height()
  if x < 0 or x >= crop.get_width():
    return
  screen.blit(crop, zoombox_pos, 
              (x - kZoomSize, y - kZoomSize, 2 * kZoomSize, 2 * kZoomSize))

def zoom(screen, click, epsilon, surface_a, surface_b, crop_a, crop_b):
  w = pygame.display.Info().current_w
  kZoomSize = w / 3
  zoombox_pos = (click[0] - kZoomSize, click[1] - kZoomSize)  
  if click[0] < w // 2:
    surface_x0 = w // 2 - epsilon - surface_a.get_width()
    zoombox(screen, click, surface_a, crop_a, surface_x0)
  else:
    surface_x0 = w // 2 + epsilon
    zoombox(screen, click, surface_b, crop_b, surface_x0)

def draw(screen, basename_a, basename_b, surface_a, surface_b, epsilon):
  w = pygame.display.Info().current_w
  clearscreen(screen)
  render_text(screen, str(basename_a), "upperleft")
  render_text(screen, str(basename_b), "upperright")
  screen.blit(surface_a, (w // 2 - surface_a.get_width() - epsilon, 0))
  screen.blit(surface_b, (w // 2 + epsilon, 0))

def main(barcode):
  pygame.init()
  beep = pygame.mixer.Sound('beep.wav')
  h = pygame.display.Info().current_h
  w = pygame.display.Info().current_w
  epsilon = w // 100
  window = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
  screen = pygame.display.get_surface()
  pygame.display.set_caption("Barcode: %s" % barcode)
  current = ""
  clearscreen(screen)
  render_text(screen, "Begin Scanning", "center")
  pygame.display.update()
  while True:
    time.sleep(0.5)
    click, newscreen = handle_user_input()
    if newscreen:
      screen = newscreen
      current = ""
    files = sorted(glob.glob('/var/tmp/playground/%s/*[13579].pnm' % barcode))
    if len(files) < 2:
      continue
    latest = files[-1]
    if latest != current:
      basename_b = get_label(latest)
      basename_a = basename_b - 1
      filename_a = '/var/tmp/playground/%s/%06d.pnm' % (barcode, basename_a)
      surface_a, surface_b, crop_a, crop_b = process_images(h, latest,
                                                            filename_a)
      draw(screen, basename_a, basename_b, surface_a, surface_b, epsilon)
      pygame.display.update()
      beep.play()
      current = latest
    if click:
      draw(screen, basename_a, basename_b, surface_a, surface_b, epsilon)
      zoom(screen, click, epsilon, surface_a, surface_b, crop_a, crop_b)
      pygame.display.update()

if __name__ == "__main__":
  main(sys.argv[1])
