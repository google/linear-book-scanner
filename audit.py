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
import os.path
import random

# Usage:
# run ./audit.py <barcode>
# then click on the page number in the image
# writes a mosaic to /var/tmp/playground/audit/<barcode>.jpg

SADDLE_HEIGHT = 3600  # scan pixels
SENSOR_OFFSET = 150
CROP_SIZE = 200

def main(barcode):
  pygame.init()
  directory = '/var/tmp/playground'
  screen_h = pygame.display.Info().current_h
  screen_w = pygame.display.Info().current_w
  window = pygame.display.set_mode((screen_w, screen_h),pygame.FULLSCREEN)
  screen = pygame.display.get_surface()

  # pick a random page
  image_number = random.randint(2,20) * 2
  filename = '%s/%s/%06d.pnm' % (directory, barcode, image_number)

  # read image
  image = pygame.image.load(filename).convert()
  crop = pygame.Surface((image.get_width(), SADDLE_HEIGHT))
  crop.blit(image, (0, 0), 
            (0, SENSOR_OFFSET, crop.get_width(), crop.get_height()))
  image_w = image.get_width() * screen_h // SADDLE_HEIGHT
  surface = pygame.transform.smoothscale(crop, (image_w, screen_h))

  # display image
  background = pygame.Surface(screen.get_size())
  background = background.convert()
  background.fill((70, 120, 173))
  screen.blit(background, (0,0))
  screen.blit(surface, (screen_w//2 - image_w//2, 0))
  pygame.display.update()

  # wait for a click
  while True:
    event = pygame.event.wait()
    if event.type == pygame.MOUSEBUTTONDOWN:
      pos = event.pos
      break
  pygame.display.set_mode((100, 100), pygame.RESIZABLE)

  # collect page numbers
  print 'reading images'
  images = []
  for image_number in range(2, 100000, 2):
    filename = '%s/%s/%06d.pnm' % (directory, barcode, image_number)
    if not os.path.exists(filename):
      break

    image = pygame.image.load(filename).convert()
    top = pos[1] * SADDLE_HEIGHT // screen_h
    left = (pos[0] - (screen_w//2 - image_w//2)) * SADDLE_HEIGHT // screen_h
    crop = pygame.Surface((CROP_SIZE, CROP_SIZE))
    crop.blit(image, (0, 0), 
              (left - CROP_SIZE//2, SENSOR_OFFSET + top - CROP_SIZE//2,
               CROP_SIZE, CROP_SIZE))
    
    images.append(crop)
    if len(images) % 5 == 0:
      print len(images) * 2

  print 'building mosaic'
  final = pygame.Surface((CROP_SIZE*10, CROP_SIZE*(len(images)//10 + 1)))
  for i in range(len(images)):
    final.blit(images[-i], (CROP_SIZE*(i%10), CROP_SIZE*(i//10)))

  # save
  try:
    os.mkdir(os.path.join(directory, 'audit'))
  except OSError:
    pass
  filename = '%s/audit/%s.jpg' % (directory, barcode)
  pygame.image.save(final, filename)

if __name__ == '__main__':
  main(sys.argv[1])
