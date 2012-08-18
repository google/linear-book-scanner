#!/usr/bin/python
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
import cStringIO
import base64
import subprocess
import re
import tempfile

paused = False           # For image inspection
image_number = None      # Scanimage starts counting at 1
book_dimensions = None   # (top, bottom, side) in pixels
fullscreen = True        # Easier to debug in a window
suppressions = set()     # Pages we don't want to keep
left_offset = 593        # Hardware sensor position in pixels
right_offset = 150       # Hardware sensor position in pixels
dpi = 300                # Hardware resolution

def blue():
  """Original scansation blue, handed down from antiquity."""
  return (70, 120, 173)

def clearscreen(screen):
  """And G-d said, "Let there be blue light!"""
  screen.fill(blue())

def get_epsilon(screen):
  """How much to separate page image from center of display."""
  return screen.get_width() / 100

def render_text(screen, msg, position):
  """Write messages to screen, such as the image number."""
  pos = [0, 0]
  font = pygame.font.SysFont('Courier', 28, bold=True)
  if image_number in suppressions:
    color = pygame.Color('red')
  else:
    color = blue()
  for line in msg.split("\n"):
    if len(line) > 0:
      text = font.render(line.rstrip('\r'), 1, (255, 255, 255))
      background = pygame.Surface(text.get_size())
      background.fill(color)
      if position == "upperright":
        pos[0] = screen.get_width() - text.get_width()
      screen.blit(background, pos)
      screen.blit(text, pos)
      pygame.display.update(pygame.Rect(pos, text.get_size()))
    pos[1] += 30
    color = blue()

def read_ppm_header(fp):
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

def scale_to_crop_coord(scale_coord, scale_size, crop_size, epsilon):
  """Scale images are displayed 2-up in the screen."""
  w2 = pygame.display.Info().current_w // 2
  is_left = scale_coord[0] < w2
  if is_left:
    x0 = w2 - epsilon - scale_size[0]
  else:
    x0 = w2 + epsilon
  x = (scale_coord[0] - x0) * crop_size[0] // scale_size[0]
  y = scale_coord[1] * crop_size[1] // scale_size[1]
  if is_left:
    x = crop_size[0] - x
  return (x, y), is_left

def crop_to_full_coord(crop_coord, is_left):
  """We always crop out saddle, and usually crop to book page."""
  x, y = crop_coord
  if book_dimensions:
    (top, bottom, side) = book_dimensions
    y += top
  if is_left:
    y += left_offset
  else:
    y += right_offset
  return x, y

def process_image(h, filename, is_left):
  """Return both screen resolution and scan resolution images."""
  kSaddleHeight = 3600  # scan pixels
  f = open(filename, "r+b")
  dimensions, headersize = read_ppm_header(f)
  map = mmap.mmap(f.fileno(), 0)
  image = pygame.image.frombuffer(buffer(map, headersize), dimensions, 'RGB')
  unused, y = crop_to_full_coord((0, 0), is_left)
  if book_dimensions:
    (top, bottom, side) = book_dimensions
    wh = (side, bottom - top)
  else:
    wh = (image.get_width(), kSaddleHeight)
  rect = pygame.Rect((0, y), wh)
  crop = image.subsurface(rect)
  w = image.get_width() * h // kSaddleHeight
  scale = pygame.transform.smoothscale(crop, (w, h))
  if is_left:
    scale = pygame.transform.flip(scale, True, False)
  return scale, crop

def clip_image_number(playground):
  """Only show images that exist."""
  global image_number
  if image_number < 1:  # scanimage starts counting at 1
    image_number = 1
  while image_number > 1:
    filename = os.path.join(playground, '%06d.pnm' % image_number)
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
    side = min(side, scale_size[0])
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

def zoom(screen, click, scale_a, scale_b, crop_a, crop_b):
  """Given a mouseclick, zoom in on the region."""
  coord, is_left = scale_to_crop_coord(click, scale_a.get_size(),
                                       crop_a.get_size(), get_epsilon(screen))
  if is_left:
    crop = crop_a
  else:
    crop = crop_b
  size = pygame.display.Info().current_w // 3
  dst = (click[0] - size, click[1] - size)
  rect = pygame.Rect((coord[0] - size, coord[1] - size), (2 * size, 2 * size))
  if is_left:
    tmp = pygame.Surface((2 * size, 2 * size))
    tmp.blit(crop, (0,0), rect)
    tmp2 = pygame.transform.flip(tmp, True, False)
    screen.blit(tmp2, dst)
  else:
    screen.blit(crop, dst, rect)

def draw(screen, image_number, scale_a, scale_b, paused):
  """Draw the page images on screen."""
  w2 = screen.get_width() // 2
  render_text(screen, "%s" % str(image_number).ljust(4), "upperleft")
  render_text(screen, "%s" % str(image_number + 1).rjust(4), "upperright")
  epsilon = get_epsilon(screen)
  render_text(screen, "\n     ", "upperleft")
  screen.blit(scale_a, (w2 - scale_a.get_width() - epsilon, 0))
  screen.blit(scale_b, (w2 + epsilon, 0))
  if paused:
    render_text(screen, "\nPAUSE", "upperleft")

def create_new_pdf(filename, width, height):    
  import reportlab.rl_config
  from reportlab.pdfgen.canvas import Canvas
  pdf = Canvas(filename, pagesize=(width, height), pageCompression=1)
  pdf.setCreator('cheesegrater')
  load_font()
  return pdf
  
def export_pdf(playground, screen):
  """Create a PDF file fit for human consumption"""
  if book_dimensions == None:
    return
  width = book_dimensions[2] * 72 / dpi
  height = (book_dimensions[1] - book_dimensions[0]) * 72 / dpi
  pdf = create_new_pdf(os.path.join(playground, "book.pdf"), width, height)
  jpegs = glob.glob(os.path.join(playground, '*.jpg'))
  jpegs.sort()
  counter = 0
  for jpeg in jpegs:
    msg = "Exporting PDF %d/%d" % (counter, len(jpegs) - 1)
    render_text(screen, msg, "upperright")
    counter += 1
    pdf.drawImage(jpeg, 0, 0, width=width, height=height)
    add_text_layer(pdf, jpeg, height)
    pdf.showPage()
  pdf.save()
  render_text(screen, " " * len(msg), "upperright")  

def add_text_layer(pdf, jpeg, height):
  """Draw an invisible text layer for OCR data"""
  from xml.etree.ElementTree import ElementTree, ParseError
  p = re.compile('bbox((\s+\d+){4})')      
  hocrfile = os.path.splitext(jpeg)[0] + ".html"
  hocr = ElementTree()
  try:
    hocr.parse(hocrfile)
  except ParseError:
    print("Parse error for %s" % hocrfile)  # Tesseract bug fixed Aug 16, 2012
    return
  except IOError:
    return  # tesseract not installed
  for line in hocr.findall(".//%sspan"%('')):
    if line.attrib['class'] != 'ocr_line':
      continue
    coords = p.search(line.attrib['title']).group(1).split()
    base = height - float(coords[3]) * 72 / dpi
    for word in line:
      if word.attrib['class'] != 'ocr_word' or word.text is None:
        continue    
      default_width = pdf.stringWidth(word.text.strip(), 'invisible', 8)
      if default_width <= 0:
        continue
      coords = p.search(word.attrib['title']).group(1).split()
      left = float(coords[0]) * 72 / dpi
      right = float(coords[2]) * 72 / dpi      
      text = pdf.beginText()
      text.setTextRenderMode(3)  # double invisible
      text.setFont('invisible', 8)
      text.setTextOrigin(left, base)
      text.setHorizScale(100.0 * (right - left) / default_width)
      text.textLine(word.text.strip())
      pdf.drawText(text)

def save_jpeg(screen, crop_a, crop_b, playground, image_number):
  """Save cropped images in reading order."""
  renumber = 999999 - image_number  # switch to reading oslarder
  a = pygame.transform.flip(crop_a, True, False)
  p1 = write_jpeg(screen, playground, a, image_number, renumber)
  p2 = write_jpeg(screen, playground, crop_b, image_number, renumber + 1)
  return (p1, p2)
  
def write_jpeg(screen, playground, img, image_number, renumber):
  """Write JPEG image if not already there, plus remove any old cruft"""
  if book_dimensions:
    d = book_dimensions
    stem = "%06d-%s-%s-%s" % (renumber, d[0], d[1], d[2])
  else:
    stem = "%06d-uncropped" % renumber
  hocrs = glob.glob(os.path.join(playground, '%06d-*.html' % renumber))
  jpegs = glob.glob(os.path.join(playground, '%06d-*.jpg' % renumber))
  for file in hocrs + jpegs:
    if os.path.splitext(os.path.basename(file))[0] != stem:
      os.remove(file)
  jpeg = os.path.join(playground, stem + ".jpg")
  if not os.path.exists(jpeg):
    pygame.image.save(img, jpeg)
  p = None
  hocr = os.path.join(playground, stem)
  if os.path.exists(hocr + ".html"):
    msg = "\n\n\n   "
  else:
    msg = "\n\n\nOCR" 
    try:
      p = subprocess.Popen(['tesseract', jpeg, hocr, 'hocr'])
    except OSError:
      pass  # Tesseract not installed; user doesn't want OCR 
  if renumber % 2 == 0:
    render_text(screen, msg,  "upperleft")
  else:
    render_text(screen, msg,  "upperright")
  return p
    
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
  """Like opening credits in a movie, but more useful."""
  clearscreen(screen)
  render_text(screen, "Looking up barcode: %s" % barcode.split("_")[0],
              "upperleft")
  clearscreen(screen)
  render_text(screen, get_bibliography(barcode), "upperleft")
  pygame.display.update()
  render_text(screen, ("\n\n\n\n\n\n\n\n\n\n"
                       "H,?         = help\n"
                       "MOUSE       = crop | mosaic | zoom\n"
                       "ARROWS      = navigation\n"
                       "PgUp/PgDn   = navigation!\n"
                       "\n"
                       "S           = screenshot\n"
                       "Q,ESC       = quit\n"
                       "\n"
                       "E           = export to pdf\n"
                       "DELETE      = delete\n"
                       "F11,F       = fullscreen\n"
                       "P,SPACE     = pause\n"
                       ), "upperleft")
  clearscreen(screen)
  pygame.time.wait(2000)

def get_suppressions(playground):
  global suppressions
  try:
    for line in open(os.path.join(playground, "suppressions")).readlines():
      if line[0] != "#":
        suppressions = set([int(x) for x in line.split(",")])
  except IOError:
    pass

def set_suppressions(playground, image_number):
  global suppressions
  if image_number in suppressions:
    suppressions.remove(image_number)
  else:
    suppressions.add(image_number)
  filename = os.path.join(playground, "suppressions")
  f = open(filename, "wb")
  f.write("#Suppressed image pairs indicated by left image number\n")
  f.write(str(suppressions).strip('set([])'))
  f.write("\n");
  f.close()

def handle_key_event(screen, event, playground, barcode, mosaic_click,
                     fullsize):
  """I find it easier to deal with keystrokes mostly in one place."""
  global image_number
  global paused
  global fullscreen
  newscreen = None
  if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
    pygame.quit()
    sys.exit()
  elif event.key == pygame.K_SPACE or event.key == pygame.K_p:
    paused = not paused
  elif event.key == pygame.K_e:
    export_pdf(playground, screen)
  elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
    set_suppressions(playground, image_number)
  elif event.key == pygame.K_F11 or event.key == pygame.K_f:
    if fullscreen:
      window = pygame.display.set_mode((fullsize[0] // 2, 
                                        fullsize[1] // 2), pygame.RESIZABLE)
    else:
      window = pygame.display.set_mode(fullsize, pygame.FULLSCREEN)
    fullscreen = not fullscreen
    newscreen = pygame.display.get_surface()
    clearscreen(newscreen)
  elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
    image_number -= 2
    paused = True
  elif event.key == pygame.K_PAGEUP:
    image_number -= 10
    paused = True
  elif event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
    image_number += 2
    paused = True
  elif event.key == pygame.K_PAGEDOWN:
    image_number += 10
    paused = True
  elif event.key == pygame.K_s:
    filename = "screenshot-" + barcode + "-" + str(image_number) + ".jpg"
    pygame.image.save(screen, filename);
    render_text(screen, filename, "upperright")
    pygame.time.wait(2000)
    render_text(screen, " " * len(filename), "upperright")
  elif event.key == pygame.K_h or event.key == pygame.K_QUESTION:
    splashscreen(screen, barcode)
    pygame.time.wait(3000)
  clip_image_number(playground)
  if mosaic_click:
    clearscreen(screen)
  return newscreen

def render(playground, screen, paused, image_number):
  """Calculate and draw entire screen, including book images."""
  filename_a = os.path.join(playground, '%06d.pnm' % image_number)
  filename_b = os.path.join(playground, '%06d.pnm' % (image_number + 1))
  h = screen.get_height()
  scale_a, crop_a = process_image(h, filename_a, True)
  scale_b, crop_b = process_image(h, filename_b, False)
  draw(screen, image_number, scale_a, scale_b, paused)
  pygame.display.update()
  return crop_a, crop_b, scale_a, scale_b, image_number

def mosaic_dimensions(screen):
  """Reduce some cut-n-past code."""
  columns = 10
  rows = 20
  h = screen.get_height() // rows
  size = (2 * h, h)
  windowsize = 2 * rows * columns
  start = max(1, image_number - windowsize + 2)
  return size, windowsize, start, columns

def navigate_mosaic(playground, screen, click):
  """Click on a mosaic tile, jump to that page."""
  global image_number
  clearscreen(screen)
  size, unused, start, columns = mosaic_dimensions(screen)
  if click[0] > columns * size[0]:
    return
  x, y = click[0] // size[0], click[1] // size[1]
  candidate = start + 2 * (columns * y + x)
  filename = os.path.join(playground, '%06d.pnm' % candidate)
  if os.path.exists(filename):
    image_number = candidate

def render_mosaic(screen, playground, click, scale_size, crop_size,
                  image_number):
  """Useful for seeing lots of page numbers at once."""
  crop_coord, is_left = scale_to_crop_coord(click, scale_size,
                                            crop_size, get_epsilon(screen))
  full_coord = crop_to_full_coord(crop_coord, is_left)
  size, windowsize, start, columns = mosaic_dimensions(screen)
  if not is_left:
    start += 1
  for i in range(start, start + windowsize, 2):
    x = ((i - start) // 2) % columns
    y = ((i - start) // 2) // columns
    filename = os.path.join(playground, '%06d.pnm' % i)
    if not os.path.exists(filename):
      break
    f = open(filename, "r+b")
    map = mmap.mmap(f.fileno(), 0)
    dimensions, headersize = read_ppm_header(f)
    image = pygame.image.frombuffer(buffer(map, headersize), dimensions, 'RGB')
    src = full_coord[0] - 3 * size[0] // 2, full_coord[1] - 3 * size[1] // 2
    rect = pygame.Rect(src, (size[0] * 3, size[1] * 3))
    crop = image.subsurface(rect)
    scale = pygame.transform.smoothscale(crop, size)
    if is_left:
      scale = pygame.transform.flip(scale, True, False)
    dst = (size[0] * x, size[1] * y)
    dirty = pygame.Rect(dst, size)
    if is_left:
      left_image_number =  i
    else:
      left_image_number =  i - 1
    screen.blit(scale, dst)
    if left_image_number in suppressions:
      red = pygame.Surface(scale.get_size())
      red.fill(pygame.Color('red'))
      red.set_alpha(128)
      screen.blit(red, dst)
    map.close()
    f.close()
    pygame.display.update(dirty)

def get_beep():
  """Not having as external file makes life easier for sysadmins."""
  wav = """
UklGRigCAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQQCAAA01jVaF1f2WGJW1FoN
U5hhMcMxoKCoiqhcogiwOJTK/zxqak9fXHxWrFYcXv08rZtQrhShk6wBoXaudZtGPcZdBlcnVqdc
N09Tatf//pN7sKKhmKkypwui3sBzZJhP+V5tUfBeq09XZALB36Fnp1mp7KEksGWUXv/eappOVV1n
VdhX41w7Pm6ai6/hn7yt5Z+Cr3uaLD71XMJXgVU4XbpOu2qE/z2UT7C9oYupM6cVosvAjGR5Tx9f
QVEgX3hPimTQwA+iOqeEqcKhS7BBlIH/vmq2TjxdfVXGV/FcMD53moWv45+8reOfhq92mjE+71zI
V3xVPF22Tr9qf/9ClEuwwqGFqTinEKLQwItkd08gX0JRHl96T4pkzsASojenhanDoUuwQJSC/7xq
uE48XXxVx1fxXC4+epqCr+afuq3kn4Wvd5oxPu9cx1d9VTtduE6+an7/RZRGsMihfqk/pwui1MCG
ZHxPG19HURpffU+HZNHAEKI4p4apwKFPsDuUh/+2asJOLl2NVbNXBV0cPouaca/5n6Wt+p9wr4ma
Ij77XMFXfFVDXalO0mpm/2OUILD2oUipgKe+oSzBImTtT6FeyFGTXghQ+mNgwYGhw6cCqTmi5K+W
lED/5WqsTiddtVVnV3pdej1bm3OuJKFNrH+hv61knCI8GF+PVbVXG1uUUIZp4f4=
"""
  f = cStringIO.StringIO(base64.decodestring(wav))
  return pygame.mixer.Sound(f)

def main(argv1):
  """Display scanned images as they are created."""
  playground = argv1.rstrip('/')
  barcode = os.path.basename(playground)
  pygame.init()
  global image_number
  global paused
  global book_dimensions
  last_drawn_image_number = 0
  get_book_dimensions(playground)
  get_suppressions(playground)
  try: 
    beep = get_beep()
  except:
    pass
  fullsize = (pygame.display.Info().current_w, pygame.display.Info().current_h)
  if fullscreen:
    window = pygame.display.set_mode(fullsize, pygame.FULLSCREEN)
  else:
    window = pygame.display.set_mode((fullsize[0] // 2, 
                                      fullsize[1] // 2), pygame.RESIZABLE)
  screen = pygame.display.get_surface()
  pygame.display.set_caption("Barcode: %s" % barcode)
  splashscreen(screen, barcode)
  scale_a = None  # prevent crash if keypress during opening splashscreen
  image_number = 1
  pygame.time.set_timer(pygame.USEREVENT, 50)
  shadow = pygame.Surface(screen.get_size())
  shadow.set_alpha(128)
  shadow.fill((0, 0, 0))
  mosaic_click = None  # Don't mode me in, bro!
  p1, p2 = None, None
  busy = False
  while True:
    for event in [ pygame.event.wait() ]:
      if event.type == pygame.MOUSEBUTTONDOWN:
        busy = True
        pygame.event.clear(pygame.USEREVENT)
      if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if mosaic_click:
          continue
        leftdownclick = event.pos
        oldscreen = screen.copy()
        shadowscreen = screen.copy()
        shadowscreen.blit(shadow, (0, 0))
        screen.blit(shadowscreen, (0, 0))
        prevroi = pygame.Rect(event.pos, (0, 0))
        pygame.display.update()
      elif event.type == pygame.MOUSEMOTION and event.buttons[0] == 1:
        if book_dimensions or mosaic_click:
          continue
        x = abs(event.pos[0] - screen.get_width() // 2)
        pos = (screen.get_width() // 2 - x, min(leftdownclick[1], event.pos[1]))
        roi = pygame.Rect(pos, (2 * x, abs(leftdownclick[1] - event.pos[1])))
        dirty = roi.union(prevroi)
        prevroi = roi.copy()
        screen.blit(shadowscreen, dirty.topleft, area = dirty)
        screen.blit(oldscreen, roi.topleft, area = roi)
        pygame.display.update(dirty)
      elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        if mosaic_click:
          navigate_mosaic(playground, screen, event.pos)
          last_drawn_image_number = None
          mosaic_click = None
        else:
          oldscreen = None
          leftclick = (leftdownclick, event.pos)
          set_book_dimensions(leftclick, get_epsilon(screen), crop_a.get_size(),
                              scale_a.get_size(), playground)
          clearscreen(screen)
          crop_a, crop_b, scale_a, scale_b, last_drawn_image_number = \
              render(playground, screen, paused, image_number)
        busy = False
      elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        draw(screen, image_number, scale_a, scale_b, paused)
        zoom(screen, event.pos, scale_a, scale_b, crop_a, crop_b)
        pygame.display.update()
      elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
        mosaic_click = None
        clearscreen(screen)
        draw(screen, image_number, scale_a, scale_b, paused)
        pygame.display.update()
        busy = False
      elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
        mosaic_click = event.pos
        if image_number != last_drawn_image_number:
          crop_a, crop_b, scale_a, scale_b, last_drawn_image_number = \
              render(playground, screen, paused, image_number)
        try:
          render_mosaic(screen, playground, mosaic_click, scale_a.get_size(),
                        crop_a.get_size(), image_number)
        except ValueError:
          mosaic_click = None
        paused = True
        busy = False
      elif event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
      elif mosaic_click and \
            event.type == pygame.KEYDOWN and \
            (event.key == pygame.K_PAGEUP or event.key == pygame.K_PAGEDOWN):
        unused, windowsize, start, unused = mosaic_dimensions(screen)
        if event.key == pygame.K_PAGEUP:
          image_number = start - 2
        elif event.key == pygame.K_PAGEDOWN:
          image_number = start + windowsize + windowsize - 2
        clip_image_number(playground)
        clearscreen(screen)
        if image_number != last_drawn_image_number:
          crop_a, crop_b, scale_a, scale_b, last_drawn_image_number = \
              render(playground, screen, paused, image_number)
        render_mosaic(screen, playground, mosaic_click, scale_a.get_size(),
                      crop_a.get_size(), image_number)
      elif event.type == pygame.KEYDOWN:
        newscreen = handle_key_event(screen, event, playground, barcode,
                                     mosaic_click, fullsize)
        mosaic_click = None
        last_drawn_image_number = None
        if newscreen:
          screen = newscreen
          clearscreen(screen)
      elif event.type == pygame.VIDEORESIZE:
        screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
        clearscreen(screen)
        last_drawn_image_number = None
      elif event.type == pygame.USEREVENT:
        if busy:
          continue
        if p1 and p1.poll() != None:
          p1 = None
          render_text(screen, "\n\n\n   ", "upperleft")
        if p2 and p2.poll() != None:
          p2 = None
          render_text(screen, "\n\n\n   ", "upperright")
        if not (paused or p1 or p2):
          image_number += 2
          clip_image_number(playground)
        if image_number != last_drawn_image_number:
          try:
            crop_a, crop_b, scale_a, scale_b, last_drawn_image_number = \
                render(playground, screen, paused, image_number)
            p1, p2 = save_jpeg(screen, crop_a, crop_b, playground, image_number)             
            if not paused:
              try:
                beep.play()
              except:
                pass
          except IOError:
            pass
          pygame.event.clear(pygame.USEREVENT)

# From http://www.angelfire.com/pr/pgpf/if.html which says
# 'Invisible font' is unrestricted freeware. Enjoy, Improve, Distribute freely
def load_font():
  font = """
AAEAAAALAIAAAwAwT1MvMrtCiDsAAAE4AAAAVmNtYXDQfj7mAAALxAAABdJnYXNw//8AAwAALyQAAAA
IZ2x5Zl9Tl/sAABa0AAAAJGhlYWTfCIBwAAAAvAAAADZoaGVhCNUN/QAAAPQAAAAkaG10eAK3AAAAAA
GQAAAKMmxvY2ERyhHcAAARmAAABRxtYXhwBu0ANgAAARgAAAAgbmFtZWxYPl0AABbYAAAE33Bvc3TnW
RzzAAAbuAAAE2wAAQAAAAEAALoUuhRfDzz1AAsIAAAAAAC/TJLwAAAAAL9MolkAAAJdAVIDzAAAAAkA
AQAAAAAAAAABAAAHPv5OAEMIwAAABGIBUgABAAAAAAAAAAAAAAAAAAACjAABAAACjQAFAAEAAAAAAAI
AEAAvAEIAAAQMAAAAAAAAAAEDiAGQAAUACAWaBTMAAAEbBZoFMwAAA9EAZgISAAACAAAAAAAAAAAAoA
ACr1AAePsAAAAAAAAAAEhMICAAQAAg+wIF0/5RATMHPgGyYAABn9/3AAAAAAYAAAAAAAAAAjkAAAI5A
AACOQAAAtcAAARzAAAEcwAABx0AAAVWAAABhwAAAqoAAAKqAAADHQAABKwAAAI5AAACqgAAAjkAAAI5
AAAEcwAABHMAAARzAAAEcwAABHMAAARzAAAEcwAABHMAAARzAAAEcwAAAjkAAAI5AAAErAAABKwAAAS
sAAAEcwAACB8AAAVWAAAFVgAABccAAAXHAAAFVgAABOMAAAY5AAAFxwAAAjkAAAQAAAAFVgAABHMAAA
aqAAAFxwAABjkAAAVWAAAGOQAABccAAAVWAAAE4wAABccAAAVWAAAHjQAABVYAAAVWAAAE4wAAAjkAA
AI5AAACOQAAA8EAAARzAAACqgAABHMAAARzAAAEAAAABHMAAARzAAACOQAABHMAAARzAAABxwAAAccA
AAQAAAABxwAABqoAAARzAAAEcwAABHMAAARzAAACqgAABAAAAAI5AAAEcwAABAAAAAXHAAAEAAAABAA
AAAQAAAACrAAAAhQAAAKsAAAErAAABVYAAAVWAAAFxwAABVYAAAXHAAAGOQAABccAAARzAAAEcwAABH
MAAARzAAAEcwAABHMAAAQAAAAEcwAABHMAAARzAAAEcwAAAjkAAAI5AAACOQAAAjkAAARzAAAEcwAAB
HMAAARzAAAEcwAABHMAAARzAAAEcwAABHMAAARzAAAEcwAAAzMAAARzAAAEcwAABHMAAALNAAAETAAA
BOMAAAXlAAAF5QAACAAAAAKqAAACqgAABGQAAAgAAAAGOQAABbQAAARkAAAEZAAABGQAAARzAAAEnAA
AA/QAAAW0AAAGlgAABGQAAAIxAAAC9gAAAuwAAAYlAAAHHQAABOMAAATjAAACqgAABKwAAARkAAAEcw
AABGQAAATlAAAEcwAABHMAAAgAAAAFVgAABVYAAAY5AAAIAAAAB40AAARzAAAIAAAAAqoAAAKqAAABx
wAAAccAAARkAAAD9AAABAAAAAVWAAABVgAABHMAAAKqAAACqgAABAAAAAQAAAAEcwAAAjkAAAHHAAAC
qgAACAAAAAVWAAAFVgAABVYAAAVWAAAFVgAAAjkAAAI5AAACOQAAAjkAAAY5AAAGOQAABjkAAAXHAAA
FxwAABccAAAI5AAACqgAAAqoAAAKqAAACqgAAAqoAAAKqAAACqgAAAqoAAAKqAAACqgAABHMAAAHHAA
AFVgAABAAAAATjAAAEAAAAAhQAAAXHAAAEcwAABVYAAAQAAAAFVgAABHMAAASsAAAErAAAAqoAAAKqA
AACqgAABqwAAAasAAAGrAAABHMAAAY5AAAEcwAAAjkAAAVWAAAEAAAABccAAAQAAAAFxwAABAAAAARz
AAAEcwAABGsAAAVWAAAEcwAABVYAAARzAAAFVgAABHMAAAXHAAAEAAAABccAAAQAAAAFxwAABOsAAAX
HAAAFVgAABHMAAAVWAAAEcwAABVYAAARzAAAFVgAABHMAAAVWAAAEcwAABjkAAARzAAAGOQAABHMAAA
Y5AAAEcwAABccAAARzAAAFxwAABHMAAAI5AAACOQAAAjkAAAI5AAACOQAAAjkAAAI5AAABxwAABeEAA
AONAAAEAAAAAccAAAVWAAAEAAAABAAAAARzAAABxwAABHMAAAHHAAAEcwAAAlUAAARzAAACrAAABccA
AARzAAAFxwAABHMAAAXHAAAEcwAABNUAAAXJAAAEcwAABjkAAARzAAAGOQAABHMAAAY5AAAEcwAABcc
AAAKqAAAFxwAAAqoAAAXHAAACqgAABVYAAAQAAAAFVgAABAAAAATjAAACOQAABOMAAAMAAAAE4wAAAj
kAAAXHAAAEcwAABccAAARzAAAFxwAABHMAAAXHAAAEcwAABccAAARzAAAFxwAABHMAAAeNAAAFxwAAB
VYAAAQAAAAE4wAABAAAAATjAAAEAAAAAccAAAVWAAAEcwAACAAAAAcdAAAGOQAABOMAAAKqAAACqgAA
BVcAAAI5AAAGRgAABrQAAAMSAAAGMgAABtgAAAYFAAABxwAABVYAAAVWAAAEaAAABVgAAAVWAAAE4wA
ABccAAAY5AAACOQAABVYAAAVYAAAGqgAABccAAAUzAAAGOQAABccAAAVWAAAE8gAABOMAAAVWAAAGYg
AABVYAAAavAAAF+wAAAjkAAAVWAAAEoAAAA5EAAARzAAABxwAABGAAAASgAAAEmgAABAAAAAR0AAADk
QAAA4cAAARzAAAEcwAAAccAAAQAAAAEAAAABJwAAAQAAAADlQAABHMAAAWFAAAEjQAAA9sAAATwAAAD
KQAABGAAAAUwAAAEMwAABbQAAAY/AAABxwAABGAAAARzAAAEYAAABj8AAAVXAAAG6wAABFUAAAXAAAA
FVgAAAjkAAAI5AAAEAAAACHUAAAgVAAAG1QAABKkAAAUVAAAFwAAABVYAAAVAAAAFVgAABFUAAAVrAA
AFVgAAB2MAAATVAAAFwAAABcAAAASpAAAFQAAABqoAAAXHAAAGOQAABcAAAAVWAAAFxwAABOMAAAUVA
AAGFQAABVYAAAXrAAAFVQAAB1UAAAeAAAAGVQAABxUAAAVAAAAFwAAACBUAAAXHAAAEcwAABJUAAARA
AAAC6wAABKsAAARzAAAFWgAAA6sAAAR4AAAEeAAAA4AAAASrAAAFgAAABGsAAARzAAAEVQAABHMAAAQ
AAAADqgAABAAAAAaVAAAEAAAABJUAAAQrAAAGawAABpUAAAUAAAAFwAAABCsAAAQVAAAGAAAABFUAAA
RzAAAEcwAAAusAAAQVAAAEAAAAAccAAAI5AAABxwAAB0AAAAaAAAAEcwAAA4AAAAQAAAAEawAAA+kAA
ANKAAAHjQAABccAAAeNAAAFxwAAB40AAAXHAAAFVgAABAAAAAgAAAAEawAAAccAAAGAAAAC1QAABAAA
AAKqAAAC6wAABHMAAAjAAAAHFQAAApYAAAiVAAAEzQAABqwAAAasAAAGrAAABqwAAAgAAAAEAAAACAA
AAAQAAAAIAAAABAAAAAQAAAAH1QAABcAAAASrAAAE1QAABKwAAATVAAAE1QAABasAAAUAAAAFqwAABa
sAAAWrAAAFqwAABasAAAWrAAAFqwAABasAAAWrAAAFqwAABasAAAWrAAAFqwAABasAAAWrAAAFqwAAB
asAAAWrAAAFqwAABasAAAWrAAAFqwAABasAAAWrAAAFqwAABasAAAWrAAAFqwAABasAAAWrAAAFqwAA
BasAAAWrAAAFqwAABasAAAWrAAAFqwAABasAAAWrAAAFqwAABasAAAWrAAAFqwAABasAAAWrAAAF1QA
ABNUAAATVAAAC1gAAAtYAAAgAAAAH6wAAB+sAAAfrAAAH6wAABNUAAATVAAAE1QAABNUAAALWAAAIKw
AACGsAAAdVAAAGAAAABgAAAARAAAAFQAAABMAAAAQVAAAEAAAABgAAAAKqAAAAAAAAAAAAAgABAAAAA
AAUAAMAAQAAARoAAAEGAAABAAAAAAAAAAECAAAAAgAAAAAAAAAAAAAAAAAAAAEAAAMEBQYHCAkKCwwN
Dg8QERITFBUWFxgZGhscHR4fICEiIyQlJicoKSorLC0uLzAxMjM0NTY3ODk6Ozw9Pj9AQUJDREVGR0h
JSktMTU5PUFFSU1RVVldYWVpbXF1eX2BhAGJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXp7fH1+f4CBgo
OEhYaHiImKi4yNjo+QkZKTlJWWl5iZmpucnZ6foKGio6SlpqeoqaqrA6ytrq+wsbKztLW2t7i5uru8v
b6/wMHCw8TFxsfIycrLzM3Oz9AA0dLT1NXW19jZ2tvc3d7fAAQEuAAAANYAgAAGAFYAfgERAR0BHwEv
ATEBQAFCAVEBUwFdAWEBdwF/AZIB/wLHAskC3QN+A4oDjAOhA84EDARPBFwEXwSRHoUe8yAVIB4gIiA
mIDAgMyA6IDwgPiBEIH8gpCCnIKwhBSETIRYhIiEmIS4hXiGVIagiAiIGIg8iEiIVIhoiHyIpIisiSC
JhImUjAiMQIyElACUCJQwlECUUJRglHCUkJSwlNCU8JWwlgCWEJYgljCWTJaElrCWyJbolvCXEJcslz
yXZJeYmPCZAJkImYCZjJmYma/AC8AX7Av//AAAAIACgARIBHgEgATABMgFBAUMBUgFUAV4BYgF4AZIB
+gLGAskC2AN+A4QDjAOOA6MEAQQOBFEEXgSQHoAe8iATIBcgICAmIDAgMiA5IDwgPiBEIH8goyCnIKw
hBSETIRYhIiEmIS4hWyGQIagiAiIGIg8iESIVIhkiHiIpIisiSCJgImQjAiMQIyAlACUCJQwlECUUJR
glHCUkJSwlNCU8JVAlgCWEJYgljCWQJaAlqiWyJbolvCXEJcolzyXYJeYmOiZAJkImYCZjJmUmavAB8
AT7Af///+MAAP/9AAD/+wAA//kAAP/3AAD/9QAA//EAAP8U/3QAAP4PAAD8oP3w/e/97v3t/bv9uv25
/bj9iOOa4y4AAAAAAADgheCV4fPghOHr4ergd+GqAADhhOAQ4SfhGuEY32rfeeEB4NXgpOCS3pbeot6
LAADepgAAAADgE95x3l8AAN4w3zzfL98g3ULdQd043TXdMt0v3SzdJd0e3RfdENz93Orc59zk3OHc3t
zS3Mrcxdy+3L3ctgAA3K3cpdyZ3EbcQ9xC3CXcI9wi3B8QvhKHBb4AAQAAANQAAAG0AAABtAAAAbQAA
AG0AAABtAAAAbgAAAAAAcIAAAHCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbQBuAHGAAAAAAAAAAAA
AAAAAAAAAAG6AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGgAAABoAGiAAAAAAAAAZ4AAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABagAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAwCjAIQAhQEAAJYA5gCGAI4AiwCdAKkApAAQAIoBAQCDAJMA8ADxA
I0AlwCIAMIA3ADvAJ4AqgDzAPIA9ACiAKwAyADGAK0AYgBjAJAAZADKAGUAxwDJAM4AywDMAM0A5wBm
ANEAzwDQAK4AZwDuAJEA1ADSANMAaADpAOsAiQBqAGkAawBtAGwAbgCgAG8AcQBwAHIAcwB1AHQAdgB
3AOgAeAB6AHkAewB9AHwAtwChAH8AfgCAAIEA6gDsALkBAgEDAQQBBQEGAQcA+wD8AQgBCQEKAQsA/Q
D+AQwBDQEOAP8A9gD3APgA1QDgAOEArwCwAPkA+gDiAOMAugFpAWoBawFsAOQA5QFtANYA3wDZANoA2
wDeANcA3QCxALICIgIjALUAtgDDAiQAswC0AMQAggDBAIcA9QIqAJkA7QDCAKUAkgI7AI8CPQC4AnsA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
SABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEg
ASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAE
gASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIA
EgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABI
AEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASAB
IAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASA
BIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgAS
ABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgA
SABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEg
ASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAE
gASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIA
EgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABI
AEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASAB
IAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASA
BIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgAS
ABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgA
SABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEgASABIAEg
ASABIAEgABAAACXQFSA8wABAAAGwI3AXZJhA/+rgOv/q4BaAf+mQAAAAAAACgB5gABAAAAAAAAADQAA
AABAAAAAAABAAkAOwABAAAAAAACAAcANAABAAAAAAADABYAOwABAAAAAAAEAAkAOwABAAAAAAAFADAA
UQABAAAAAAAGAAkAOwABAAAAAAAKAEAAgQADAAEEAwACAAwCrwADAAEEBQACABAAwQADAAEEBgACAAw
A0QADAAEEBwACABAA3QADAAEECAACABAA7QADAAEECQAAAGgA/QADAAEECQABABIBcwADAAEECQACAA
4BZQADAAEECQADACwBcwADAAEECQAEABIBcwADAAEECQAFAGABnwADAAEECQAGABIBcwADAAEECQAKA
IAB/wADAAEECgACAAwCrwADAAEECwACABACfwADAAEEDAACAAwCrwADAAEEDgACAAwCzQADAAEEEAAC
AA4CjwADAAEEEwACABICnQADAAEEFAACAAwCrwADAAEEFQACABACrwADAAEEFgACAAwCrwADAAEEGQA
CAA4CvwADAAEEGwACABACzQADAAEEHQACAAwCrwADAAEEHwACAAwCrwADAAEEJAACAA4C3QADAAEELQ
ACAA4C6wADAAEICgACAAwCrwADAAEIFgACAAwCrwADAAEMCgACAAwCrwADAAEMDAACAAwCr1R5cGVmY
WNlIKkgKHlvdXIgY29tcGFueSkuIDIwMDUuIEFsbCBSaWdodHMgUmVzZXJ2ZWRSZWd1bGFyaW52aXNp
YmxlOlZlcnNpb24gMS4wMFZlcnNpb24gMS4wMCBTZXB0ZW1iZXIgMTMsIDIwMDUsIGluaXRpYWwgcmV
sZWFzZVRoaXMgZm9udCB3YXMgY3JlYXRlZCB1c2luZyBGb250IENyZWF0b3IgNS4wIGZyb20gSGlnaC
1Mb2dpYy5jb20AbwBiAHkBDQBlAGoAbgDpAG4AbwByAG0AYQBsAFMAdABhAG4AZABhAHIAZAOaA7EDv
QO/A70DuQO6A6wAVAB5AHAAZQBmAGEAYwBlACAAqQAgACgAeQBvAHUAcgAgAGMAbwBtAHAAYQBuAHkA
KQAuACAAMgAwADAANQAuACAAQQBsAGwAIABSAGkAZwBoAHQAcwAgAFIAZQBzAGUAcgB2AGUAZABSAGU
AZwB1AGwAYQByAGkAbgB2AGkAcwBpAGIAbABlADoAVgBlAHIAcwBpAG8AbgAgADEALgAwADAAVgBlAH
IAcwBpAG8AbgAgADEALgAwADAAIABTAGUAcAB0AGUAbQBiAGUAcgAgADEAMwAsACAAMgAwADAANQAsA
CAAaQBuAGkAdABpAGEAbAAgAHIAZQBsAGUAYQBzAGUAVABoAGkAcwAgAGYAbwBuAHQAIAB3AGEAcwAg
AGMAcgBlAGEAdABlAGQAIAB1AHMAaQBuAGcAIABGAG8AbgB0ACAAQwByAGUAYQB0AG8AcgAgADUALgA
wACAAZgByAG8AbQAgAEgAaQBnAGgALQBMAG8AZwBpAGMALgBjAG8AbQBOAG8AcgBtAGEAYQBsAGkATg
BvAHIAbQBhAGwAZQBTAHQAYQBuAGQAYQBhAHIAZABOAG8AcgBtAGEAbABuAHkEHgQxBEsERwQ9BEsEO
QBOAG8AcgBtAOEAbABuAGUATgBhAHYAYQBkAG4AbwBBAHIAcgB1AG4AdABhAAACAAAAAAAA/ycAlgAA
AAAAAAAAAAAAAAAAAAAAAAAAAo0AAAECAQMAAwAEAAUABgAHAAgACQAKAAsADAANAA4ADwAQABEAEgA
TABQAFQAWABcAGAAZABoAGwAcAB0AHgAfACAAIQAiACMAJAAlACYAJwAoACkAKgArACwALQAuAC8AMA
AxADIAMwA0ADUANgA3ADgAOQA6ADsAPAA9AD4APwBAAEEAQgBDAEQARQBGAEcASABJAEoASwBMAE0AT
gBPAFAAUQBSAFMAVABVAFYAVwBYAFkAWgBbAFwAXQBeAF8AYABhAGIAYwBkAGUAZgBnAGgAaQBqAGsA
bABtAG4AbwBwAHEAcgBzAHQAdQB2AHcAeAB5AHoAewB8AH0AfgB/AIAAgQCCAIMAhACFAIYAhwCIAIk
AigCLAIwAjQCOAI8AkACRAJIAkwCUAJUAlgCXAJgAmQCaAQQAnACdAJ4AnwCgAKEAogCjAKQApQCmAK
cAqACpAKoAqwCtAK4ArwCwALEAsgCzALQAtQC2ALcAuAC5ALoAuwC8AQUAvgC/AQYBBwDCAMMAxADFA
MYAxwDIAMkAygDLAMwAzQDOAM8A0ADRANMA1ADVANYA1wDYANkBCADbANwA3QDeAN8A4ADhAOIA4wDk
AOUA5gDnAOgA6QDqAOsA7ADtAO4A7wDwAQkBCgELAPQA9QD2APcA+AD5AQwA+wD8AP0A/gD/AQABAQC
9ANoBDQEOAQ8BEAERARIBEwEUARUBFgEXARgBGQEaARsBHAEdAR4BHwEgASEBIgEjASQBJQEmAScBKA
EpASoBKwEsAS0BLgEvATABMQEyATMBNAE1ATYBNwE4ATkBOgE7ATwBPQE+AT8BQAFBAUIBQwFEAUUBR
gFHAUgBSQFKAUsBTAFNAU4BTwFQAVEBUgFTAVQBVQFWAVcBWAFZAVoBWwFcAV0BXgFfAWABYQFiAWMB
ZAFlAWYBZwFoAWkBagFrAWwBbQFuAW8BcAFxAXIBcwF0AXUBdgF3AXgBeQF6AXsBfAF9AX4BfwGAAYE
BggGDAYQBhQGGAYcBiAGJAYoBiwGMAY0BjgGPAZABkQGSAZMBlAGVAZYBlwGYAZkBmgGbAZwBnQGeAZ
8BoAGhAaIBowGkAaUBpgGnAagBqQGqAasBrAGtAa4BrwGwAbEBsgGzAbQBtQG2AbcAmwG4AbkBugG7A
bwBvQG+Ab8BwAHBAcIBwwHEAcUBxgHHAcgByQHKAcsBzAHNAc4BzwHQAdEB0gHTAdQB1QHWAdcB2AHZ
AdoB2wHcAd0B3gHfAeAB4QHiAeMB5AHlAeYB5wHoAekB6gHrAewB7QHuAe8B8AHxAfIB8wH0AfUB9gH
3AfgB+QH6AfsB/AH9Af4B/wIAAgECAgIDAgQCBQIGAgcCCAIJAgoCCwIMAg0CDgIPAhACEQISAhMCFA
IVAhYCFwIYAhkCGgIbAhwCHQIeAh8CIAIhAiICIwIkAiUCJgInAigCKQIqAisCLAItAi4CLwIwAjECM
gIzAjQCNQI2AjcCOAI5AjoCOwI8Aj0CPgI/AkACQQJCAkMCRAJFAkYCRwJIAkkCSgJLAkwCTQJOAk8C
UAJRAlICUwJUAlUCVgJXAlgCWQJaAlsCXAJdAl4CXwJgAmECYgJjAmQCZQJmAmcCaAJpAmoCawJsAm0
CbgJvAnACcQJyAnMCdAJ1AnYCdwJ4AnkCegJ7AnwCfQJ+An8CgAKBAoICgwKEAoUChgKHAogCiQKKAo
sCjAKNAo4CjwKQApECkgKTApQClQKWBS5udWxsEG5vbm1hcmtpbmdyZXR1cm4ABEV1cm8HdW5pRjAwM
Qd1bmlGMDAyB3VuaTAyQzkHdW5pMDBCOQd1bmkwMEIyB3VuaTAwQjMKSWRvdGFjY2VudAdBbWFjcm9u
B2FtYWNyb24GQWJyZXZlBmFicmV2ZQdBb2dvbmVrB2FvZ29uZWsLQ2NpcmN1bWZsZXgLY2NpcmN1bWZ
sZXgKQ2RvdGFjY2VudApjZG90YWNjZW50BkRjYXJvbgZkY2Fyb24GRGNyb2F0B0VtYWNyb24HZW1hY3
JvbgZFYnJldmUGZWJyZXZlCkVkb3RhY2NlbnQKZWRvdGFjY2VudAdFb2dvbmVrB2VvZ29uZWsGRWNhc
m9uBmVjYXJvbgtHY2lyY3VtZmxleAtnY2lyY3VtZmxleApHZG90YWNjZW50Cmdkb3RhY2NlbnQMR2Nv
bW1hYWNjZW50DGdjb21tYWFjY2VudAtIY2lyY3VtZmxleAtoY2lyY3VtZmxleARIYmFyBGhiYXIGSXR
pbGRlBml0aWxkZQdJbWFjcm9uB2ltYWNyb24GSWJyZXZlBmlicmV2ZQdJb2dvbmVrB2lvZ29uZWsCSU
oCaWoLSmNpcmN1bWZsZXgLamNpcmN1bWZsZXgMS2NvbW1hYWNjZW50DGtjb21tYWFjY2VudAxrZ3JlZ
W5sYW5kaWMGTGFjdXRlBmxhY3V0ZQxMY29tbWFhY2NlbnQMbGNvbW1hYWNjZW50BkxjYXJvbgZsY2Fy
b24ETGRvdARsZG90Bk5hY3V0ZQZuYWN1dGUMTmNvbW1hYWNjZW50DG5jb21tYWFjY2VudAZOY2Fyb24
GbmNhcm9uC25hcG9zdHJvcGhlA0VuZwNlbmcHT21hY3JvbgdvbWFjcm9uBk9icmV2ZQZvYnJldmUNT2
h1bmdhcnVtbGF1dA1vaHVuZ2FydW1sYXV0BlJhY3V0ZQZyYWN1dGUMUmNvbW1hYWNjZW50DHJjb21tY
WFjY2VudAZSY2Fyb24GcmNhcm9uBlNhY3V0ZQZzYWN1dGULU2NpcmN1bWZsZXgLc2NpcmN1bWZsZXgM
VGNvbW1hYWNjZW50DHRjb21tYWFjY2VudAZUY2Fyb24GdGNhcm9uBFRiYXIEdGJhcgZVdGlsZGUGdXR
pbGRlB1VtYWNyb24HdW1hY3JvbgZVYnJldmUGdWJyZXZlBVVyaW5nBXVyaW5nDVVodW5nYXJ1bWxhdX
QNdWh1bmdhcnVtbGF1dAdVb2dvbmVrB3VvZ29uZWsLV2NpcmN1bWZsZXgLd2NpcmN1bWZsZXgLWWNpc
mN1bWZsZXgLeWNpcmN1bWZsZXgGWmFjdXRlBnphY3V0ZQpaZG90YWNjZW50Cnpkb3RhY2NlbnQFbG9u
Z3MKQXJpbmdhY3V0ZQphcmluZ2FjdXRlB0FFYWN1dGUHYWVhY3V0ZQtPc2xhc2hhY3V0ZQtvc2xhc2h
hY3V0ZQV0b25vcw1kaWVyZXNpc3Rvbm9zCkFscGhhdG9ub3MJYW5vdGVsZWlhDEVwc2lsb250b25vcw
hFdGF0b25vcwlJb3RhdG9ub3MMT21pY3JvbnRvbm9zDFVwc2lsb250b25vcwpPbWVnYXRvbm9zEWlvd
GFkaWVyZXNpc3Rvbm9zBUFscGhhBEJldGEFR2FtbWEHdW5pMDM5NAdFcHNpbG9uBFpldGEDRXRhBVRo
ZXRhBElvdGEFS2FwcGEGTGFtYmRhAk11Ak51AlhpB09taWNyb24CUGkDUmhvBVNpZ21hA1RhdQdVcHN
pbG9uA1BoaQNDaGkDUHNpB3VuaTAzQTkMSW90YWRpZXJlc2lzD1Vwc2lsb25kaWVyZXNpcwphbHBoYX
Rvbm9zDGVwc2lsb250b25vcwhldGF0b25vcwlpb3RhdG9ub3MUdXBzaWxvbmRpZXJlc2lzdG9ub3MFY
WxwaGEEYmV0YQVnYW1tYQVkZWx0YQdlcHNpbG9uBHpldGEDZXRhBXRoZXRhBGlvdGEFa2FwcGEGbGFt
YmRhB3VuaTAzQkMCbnUCeGkHb21pY3JvbgNyaG8Gc2lnbWExBXNpZ21hA3RhdQd1cHNpbG9uA3BoaQN
jaGkDcHNpBW9tZWdhDGlvdGFkaWVyZXNpcw91cHNpbG9uZGllcmVzaXMMb21pY3JvbnRvbm9zDHVwc2
lsb250b25vcwpvbWVnYXRvbm9zCWFmaWkxMDAyMwlhZmlpMTAwNTEJYWZpaTEwMDUyCWFmaWkxMDA1M
wlhZmlpMTAwNTQJYWZpaTEwMDU1CWFmaWkxMDA1NglhZmlpMTAwNTcJYWZpaTEwMDU4CWFmaWkxMDA1
OQlhZmlpMTAwNjAJYWZpaTEwMDYxCWFmaWkxMDA2MglhZmlpMTAxNDUJYWZpaTEwMDE3CWFmaWkxMDA
xOAlhZmlpMTAwMTkJYWZpaTEwMDIwCWFmaWkxMDAyMQlhZmlpMTAwMjIJYWZpaTEwMDI0CWFmaWkxMD
AyNQlhZmlpMTAwMjYJYWZpaTEwMDI3CWFmaWkxMDAyOAlhZmlpMTAwMjkJYWZpaTEwMDMwCWFmaWkxM
DAzMQlhZmlpMTAwMzIJYWZpaTEwMDMzCWFmaWkxMDAzNAlhZmlpMTAwMzUJYWZpaTEwMDM2CWFmaWkx
MDAzNwlhZmlpMTAwMzgJYWZpaTEwMDM5CWFmaWkxMDA0MAlhZmlpMTAwNDEJYWZpaTEwMDQyCWFmaWk
xMDA0MwlhZmlpMTAwNDQJYWZpaTEwMDQ1CWFmaWkxMDA0NglhZmlpMTAwNDcJYWZpaTEwMDQ4CWFmaW
kxMDA0OQlhZmlpMTAwNjUJYWZpaTEwMDY2CWFmaWkxMDA2NwlhZmlpMTAwNjgJYWZpaTEwMDY5CWFma
WkxMDA3MAlhZmlpMTAwNzIJYWZpaTEwMDczCWFmaWkxMDA3NAlhZmlpMTAwNzUJYWZpaTEwMDc2CWFm
aWkxMDA3NwlhZmlpMTAwNzgJYWZpaTEwMDc5CWFmaWkxMDA4MAlhZmlpMTAwODEJYWZpaTEwMDgyCWF
maWkxMDA4MwlhZmlpMTAwODQJYWZpaTEwMDg1CWFmaWkxMDA4NglhZmlpMTAwODcJYWZpaTEwMDg4CW
FmaWkxMDA4OQlhZmlpMTAwOTAJYWZpaTEwMDkxCWFmaWkxMDA5MglhZmlpMTAwOTMJYWZpaTEwMDk0C
WFmaWkxMDA5NQlhZmlpMTAwOTYJYWZpaTEwMDk3CWFmaWkxMDA3MQlhZmlpMTAwOTkJYWZpaTEwMTAw
CWFmaWkxMDEwMQlhZmlpMTAxMDIJYWZpaTEwMTAzCWFmaWkxMDEwNAlhZmlpMTAxMDUJYWZpaTEwMTA
2CWFmaWkxMDEwNwlhZmlpMTAxMDgJYWZpaTEwMTA5CWFmaWkxMDExMAlhZmlpMTAxOTMJYWZpaTEwMD
UwCWFmaWkxMDA5OAZXZ3JhdmUGd2dyYXZlBldhY3V0ZQZ3YWN1dGUJV2RpZXJlc2lzCXdkaWVyZXNpc
wZZZ3JhdmUGeWdyYXZlCWFmaWkwMDIwOA11bmRlcnNjb3JlZGJsDXF1b3RlcmV2ZXJzZWQGbWludXRl
BnNlY29uZAlleGNsYW1kYmwHdW5pMjAzRQd1bmkyMDdGBGxpcmEGcGVzZXRhCWFmaWk2MTI0OAlhZml
pNjEyODkJYWZpaTYxMzUyCWVzdGltYXRlZAlvbmVlaWdodGgMdGhyZWVlaWdodGhzC2ZpdmVlaWdodG
hzDHNldmVuZWlnaHRocwlhcnJvd2xlZnQHYXJyb3d1cAphcnJvd3JpZ2h0CWFycm93ZG93bglhcnJvd
2JvdGgJYXJyb3d1cGRuDGFycm93dXBkbmJzZQpvcnRob2dvbmFsDGludGVyc2VjdGlvbgtlcXVpdmFs
ZW5jZQVob3VzZQ1yZXZsb2dpY2Fsbm90CmludGVncmFsdHAKaW50ZWdyYWxidAhTRjEwMDAwMAhTRjE
xMDAwMAhTRjAxMDAwMAhTRjAzMDAwMAhTRjAyMDAwMAhTRjA0MDAwMAhTRjA4MDAwMAhTRjA5MDAwMA
hTRjA2MDAwMAhTRjA3MDAwMAhTRjA1MDAwMAhTRjQzMDAwMAhTRjI0MDAwMAhTRjUxMDAwMAhTRjUyM
DAwMAhTRjM5MDAwMAhTRjIyMDAwMAhTRjIxMDAwMAhTRjI1MDAwMAhTRjUwMDAwMAhTRjQ5MDAwMAhT
RjM4MDAwMAhTRjI4MDAwMAhTRjI3MDAwMAhTRjI2MDAwMAhTRjM2MDAwMAhTRjM3MDAwMAhTRjQyMDA
wMAhTRjE5MDAwMAhTRjIwMDAwMAhTRjIzMDAwMAhTRjQ3MDAwMAhTRjQ4MDAwMAhTRjQxMDAwMAhTRj
Q1MDAwMAhTRjQ2MDAwMAhTRjQwMDAwMAhTRjU0MDAwMAhTRjUzMDAwMAhTRjQ0MDAwMAd1cGJsb2NrB
2RuYmxvY2sFYmxvY2sHbGZibG9jawdydGJsb2NrB2x0c2hhZGUFc2hhZGUHZGtzaGFkZQlmaWxsZWRi
b3gGSDIyMDczBkgxODU0MwZIMTg1NTEKZmlsbGVkcmVjdAd0cmlhZ3VwB3RyaWFncnQHdHJpYWdkbgd
0cmlhZ2xmBmNpcmNsZQZIMTg1MzMJaW52YnVsbGV0CWludmNpcmNsZQpvcGVuYnVsbGV0CXNtaWxlZm
FjZQxpbnZzbWlsZWZhY2UDc3VuBmZlbWFsZQRtYWxlBXNwYWRlBGNsdWIFaGVhcnQHZGlhbW9uZAttd
XNpY2Fsbm90ZQ5tdXNpY2Fsbm90ZWRibAd1bmlGMDA0B3VuaUYwMDUAAAAB//8AAg=="""
  f = base64.decodestring(font)
  tmp = tempfile.NamedTemporaryFile()
  tmp.write(f)
  filename = tmp.name
  from reportlab.pdfbase import pdfmetrics
  from reportlab.pdfbase.ttfonts import TTFont
  pdfmetrics.registerFont(TTFont('invisible', filename))
  tmp.close()

if __name__ == "__main__":
  if len(sys.argv) == 1:
    print("Usage: %s <imgdir>\n" % os.path.basename(sys.argv[0]))
  else:
    main(sys.argv[1])

