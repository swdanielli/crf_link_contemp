#! /usr/bin/env python

import os
import re
import sys

def _main( ):
  root_dir = sys.argv[1]
  if len(sys.argv) > 2:
    fea_type = sys.argv[2]
  else:
    fea_type = ''
  '''
  for root, _, files in os.walk(root_dir):
    for filename in files:
      with open(root + '/' + filename) as f:
        for line in f:
          matches = re.match('Item accuracy: \d+ / \d+ \((\d+\.\d+)\)', line)
          if matches:
            print root + '/' + filename + ': ' + str(matches.group(1))
            break
  '''
  if fea_type == 'usePosMask_useCosSim_v2':
    params1 = [0.001, 0.004, 0.007, 0.01, 0.04, 0.07, 0.1, 0.4, 0.7, 1, 4, 7, 10]
    params2 = [1, 2, 3, 4, 5, 7, 9, 11, 13, 15, 20, 25]
    params3 = [1, 2, 3, 4, 5, 7, 9, 11, 13, 15, 20, 25]
  else:
    params1 = [0.001, 0.004, 0.007, 0.01, 0.04, 0.07, 0.1, 0.4, 0.7, 1, 4, 7, 10]
    params2 = [1, 2, 3, 4, 5, 7, 9]
    params3 = [1, 2, 3, 5, 7, 9, 11, 13]

  algorithms = ['lbfgs', 'ap', 'pa', 'arow', 'l2sgd']
  for param1 in params1:
    for param2 in params2:
      for param3 in params3:
        for algorithm in algorithms:
          filename = root_dir + '/' + str(param1) + '_' + str(param2) + '_' + str(param3) + '/log.crfsuite_' + algorithm
          if os.path.exists(filename):
            with open(filename) as f:
              for line in f:
                if fea_type == 'usePosMask_useCosSim_v2':
                  matches = re.match('.*y: \(\d+, \d+, \d+\)\ (\(.*\))', line)
                else:
                  matches = re.match('Item accuracy: \d+ / \d+ \((\d+\.\d+)\)', line)
                if matches:
                  print filename + ': ' + str(matches.group(1))
                  break

if __name__ == '__main__':
  _main( )
