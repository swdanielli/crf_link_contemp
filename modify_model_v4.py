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

# Lexical attributes
shared_attr_from = int(sys.argv[4])
shared_attr_to = int(sys.argv[5])
# Visual attributes
vis_attr_dim = int(sys.argv[6])
vis_attr_context = int(sys.argv[7])
neg_context_offset = int(sys.argv[8])

shared_attrs = []
vis_attrs = []
attr_is_first = ''
attr_is_last = {}
for attr_dict in model['ATTRIBUTES']:
  key = int(attr_dict.keys()[0])
  if key >= shared_attr_from and key <= shared_attr_to:
    shared_attrs.append(attr_dict.values()[0])
  # vis attr and positive context
  if key < vis_attr_dim*(vis_attr_context+1):
    vis_attrs.append(attr_dict.values()[0])
  # negative vis context
  if key >= neg_context_offset and key < neg_context_offset+vis_attr_dim*vis_attr_context:
    vis_attrs.append(attr_dict.values()[0])
  # attr is_first
  if key == shared_attr_to + 1:
    attr_is_first = attr_dict.values()[0]
  # attr is_last
  for shift in range(2, 10):
    if key == shared_attr_to + shift:
      if shift == 9:
        attr_is_last[attr_dict.values()[0]] = str(1+shift)
      else:
        attr_is_last[attr_dict.values()[0]] = str(shift)

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

  prev_value = 0
  prev_attr_idx = ''
  prev_label_idx = ''
  buf_name = []
  buf_weight = []
  is_transition = []
  weight_sum = 0.0
  weight_count = 0
  for tag_dict in model['STATE_FEATURES']:
    (attr_idx, label_idx) = parse_tags(tag_dict.keys()[0])
    if prev_attr_idx != attr_idx and len(buf_name) > 0:
      (buf_name, buf_weight, is_transition, weight_sum, weight_count) = save_vis_attr(buf_name, buf_weight, is_transition, weight_sum, weight_count, f_o)

    # shared vis weight among transition states
    if attr_idx in vis_attrs:
      buf_name.append(f.read(12))
      buf_weight.append(struct.unpack('d', f.read(8))[0])
      if re.match('\d+_t', label_idx):
        is_transition.append(True)
        weight_sum += buf_weight[-1]
        weight_count += 1
      else:
        is_transition.append(False)
    else:
      f_o.write(f.read(12))
      value = struct.unpack('d', f.read(8))[0]

      # shared lex weight between state i and i_t, i = 1 to 10
      if attr_idx in shared_attrs and label_idx == prev_label_idx + '_t':
        value = prev_value
      # should start from the fisrt state
      elif attr_idx == attr_is_first and label_idx == '1':
        value = FLOAT_MAX
      # should end at the last page
      elif attr_idx in attr_is_last and label_idx == attr_is_last[attr_idx]:
        value = FLOAT_MAX

      f_o.write(struct.pack('d', value))
      prev_value = value
    prev_attr_idx = attr_idx
    prev_label_idx = label_idx

  if len(buf_name) > 0:
    (buf_name, buf_weight, is_transition, weight_sum, weight_count) = save_vis_attr(buf_name, buf_weight, is_transition, weight_sum, weight_count, f_o)

  for tag_dict in model['TRANSITIONS']:
    (from_label_idx, to_label_idx) = parse_tags(tag_dict.keys()[0])
    f_o.write(f.read(12))

    value = struct.unpack('d', f.read(8))[0]
    matches = re.match('(\d+)_t', from_label_idx)
    if matches:
      if str(int(matches.group(1)) + 1) != to_label_idx:
        value = FLOAT_MIN
    else:
      if to_label_idx != from_label_idx and to_label_idx != from_label_idx + '_t':
        value = FLOAT_MIN

    f_o.write(struct.pack('d', value))

  byte = f.read(1)
  while byte != '':
    # Write the rest of the model to model.mod
    f_o.write(byte)
    byte = f.read(1)

#../script/modify_model.py model.less
#../script/crfsuite-0.12/bin/crfsuite dump model.less.mod > model.less.mod.txt
