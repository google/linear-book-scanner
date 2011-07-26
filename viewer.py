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

import sys
import Tkinter
from PIL import Image, ImageTk, ImageDraw
from pnm import pnm_header
from split import detect_pagefeed

def walk_through_lines(linesize, ratio):
  """Throw out several scan lines for each one that we keep."""
  for unused in range(ratio):
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      return None
    sys.stdout.write(scanline)
    sys.stdout.flush()
    if detect_pagefeed(scanline):
      return "Pagefeed"
  return scanline

def process(ratio):
  """View an image as it passes from stdin to stdout. Downsize by ratio
  so that it can fit on a computer screen."""
  n = 0
  y = 0
  h = 800
  linewidth, linecount, channels = pnm_header()
  linesize = linewidth * channels
  w = linewidth // ratio
  if channels == 1:
    image_type = "L"
  elif channels == 3:
    image_type = "RGB"
  im = Image.new(image_type, (w, h))
  draw = ImageDraw.Draw(im)
  root = Tkinter.Tk()
  root.geometry("%dx%d" % (w, h))
  root.title('Pass Through Viewer')
  tkpi = ImageTk.PhotoImage(im)
  label_image = Tkinter.Label(root, image=tkpi, width=w, height=h)
  label_image.place(x=0, y=0, width=w, height=h)
  while True:
    scanline = walk_through_lines(linesize, ratio)
    n += ratio
    if scanline == None:
      break
    if y % h == 0:
      root.title('Pass Through Viewer - %d' % n)
    if scanline == "Pagefeed":
      y = 0
    else:
      image_line = Image.fromstring(image_type, (linewidth, 1), scanline)
      im.paste(image_line.resize((w, 1)), (0, y % h))
    y += 1
    if y % 40 == 0 or scanline == "Pagefeed":
      draw.line((0, y % h, w, y % h), fill="green")
      tkpi = ImageTk.PhotoImage(im)
      label_image.configure(image=tkpi)
      root.after(1, root.quit)
      root.mainloop(0)

if __name__ == "__main__":
  ratio = 5
  if len(sys.argv) == 2:
    ratio = int(sys.argv[1])
  process(ratio)
