#! /usr/bin/python3
from __future__ import division, print_function, unicode_literals

import numpy as np

def interleave_arrays(*arrays):
    for i in range(1, len(arrays)):
        if arrays[i-1].shape != arrays[i].shape:
            raise ValueError("array sizes are not equal")

    array = np.array(arrays)
    array = array.T
    array = array.reshape(len(arrays) * len(arrays[0]))

    split_array(array, len(arrays))

    return array

def interleave_files(out_fn, *in_fns):
    arrays = []
    for fn in in_fns:
        array = np.fromfile(fn, dtype = 'B')
        if arrays and len(arrays[-1]) != len(array):
            raise ValueError("file sizes are not equal")
        arrays.append(array)

    array = interleave_arrays(*arrays)

    array.tofile(out_fn)

def split_array(array, parts):
    if len(array) % parts:
        raise ValueError("length of array is not a multiple of parts")

    array = array.reshape((len(array) // parts, parts))
    array = array.T

    return array

def split_file(in_fn, *out_fns):
    array = np.fromfile(in_fn, dtype = 'B')
    arrays = split_array(array, len(out_fns))
    for i in range(len(arrays)):
        arrays[i].tofile(out_fns[i])

if __name__ == '__main__':
    interleave_files('A0',
                     'w140_roms/160-6988-03.bin',
                     'w140_roms/160-6989-03.bin')
    split_file('A0', 'A1', 'A2')
