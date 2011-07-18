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
#
# Jeff Breidenbach
# View an image as it passes from stdin to stdout

import sys
import Tkinter
from PIL import Image, ImageTk, ImageDraw
from ppm_header import ppm_header
from split import detect_pagefeed

def walk_through_lines(linesize, ratio):
  for unused in range(ratio):
    scanline = sys.stdin.read(linesize)
    if len(scanline) != linesize:
      return None
    sys.stdout.write(scanline)
    if detect_pagefeed(scanline):
      return "Pagefeed"
  return scanline

def process(ratio):
  n = 0
  y = 0
  h = 800
  linesize, linecount = ppm_header()
  linewidth = linesize / 3
  w = linewidth // ratio
  im = Image.new("RGB", (w, h))
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
    if scanline == "Pagefeed":
      y = 0
      continue
    image_line = Image.fromstring("RGB", (linewidth, 1), scanline)
    im.paste(image_line.resize((w, 1)), (0, y % h))
    if y % h == 0:
      root.title('Pass Through Viewer - %d' % n)
    y += 1
    if y % 40 == 0:
      draw.line((0, y % h, w, y % h), fill="green")
      tkpi = ImageTk.PhotoImage(im)
      label_image.configure(image=tkpi)
      root.after(1, root.quit)
      root.mainloop(0)

if __name__ == "__main__":
  ratio = 4
  if len(sys.argv) == 2:
    ratio = int(sys.argv[1])
  process(ratio)
