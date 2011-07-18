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
# Monitor most recent image page

import sys
import Tkinter
from PIL import Image, ImageTk
import os
import glob
import operator
import time

def latest(dir):
    """Return most recently modified file """
    flist = glob.glob(dir)
    if len(flist) == 0:
        return None
    for i in range(len(flist)):
	statinfo = os.stat(flist[i])
	flist[i] = flist[i],statinfo.st_ctime
    flist.sort(key=operator.itemgetter(1))
    return flist[-1]

def process():
  kDir = "/tmp/playground/*.ppm"
  w = 500
  h = 700
  ctime = 0
  im = Image.new("RGB", (w, h))
  root = Tkinter.Tk()
  root.geometry("%dx%d" % (w, h))
  root.title('Most Recent Page')
  tkpi = ImageTk.PhotoImage(im)
  label_image = Tkinter.Label(root, image=tkpi, width=w, height=h)
  label_image.place(x=0, y=0, width=w, height=h)
  root.after(10, root.quit)
  root.mainloop(0)
  while True:
    time.sleep(1.0)
    latest_file = latest(kDir)
    if latest_file and ctime != latest_file[1]:
      try:
        im = Image.open(latest_file[0])
        im.thumbnail((w, h))
        tkpi = ImageTk.PhotoImage(im)
        label_image.configure(image=tkpi)
        root.title('Most Recent Page - %s' % latest_file[0])
        ctime = latest_file[1]
      except:
        pass
    root.after(10, root.quit)
    root.mainloop(0)

if __name__ == "__main__":
  process()
