#! /usr/bin/env python

import copy
import my_util
import re
import sys

def load_trans(filename):
  with open(filename) as f:
    for line in f:
      if "++++++++++" in line or "==========" in line:
        continue
      items = line.strip().split('\t')
      yield (my_util.str_to_sparse(items[0]), int(items[1]))

def get_n_sent(l_id, raw_trans_dir):
  n_sent = 0
  for _ in load_trans(raw_trans_dir + '/' + l_id):
    n_sent += 1
  return n_sent

def _main( ):
  filename = sys.argv[1]

  f_o = open(sys.argv[3] + '/sent_list', 'w')
  n_sent_list = []
  with open(filename) as f:
    for line in f:
      n_sent = get_n_sent(line.strip(), sys.argv[4])
      n_sent_list.append(n_sent)
      f_o.write(str(n_sent) + '\n')

  n_folds = int(sys.argv[2])
  for fold_idx in range(n_folds):
    f_o_train = open(sys.argv[3] + '/sent_list.' + str(fold_idx) + '.train', 'w')
    f_o_test = open(sys.argv[3] + '/sent_list.' + str(fold_idx) + '.test', 'w')

    lec_count = 0
    for n_sent in n_sent_list:
      if lec_count % n_folds == fold_idx:
        f_o_test.write(str(n_sent) + '\n')
      else:
        f_o_train.write(str(n_sent) + '\n')
      lec_count += 1

if __name__ == '__main__':
  _main( )
