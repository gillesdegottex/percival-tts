# http://pymbook.readthedocs.io/en/latest/testing.html

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))+'/external/')
from utils import *
print_sysinfo()

print_log('Global configurations')
cfg = configuration() # Init configuration structure

# Corpus/Voice(s) options
cp = 'test/slttest/' # The main directory where the data of the voice is stored
cfg.fileids = cp+'/file_id_list.scp'
cfg.id_valid_start = 8
cfg.id_valid_nb = 1
cfg.id_test_nb = 1

# Input text labels
in_size = 601
label_dir = 'binary_label_'+str(in_size)
label_path = cp+label_dir+'/*.lab'
cfg.indir = cp+label_dir+'_norm_minmaxm11/*.lab:(-1,'+str(in_size)+')' # Merlin-minmaxm11 eq.

# Output features
cfg.fs = 32000
cfg.shift = 0.005
f0_min, f0_max = 60, 600
spec_size = 65
nm_size = 17
out_size = 1+spec_size+nm_size
wav_dir = 'wav'
wav_path = cp+wav_dir+'/*.wav'
f0_path = cp+wav_dir+'_lf0/*.lf0'
spec_path = cp+wav_dir+'_fwspec'+str(spec_size)+'/*.fwspec'
nm_path = cp+wav_dir+'_fwnm'+str(nm_size)+'/*.fwnm'
cfg.outdir = cp+wav_dir+'_cmp_lf0_fwspec'+str(spec_size)+'_fwnm'+str(nm_size)+'_bndnmnoscale/*.cmp:(-1,'+str(out_size)+')'
cfg.wdir = cp+wav_dir+'_fwspec'+str(spec_size)+'_weights/*.w:(-1,1)'

cfg.print_content()

class TestBase(unittest.TestCase):

    def test_vocoder_pulsemodel_features_extraction_and_composition(self):
        import pulsemodel
        with open(cfg.fileids) as f:
            fids = filter(None, [x for x in map(str.strip, f.readlines()) if x])
            for fid in fids:
                print('Extracting features from: '+fid)
                pulsemodel.analysisf(wav_path.replace('*',fid), f0_min=f0_min, f0_max=f0_max, f0_file=f0_path.replace('*',fid), f0_log=True,
                spec_file=spec_path.replace('*',fid), spec_nbfwbnds=spec_size, nm_file=nm_path.replace('*',fid), nm_nbfwbnds=nm_size, verbose=1)


        import compose

        # Compose the inputs
        # The input files are binary labels, as the come from the NORMLAB Process of Merlin TTS pipeline https://github.com/CSTR-Edinburgh/merlin
        compose.compose([label_path+':(-1,'+str(in_size)+')'], cfg.fileids, cfg.indir, id_valid_start=cfg.id_valid_start, normfn=compose.normalise_minmax, do_finalcheck=True, wins=[])

        # Compose the outputs
        compose.compose([f0_path, spec_path+':(-1,'+str(spec_size)+')', nm_path+':(-1,'+str(nm_size)+')'], cfg.fileids, cfg.outdir, id_valid_start=cfg.id_valid_start, normfn=compose.normalise_meanstd_bndnmnoscale)

        # Create time weights (column vector in [0,1]). The frames at begining or end of
        # each file whose weights are smaller than 0.5 will be ignored by the training
        compose.create_weights(spec_path+':(-1,'+str(spec_size)+')', cfg.fileids, cfg.wdir)


if __name__ == '__main__':
    unittest.main()