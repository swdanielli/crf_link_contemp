#!/usr/bin/env python

"""
A feature extractor for chunking.
Copyright 2010,2011 Naoaki Okazaki.
"""

# Separator of field values.
separator = ' '

# Field names of the input data.
'''
fields = 'f1 f2 y'
'''
fields = ''

# Attribute templates.
'''
templates_w_freq = (
    (('f1', -1), ),
    (('f1',  0), ),
    (('f1',  1), ),
    (('f1', -1), ('f1',  0)),
    (('f1',  0), ('f1',  1)),
    (('f2', -1), ),
    (('f2',  0), ),
    (('f2',  1), ),
    (('f2', -1), ('f2',  0)),
    (('f2', 0), ('f2',  1)),
    )
'''
templates_w_freq = ()

templates = ()
fea_prefix = 'f'

config_key_prefix = {
  'max_ntrans_wins': 'p',
  'max_ntargets': 'tp',
  'others': 'o'
}

import crfutils
import sys

def gen_fields(vocab_size, window_size, configuration=None):
  # declare global only when we have to modify it
  global fields
  # vocab_size*2 => trans + slides
  if 'vocab_duplicate' in configuration:
    vocab_duplicate = configuration['vocab_duplicate']
  else:
    vocab_duplicate = 2

  fields_arr = [fea_prefix + str(idx) for idx in range(vocab_size*vocab_duplicate)]
  if configuration:
    for key, prefix in config_key_prefix.iteritems():
      if key in configuration:
        fields_arr += [prefix + str(idx) for idx in range(configuration[key])]

  fields_arr.append('y')
  fields = separator.join(fields_arr)

def gen_templates(vocab_size, window_size, configuration=None):
  # declare global only when we have to modify it
  global templates_w_freq
  if 'shift' in configuration:
    shift = configuration['shift']
  else:
    shift = 1
  if 'vocab_duplicate' in configuration:
    for f_idx in range(vocab_size*configuration['vocab_duplicate']):
      for window_idx in range(-1*window_size*shift, window_size*shift+1, shift):
        templates_w_freq += (((fea_prefix + str(f_idx), window_idx), ), )
  else:
    f_type = ''
    window = {'trans': window_size, 'slides': 0}
    for f_idx in range(vocab_size*2):
      if f_idx < vocab_size:
        f_type = 'trans'
      else:
        f_type = 'slides'
      for window_idx in range(-1*window[f_type]*shift, window[f_type]*shift+1, shift):
        templates_w_freq += (((fea_prefix + str(f_idx), window_idx), ), )

  if configuration:
    for key, prefix in config_key_prefix.iteritems():
      if key in configuration:
        for idx in range(configuration[key]):
          templates_w_freq += (((prefix + str(idx), 0), ), )

def feature_extractor(X):
  # Apply attribute templates to obtain features (in fact, attributes)
  crfutils.apply_templates(X, templates)
  crfutils.apply_templates_w_freq(X, templates_w_freq)
  #if X:
    # Append BOS and EOS features manually
    #X[0]['F'].append('__BOS__')     # BOS feature
    #X[-1]['F'].append('__EOS__')    # EOS feature

if __name__ == '__main__':
  f_i = open(sys.argv[1], 'r')
  configuration = {}
  if len(sys.argv) > 4:
    if sys.argv[4] == 'use_pos_use_tpos':
      configuration['max_ntrans_wins'] = int(sys.argv[5])
      configuration['max_ntargets'] = int(sys.argv[6])
    elif sys.argv[4] == 'use_pos_use_mul':
      configuration['max_ntrans_wins'] = int(sys.argv[5])
      configuration['vocab_duplicate'] = int(sys.argv[6])
    elif sys.argv[4] in ['useWord2vec_useOOVonehot_specifyMaxSlides_useVis', 'useWord2vec_specifyMaxSlides_useVis', 'useCosSim_useDoc2vec_specifyMaxSlides_useVis', 'useCosSim_v2', 'useCosSim_specifyMaxSlides_useVis', 'useCosSim_specifyMaxSlides_keyword', 'useCosSim_specifyMaxSlides', 'usePos_useMul_specifyMaxSlides', 'usePos_useCosSim_specifyMaxSlides', 'usePos_useCosSim_useSmoothing_specifyMaxSlides', 'usePos_useCosSim_useSmoothing_specifyMaxSlides_keyword', 'useCosSim_useWord2vec_specifyMaxSlides_useVis']:
      configuration['max_ntrans_wins'] = int(sys.argv[5])
      configuration['vocab_duplicate'] = 1
      configuration['others'] = int(sys.argv[6])
      configuration['shift'] = int(sys.argv[7])
    elif sys.argv[4] in ['useCosSim_tx']:
      configuration['vocab_duplicate'] = 1
      configuration['others'] = int(sys.argv[5])

  gen_fields(int(sys.argv[2]), int(sys.argv[3]), configuration)
  gen_templates(int(sys.argv[2]), int(sys.argv[3]), configuration)

#    f_o = open(sys.argv[2], 'a')
  crfutils.main(feature_extractor, fields=fields, sep=separator, fi=f_i)
