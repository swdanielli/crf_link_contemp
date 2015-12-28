#! /usr/bin/env python

import copy
import my_util
import re
import sys

smoothing = 0.01

FLOAT_MIN = -1
FLOAT_MAX = 1
def load_trans(filename):
  with open(filename) as f:
    for line in f:
      if "++++++++++" in line or "==========" in line:
        continue
      items = line.strip().split('\t')
      yield (my_util.str_to_sparse(items[0]), int(items[1]))

def load_slides(filename):
  with open(filename) as f:
    for line in f:
      items = line.strip().split('_')
      yield my_util.str_to_sparse(items[1])

def load_external_fea(fea_dir, l_id, fea_weight=10):
  fea = []
  with open(fea_dir + '/' + l_id) as f:
    for line in f:
      fea.append(map(lambda x: fea_weight*float(x), re.sub('nan', '0', line.strip()).split('\t')))
  return fea

def gen_raw_fea(l_id, raw_slides_dir, raw_trans_dir, f_o, dimension, pos_vec_size, context_size, max_ntargets, window_size, multiplier, use_smoothing=False, keyword_param=None, use_pos=True, vis_fea=None, use_transition_state=False, external_lex_fea=None):
  f_vec = [0 for _ in xrange(dimension)]
  f_vec_smoothing = [smoothing*smoothing for _ in xrange(dimension)]
  f_slides = [0 for _ in xrange(max_ntargets)]
  f_slides_mask = [FLOAT_MIN for _ in xrange(max_ntargets)]
  f_pos = [0 for _ in xrange(max_ntargets*30)]
  f_cos = [0 for _ in xrange(max_ntargets*(context_size*2+1))]

  labels = []
  trans_sparses = []
  trans_sparses_temp = []
  for trans_sparse, label in load_trans(raw_trans_dir + '/' + l_id):
    labels.append(label)
    trans_sparses_temp.append(copy.deepcopy(trans_sparse))
  for trans_idx in range(len(trans_sparses_temp)):
    trans_sparse = {}
    for idx in range(-1*window_size+trans_idx, window_size+trans_idx+1):
      if idx < 0 or idx >= len(trans_sparses_temp):
        continue
      trans_sparse = my_util.sparse_add(trans_sparse, trans_sparses_temp[idx])

    if keyword_param:
      trans_sparse = my_util.modify_sparse(trans_sparse, keyword_param['w_dimension'], keyword_param['start_keyw_idx']-1, keyword_param['start_keyw_idx'], keyword_param['end_keyw_idx'], keyword_param['keyword_weight'])
    else:
      trans_sparse = my_util.modify_sparse(trans_sparse, dimension-1, dimension-1)

    trans_sparses.append(trans_sparse)

  for trans_idx in range(len(trans_sparses)):
    cos_sims = f_cos[:]
    if external_lex_fea:
      external_lex_fea_matrix = []
      for _ in range(len(external_lex_fea)):
        external_lex_fea_matrix.append(f_cos[:])
    positions = f_pos[:]
    is_first = 0
    is_last = f_slides[:]

    slides_page = 0
    for slides_sparse in load_slides(raw_slides_dir + '/' + l_id):
      if keyword_param:
        slides_sparse = my_util.modify_sparse(slides_sparse, keyword_param['w_dimension'], keyword_param['start_keyw_idx']-1, keyword_param['start_keyw_idx'], keyword_param['end_keyw_idx'], keyword_param['keyword_weight'])
      else:
        slides_sparse = my_util.modify_sparse(slides_sparse, dimension-1, dimension-1)

      for idx in range(-1*context_size+trans_idx, context_size+trans_idx+1):
        if idx < 0 or idx >= len(trans_sparses):
          continue
        if use_smoothing:
          pass
        else:
          if trans_sparses[idx] and slides_sparse and multiplier != 0:
            cos_sims[slides_page+(idx+context_size-trans_idx)*max_ntargets] = my_util.cos_sim(trans_sparses[idx], slides_sparse, f_vec[:]) * multiplier
          if external_lex_fea:
            for external_lex_fea_idx in range(len(external_lex_fea)):
              external_lex_fea_matrix[external_lex_fea_idx][slides_page+(idx+context_size-trans_idx)*max_ntargets] = external_lex_fea[external_lex_fea_idx][idx][slides_page]

      slides_page += 1

    for idx in range(-1*pos_vec_size+trans_idx, pos_vec_size+trans_idx+1):
      if idx < 0:
        positions[0] += 1
      else:
        pos_idx = int(float(idx)*30*slides_page/len(trans_sparses))
        if pos_idx >= len(positions):
          pos_idx = len(positions) - 1
        positions[pos_idx] += 1

    if trans_idx == 0:
      is_first = FLOAT_MAX
    if trans_idx == len(trans_sparses)-1:
      is_last[slides_page-1] = FLOAT_MAX

    # print visual features
    if vis_fea:
      f_o.write(my_util.vec_to_string(vis_fea[trans_idx])+ ' ')
    # print cosine similarity features
    if multiplier != 0:
      f_o.write(my_util.vec_to_string(cos_sims) + ' ')
    # print external lexical features
    if external_lex_fea:
      for external_lex_fea_idx in range(len(external_lex_fea)):
        f_o.write(my_util.vec_to_string(external_lex_fea_matrix[external_lex_fea_idx]) + ' ')
    if use_pos:
      f_o.write(my_util.vec_to_string(positions) + ' ')
    f_o.write(str(is_first) + ' ')
    f_o.write(my_util.vec_to_string(is_last) + ' ')

    # print transition state
    if use_transition_state and trans_idx < len(trans_sparses)-1 and labels[trans_idx] != labels[trans_idx+1]:
      f_o.write(str(labels[trans_idx]) + '_t\n')
    # print state
    else:
      f_o.write(str(labels[trans_idx]) + '\n')
  f_o.write('\n')

def gen_raw_fea_v2(l_id, raw_slides_dir, raw_trans_dir, f_o, dimension, context_size, slides_context_size, window_size, multiplier):
  f_vec = [0 for _ in xrange(dimension)]
  f_cos_sim_context = [0 for _ in xrange((slides_context_size*2+1)*(context_size*2+1))]
  #f_pos = [0 for _ in xrange(pos_vec_length*2+1)]?

  labels = []
  trans_sparses = []
  trans_sparses_temp = []
  for trans_sparse, label in load_trans(raw_trans_dir + '/' + l_id):
    labels.append(label)
    trans_sparses_temp.append(copy.deepcopy(trans_sparse))
  for trans_idx in range(len(trans_sparses_temp)):
    trans_sparse = {}
    for idx in range(-1*window_size+trans_idx, window_size+trans_idx+1):
      if idx < 0 or idx >= len(trans_sparses_temp):
        continue
      trans_sparse = my_util.sparse_add(trans_sparse, trans_sparses_temp[idx])
    trans_sparses.append(trans_sparse)

#  n_pages = 0
  slides = []
  for slides_sparse in load_slides(raw_slides_dir + '/' + l_id):
    slides.append(slides_sparse)
#    n_pages += 1
  #pos_vec_win = int(pos_vec_frac*len(trans_sparses)/n_pages)
  #pos_hit_score = float(pos_vec_length*2+1)/(pos_vec_win*2+1)

  for slides_page in range(len(slides)):
    for trans_idx in range(len(trans_sparses)):
      cos_sims = f_cos_sim_context[:]
      positions = [-abs(trans_idx - float(len(trans_sparses))/len(slides)*(float(slides_page)+0.5))]

      for slides_idx in range(-1*slides_context_size+slides_page, slides_context_size+slides_page+1):
        for idx in range(-1*context_size+trans_idx, context_size+trans_idx+1):
          if slides_idx < 0 or slides_idx >= len(slides) or idx < 0 or idx >= len(trans_sparses):
            continue
          if not trans_sparses[idx] or not slides[slides_idx]:
            continue
          cos_sims[slides_idx+slides_context_size-slides_page+(idx+context_size-trans_idx)*(slides_context_size*2+1)] = my_util.cos_sim(trans_sparses[idx], slides[slides_idx], f_vec[:]) * multiplier

      f_o.write(my_util.vec_to_string(cos_sims) + ' ')
      f_o.write(my_util.vec_to_string(positions) + ' ')
      if (labels[trans_idx]-1) == slides_page:
        f_o.write('y\n')
      else:
        f_o.write('n\n')
    f_o.write('\n')

def gen_raw_fea_bak(ch_id, raw_tx_dir, raw_trans_dir, f_o, dimension, mapping):
  f_vec = [0 for _ in xrange(dimension)]

  for tx_sparse, tx_sec in load_tx(raw_tx_dir + '/' + ch_id):
    tx_vec_str = ' '.join(str(x) for x in my_util.sparse_to_vec(tx_sparse, f_vec[:]))

    with open(mapping) as f:
      for line in f:
        for trans_sparse, labels in load_trans(raw_trans_dir + '/' + line.strip().split('.pdf\t')[0]):
          trans_vec_str = ' '.join(str(x) for x in my_util.sparse_to_vec(trans_sparse, f_vec[:]))
          f_o.write(trans_vec_str + ' ' + tx_vec_str)
          if tx_sec in labels:
            f_o.write(' y\n')
          else:
            f_o.write(' n\n')
        f_o.write('\n')

def _main( ):
  filename = sys.argv[1]
  fea_type = ''
  if len(sys.argv) > 6:
    fea_type = sys.argv[6]
  if fea_type in ['usePos_useCosSim_specifyMaxSlides', 'usePos_useCosSim_useSmoothing_specifyMaxSlides', 'useCosSim_specifyMaxSlides']:
    pos_vec_size = int(sys.argv[7])
    context_size = int(sys.argv[8])
    max_ntargets = int(sys.argv[9])
    window_size = int(sys.argv[10])
    multiplier = float(sys.argv[11])
  elif fea_type in ['useCosSim_specifyMaxSlides_keyword', 'usePos_useCosSim_useSmoothing_specifyMaxSlides_keyword']:
    # example: 1781_1488
    # words: 0 - 1486
    # empty sent: 1487, 1488
    # keywords: 1489 - 1780
    keyword_param = {
      'w_dimension': int(sys.argv[5].split('_')[1]) - 1,
      'start_keyw_idx': int(sys.argv[5].split('_')[1]) + 1,
      'end_keyw_idx': int(sys.argv[5].split('_')[0]) - 1,
      'keyword_weight': float(sys.argv[12])
    }
    pos_vec_size = int(sys.argv[7])
    context_size = int(sys.argv[8])
    max_ntargets = int(sys.argv[9])
    window_size = int(sys.argv[10])
    multiplier = float(sys.argv[11])
  elif fea_type in ['useCosSim_v2']:
    context_size = int(sys.argv[7])
    slides_context_size = int(sys.argv[8])
    window_size = int(sys.argv[9])
    multiplier = float(sys.argv[10])
  elif fea_type in ['useCosSim_specifyMaxSlides_useVis', 'useCosSim_useDoc2vec_specifyMaxSlides_useVis', 'useWord2vec_specifyMaxSlides_useVis', 'useWord2vec_useOOVonehot_specifyMaxSlides_useVis', 'useCosSim_useWord2vec_specifyMaxSlides_useVis']:
    vis_fea_dir = sys.argv[7]
    context_size = int(sys.argv[8])
    max_ntargets = int(sys.argv[9])
    window_size = int(sys.argv[10])
    # if multiplier == 0: won't use CosSim
    multiplier = float(sys.argv[11])
    if 'useWord2vec' in fea_type or 'useDoc2vec' in fea_type:
      doc2vec_weight = float(sys.argv[12])
      doc2vec_fea_dir = sys.argv[13]
    if 'useOOVonehot' in fea_type:
      oov_weight = float(sys.argv[14])

  f_o = open(sys.argv[4], 'w')
  with open(filename) as f:
    for line in f:
      if fea_type == 'usePos_useCosSim_specifyMaxSlides':
        gen_raw_fea(line.strip(), sys.argv[2], sys.argv[3], f_o, int(sys.argv[5]), max_ntargets, window_size, multiplier)
      elif fea_type == 'usePos_useCosSim_useSmoothing_specifyMaxSlides':
        gen_raw_fea(line.strip(), sys.argv[2], sys.argv[3], f_o, int(sys.argv[5]), pos_vec_size, context_size, max_ntargets, window_size, multiplier, use_smoothing=False)
      elif fea_type == 'usePos_useCosSim_useSmoothing_specifyMaxSlides_keyword':
        gen_raw_fea(line.strip(), sys.argv[2], sys.argv[3], f_o, keyword_param['end_keyw_idx']+1, pos_vec_size, context_size, max_ntargets, window_size, multiplier, use_smoothing=False, keyword_param=keyword_param)
      elif fea_type == 'useCosSim_specifyMaxSlides_keyword':
        gen_raw_fea(line.strip(), sys.argv[2], sys.argv[3], f_o, keyword_param['end_keyw_idx']+1, 0, context_size, max_ntargets, window_size, multiplier, use_smoothing=False, use_pos=False, keyword_param=keyword_param)
      elif fea_type == 'useCosSim_specifyMaxSlides':
        gen_raw_fea(line.strip(), sys.argv[2], sys.argv[3], f_o, int(sys.argv[5]), 0, context_size, max_ntargets, window_size, multiplier, use_smoothing=False, use_pos=False)
      elif fea_type == 'useCosSim_v2':
        gen_raw_fea_v2(line.strip(), sys.argv[2], sys.argv[3], f_o, int(sys.argv[5]), context_size, slides_context_size, window_size, multiplier)
      elif fea_type == 'useCosSim_specifyMaxSlides_useVis':
        vis_fea = load_external_fea(vis_fea_dir, line.strip())
        gen_raw_fea(line.strip(), sys.argv[2], sys.argv[3], f_o, int(sys.argv[5]), 0, context_size, max_ntargets, window_size, multiplier, use_smoothing=False, use_pos=False, vis_fea=vis_fea, use_transition_state=True)
      elif ('useWord2vec' in fea_type or 'useDoc2vec' in fea_type) and ('useVis' in fea_type):
        vis_fea = load_external_fea(vis_fea_dir, line.strip())
        external_lex_fea = (load_external_fea(doc2vec_fea_dir, line.strip(), doc2vec_weight),)
        if 'useOOVonehot' in fea_type:
          external_lex_fea = external_lex_fea + (load_external_fea(doc2vec_fea_dir, line.strip() + '.oov', oov_weight),)
        gen_raw_fea(line.strip(), sys.argv[2], sys.argv[3], f_o, int(sys.argv[5]), 0, context_size, max_ntargets, window_size, multiplier, use_smoothing=False, use_pos=False, vis_fea=vis_fea, use_transition_state=True, external_lex_fea=external_lex_fea)
if __name__ == '__main__':
  _main( )
