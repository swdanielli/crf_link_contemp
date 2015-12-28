#! /usr/bin/env python

import re
import struct
import subprocess
import sys

'''
  vis_fea(pos and 0) 
  <some room>
  lexical_fea(10*(2*win+1))
  is_first(1)
  is_last(8)
  <some room>
  vis_fea(neg)
  <some room>
'''

def parse_tags(tags):
  items = tags.split(' ')
  return (items[1], items[3])

def save_vis_attr(buf_name, buf_weight, is_transition, weight_sum, weight_count, f_o):
  weight_sum /= weight_count
  for idx in range(len(buf_weight)):
    if is_transition[idx]:
      buf_weight[idx] = weight_sum

  for idx in range(len(buf_weight)):
    f_o.write(buf_name[idx])
    f_o.write(struct.pack('d', buf_weight[idx]))

  return ([], [], [], 0.0, 0)

model_name = sys.argv[1]
model_txt_name = sys.argv[2]
'''
crf_exe = '/usr/users/swli/scratch_bak/stat2.1x/nlp/crf/script/crfsuite-0.12/bin/crfsuite'

subprocess.Popen(
  '%s dump %s > %s' % (crf_exe, model_name, model_txt_name),
  shell=True
)
'''

model = {
  'LABELS': [],
  'ATTRIBUTES': [],
  'TRANSITIONS': [],
  'STATE_FEATURES': []
}
keys = ''
for line in open(model_txt_name):
  line = line.strip()

  matches = re.match('(.+) = {$', line)
  if matches:
    keys = matches.group(1)
    continue

  matches = re.match('(.+): (.+)$', line)
  if matches and keys in model:
    model[keys].append({matches.group(1): matches.group(2)})

f_o = open(sys.argv[3], 'wb')

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

  for tag_dict in model['STATE_FEATURES']:
    (attr_idx, label_idx) = parse_tags(tag_dict.keys()[0])

    f_o.write(f.read(12))
    value = struct.unpack('d', f.read(8))[0]
    matches = re.match('o(\d+)\[0\]', attr_idx)
    if matches:
      # should start from the fisrt state
      if matches.group(1) == '0' and label_idx == '1':
        value = FLOAT_MAX
      # should end at the last page
      elif matches.group(1) == label_idx:
        value = FLOAT_MAX

    f_o.write(struct.pack('d', value))

  for tag_dict in model['TRANSITIONS']:
    (from_label_idx, to_label_idx) = parse_tags(tag_dict.keys()[0])
    f_o.write(f.read(12))

    value = struct.unpack('d', f.read(8))[0]
    from_label_idx = int(from_label_idx)
    to_label_idx = int(to_label_idx)

    if to_label_idx != from_label_idx and to_label_idx != from_label_idx + 1:
      value = FLOAT_MIN

    f_o.write(struct.pack('d', value))

  byte = f.read(1)
  while byte != '':
    # Write the rest of the model to model.mod
    f_o.write(byte)
    byte = f.read(1)

#../script/modify_model.py model.less
#../script/crfsuite-0.12/bin/crfsuite dump model.less.mod > model.less.mod.txt
