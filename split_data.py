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
  for fold_idx in range(n_folds):
    f_o_train = open(sys.argv[2] + '/fea_cv.' + str(fold_idx) + '.train.raw', 'w')
    f_o_test = open(sys.argv[2] + '/fea_cv.' + str(fold_idx) + '.test.raw', 'w')

    instance_count = 0
    sent_count = 0
    with open(sys.argv[1]) as f:
      for line in f:
        if instance_count == 30:
          if sent_count % n_folds == fold_idx:
            f_o_test.write(line)
          else:
            f_o_train.write(line)
          sent_count += 1
        else:
          if instance_count % n_folds == fold_idx:
            f_o_test.write(line)
          else:
            f_o_train.write(line)

        if not line.strip():
          instance_count += 1
    f_o_test.write('\n')
    f_o_train.write('\n')

if __name__ == '__main__':
  _main( )
