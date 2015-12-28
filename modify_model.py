#! /usr/bin/env python

import struct
import sys

n_labels = 10

n_transition = n_labels*n_labels
#n_transition = 19

byte_per_value = 8
byte_per_entry = 20

#model_name = 'model.less'
model_name = sys.argv[1]
f_o = open(model_name + '.mod', 'wb')

FLOAT_MIN = -1.0e+100
with open(model_name, 'rb') as f:
  # Header
  f_o.write(f.read(32))
  # off_labels
  off_labels = struct.unpack('i', f.read(4))[0]
  f_o.write(struct.pack('i', off_labels))
  print off_labels
  already_read = 36

  # Some other header and state_features
  f_o.write(f.read(off_labels - byte_per_value - (n_transition-1)*20 - already_read))

#  for transition in range(n_transition):
  for from_label in range(n_labels):
    for to_label in range(n_labels):
      value = struct.unpack('d', f.read(8))[0]
      if from_label != to_label and from_label != to_label-1:
        value = FLOAT_MIN

      f_o.write(struct.pack('d', value))
      # Some unknown value for each entry, perhaps the name of the feature function
      f_o.write(f.read(byte_per_entry - byte_per_value))

  byte = f.read(1)
  while byte != '':
    # Write the rest of the model to model.mod
    f_o.write(byte)
    byte = f.read(1)

#../script/modify_model.py model.less
#../script/crfsuite-0.12/bin/crfsuite dump model.less.mod > model.less.mod.txt
