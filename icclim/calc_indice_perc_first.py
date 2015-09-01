#  Copyright CERFACS (http://cerfacs.fr/)
#  Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
#
#  Author: Natalia Tatarinova


import numpy

import ctypes
from numpy.ctypeslib import ndpointer
import os
import calc_indice

my_rep = os.path.dirname(os.path.abspath(__file__)) + os.sep

libraryC = ctypes.cdll.LoadLibrary(my_rep+'libC.so')


'''
Elementary functions computing percentile based indices:
- TG10p
- TX10p
- TN10p
- TG90p
- TX90p
- TN90p
- WSDI
- CSDI
- R75p
- R75TOT
- R95p
- R95TOT
- R99p
- R99TOT
- CD
- CW
- WD
- WW
'''

############# utility functions: begin #############
def get_binary_arr(arr1, arr2, logical_operation):
    '''
    Compare "arr1" with "arr2" and return a binary array with the result.
    
    :param arr1: array to comparer with arr2
    :type arr1: numpy.ndarray
    :param arr2: reference array 
    :type arr1: numpy.ndarray
    :rtype: binary numpy.ndarray
    
    ..warning:: "arr1" and "arr2" must have the same shape
    
    '''

    if logical_operation == 'gt':
        binary_arr = arr1 > arr2
        
    elif logical_operation == 'get':
            binary_arr = arr1 >= arr2
            
    elif logical_operation == 'lt':
            binary_arr = arr1 < arr2
            
    elif logical_operation == 'let':
            binary_arr = arr1 <= arr2 
    
    
    binary_arr = binary_arr.astype(int) # True/False ---> 1/0

    # if binary_arr is masked array, we fill masked values with 0
    if isinstance(binary_arr, numpy.ma.MaskedArray):
        binary_arr = binary_arr.filled(0.0)

    
    return binary_arr


def get_masked_arr(arr, fill_val):
    '''
    If a masked array is passed, this function does nothing.
    If a filled array is passed (fill_value must be passed also), it will be transformed into a masked array.
    
    '''
    if isinstance(arr, numpy.ma.MaskedArray):               # numpy.ma.MaskedArray
        masked_arr = arr
    else:                                                   # numpy.ndarray
        if (fill_val==None):
            raise(ValueError('If input array is not a masked array, a "fill_value" must be provided.'))
        mask_arr = (arr==fill_val)
        masked_arr = numpy.ma.masked_array(arr, mask=mask_arr, fill_value=fill_val)
    
    return masked_arr

##### utility function: end #####################



def TG90p_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the TG90p indice: number of warm days (i.e. days with daily mean temperature > 90th percentile of daily mean temperature in the base period).
    
    :param arr: daily mean temperature (e.g. "tas")
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 90th percentile of daily mean temperature 
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)    
    
    .. warning:: Units of "arr" and percentile values of "percentile_dict" must be the same.
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''

    TG90p = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    arr_masked = get_masked_arr(arr, fill_val)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        # we take the 2D array corresponding to the current calendar day
        current_perc_arr = percentile_dict[m,d]
                    
        # we are looking for the values which are greater than the 90th percentile  
        bin_arr = get_binary_arr(arr_masked[i,:,:], current_perc_arr, logical_operation='gt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        TG90p = TG90p + bin_arr
        
        i+=1
        
#     if not isinstance(arr, numpy.ma.MaskedArray):
#         TG90p = TG90p.filled(fill_value=arr_masked.fill_value)    
    
    return TG90p


def TX90p_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the TX90p indice: number of warm days-times (i.e. days with daily max temperature > 90th percentile of daily max temperature in the base period).
    
    :param arr: daily max temperature (e.g. "tasmax")
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 90th percentile of daily max temperature 
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)       
    
    .. warning:: Units of "arr" and percentile values of "percentile_dict" must be the same.
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''

    TX90p = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    arr_masked = get_masked_arr(arr, fill_val)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are greater than the 90th percentile  
        bin_arr = get_binary_arr(arr_masked[i,:,:], current_perc_arr, logical_operation='gt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        TX90p = TX90p + bin_arr
        
        i+=1

#     if not isinstance(arr, numpy.ma.MaskedArray):
#         TX90p = TX90p.filled(fill_value=arr_masked.fill_value)    
    
    return TX90p
    

def WSDI_calculation(arr, dt_arr, percentile_dict, fill_val=None, N=6):
    '''
    Calculate the WSDI indice (warm-spell duration index): number of days where, in intervals of at least 6 consecutive days, 
    daily max temperature > 90th percentile of daily max temperature in the base period).
    This function calls C function "WSDI_CSDI_3d" from libC.c
    
    :param arr: daily max temperature (e.g. "tasmax")
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 90th percentile of daily max temperature 
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    :param N: number of consecutive days (default: 6)
    :type N: int
    
    :rtype: numpy.ndarray (2D)       
    '''
    
        
    #.. warning:: Units of "arr" and percentile values of "percentile_dict" must be the same.
    #
    #.. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.
 
    arr_masked = get_masked_arr(arr, fill_val)
    
    # step1: we get a 3D binary array from arr (if arr value > corresponding 90th percentile value: 1, else: 0)    
    bin_arr = numpy.zeros((arr.shape[0], arr.shape[1], arr.shape[2]))
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are greater than the 90th percentile  
        bin_arr_current_slice = get_binary_arr(arr_masked[i,:,:], current_perc_arr, logical_operation='gt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        bin_arr_current_slice = bin_arr_current_slice.filled(fill_value=0) # we fill the bin_arr_current_slice with zeros
        bin_arr[i,:,:] = bin_arr_current_slice

        i+=1
    
    # step2: now we will pass our 3D binary array (bin_arr) to C function WSDI_CSDI_3d
    
    # array data type should be 'float32' to pass it to C function  
    if bin_arr.dtype != 'float32':
        bin_arr = numpy.array(bin_arr, dtype='float32')
    
    
    WSDI_CSDI_C = libraryC.WSDI_CSDI_3d    
    WSDI_CSDI_C.restype = None
    WSDI_CSDI_C.argtypes = [ndpointer(ctypes.c_float),
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_int,
                            ndpointer(ctypes.c_double),
                            ctypes.c_int] 
        
    WSDI = numpy.zeros([arr.shape[1], arr.shape[2]]) # reserve memory
        
    WSDI_CSDI_C(bin_arr, bin_arr.shape[0], bin_arr.shape[1], bin_arr.shape[2], WSDI, N)
    
    WSDI = WSDI.reshape(arr.shape[1], arr.shape[2])
    
#     if isinstance(arr, numpy.ma.MaskedArray):
#         WSDI = numpy.ma.array(WSDI, mask=(WSDI==fill_val), fill_value=fill_val)

    return WSDI    
    


def TN90p_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    
    
    
    '''
    Calculate the TN90p indice: number of warm nights (i.e. days with daily min temperature > 90th percentile of daily min temperature in the base period).
    
    :param arr: daily min temperature (e.g. "tasmin")
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 90th percentile of daily min temperature 
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        
    
    .. warning:: Units of "arr" and percentile values of "percentile_dict" must be the same.
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''

    TN90p = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    arr_masked = get_masked_arr(arr, fill_val)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are greater than the 90th percentile  
        bin_arr = get_binary_arr(arr_masked[i,:,:], current_perc_arr, logical_operation='gt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        TN90p = TN90p + bin_arr
        
        i+=1

#     if not isinstance(arr, numpy.ma.MaskedArray):
#         TN90p = TN90p.filled(fill_value=arr_masked.fill_value)    
    
    return TN90p    


    
    
def TG10p_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the TG10p indice: number of cold days (i.e. days with daily mean temperature < 10th percentile of daily mean temperature in the base period).
    
    :param arr: daily mean temperature (e.g. "tas")
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 10th percentile of daily mean temperature 
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        
    
    .. warning:: Units of "arr" and percentile values of "percentile_dict" must be the same.
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''

    TG10p = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    arr_masked = get_masked_arr(arr, fill_val)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day
        
        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are less than the 10th percentile  
        bin_arr = get_binary_arr(arr_masked[i,:,:], current_perc_arr, logical_operation='lt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        TG10p = TG10p + bin_arr
        
        i+=1
        
#     if not isinstance(arr, numpy.ma.MaskedArray):
#         TG10p = TG10p.filled(fill_value=arr_masked.fill_value)    
    
    return TG10p      
    
    
    
def TX10p_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the TX10p indice: number of cold day-times (i.e. days with daily max temperature < 10th percentile of daily max temperature in the base period).
    
    :param arr: daily max temperature (e.g. "tasmax")
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 10th percentile of daily max temperature 
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        
    
    .. warning:: Units of "arr" and percentile values of "percentile_dict" must be the same.
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''

    TX10p = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    arr_masked = get_masked_arr(arr, fill_val)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are less than the 10th percentile  
        bin_arr = get_binary_arr(arr_masked[i,:,:], current_perc_arr, logical_operation='lt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        TX10p = TX10p + bin_arr
        
        i+=1
        
#     if not isinstance(arr, numpy.ma.MaskedArray):
#         TX10p = TX10p.filled(fill_value=arr_masked.fill_value)    
    
    return TX10p      
    

def TN10p_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the TN10p indice: number of cold nights (i.e. days with daily min temperature < 10th percentile of daily min temperature in the base period).
    
    :param arr: daily min temperature (e.g. "tasmin")
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 10th percentile of daily min temperature 
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        
    '''
    
    #.. warning:: Units of "arr" and percentile values of "percentile_dict" must be the same.
    #
    #.. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.


    TN10p = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    arr_masked = get_masked_arr(arr, fill_val)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are less than the 10th percentile  
        bin_arr = get_binary_arr(arr_masked[i,:,:], current_perc_arr, logical_operation='lt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        TN10p = TN10p + bin_arr
        
        i+=1
        
#     if not isinstance(arr, numpy.ma.MaskedArray):
#         TN10p = TN10p.filled(fill_value=arr_masked.fill_value)    
    
    return TN10p    


def CSDI_calculation(arr, dt_arr, percentile_dict, fill_val=None, N=6):
    '''
    Calculate the CSDI indice (cold-spell duration index): number of days where, in intervals of at least 6 consecutive days, 
    daily min temperature < 10th percentile of daily min temperature in the base period).
    This function calls C function "WSDI_CSDI_3d" from libC.c
    
    :param arr: daily min temperature (e.g. "tasmin")
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 10th percentile of daily max temperature 
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    :param N: number of consecutive days (default: 6)
    :type N: int
    
    :rtype: numpy.ndarray (2D)        
    
    .. warning:: Units of "arr" and percentile values of "percentile_dict" must be the same.
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''
 
    arr_masked = get_masked_arr(arr, fill_val)
    
    # step1: we get a 3D binary array from arr (if arr value < corresponding 10th percentile value: 1, else: 0)    
    bin_arr = numpy.zeros((arr.shape[0], arr.shape[1], arr.shape[2]))
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are less than the 10th percentile  
        bin_arr_current_slice = get_binary_arr(arr_masked[i,:,:], current_perc_arr, logical_operation='lt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        bin_arr_current_slice = bin_arr_current_slice.filled(fill_value=0) # we fill the bin_arr_current_slice with zeros
        bin_arr[i,:,:] = bin_arr_current_slice

        i+=1
    
    # step2: now we will pass our 3D binary array (bin_arr) to C function WSDI_CSDI_3d
    
    # array data type should be 'float32' to pass it to C function  
    if bin_arr.dtype != 'float32':
        bin_arr = numpy.array(bin_arr, dtype='float32')
    
    
    WSDI_CSDI_C = libraryC.WSDI_CSDI_3d    
    WSDI_CSDI_C.restype = None
    WSDI_CSDI_C.argtypes = [ndpointer(ctypes.c_float),
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_int,
                            ndpointer(ctypes.c_double),
                            ctypes.c_int] 
        
    CSDI = numpy.zeros([arr.shape[1], arr.shape[2]]) # reserve memory
        
    WSDI_CSDI_C(bin_arr, bin_arr.shape[0], bin_arr.shape[1], bin_arr.shape[2], CSDI, N)
    
    CSDI = CSDI.reshape(arr.shape[1], arr.shape[2])
    
#     if isinstance(arr, numpy.ma.MaskedArray):
#         CSDI = numpy.ma.array(CSDI, mask=(CSDI==fill_val), fill_value=fill_val)

    return CSDI

    

def R75p_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the R75p indice: number of moderate wet days (i.e. days with daily precipitation amount > 75th percentile of daily amount in the base period).
    
    :param arr: daily precipitation flux (liquid form) (e.g. "pr") in mm/s
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 75th percentile of daily precipitation amount at wet days in mm/day
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''
    R75p = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    pr_thresh = 1                               # precipitation threshold = 1 mm
    
    arr_masked = get_masked_arr(arr, fill_val)  # mm/s
    arr_masked = arr_masked*60*60*24            # mm/day
    
    # we need to check only wet days (i.e. days with RR >= 1 mm)
    # so, we mask all values < 1 mm with the same fill_value
    mask_arr_masked = arr_masked < 1.0 # mask
    arr_masked_masked = numpy.ma.array(arr_masked, mask=mask_arr_masked, fill_value=arr_masked.fill_value)
      
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]

        # we are looking for the values which are greater than the 75th percentile  
        bin_arr = get_binary_arr(arr_masked_masked[i,:,:], current_perc_arr, logical_operation='gt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        R75p = R75p + bin_arr
        
        i+=1

#     if not isinstance(arr, numpy.ma.MaskedArray):
#         R75p = R75p.filled(fill_value=arr_masked.fill_value)    
    
    return R75p    


def R95p_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the R95p indice: number of very wet days (i.e. days with daily precipitation amount > 95th percentile of daily amount in the base period).
    
    :param arr: daily precipitation flux (liquid form) (e.g. "pr") in mm/s
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 95th percentile of daily precipitation amount at wet days in mm/day
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''
    R95p = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    pr_thresh = 1                               # precipitation threshold = 1 mm
    
    arr_masked = get_masked_arr(arr, fill_val)  # mm/s
    arr_masked = arr_masked*60*60*24            # mm/day
    
    # we need to check only wet days (i.e. days with RR >= 1 mm)
    # so, we mask all values < 1 mm with the same fill_value
    mask_arr_masked = arr_masked < 1.0 # mask
    arr_masked_masked = numpy.ma.array(arr_masked, mask=mask_arr_masked, fill_value=arr_masked.fill_value)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
                 
        # we are looking for the values which are greater than the 95th percentile  
        bin_arr = get_binary_arr(arr_masked_masked[i,:,:], current_perc_arr, logical_operation='gt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        R95p = R95p + bin_arr

        i+=1

#     if not isinstance(arr, numpy.ma.MaskedArray):
#         R95p = R95p.filled(fill_value=arr_masked.fill_value)  

    return R95p


def R99p_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the R99p indice: number of extremely wet days (i.e. days with daily precipitation amount > 99th percentile of daily amount in the base period).
    
    :param arr: daily precipitation flux (liquid form) (e.g. "pr") in mm/s
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 99th percentile of daily precipitation amount at wet days in mm/day
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        

    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''
    R99p = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    pr_thresh = 1                               # precipitation threshold = 1 mm
    
    arr_masked = get_masked_arr(arr, fill_val)  # mm/s
    arr_masked = arr_masked*60*60*24            # mm/day
    
    # we need to check only wet days (i.e. days with RR >= 1 mm)
    # so, we mask all values < 1 mm with the same fill_value
    mask_arr_masked = arr_masked < 1.0 # mask
    arr_masked_masked = numpy.ma.array(arr_masked, mask=mask_arr_masked, fill_value=arr_masked.fill_value)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are greater than the 99th percentile  
        bin_arr = get_binary_arr(arr_masked_masked[i,:,:], current_perc_arr, logical_operation='gt') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        R99p = R99p + bin_arr
        
        i+=1
        
#     if not isinstance(arr, numpy.ma.MaskedArray):
#         R99p = R99p.filled(fill_value=arr_masked.fill_value)    
    
    return R99p


def R75TOT_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the R75TOT indice: precipitation fraction due to moderate wet days (i.e. days with daily precipitation amount > 75th percentile of daily amount in the base period) [%]
    
    :param arr: daily precipitation flux (liquid form) (e.g. "pr") in mm/s
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 75th percentile of daily precipitation amount at wet days in mm/day
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        (if "arr" is numpy.ndarray)
        or numpy.ma.MaskedArray (2D) (if "arr" is numpy.ma.MaskedArray)
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''
    
    pr_thresh = 1                               # precipitation threshold = 1 mm

    # we calculate the numerator (see the formula in the doc): sum of all daily precipitation amounts >= 1.O mm
    numerator = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    arr_masked = get_masked_arr(arr, fill_val)  # mm/s
    arr_masked = arr_masked*60*60*24            # mm/day
    
    # we need to check only wet days (i.e. days with RR >= 1 mm)
    # so, we mask all values < 1 mm with the same fill_value
    mask_arr_masked = arr_masked < 1.0
    arr_masked_masked = numpy.ma.array(arr_masked, mask=mask_arr_masked, fill_value=arr_masked.fill_value)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are greater than the 75th percentile
        # so, we need first to mask all values <= 75th percentile
        mask = get_binary_arr(arr_masked_masked[i,:,:], current_perc_arr, logical_operation='let') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        arr_current_slice_masked = numpy.ma.array(arr_masked_masked[i,:,:], mask=mask, fill_value=0.0) # we mask again the arr_masked_masked 
        arr_current_slice = arr_current_slice_masked.filled() # filled with 0.0 ==> array with daily precipitation amount >= 1.O mm 
        
        numerator = numerator + arr_current_slice # sum of all daily precipitation amounts >= 1.O mm
        
        i+=1
    
#     # we calculate the denominator: all sum for the period
#     denominator = calc_indice.PRCTOT_calculation(arr, fill_val)
#     
#     if isinstance(denominator, numpy.ma.MaskedArray):
#         denominator = denominator.filled(fill_value=-1) # we fill with -1
#         
#     R75TOT = 100*(numerator/denominator)
#     R75TOT[R75TOT<0]=fill_val
#     
#     if isinstance(arr, numpy.ma.MaskedArray):
#         mask_R75TOT = R75TOT==fill_val
#         R75TOT = numpy.ma.array(R75TOT, mask=mask_R75TOT, fill_value=arr.fill_value)
    
    R75TOT = numerator
    
    return R75TOT
    

def R95TOT_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the R95TOT indice: precipitation fraction due to very wet days (i.e. days with daily precipitation amount > 95th percentile of daily amount in the base period) [%]
    
    :param arr: daily precipitation flux (liquid form) (e.g. "pr") in mm/s
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 95th percentile of daily precipitation amount at wet days in mm/day
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        (if "arr" is numpy.ndarray)
        or numpy.ma.MaskedArray (2D) (if "arr" is numpy.ma.MaskedArray)
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''
    
    pr_thresh = 1                               # precipitation threshold = 1 mm

    # we calculate the numerator (see the formula in the doc): sum of all daily precipitation amounts >= 1.O mm
    numerator = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    arr_masked = get_masked_arr(arr, fill_val)  # mm/s
    arr_masked = arr_masked*60*60*24            # mm/day
    
    # we need to check only wet days (i.e. days with RR >= 1 mm)
    # so, we mask all values < 1 mm with the same fill_value
    mask_arr_masked = arr_masked < 1.0
    arr_masked_masked = numpy.ma.array(arr_masked, mask=mask_arr_masked, fill_value=arr_masked.fill_value)
    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
#         # we are looking for the values which are greater than the 95th percentile
#         # so, we need first to mask all values <= 95th percentile
#         mask = get_binary_arr(arr_masked_masked[i,:,:], current_perc_arr, logical_operation='let') # bin_arr is a masked array with fill_value=arr_masked.fill_value
#         arr_current_slice_masked = numpy.ma.array(arr_masked_masked[i,:,:], mask=mask, fill_value=0.0) # we mask again the arr_masked_masked 
#         arr_current_slice = arr_current_slice_masked.filled() # filled with 0.0 ==> array with daily precipitation amount >= 1.O mm 
#       

        print "arr_masked[i,:,:]: "  
        print arr_masked[i,:,:]

        print "arr_masked_masked[i,:,:]: "  
        print arr_masked_masked[i,:,:]
        
        print "current_perc_arr: "
        print current_perc_arr
        # we are looking for the values which are greater than the 95th percentile
        # so, we need first to mask all values <= 95th percentile
        mask = get_binary_arr(arr_masked_masked[i,:,:], current_perc_arr, logical_operation='let') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        
        print "mask: "
        print mask
        
        arr_current_slice_masked = numpy.ma.array(arr_masked_masked[i,:,:], mask=mask, fill_value=0.0) # we mask again the arr_masked_masked 
        
        print "arr_current_slice_masked: "
        print arr_current_slice_masked
        
        arr_current_slice = arr_current_slice_masked.filled() # filled with 0.0 ==> array with daily precipitation amount >= 1.O mm 
        
        print "arr_current_slice: "
        print arr_current_slice
        
        
        numerator = numerator + arr_current_slice # sum of all daily precipitation amounts >= 1.O mm
        
        print "numerator: "
        print numerator
        print "=="
        i+=1
    
#     # we calculate the denominator: all sum for the period
#     denominator = calc_indice.PRCTOT_calculation(arr, fill_val)
#     
#     if isinstance(denominator, numpy.ma.MaskedArray):
#         denominator = denominator.filled(fill_value=-1) # we fill with -1
#         
#     R95TOT = 100*(numerator/denominator)
#     R95TOT[R95TOT<0]=fill_val
#     
#     if isinstance(arr, numpy.ma.MaskedArray):
#         mask_R95TOT = R95TOT==fill_val
#         R95TOT = numpy.ma.array(R95TOT, mask=mask_R95TOT, fill_value=arr.fill_value)
    
    
    R95TOT = numerator
    
    return R95TOT

def R99TOT_calculation(arr, dt_arr, percentile_dict, fill_val=None):
    '''
    Calculate the R99TOT indice: precipitation fraction due to extremely wet days (i.e. days with daily precipitation amount > 99th percentile of daily amount in the base period) [%]
    
    :param arr: daily precipitation flux (liquid form) (e.g. "pr") in mm/s
    :type arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param dt_arr: corresponding time steps vector
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param percentile_dict: 99th percentile of daily precipitation amount at wet days in mm/day
    :type percentile_dict: dict
    :param fill_val: fill value
    :type fill_val: float
    
    :rtype: numpy.ndarray (2D)        (if "arr" is numpy.ndarray)
        or numpy.ma.MaskedArray (2D) (if "arr" is numpy.ma.MaskedArray)
    
    .. warning:: If "arr" is a masked array, the parameter "fill_val" is ignored, because it has no sense in this case.

    '''
    
    pr_thresh = 1                               # precipitation threshold = 1 mm

    # we calculate the numerator (see the formula in the doc): sum of all daily precipitation amounts >= 1.O mm
    numerator = numpy.zeros((arr.shape[1], arr.shape[2]))
    
    arr_masked = get_masked_arr(arr, fill_val)  # mm/s
    arr_masked = arr_masked*60*60*24            # mm/day
    
    # we need to check only wet days (i.e. days with RR >= 1 mm)
    # so, we mask all values < 1 mm with the same fill_value
    mask_arr_masked = arr_masked < 1.0
    arr_masked_masked = numpy.ma.array(arr_masked, mask=mask_arr_masked, fill_value=arr_masked.fill_value)
  
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        current_perc_arr = percentile_dict[m,d]
        
        # we are looking for the values which are greater than the 99th percentile
        # so, we need first to mask all values <= 99th percentile
        mask = get_binary_arr(arr_masked_masked[i,:,:], current_perc_arr, logical_operation='let') # bin_arr is a masked array with fill_value=arr_masked.fill_value
        arr_current_slice_masked = numpy.ma.array(arr_masked_masked[i,:,:], mask=mask, fill_value=0.0) # we mask again the arr_masked_masked 
        arr_current_slice = arr_current_slice_masked.filled() # filled with 0.0 ==> array with daily precipitation amount >= 1.O mm 
        
        numerator = numerator + arr_current_slice # sum of all daily precipitation amounts >= 1.O mm
        
        i+=1
    
#     # we calculate the denominator: all sum for the period
#     denominator = calc_indice.PRCTOT_calculation(arr, fill_val)
#     
#     if isinstance(denominator, numpy.ma.MaskedArray):
#         denominator = denominator.filled(fill_value=-1) # we fill with -1
#         
#     R99TOT = 100*(numerator/denominator)
#     R99TOT[R99TOT<0]=fill_val
#     
#     if isinstance(arr, numpy.ma.MaskedArray):
#         mask_R99TOT = R99TOT==fill_val
#         R99TOT = numpy.ma.array(R99TOT, mask=mask_R99TOT, fill_value=arr.fill_value)
    
    R99TOT = numerator
    
    return R99TOT


def CD_calculation(t_arr, t_25th_percentile_dict, p_arr, p_25th_percentile_dict, dt_arr, fill_val1=None, fill_val2=None):
    '''
    Calculate the CD indice: number of cold and dry days.
    
    :param t_arr: daily mean temperature (e.g. "tas")
    :type t_arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param t_25th_percentile_dict: 25th percentile of daily min temperature
    :type t_25th_percentile_dict: dict
    :param p_arr: daily precipitation amount at wet day (RR >= 1.0 mm) (e.g. "pr") in mm/s
    :type p_arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param p_25th_percentile_dict: 25th percentile of daily precipitation amount at wet days in mm/day
    :type p_25th_percentile_dict: dict
    :param dt_arr: time steps vector corresponding to both input arrays (``t_arr`` and ``dt_arr``) 
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param fill_val1: fill value of t_arr
    :type fill_val1: float
    :param fill_val2: fill value of p_arr
    :type fill_val2: float   
    
    :rtype: numpy.ndarray (2D)        (if ``t_arr`` and ``p_arr`` is numpy.ndarray) or numpy.ma.MaskedArray (2D) (if ``t_arr`` and ``p_arr`` is numpy.ma.MaskedArray)
    
    .. warning:: If "t_arr" and "p_arr" are masked arrays, the parameters "fill_val1" and "fill_val2" are ignored, because they have no sense in this case.
    
    .. note:: Both input array must be the same type.
    
    '''
    # we intitialize the indice array
    CD = numpy.zeros((t_arr.shape[1], t_arr.shape[2]))
        
    
    # 1) we mask both arrays: t_arr and p_arr
    t_arr_masked = get_masked_arr(t_arr, fill_val1)
    p_arr_masked = get_masked_arr(p_arr, fill_val2)

    # 2) p_arr: mm/s ---> mm/day ; we are looking only for wet days (RR > 1 mm), i.e. we mask values < 1 mm
    p_arr_masked = p_arr_masked*60*60*24            # mm/day
    mask_p_arr = p_arr_masked<1.0
    p_arr_masked_masked = numpy.ma.array(p_arr_masked, mask=mask_p_arr) # CHECK !

    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        t_current_perc_arr = t_25th_percentile_dict[m,d]
        p_current_perc_arr = p_25th_percentile_dict[m,d]
        
        # 3) we compare daily mean temperature (t_arr) with its 25th percentile (t_25th_percentile_dict)                    ==> result 1        
        # temperature: we are looking for the values which are less than the 25th percentile  
        t_bin_arr = get_binary_arr(t_arr_masked[i,:,:], t_current_perc_arr, logical_operation='lt') # t_bin_arr is a masked array with fill_value=arr_masked.fill_value    
        
        # 4) we compare  daily precipitation amount at wet day (p_arr) with its 25th percentile (p_25th_percentile_dict)    ==> result 2        
        # precipitation (wet days): we are looking for the values which are less than the 25th percentile
        p_bin_arr = get_binary_arr(p_arr_masked_masked[i,:,:], p_current_perc_arr, logical_operation='lt') # p_bin_arr is a masked array with fill_value=arr_masked.fill_value 
    
        # 5) result 1 AND result 2 ==> indice CD        
        t_bin_arr_AND_p_bin_arr = numpy.logical_and(t_bin_arr, p_bin_arr) # masked array                
        t_bin_arr_AND_p_bin_arr_filled = t_bin_arr_AND_p_bin_arr.filled(fill_value=0)
        
        CD = CD + t_bin_arr_AND_p_bin_arr_filled
        
        #print "CD: \n"    
        #print CD[70:80,70:80]
        #print "========="        
        
        
        i+=1


    #if not isinstance(t_arr, numpy.ma.MaskedArray):
    #    CD = CD.filled(fill_value=t_arr_masked.fill_value)    
    
    return CD


def CW_calculation(t_arr, t_25th_percentile_dict, p_arr, p_75th_percentile_dict, dt_arr, fill_val1=None, fill_val2=None):
    '''
    Calculate the CW indice: number of cold and wet days.
    
    :param t_arr: daily mean temperature (e.g. "tas")
    :type t_arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param t_25th_percentile_dict: 25th percentile of daily min temperature
    :type t_25th_percentile_dict: dict
    :param p_arr: daily precipitation amount at wet day (RR >= 1.0 mm) (e.g. "pr") in mm/s
    :type p_arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param p_75th_percentile_dict: 75th percentile of daily precipitation amount at wet days in mm/day
    :type p_75th_percentile_dict: dict
    :param dt_arr: time steps vector corresponding to both input arrays (``t_arr`` and ``dt_arr``) 
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param fill_val1: fill value of t_arr
    :type fill_val1: float
    :param fill_val2: fill value of p_arr
    :type fill_val2: float 
    
    :rtype: numpy.ndarray (2D)        (if ``t_arr`` and ``p_arr`` is numpy.ndarray) or numpy.ma.MaskedArray (2D) (if ``t_arr`` and ``p_arr`` is numpy.ma.MaskedArray)
    
    .. warning:: If "t_arr" and "p_arr" are masked arrays, the parameters "fill_val1" and "fill_val2" are ignored, because they have no sense in this case.
    
    .. note:: Both input array must be the same type.
    
    '''
    # we intitialize the indice array
    CW = numpy.zeros((t_arr.shape[1], t_arr.shape[2]))
        
    
    # 1) we mask both arrays: t_arr and p_arr
    t_arr_masked = get_masked_arr(t_arr, fill_val1)
    p_arr_masked = get_masked_arr(p_arr, fill_val2)

    # 2) p_arr: mm/s ---> mm/day ; we are looking only for wet days (RR > 1 mm), i.e. we mask values < 1 mm
    p_arr_masked = p_arr_masked*60*60*24            # mm/day
    mask_p_arr = p_arr_masked<1.0
    p_arr_masked_masked = numpy.ma.array(p_arr_masked, mask=mask_p_arr) # CHECK !

    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        t_current_perc_arr = t_25th_percentile_dict[m,d]
        p_current_perc_arr = p_75th_percentile_dict[m,d]
        
        # 3) we compare daily mean temperature (t_arr) with its 25th percentile (t_25th_percentile_dict)                    ==> result 1        
        # temperature: we are looking for the values which are less than the 25th percentile  
        t_bin_arr = get_binary_arr(t_arr_masked[i,:,:], t_current_perc_arr, logical_operation='lt') # t_bin_arr is a masked array with fill_value=arr_masked.fill_value    
        
        # 4) we compare  daily precipitation amount at wet day (p_arr) with its 75th percentile (p_75th_percentile_dict)    ==> result 2        
        # precipitation (wet days): we are looking for the values which are greater than the 75th percentile
        p_bin_arr = get_binary_arr(p_arr_masked_masked[i,:,:], p_current_perc_arr, logical_operation='gt') # p_bin_arr is a masked array with fill_value=arr_masked.fill_value 
    
        # 5) result 1 AND result 2 ==> indice CW        
        t_bin_arr_AND_p_bin_arr = numpy.logical_and(t_bin_arr, p_bin_arr) # masked array                
        t_bin_arr_AND_p_bin_arr_filled = t_bin_arr_AND_p_bin_arr.filled(fill_value=0)
        
        CW = CW + t_bin_arr_AND_p_bin_arr_filled
        
        #print "CW: \n"    
        #print CW[70:80,70:80]
        #print "========="        
        
        
        i+=1


    #if not isinstance(t_arr, numpy.ma.MaskedArray):
    #    CW = CW.filled(fill_value=t_arr_masked.fill_value)    
    
    return CW



def WD_calculation(t_arr, t_75th_percentile_dict, p_arr, p_25th_percentile_dict, dt_arr, fill_val1=None, fill_val2=None):
    '''
    Calculate the WD indice: number of warm and dry days.
    
    :param t_arr: daily mean temperature (e.g. "tas")
    :type t_arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param t_75th_percentile_dict: 75th percentile of daily min temperature
    :type t_75th_percentile_dict: dict
    :param p_arr: daily precipitation amount at wet day (RR >= 1.0 mm) (e.g. "pr") in mm/s
    :type p_arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param p_25th_percentile_dict: 25th percentile of daily precipitation amount at wet days in mm/day
    :type p_25th_percentile_dict: dict
    :param dt_arr: time steps vector corresponding to both input arrays (``t_arr`` and ``dt_arr``) 
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param fill_val1: fill value of t_arr
    :type fill_val1: float
    :param fill_val2: fill value of p_arr
    :type fill_val2: float 
    
    :rtype: numpy.ndarray (2D)        (if ``t_arr`` and ``p_arr`` is numpy.ndarray) or numpy.ma.MaskedArray (2D) (if ``t_arr`` and ``p_arr`` is numpy.ma.MaskedArray)
    
    .. warning:: If "t_arr" and "p_arr" are masked arrays, the parameters "fill_val1" and "fill_val2" are ignored, because they have no sense in this case.
    
    .. note:: Both input array must be the same type.
    
    '''
    # we intitialize the indice array
    WD = numpy.zeros((t_arr.shape[1], t_arr.shape[2]))
        
    
    # 1) we mask both arrays: t_arr and p_arr
    t_arr_masked = get_masked_arr(t_arr, fill_val1)
    p_arr_masked = get_masked_arr(p_arr, fill_val2)

    # 2) p_arr: mm/s ---> mm/day ; we are looking only for wet days (RR > 1 mm), i.e. we mask values < 1 mm
    p_arr_masked = p_arr_masked*60*60*24            # mm/day
    mask_p_arr = p_arr_masked<1.0
    p_arr_masked_masked = numpy.ma.array(p_arr_masked, mask=mask_p_arr) # CHECK !

    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        t_current_perc_arr = t_75th_percentile_dict[m,d]
        p_current_perc_arr = p_25th_percentile_dict[m,d]
        
        # 3) we compare daily mean temperature (t_arr) with its 75th percentile (t_75th_percentile_dict)                    ==> result 1        
        # temperature: we are looking for the values which are greater than the 75th percentile  
        t_bin_arr = get_binary_arr(t_arr_masked[i,:,:], t_current_perc_arr, logical_operation='gt') # t_bin_arr is a masked array with fill_value=arr_masked.fill_value    
        
        # 4) we compare  daily precipitation amount at wet day (p_arr) with its 25th percentile (p_25th_percentile_dict)    ==> result 2        
        # precipitation (wet days): we are looking for the values which are less than the 25th percentile
        p_bin_arr = get_binary_arr(p_arr_masked_masked[i,:,:], p_current_perc_arr, logical_operation='lt') # p_bin_arr is a masked array with fill_value=arr_masked.fill_value 
    
        # 5) result 1 AND result 2 ==> indice WD        
        t_bin_arr_AND_p_bin_arr = numpy.logical_and(t_bin_arr, p_bin_arr) # masked array                
        t_bin_arr_AND_p_bin_arr_filled = t_bin_arr_AND_p_bin_arr.filled(fill_value=0)
        
        WD = WD + t_bin_arr_AND_p_bin_arr_filled
        
        #print "WD: \n"    
        #print WD[70:80,70:80]
        #print "========="        
        
        
        i+=1


    #if not isinstance(t_arr, numpy.ma.MaskedArray):
    #    WD = WD.filled(fill_value=t_arr_masked.fill_value)    
    
    return WD


def WW_calculation(t_arr, t_75th_percentile_dict, p_arr, p_75th_percentile_dict, dt_arr, fill_val1=None, fill_val2=None):
    '''
    Calculate the WW indice: number of warm and wet days.
    
    :param t_arr: daily mean temperature (e.g. "tas")
    :type t_arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param t_75th_percentile_dict: 75th percentile of daily min temperature
    :type t_75th_percentile_dict: dict
    :param p_arr: daily precipitation amount at wet day (RR >= 1.0 mm) (e.g. "pr") in mm/s
    :type p_arr: numpy.ndarray (3D) or numpy.ma.MaskedArray (3D)
    :param p_75th_percentile_dict: 75th percentile of daily precipitation amount at wet days in mm/day
    :type p_75th_percentile_dict: dict
    :param dt_arr: time steps vector corresponding to both input arrays (``t_arr`` and ``dt_arr``) 
    :type dt_arr: numpy.ndarray (1D) of datetime objects
    :param fill_val1: fill value of t_arr
    :type fill_val1: float
    :param fill_val2: fill value of p_arr
    :type fill_val2: float 
    
    :rtype: numpy.ndarray (2D)        (if ``t_arr`` and ``p_arr`` is numpy.ndarray) or numpy.ma.MaskedArray (2D) (if ``t_arr`` and ``p_arr`` is numpy.ma.MaskedArray)
    
    .. warning:: If "t_arr" and "p_arr" are masked arrays, the parameters "fill_val1" and "fill_val2" are ignored, because they have no sense in this case.
    
    .. note:: Both input array must be the same type.
    
    '''
    # we intitialize the indice array
    WW = numpy.zeros((t_arr.shape[1], t_arr.shape[2]))
        
    
    # 1) we mask both arrays: t_arr and p_arr
    t_arr_masked = get_masked_arr(t_arr, fill_val1)
    p_arr_masked = get_masked_arr(p_arr, fill_val2)

    # 2) p_arr: mm/s ---> mm/day ; we are looking only for wet days (RR > 1 mm), i.e. we mask values < 1 mm
    p_arr_masked = p_arr_masked*60*60*24            # mm/day
    mask_p_arr = p_arr_masked<1.0
    p_arr_masked_masked = numpy.ma.array(p_arr_masked, mask=mask_p_arr) # CHECK !

    
    i=0
    for dt in dt_arr:
        
        # current calendar day
        m = dt.month
        d = dt.day

        t_current_perc_arr = t_75th_percentile_dict[m,d]
        p_current_perc_arr = p_75th_percentile_dict[m,d]
        
        # 3) we compare daily mean temperature (t_arr) with its 75th percentile (t_75th_percentile_dict)                    ==> result 1        
        # temperature: we are looking for the values which are greater than the 75th percentile  
        t_bin_arr = get_binary_arr(t_arr_masked[i,:,:], t_current_perc_arr, logical_operation='gt') # t_bin_arr is a masked array with fill_value=arr_masked.fill_value    
        
        # 4) we compare  daily precipitation amount at wet day (p_arr) with its 75th percentile (p_75th_percentile_dict)    ==> result 2        
        # precipitation (wet days): we are looking for the values which are greater than the 75th percentile
        p_bin_arr = get_binary_arr(p_arr_masked_masked[i,:,:], p_current_perc_arr, logical_operation='gt') # p_bin_arr is a masked array with fill_value=arr_masked.fill_value 
    
        # 5) result 1 AND result 2 ==> indice WW        
        t_bin_arr_AND_p_bin_arr = numpy.logical_and(t_bin_arr, p_bin_arr) # masked array                
        t_bin_arr_AND_p_bin_arr_filled = t_bin_arr_AND_p_bin_arr.filled(fill_value=0)
        
        WW = WW + t_bin_arr_AND_p_bin_arr_filled
        
        #print "WW: \n"    
        #print WW[70:80,70:80]
        #print "========="        
        
        
        i+=1


    #if not isinstance(t_arr, numpy.ma.MaskedArray):
    #    WW = WW.filled(fill_value=t_arr_masked.fill_value)    
    
    return WW