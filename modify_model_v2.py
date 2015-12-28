#! /usr/bin/env python

import struct
import sys

#n_labels = 19

#n_transition = n_labels*n_labels
#n_transition = 19

model_name = sys.argv[1]
shared_attr_from = int(sys.argv[2])
shared_attr_to = int(sys.argv[3])
shared_attrs = range(shared_attr_from, shared_attr_to + 1)

attr_is_first = shared_attr_to + 1
attr_is_last = {
  shared_attr_to + 2: 2*2-2,
  shared_attr_to + 3: 3*2-2,
  shared_attr_to + 4: 4*2-2,
  shared_attr_to + 5: 5*2-2,
  shared_attr_to + 6: 6*2-2,
  shared_attr_to + 7: 7*2-2,
  shared_attr_to + 8: 8*2-2,
  shared_attr_to + 9: 10*2-2
}

f_o = open(model_name + '.mod', 'wb')
#f_o = open(model_name + '.test', 'w')

FLOAT_MIN = -100000
FLOAT_MAX = 100000000
with open(model_name, 'rb') as f:
  f_o.write(f.read(4)) # magic
  f_o.write(f.read(4)) # size
  f_o.write(f.read(4)) # type
  f_o.write(f.read(4)) # version
  f_o.write(f.read(4)) # num_features
  byte = f.read(4)
  num_labels = struct.unpack('i', byte)[0]
  n_transition = num_labels * num_labels
  f_o.write(byte) # num_labels

  byte = f.read(4)
  num_attrs = struct.unpack('i', byte)[0]
  f_o.write(byte) # num_attrs
  f_o.write(f.read(4)) # off_features
  f_o.write(f.read(4)) # off_labels
  f_o.write(f.read(4)) # off_attrs
  f_o.write(f.read(4)) # off_labelrefs
  f_o.write(f.read(4)) # off_attrrefs

  f_o.write(f.read(12))
  value_before = 0
  for attr_idx in range(num_attrs):
    # fea = []
    for label_idx in range(num_labels):
      f_o.write(f.read(12))

      value = struct.unpack('d', f.read(8))[0]
      if attr_idx in shared_attrs and label_idx % 2 == 1:
        value = value_before
      elif attr_idx == attr_is_first and label_idx == 0:
        value = FLOAT_MAX
      elif attr_idx in attr_is_last and label_idx == attr_is_last[attr_idx]:
        value = FLOAT_MAX
      f_o.write(struct.pack('d', value))
      # fea.append(str(value))
      value_before = value
    # f_o.write(' '.join(fea) + '\n')

  for from_label in range(num_labels):
    for to_label in range(num_labels):
      f_o.write(f.read(12))

      value = struct.unpack('d', f.read(8))[0]
      if from_label % 2 == 0:
        if from_label != to_label and from_label != to_label-1:
          value = FLOAT_MIN
      else:
        if from_label != to_label-1:
          value = FLOAT_MIN
      f_o.write(struct.pack('d', value))
      # f_o.write(str(value) + '\n')

  byte = f.read(1)
  while byte != '':
    # Write the rest of the model to model.mod
    f_o.write(byte)
    byte = f.read(1)

#../script/modify_model.py model.less
#../script/crfsuite-0.12/bin/crfsuite dump model.less.mod > model.less.mod.txt
