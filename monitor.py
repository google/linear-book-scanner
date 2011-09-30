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
import urllib2

paused = False
image_number = 1         # Scanimage starts counting at 1
book_dimensions = None   # Pixels

def blue():
  """Original scansation blue, handed down from antiquity"""
  return (70, 120, 173)

def clearscreen(screen):
  """And G-d said, "Let there be blue light!"""
  background = pygame.Surface(screen.get_size())
  background = background.convert()
  background.fill(blue())
  screen.blit(background, (0,0))

def render_text(screen, msg, position):
  """Write messages to screen, such as the image number."""
  pos = [0, 0]
  font = pygame.font.SysFont('Courier', 28, bold=True)
  for line in msg.split("\n"):
    text = font.render(line.strip(), 1, (255, 255, 255))
    background = pygame.Surface(text.get_size())
    background = background.convert()
    background.fill(blue())
    if position == "upperright":
      pos[0] = screen.get_width() - text.get_width()
    screen.blit(background, pos)
    screen.blit(text, pos)
    pos[1] += 30

def process_image(h, filename, is_left):
  """Returns both screen size and full size images."""
  kSaddleHeight = 3600
  if is_left:
    sensor_offset = 600
  else:
    sensor_offset = 150
  image = pygame.image.load(filename)
  if book_dimensions:
    crop = pygame.Surface(book_dimensions)
  else:
    crop = pygame.Surface((image.get_width(), kSaddleHeight))
  crop.blit(image, (0, 0), 
            (0,
             sensor_offset + kSaddleHeight - crop.get_height(), 
             crop.get_width(),
             crop.get_height()))
  if is_left:
    crop = pygame.transform.flip(crop, True, False)
  w = image.get_width() * h / kSaddleHeight
  surface = pygame.transform.smoothscale(crop, (w, h))
  return surface, crop  

def clip_image_number(playground):
  global image_number
  if image_number < 1:
    image_number = 1
  while image_number > 1:
    filename = '%s/%06d.pnm' % (playground, image_number)
    if os.path.exists(filename):
      break
    image_number -= 2

def handle_user_input(playground):
  """ You get the idea."""
  global paused
  global image_number
  leftclick = None
  rightclick = None
  screen = None
  for event in pygame.event.get():
    if event.type == pygame.MOUSEBUTTONDOWN:
      if event.button == 1:
        leftclick = event.pos
      if event.button == 3:
        rightclick = event.pos
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
        return leftclick, rightclick, screen
      elif event.key == pygame.K_SPACE:
        if paused:
          paused = False
          image_number += 2
        else:
          paused = True
        return leftclick, rightclick, screen
      elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
        image_number -= 2
      elif event.key == pygame.K_PAGEUP:
        image_number -= 10
      elif event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
        image_number += 2
      elif event.key == pygame.K_PAGEDOWN:
        image_number += 10
      paused = True
      clip_image_number(playground)
  return leftclick, rightclick, screen

def wait_for_mouseup():
  while True:
    for event in pygame.event.get():
      if event.type == pygame.MOUSEBUTTONUP:
        return
    time.sleep(0.2)

def set_book_dimensions(click, epsilon, crop, surface):
  global book_dimensions
  if book_dimensions == None:
    w = pygame.display.Info().current_w
    if click[0] < w // 2:
      surface_x0 = w // 2 - epsilon - surface.get_width()
      x = ((surface.get_width() - click[0] + surface_x0) 
           * crop.get_width() // surface.get_width())
    else:
      surface_x0 = w // 2 + epsilon
      x = ((click[0] - surface_x0) 
           * crop.get_width() // surface.get_width())
    y = ((surface.get_height() - click[1]) 
         * crop.get_height() // surface.get_height())
    book_dimensions = (x, y)
  else:
    book_dimensions = None

def zoombox(screen, click, surface, crop, surface_x0):
  """Helper function created during refactoring. Draws the actual zoombox"""
  x = (click[0] - surface_x0) * crop.get_width() // surface.get_width()
  y = click[1] * crop.get_height() // surface.get_height()
  if x < 0 or x >= crop.get_width():
    return
  kZoomSize = pygame.display.Info().current_w / 3
  zoombox_pos = (click[0] - kZoomSize, click[1] - kZoomSize)
  screen.blit(crop, zoombox_pos,
              (x - kZoomSize, y - kZoomSize, 2 * kZoomSize, 2 * kZoomSize))

def zoom(screen, click, epsilon, surface_a, surface_b, crop_a, crop_b):
  """Given a mouseclick, zoom in on the region."""
  w = pygame.display.Info().current_w
  if click[0] < w // 2:
    surface_x0 = w // 2 - epsilon - surface_a.get_width()
    zoombox(screen, click, surface_a, crop_a, surface_x0)
  else:
    surface_x0 = w // 2 + epsilon
    zoombox(screen, click, surface_b, crop_b, surface_x0)

def draw(screen, image_number, surface_a, surface_b, epsilon, paused):
  """Draw the page images on screen."""
  w = pygame.display.Info().current_w
  clearscreen(screen)
  render_text(screen, str(image_number), "upperleft")
  render_text(screen, str(image_number + 1), "upperright")
  screen.blit(surface_a, (w // 2 - surface_a.get_width() - epsilon, 0))
  screen.blit(surface_b, (w // 2 + epsilon, 0))
  if paused:
    render_text(screen, "paused", "upperright")        


def get_bibliography(barcode):
  """Hit up Google Books for bibliographic data. Thanks, Leonid."""
  if barcode[0:3] == "978":
    url = ("http://books.google.com/books/download/"
           "?vid=isbn%s&output=enw&source=cheese" % barcode[0:13])
    try:
      bib = urllib2.urlopen(url, None, 2).read()
    except IOError:
      return "Error looking up barcode: %s" % barcode.split("_")[0]
    return bib
  return "Unknown Barcode: %s" % barcode.split("_")[0]

def splashscreen(screen, barcode):
  clearscreen(screen)
  render_text(screen, "Looking up barcode: %s" % barcode.split("_")[0],
              "upperleft")
  pygame.display.update()
  clearscreen(screen)
  render_text(screen, get_bibliography(barcode), "upperleft")
  render_text(screen, ("\n\n\n\n\n\n\n\n\n\n"
                       "L MOUSE     = zoom\n"
                       "R MOUSE     = crop\n"
                       "SPACE       = pause\n"
                       "ARROWS      = navigation\n"
                       "PgUp/PgDn   = navigation!\n"
                       ), "upperleft")
  pygame.display.update()
  time.sleep(2.0)  

def main(barcode):
  """Monitor the scanning for images and display them."""
  pygame.init()
  global image_number
  last_drawn_image_number = 0
  playground = "/var/tmp/playground/%s" % barcode
  beep = pygame.mixer.Sound('beep.wav')
  h = pygame.display.Info().current_h
  w = pygame.display.Info().current_w
  epsilon = w // 100
  window = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
  screen = pygame.display.get_surface()
  pygame.display.set_caption("Barcode: %s" % barcode)
  splashscreen(screen, barcode)
  while True:
    leftclick, rightclick, newscreen = handle_user_input(playground)
    if newscreen:
      screen = newscreen
    if leftclick:
      draw(screen, image_number, surface_a, surface_b, epsilon, paused)
      zoom(screen, leftclick, epsilon, surface_a, surface_b, crop_a, crop_b)
      pygame.display.update()
      wait_for_mouseup()
      draw(screen, image_number, surface_a, surface_b, epsilon, paused)
      pygame.display.update()
    if rightclick:
      set_book_dimensions(rightclick, epsilon, crop_a, surface_a)
      try:
        surface_a, crop_a = process_image(h, filename_a, True)
        surface_b, crop_b = process_image(h, filename_b, False)
      except:
        pass
      draw(screen, image_number, surface_a, surface_b, epsilon, paused)
      pygame.display.update()
    if last_drawn_image_number != image_number:
      filename_a = '%s/%06d.pnm' % (playground, image_number)
      filename_b = '%s/%06d.pnm' % (playground, image_number + 1)
      try:
        surface_a, crop_a = process_image(h, filename_a, True)
        surface_b, crop_b = process_image(h, filename_b, False)
      except pygame.error:
        time.sleep(0.2)
        continue
      draw(screen, image_number, surface_a, surface_b, epsilon, paused)
      pygame.display.update()
      last_drawn_image_number = image_number
    if not paused:
      image_number += 2
      beep.play()
    time.sleep(0.1)

if __name__ == "__main__":
  main(sys.argv[1])
