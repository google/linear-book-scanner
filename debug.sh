#!/bin/bash
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
# Process pre-recorded data for debugging purposes.

SRC=/var/tmp
PATH=$PATH:.

cat /tmp/debug.ppm | pnmcut -bottom 4625 |\
  tee /tmp/before |\
  wobble.py | viewer.py > /tmp/after

exit 

convert -density 300 testdata/stripes.png ppm:- |\
  pnmdepth 255 | tee /tmp/before | viewer.py |\
  wobble.py | viewer.py > /tmp/after




#convert -density 300 testdata/stripes.png ppm:- |\
#  pnmdepth 255 | wobble.py | viewer.py > /tmp/f

#convert -density 300 testdata/stripes.svg ppm:- |\
#  pnmdepth 255 | viewer.py | phase.py > /dev/null


