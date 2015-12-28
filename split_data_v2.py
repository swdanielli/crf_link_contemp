#! /usr/bin/env python

import copy
import my_util
import re
import sys

def _main( ):
  '''
  filename = sys.argv[1]
  f_o = open(sys.argv[4], 'w')
  fea_type = ''

  if len(sys.argv) > 6:
    fea_type = sys.argv[6]
    max_targets = int(sys.argv[7])
    window_size = int(sys.argv[8])
  '''
  n_folds = int(sys.argv[3])
  with open(sys.argv[4]) as f:
    n_sent_list = [int(x.strip()) for x in f.readlines()]

  for fold_idx in range(n_folds):
    f_o_train = open(sys.argv[2] + '/fea_cv.' + str(fold_idx) + '.train.raw', 'w')
    f_o_test = open(sys.argv[2] + '/fea_cv.' + str(fold_idx) + '.test.raw', 'w')

    lec_count = 0
    sent_count = 0
    with open(sys.argv[1]) as f:
      for line in f:
        if lec_count % n_folds == fold_idx:
          f_o_test.write(line)
        else:
          f_o_train.write(line)

        if not line.strip():
          sent_count += 1
          if sent_count == n_sent_list[lec_count]:
            lec_count += 1
            sent_count = 0

if __name__ == '__main__':
  _main( )
