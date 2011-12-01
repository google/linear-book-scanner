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
import BaseHTTPServer

paused = False           # For image inspection
image_number = 1         # Scanimage starts counting at 1
book_dimensions = None   # (top, bottom, side) in pixels
fullscreen = True        # Easier to debug in a window

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
  kSaddleHeight = 3600   # scan pixels
  if is_left:
    sensor_offset = 600
  else:
    sensor_offset = 150
  image = pygame.image.load(filename)
  if book_dimensions:
    (top, bottom, side) = book_dimensions
    crop = pygame.Surface((side, top - bottom))
  else:
    bottom = 0
    crop = pygame.Surface((image.get_width(), kSaddleHeight))
  crop.blit(image, (0, 0), 
            (0,
             sensor_offset + bottom, 
             crop.get_width(),
             crop.get_height()))
  if is_left:
    crop = pygame.transform.flip(crop, True, False)
  w = image.get_width() * h / kSaddleHeight
  surface = pygame.transform.smoothscale(crop, (w, h))
  return surface, crop  

def clip_image_number(playground):
  """ Only show images that exist."""
  global image_number
  if image_number < 1:
    image_number = 1
  while image_number > 1:
    filename = '%s/%06d.pnm' % (playground, image_number)
    if os.path.exists(filename):
      break
    image_number -= 2

def handle_user_input(playground):
  """ Handle keypresses directly, return mouseclicks to caller."""
  global paused
  global image_number
  global fullscreen
  leftclick = None
  rightclick = None
  screen = None
  for event in pygame.event.get():
    if event.type == pygame.MOUSEBUTTONDOWN:
      if event.button == 3:
        rightclick = event.pos
      if event.button == 1:
        down = event.pos
        up = wait_for_mouseup()
        leftclick = (down, up)
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
        if fullscreen:
          window = pygame.display.set_mode((w, h))
        else:
          window = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
        fullscreen = not fullscreen
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
        return event.pos
    time.sleep(0.2)

def get_book_dimensions(playground):
  """ User saved book dimensions in some earlier run."""
  global book_dimensions
  try:
    data = open(os.path.join(playground, "book_dimensions")).read()
    book_dimensions = [int(x) for x in data.split(",")]
  except IOError:
    pass

def set_book_dimensions(click, epsilon, crop, surface, playground):
  """ User has clicked to specify book position in image."""
  global book_dimensions
  down = list(click[0])
  up = list(click[1])
  filename = os.path.join(playground, "book_dimensions")
  min_book_height = 30  # screen pixels
  if book_dimensions == None:
    w2 = pygame.display.Info().current_w // 2
    down[0] = abs(w2 - down[0]) + w2
    up[0] =  abs(w2 - up[0]) + w2
    if abs(down[1] - up[1]) < min_book_height:
      return
    side = max(down[0], up[0]) - w2 - epsilon 
    top = max(down[1], up[1])
    bottom = min(down[1], up[1])
    side = side * crop.get_width() // surface.get_width()
    top = top * crop.get_height() // surface.get_height()
    bottom = bottom * crop.get_height() // surface.get_height()
    book_dimensions = (top, bottom, side)
    f = open(filename, "wb")
    f.write("%s,%s,%s\n" % book_dimensions)
    f.close()
  else:
    book_dimensions = None
    os.unlink(filename)
  

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
  w2 = pygame.display.Info().current_w // 2
  if click[0] < w2:
    surface_x0 = w2 - epsilon - surface_a.get_width()
    zoombox(screen, click, surface_a, crop_a, surface_x0)
  else:
    surface_x0 = w2 + epsilon
    zoombox(screen, click, surface_b, crop_b, surface_x0)

def draw(screen, image_number, surface_a, surface_b, epsilon, paused):
  """Draw the page images on screen."""
  w = pygame.display.Info().current_w
  h = pygame.display.Info().current_h
  clearscreen(screen)
  render_text(screen, str(image_number), "upperleft")
  render_text(screen, str(image_number + 1), "upperright")
  screen.blit(surface_a, (w // 2 - surface_a.get_width() - epsilon, 0))
  screen.blit(surface_b, (w // 2 + epsilon, 0))
  if paused:
    render_text(screen, "paused", "upperright")        
    pygame.draw.line(screen, (255, 0, 0), (0, 0), (w, h))

def save(crop_a, crop_b, playground, image_number):
  """Save in something closer to reading order."""
  try:
    os.mkdir(os.path.join(playground, 'export'))
  except OSError:
    pass
  filename_a = '%s/export/%06d.jpg' % (playground, 999999 - image_number + 1)
  filename_b = '%s/export/%06d.jpg' % (playground, 999999 - image_number)
  pygame.image.save(crop_b, filename_a)
  pygame.image.save(crop_a, filename_b)

def get_bibliography(barcode):
  """Hit up Google Books for bibliographic data. Thanks, Leonid."""
  if barcode[0:3] == "978":
    url = ("http://books.google.com/books/download/"
           "?vid=isbn%s&output=enw&source=cheese" % barcode[0:13])
    try:
      bib = urllib2.urlopen(url, None, 2).read()
    except urllib2.URLError, e:
      if hasattr(e, 'reason'):
        excuse =  e.reason
      elif hasattr(e, 'code'):
        excuse = "HTTP return code %d\n" % e.code
        excuse += BaseHTTPServer.BaseHTTPRequestHandler.responses[e.code][0]
      return "Error looking up barcode: %s\n\n%s" % (barcode.split("_")[0],
                                                     excuse)
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
                       "R MOUSE     = zoom\n"
                       "L MOUSE     = crop\n"
                       "SPACE       = pause\n"
                       "F11         = fullscreen\n"
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
  get_book_dimensions(playground)
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
      draw(screen, image_number, surface_a, surface_b, epsilon, paused)
      pygame.display.update()
    if rightclick:
      draw(screen, image_number, surface_a, surface_b, epsilon, paused)
      zoom(screen, rightclick, epsilon, surface_a, surface_b, crop_a, crop_b)
      pygame.display.update()
      wait_for_mouseup()
      draw(screen, image_number, surface_a, surface_b, epsilon, paused)
      pygame.display.update()
    if leftclick:
      set_book_dimensions(leftclick, epsilon, crop_a, surface_a, playground)
      try:
        filename_a = '%s/%06d.pnm' % (playground, last_drawn_image_number)
        filename_b = '%s/%06d.pnm' % (playground, last_drawn_image_number + 1)
        surface_a, crop_a = process_image(h, filename_a, True)
        surface_b, crop_b = process_image(h, filename_b, False)
      except:
        pass
      draw(screen, image_number, surface_a, surface_b, epsilon, paused)
      pygame.display.update()
      save(crop_a, crop_b, playground, image_number)
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
      save(crop_a, crop_b, playground, image_number)
      last_drawn_image_number = image_number
    if not paused:
      image_number += 2
      beep.play()
    time.sleep(0.1)

if __name__ == "__main__":
  main(sys.argv[1])
