'''
Useful functions related to Theano.

Copyright(C) 2017 Engineering Department, University of Cambridge, UK.

License
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

Author
    Gilles Degottex <gad27@cam.ac.uk>
'''

import numpy as np
import theano
import theano.tensor as T
import theano.sandbox.cuda

import os
import subprocess
import xml.etree.ElementTree as ET

def th_memfree():
    meminfo = theano.sandbox.cuda.basic_ops.cuda_ndarray.cuda_ndarray.mem_info()
    return '{}MB mem free'.format(meminfo[0]/(1024*1024))

def nvidia_smi_current_gpu():
    xml = subprocess.Popen(['nvidia-smi', '-q', '-x'], stdout=subprocess.PIPE).communicate()[0]
    root = ET.fromstring(xml)
    for gpu in root.findall('gpu'):
        for proc in gpu.find('processes').findall('process_info'):
            if int(proc.find('pid').text) == os.getpid():
                return int(gpu.find('minor_number').text)
    return -1

def nvidia_smi_proc_memused():
    # Returns MiB
    xml = subprocess.Popen(['nvidia-smi', '-q', '-x'], stdout=subprocess.PIPE).communicate()[0]
    root = ET.fromstring(xml)
    for gpu in root.findall('gpu'):
        for proc in gpu.find('processes').findall('process_info'):
            if int(proc.find('pid').text) == os.getpid():
                return int(proc.find('used_memory').text.split(' ')[0])
    return -1

def th_print(msg, op):
    print_shape = theano.printing.Print(msg, attrs = [ 'shape' ])
    print_val = theano.printing.Print(msg)
    op = print_val(print_shape(op))
    return op

def paramss_count(paramss):
    nbparams = 0
    for p in paramss:
        shap = p.get_value().shape
        if len(shap)==1: nbparams += shap[0]
        else:            nbparams += np.prod(shap)
    return nbparams

def linear_and_bndnmoutput_deltas_tanh(x, specsize, nmsize):

    #coef = 1.01*(1.0/(2.0*0.288675135))
    coef = 1.01*1.0

    y = T.set_subtensor(x[:,:,1+specsize:1+specsize+nmsize], coef*T.tanh(x[:,:,1+specsize:1+specsize+nmsize])) # TODO sigmoid
    y = T.set_subtensor(y[:,:,85+61:85+61+24], coef*T.tanh(y[:,:,85+61:85+61+24]))
    y = T.set_subtensor(y[:,:,2*85+61:2*85+61+24], coef*T.tanh(y[:,:,2*85+61:2*85+61+24]))

    return y

def linear_nmsigmoid(x, specsize, nmsize):

    #coef = 1.01*(1.0/(2.0*0.288675135))
    coef = 1.01*1.0

    y = T.set_subtensor(x[:,:,1+specsize:1+specsize+nmsize], coef*T.nnet.nnet.sigmoid(x[:,:,1+specsize:1+specsize+nmsize]))

    return y

def nonlin_tanh_saturated(x, coef=1.01):
    return coef*T.tanh(x)

# def nonlin_tanh_byultrafastsigmoid(x):
    # return (T.nnet.ultra_fast_sigmoid(x)-0.5)*(1.0049698233144269*2.0)
def nonlin_tanh_bysigmoid(x):
    return (T.nnet.sigmoid(x)-0.5)*2.0

def nonlin_tanhcm11(x):
    # max 2nd deriv at -1;+1
    return T.tanh((2.0/3.0)*x)

def nonlin_saturatedsigmoid(x, coef=1.01):
    return coef*theano.tensor.nnet.sigmoid(x)

def nonlin_sigmoidbinary(x):
    #return T.nnet.nnet.ultra_fast_sigmoid(x)
    return T.nnet.nnet.sigmoid(x)*1.001

## This one gives potential speedup using option ultra_fast_sigmoid
## Doesn't improve anything
#def tanh_bysigmoid(x):
    #return 2*T.nnet.sigmoid(2*x)-1

def nonlin_softsign(x):
    return x / (1.0+abs(x))

def nonlin_sigmoidparm(x, c=0.0, f=1.0):
  return 1.0 / (1.0 + np.exp(-(x-c)*f))

def weights_normal_ortho(insiz, outsiz, std, rng):
    # Preserve std!
    a = rng.normal(0.0, std, size=(insiz, outsiz))
    u, s, v = np.linalg.svd(a, full_matrices=0)
    if u.shape!=(insiz, outsiz): u=v
    u = u.reshape((insiz, outsiz))
    return np.asarray(u, dtype=theano.config.floatX)