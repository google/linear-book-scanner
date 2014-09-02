#!/usr/bin/python
#
# Pass through 2-up viewer for SANE (requires the SANE
# source code to be newer than July 15, 2014)
#
# scanimage --swcrop --mode=Color --resolution=300 \
#   -b --batch-print | ./vsane.py

import pygame
import sys
import mmap

def read_ppm_header(fp, filename):
  magic_number = fp.readline()
  comment = fp.readline()
  dimensions = fp.readline()
  maxval = fp.readline()
  headersize = len(magic_number) + len(comment) + len(dimensions) + len(maxval)
  w, h = int(dimensions.split(" ")[0]), int(dimensions.split(" ")[1])
  return (w, h), headersize

def process_image(h, filename):
  f = open(filename, "r+b")
  dimensions, headersize = read_ppm_header(f, filename)
  map = mmap.mmap(f.fileno(), 0)
  image = pygame.image.frombuffer(buffer(map, headersize), dimensions, 'RGB')
  w = h * image.get_width() // image.get_height()
  return pygame.transform.smoothscale(image, (w, h))

def main(argv):
  pygame.init()
  h = pygame.display.Info().current_h * 4 // 5
  pygame.display.set_mode((h * 16 // 9, h))
  pygame.display.set_caption("Waiting for data...")
  while True:
    a, b = sys.stdin.readline(), sys.stdin.readline()
    if not a or not b:
      break
    screen = pygame.display.get_surface()
    screen.fill((70, 120, 173))
    sys.stdout.write(a + b)
    sys.stdout.flush()
    img_a, img_b = process_image(h, a.strip()), process_image(h, b.strip())
    w2 = screen.get_width() // 2
    epsilon = screen.get_width() // 200
    screen.blit(img_a, (w2 - img_a.get_width() - epsilon, 0))
    screen.blit(img_b, (w2 + epsilon, 0))
    pygame.display.set_caption("%s | %s" % (a.strip(), b.strip()))
    pygame.display.update()

if __name__ == "__main__":
  main(sys.argv)
