# http://pymbook.readthedocs.io/en/latest/testing.html

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import unittest

from utils import *
import data

global cfg
cfg = configuration() # Init configuration structure

cptest = 'test/slttest/' # The main directory where the data of the voice is stored
cfg.fileids = cptest+'/file_id_list.scp'
fid_lst = data.loadids(cfg.fileids)
cfg.id_valid_start = 8
cfg.id_valid_nb = 1
cfg.id_test_nb = 1
cfg.indir = cptest+'binary_label_601_norm_minmaxm11/*.lab:(-1,601)'
cfg.outdir = cptest+'wav_cmp_lf0_fwspec65_fwnm17_bndnmnoscale/*.cmp:(-1,83)'
cfg.wdir = cptest+'wav_fwspec65_weights/*.w:(-1,1)'

cfg.train_batchsize = 2

fid_lst_tra = fid_lst[:cfg.id_train_nb()]
fid_lst_val = fid_lst[cfg.id_valid_start:cfg.id_valid_start+cfg.id_valid_nb]

spec_size = 65
nm_size = 17
cfg.shift = 0.005   # Time shift between 2 frames
cfg.fs = 32000      # Sampling frequency of the samples used for testing

class TestSmokeTheano(unittest.TestCase):
    def test_model(self):
        makedirs('test/test_made__smoke_theano_model')

        import models_basic
        model = models_basic.ModelFC(601, 1+spec_size+17, spec_size, nm_size, hiddensize=4, nblayers=2)
        modelwdeltas = models_basic.ModelFC(601, 3*(1+spec_size+17), spec_size, nm_size, hiddensize=4, nblayers=2) # TODO Should train it too


        print("modgan.nbParams={}".format(model.nbParams()))
        # self.assertEqual(model.nbParams(), TODO) # TODO Check number of params. Should be known.

        global cfg
        cfg.train_nbtrials = 1        # Just run one training only
        cfg.train_hypers = []
        cost_val = 67.43
        model.saveAllParams('test/test_made__smoke_theano_model/smokymodelparams.pkl')
        model.saveAllParams('test/test_made__smoke_theano_model/smokymodelparams.pkl', cfg=cfg, extras={'cost_val':cost_val})
        model.saveAllParams('test/test_made__smoke_theano_model/smokymodelparams.pkl', cfg=cfg, extras={'cost_val':cost_val})

        cfg_loaded, extras_loaded = model.loadAllParams('test/test_made__smoke_theano_model/smokymodelparams.pkl')
        self.assertEqual(cfg, cfg_loaded)
        self.assertEqual({'cost_val':cost_val}, extras_loaded)


        import optimizer
        optigan = optimizer.Optimizer(model, errtype=None)

        optigan.saveTrainingState('test/test_made__smoke_theano_model/smokytrainingstate.pkl', cfg=cfg, extras={'cost_val':cost_val})

        cfg_loaded, extras_loaded = optigan.loadTrainingState('test/test_made__smoke_theano_model/smokytrainingstate.pkl', cfg=cfg)
        self.assertEqual(cfg, cfg_loaded)
        self.assertEqual({'cost_val':cost_val}, extras_loaded)

        cfg, hyperstr = optigan.randomize_hyper(cfg)
        print('randomize_hyper: hyperstr='+hyperstr)
        cfg.print_content()

        cfg.train_hypers = [('train_learningrate_log10', -6.0, -2.0), ('train_adam_beta1', 0.8, 1.0), ('train_batchsize', 1, 4)] # For ADAM
        cfg_hyprnd1, hyperstr1 = optigan.randomize_hyper(cfg)
        print('randomize_hyper: hyperstr1='+hyperstr1)
        cfg_hyprnd1.print_content()
        cfg_hyprnd2, hyperstr2 = optigan.randomize_hyper(cfg)
        print('randomize_hyper: hyperstr2='+hyperstr2)
        cfg_hyprnd2.print_content()
        self.assertNotEqual(cfg_hyprnd1, cfg_hyprnd2)

        makedirs('test/test_made__smoke_theano_model_train')
        cfg.train_max_nbepochs = 5
        cfg.train_nbtrials = 5        # Just run one training only
        optigan.train_multipletrials(cfg.indir, cfg.outdir, cfg.wdir, fid_lst_tra, fid_lst_val, model.params_trainable, 'test/test_made__smoke_theano_model_train/smokymodelparams.pkl', cfgtomerge=cfg, cont=False)


        # Go back to single trial for the next tests
        cfg.train_nbtrials = 1
        cfg.train_hypers = []

        optigan.train_multipletrials(cfg.indir, cfg.outdir, cfg.wdir, fid_lst_tra, fid_lst_val, model.params_trainable, 'test/test_made__smoke_theano_model_train/smokymodelparams.pkl', cfgtomerge=cfg, cont=False)

        cfg.train_max_nbepochs = 10
        optigan.train_multipletrials(cfg.indir, cfg.outdir, cfg.wdir, fid_lst_tra, fid_lst_val, model.params_trainable, 'test/test_made__smoke_theano_model_train/smokymodelparams.pkl', cfgtomerge=cfg, cont=True)

        model.saveAllParams('test/test_made__smoke_theano_model_train/smokymodelparams.pkl')
        model.generate('test/test_made__smoke_theano_model_train/smokymodelparams.pkl', '-snd', cfg, do_objmeas=True, do_resynth=True, indicestosynth=None, spec_comp='fwspec', spec_size=spec_size, nm_size=nm_size)
        model.generate('test/test_made__smoke_theano_model_train/smokymodelparams.pkl', '-snd-pp_spec_extrapfreq', cfg, do_objmeas=True, do_resynth=True, indicestosynth=None, spec_comp='fwspec', spec_size=spec_size, nm_size=nm_size, pp_spec_extrapfreq=8000)
        model.generate('test/test_made__smoke_theano_model_train/smokymodelparams.pkl', '-snd-pp_spec_pf_coef', cfg, do_objmeas=True, do_resynth=True, indicestosynth=None, spec_comp='fwspec', spec_size=spec_size, nm_size=nm_size, pp_spec_pf_coef=1.2)

        # Test MLPG
        cfg.outdir = 'test/test_made__smoke_compose_compose2_cmp_deltas/*.cmp:(-1,249)'
        optiganwdeltas = optimizer.Optimizer(modelwdeltas, errtype=None)
        optiganwdeltas.train_multipletrials(cfg.indir, cfg.outdir, cfg.wdir, fid_lst_tra, fid_lst_val, modelwdeltas.params_trainable, 'test/test_made__smoke_theano_model_train/smokymodelparams_wdeltas.pkl', cfgtomerge=cfg, cont=False)
        modelwdeltas.saveAllParams('test/test_made__smoke_theano_model_train/smokymodelparams_wdeltas.pkl')
        modelwdeltas.generate('test/test_made__smoke_theano_model_train/smokymodelparams_wdeltas.pkl', '-snd', cfg, do_objmeas=True, do_resynth=True, indicestosynth=None, spec_comp='fwspec', spec_size=spec_size, nm_size=nm_size, do_mlpg=True)

        cfg.outdir = cptest+'wav_cmp_lf0_fwspec65_fwnm17_bndnmnoscale/*.cmp:(-1,83)'


        # Now test the various models available

        model = models_basic.ModelBGRU(601, 1+spec_size+17, spec_size, nm_size, hiddensize=4, nblayers=1)
        modelwdeltas = models_basic.ModelBGRU(601, 3*(1+spec_size+nm_size), spec_size, nm_size, hiddensize=4, nblayers=1)
        optigan = optimizer.Optimizer(model, errtype=None)
        optigan.train_multipletrials(cfg.indir, cfg.outdir, cfg.wdir, fid_lst_tra, fid_lst_val, model.params_trainable, 'test/test_made__smoke_theano_model_train/smokymodelparams.pkl', cfgtomerge=cfg, cont=False)
        # model.generate('test/test_made__smoke_theano_model_train/smokymodelparams.pkl', '-snd', cfg, do_objmeas=True, do_resynth=True, indicestosynth=None, spec_comp='fwspec', spec_size=spec_size, nm_size=nm_size)

        model = models_basic.ModelBLSTM(601, 1+spec_size+17, spec_size, nm_size, hiddensize=4, nblayers=1)
        modelwdeltas = models_basic.ModelBLSTM(601, 3*(1+spec_size+nm_size), spec_size, nm_size, hiddensize=4, nblayers=1)
        optigan = optimizer.Optimizer(model, errtype=None)
        optigan.train_multipletrials(cfg.indir, cfg.outdir, cfg.wdir, fid_lst_tra, fid_lst_val, model.params_trainable, 'test/test_made__smoke_theano_model_train/smokymodelparams.pkl', cfgtomerge=cfg, cont=False)
        # model.generate('test/test_made__smoke_theano_model_train/smokymodelparams.pkl', '-snd', cfg, do_objmeas=True, do_resynth=True, indicestosynth=None, spec_comp='fwspec', spec_size=spec_size, nm_size=nm_size)

        import models_cnn
        model = models_cnn.ModelCNN(601, spec_size, nm_size, hiddensize=4, nbprelayers=1, nbcnnlayers=1, nbfilters=2, spec_freqlen=3, nm_freqlen=3, windur=0.020)
        optigan = optimizer.Optimizer(model, errtype=None)
        optigan.train_multipletrials(cfg.indir, cfg.outdir, cfg.wdir, fid_lst_tra, fid_lst_val, model.params_trainable, 'test/test_made__smoke_theano_model_train/smokymodelparams.pkl', cfgtomerge=cfg, cont=False)
        # # model.generate('test/test_made__smoke_theano_model_train/smokymodelparams.pkl', '-snd', cfg, do_objmeas=True, do_resynth=True, indicestosynth=None, spec_comp='fwspec', spec_size=spec_size, nm_size=nm_size)

        optigan = optimizer.Optimizer(model, errtype='WGAN')
        optigan.train_multipletrials(cfg.indir, cfg.outdir, cfg.wdir, fid_lst_tra, fid_lst_val, model.params_trainable, 'test/test_made__smoke_theano_model_train/smokymodelparams.pkl', cfgtomerge=cfg, cont=False)
        # model.generate('test/test_made__smoke_theano_model_train/smokymodelparams.pkl', '-snd', cfg, do_objmeas=True, do_resynth=True, indicestosynth=None, spec_comp='fwspec', spec_size=spec_size, nm_size=nm_size)



    def test_utils_theano(self):
        import utils_theano

        import theano.tensor as T

        # Test the following if CUDA is available: (won't be tested on travis anyway since no GPU are available on travis)
        if utils_theano.th_cuda_available():
            print('nvidia_smi_current_gpu={}'.format(nvidia_smi_current_gpu()))  # Can't test it because needs CUDA
            print('nvidia_smi_gpu_memused={}'.format(nvidia_smi_gpu_memused())) # Can't test it because needs CUDA

        x = T.ftensor3('x')

        y = utils_theano.th_print('smoky debug message', x)

        y = utils_theano.nonlin_tanh_saturated(x, coef=1.01)
        y = utils_theano.nonlin_tanh_bysigmoid(x)
        y = utils_theano.nonlin_tanhcm11(x)
        y = utils_theano.nonlin_saturatedsigmoid(x, coef=1.01)
        y = utils_theano.nonlin_sigmoidbinary(x)
        y = utils_theano.nonlin_softsign(x)
        y = utils_theano.nonlin_sigmoidparm(x, c=0.0, f=1.0)


if __name__ == '__main__':
    unittest.main()