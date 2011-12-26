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
import pygame
import sys
import os.path
import urllib2
import BaseHTTPServer
import mmap

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
  background.fill(blue())
  screen.blit(background, (0,0))

def render_text(screen, msg, position):
  """Write messages to screen, such as the image number."""
  pos = [0, 0]
  font = pygame.font.SysFont('Courier', 28, bold=True)
  for line in msg.split("\n"):
    text = font.render(line, 1, (255, 255, 255))
    background = pygame.Surface(text.get_size())
    background.fill(blue())
    if position == "upperright":
      pos[0] = screen.get_width() - text.get_width()
    screen.blit(background, pos)
    screen.blit(text, pos)
    pos[1] += 30

def read_pnm_header(fp):
  """Read dimensions and headersize from a PPM file."""
  headersize = 0
  magic_number = fp.readline()
  if magic_number != "P6\n":
    raise TypeError("Hey! Not a ppm image file.")
  headersize += len(magic_number)
  comment = fp.readline()
  if comment[0] == "#":
    headersize += len(comment)
    dimensions = fp.readline()
  else:
    dimensions = comment
  headersize += len(dimensions)
  max_value = fp.readline()
  if max_value != "255\n":
    raise ValueError("I only work with 8 bits per color channel")
  headersize += len(max_value)
  w = int(dimensions.split(" ")[0])
  h = int(dimensions.split(" ")[1])
  return (w, h), headersize

def crop_to_full_coord(crop_coord, is_left):
  if is_left:
    offset = 593
  else:
    offset = 150
  if book_dimensions:
    (top, bottom, side) = book_dimensions
    offset += top
  full_coord = crop_coord[0], crop_coord[1] + offset
  return full_coord


def process_image(h, filename, is_left):
  """Return both screen resolution and scan resolution images."""
  kSaddleHeight = 3600  # scan pixels
  f = open(filename, "r+b")
  dimensions, headersize = read_pnm_header(f)
  map = mmap.mmap(f.fileno(), 0)
  image = pygame.image.frombuffer(buffer(map, headersize), dimensions, 'RGB')
  full_coord = crop_to_full_coord((0, 0), is_left)
  if book_dimensions:
    (top, bottom, side) = book_dimensions
    wh = (side, bottom - top)
  else:
    wh = (image.get_width(), kSaddleHeight)
  rect = pygame.Rect(full_coord, wh)
  crop = image.subsurface(rect)
  w = image.get_width() * h // kSaddleHeight
  scale = pygame.transform.smoothscale(crop, (w, h))
  if is_left:
    scale = pygame.transform.flip(scale, True, False)
  return scale, crop  

def clip_image_number(playground):
  """Only show images that exist."""
  global image_number
  if image_number < 1:
    image_number = 1
  while image_number > 1:
    filename = '%s/%06d.pnm' % (playground, image_number)
    if os.path.exists(filename):
      break
    image_number -= 2

def get_book_dimensions(playground):
  """User saved book dimensions in some earlier run."""
  global book_dimensions
  try:
    for line in open(os.path.join(playground, "book_dimensions")).readlines():
      if line[0] != "#":
        book_dimensions = [int(x) for x in line.split(",")]
  except IOError:
    pass

def set_book_dimensions(click, epsilon, crop_size, scale_size, playground):
  """User has dragged mouse to specify book position in image."""
  global book_dimensions
  down = list(click[0])
  up = list(click[1])
  filename = os.path.join(playground, "book_dimensions")
  min_book_dimension = 30  # screen pixels
  if book_dimensions == None:
    w2 = pygame.display.Info().current_w // 2
    down[0] = abs(w2 - down[0]) + w2
    up[0] =  abs(w2 - up[0]) + w2
    if min(abs(down[1] - up[1]), abs(up[0] - w2)) < min_book_dimension:
      return
    side = max(down[0], up[0]) - w2 - epsilon 
    top = min(down[1], up[1])
    bottom = max(down[1], up[1])
    side = side * crop_size[0] // scale_size[0]
    top = top * crop_size[1] // scale_size[1]
    bottom = bottom * crop_size[1] // scale_size[1]
    book_dimensions = (top, bottom, side)
    f = open(filename, "wb")
    f.write("#top,bottom,side\n%s,%s,%s\n" % book_dimensions)
    f.close()
  else:
    book_dimensions = None
    os.unlink(filename)

def scale_to_crop_coord(scale_coord, scale_size, crop_size, epsilon):
  w2 = pygame.display.Info().current_w // 2
  if scale_coord[0] < w2:
    x0 = w2 - epsilon - scale_size[0]
    is_left = True
  else:
    x0 = w2 + epsilon
    is_left = False
  x = (scale_coord[0] - x0) * crop_size[0] // scale_size[0]
  y = scale_coord[1] * crop_size[1] // scale_size[1]
  return (x, y), is_left

def zoom(screen, click, epsilon, scale_a, scale_b, crop_a, crop_b):
  """Given a mouseclick, zoom in on the region."""
  coordinates, is_left = scale_to_crop_coord(click, scale_a.get_size(),
                                crop_a.get_size(), epsilon)
  w2 = pygame.display.Info().current_w // 2
  if is_left:
    crop_a = pygame.transform.flip(crop_a, True, False)
    crop = crop_a
    scale = scale_a
  else:
    crop = crop_b
    scale = scale_b
  kZoomSize = pygame.display.Info().current_w // 3
  zoombox_pos = (click[0] - kZoomSize, click[1] - kZoomSize)
  screen.blit(crop, zoombox_pos,
              (coordinates[0] - kZoomSize,
               coordinates[1] - kZoomSize, 2 * kZoomSize, 2 * kZoomSize))

def draw(screen, image_number, scale_a, scale_b, epsilon, paused):
  """Draw the page images on screen."""
  (w, h) = screen.get_size()
  render_text(screen, "%d           " % image_number, "upperleft")
  render_text(screen, "           %d" % (image_number + 1), "upperright")
  screen.blit(scale_a, (w // 2 - scale_a.get_width() - epsilon, 0))
  screen.blit(scale_b, (w // 2 + epsilon, 0))
  if paused:
    render_text(screen, "**  pause  **", "upperleft")

def save(crop_a, crop_b, playground, image_number):
  """Save cropped images in reading order."""
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
  clearscreen(screen)
  pygame.time.wait(2000)

def handle_key_event(screen, event, playground):
  global image_number
  global paused
  global fullscreen
  newscreen = None
  if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
    pygame.quit()
    sys.exit()
  elif event.key == pygame.K_SPACE:
    if paused:
      paused = False
      return newscreen
  paused = True
  if event.key == pygame.K_F11:
    (w, h) = screen.get_size()
    if fullscreen:
      window = pygame.display.set_mode((w, h))
    else:
      window = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
    fullscreen = not fullscreen
    newscreen = pygame.display.get_surface()
  elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
    image_number -= 2
  elif event.key == pygame.K_PAGEUP:
    image_number -= 10
  elif event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
    image_number += 2
  elif event.key == pygame.K_PAGEDOWN:
    image_number += 10
  clip_image_number(playground)
  return newscreen

def render(playground, h, screen, epsilon):
  global paused
  global image_number
  filename_a = '%s/%06d.pnm' % (playground, image_number)
  filename_b = '%s/%06d.pnm' % (playground, image_number + 1)
  scale_a, crop_a = process_image(h, filename_a, True)
  scale_b, crop_b = process_image(h, filename_b, False)
  draw(screen, image_number, scale_a, scale_b, epsilon, paused)
  pygame.display.update()
#  save(crop_a, crop_b, playground, image_number)
  return crop_a, crop_b, scale_a, scale_b

def create_mosaic(screen, playground, click, scale_size, crop_size, epsilon):
  kSize = screen.get_height() // 10
  crop_coord, is_left = scale_to_crop_coord(click, scale_size, 
                                            crop_size, epsilon)
  full_coord = crop_to_full_coord(crop_coord, is_left)
  for i in range(2, 100000, 2):
    j = i // 2
    filename = os.path.join(playground, '%06d.pnm' % i)
    if not os.path.exists(filename):
      break
    f = open(filename, "r+b")
    map = mmap.mmap(f.fileno(), 0)
    dimensions, headersize = read_pnm_header(f)
    image = pygame.image.frombuffer(buffer(map, headersize), dimensions, 'RGB')
    dst = (kSize * (j // 10), kSize * (j % 10))
    src = full_coord[0] - kSize // 2, full_coord[1] - kSize // 2
    wh = (kSize, kSize)
    dirty = pygame.Rect(dst, wh)
    screen.blit(image, dst, (src, wh))
    map.close()
    f.close()
    pygame.display.update(dirty)

def main(barcode):
  """Display scanned images as they are created."""
  pygame.init()
  global image_number
  global paused
  global fullscreen
  global book_dimensions
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
  pygame.time.set_timer(pygame.USEREVENT, 10)
  shadow = pygame.Surface(screen.get_size())
  shadow.set_alpha(128)
  shadow.fill((0, 0, 0))
  busy = False
  while True:
    for event in [ pygame.event.wait() ]:
      if event.type == pygame.MOUSEBUTTONDOWN:
        busy = True
        pygame.event.clear(pygame.USEREVENT)
      if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        leftdownclick = event.pos
        oldscreen = screen.copy()  
        shadowscreen = screen.copy()
        shadowscreen.blit(shadow, (0, 0))
        screen.blit(shadowscreen, (0, 0))
        prevroi = pygame.Rect(event.pos, (0, 0))
        pygame.display.update()
      elif event.type == pygame.MOUSEMOTION and event.buttons[0] == 1:
        if book_dimensions:
          continue
        x = abs(event.pos[0] - w // 2)
        pos = (w // 2 - x, min(leftdownclick[1], event.pos[1]))
        roi = pygame.Rect(pos, (2 * x, abs(leftdownclick[1] - event.pos[1])))
        dirty = roi.union(prevroi)
        prevroi = roi.copy()
        screen.blit(shadowscreen, dirty.topleft, area = dirty)
        screen.blit(oldscreen, roi.topleft, area = roi)
        pygame.display.update(dirty)
      elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        oldscreen = None
        leftclick = (leftdownclick, event.pos)
        set_book_dimensions(leftclick, epsilon, crop_a.get_size(),
                            scale_a.get_size(), playground)
        clearscreen(screen)
        crop_a, crop_b, scale_a, scale_b = render(playground,
                                                      h, screen, epsilon)
        busy = False
      elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        draw(screen, image_number, scale_a, scale_b, epsilon, paused)
        zoom(screen, event.pos, epsilon, scale_a, scale_b, crop_a, crop_b)
        pygame.display.update()
      elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
        clearscreen(screen)
        draw(screen, image_number, scale_a, scale_b, epsilon, paused)
        pygame.display.update()
        busy = False
      elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
        clearscreen(screen)
        create_mosaic(screen, playground, event.pos,
                      scale_a.get_size(), crop_a.get_size(), epsilon)
        busy = False
      elif event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
      elif event.type == pygame.KEYDOWN:
        newscreen = handle_key_event(screen, event, playground)
        if newscreen:
          screen = newscreen
        draw(screen, image_number, scale_a, scale_b, epsilon, paused)
        pygame.display.update()
      elif event.type == pygame.USEREVENT:
        if busy:
          continue
        if not paused:
          image_number += 2
          clip_image_number(playground)
        if image_number != last_drawn_image_number:
          try:
            crop_a, crop_b, scale_a, scale_b = render(playground, 
                                                      h, screen, epsilon)
            last_drawn_image_number = image_number
            if not paused:
              beep.play()
          except pygame.error:
            pass
          pygame.event.clear(pygame.USEREVENT)

if __name__ == "__main__":
  main(sys.argv[1])
