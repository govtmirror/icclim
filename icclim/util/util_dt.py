
from netcdftime import utime
from datetime import datetime, timedelta
#from netCDF4 import num2date, date2num, Dataset, MFDataset
from netCDF4 import Dataset
import numpy


def get_list_dates_from_nc(nc, type_dates):
    
    '''
    Returns list of dates from NetCDF dataset.
    
    :param nc: NetCDF dataset
    :type nc: netCDF4.Dataset
    :param type_dates: type of dates ('dt' for datetime objects, 'num' for float objects) 
    :type type_dates: str

    :rtype: list of datetime/float 
    
    '''
    
    ncVar_values_time = nc.variables['time']
    time_units = var_time.units # str (ex.: 'days since 1850-01-01 00:00:00')
    try:
       time_calend = var_time.calendar # str (ex.: 'standard'/'gregorian'/...)
    except:
        time_calend = 'gregorian'
    
    if type_dates == 'num':
        arr_dt = var_time[:]
        list_dt = arr_dt.tolist() # numpy array -> list
        
    if type_dates == 'dt':
        t = utime(time_units, time_calend) # <netcdftime.utime instance at 0xecae18>
        arr_dt = t.num2date(var_time[:]) # arr_dt: numpy array of dates datetime; var_time[:]: time values (ex.: [49323.5, 49353, 49382.5, ...])
        list_dt = arr_dt.tolist() # numpy array -> list
    del arr_dt
    
    return list_dt



def get_list_dates(ifile, type_dates):
    
    '''
    Returns list of dates from one file.
    
    :param ifile: NetCDF file
    :type ifile: str
    :param type_dates: type of dates ('dt' for datetime objects, 'num' for float objects) 
    :type type_dates: str

    :rtype: list of datetime/float 
    
    '''
    
    nc = Dataset(ifile, 'r')
    var_time = nc.variables['time']
    time_units = var_time.units # str (ex.: 'days since 1850-01-01 00:00:00')
    try:
       time_calend = var_time.calendar # str (ex.: 'standard'/'gregorian'/...)
    except:
        time_calend = 'gregorian'
    
    
    if type_dates == 'num':
        arr_dt = var_time[:]
        list_dt = arr_dt.tolist() # numpy array -> list
        
    if type_dates == 'dt':
        t = utime(time_units, time_calend) # <netcdftime.utime instance at 0xecae18>
        arr_dt = t.num2date(var_time[:]) # arr_dt: numpy array of dates datetime; var_time[:]: time values (ex.: [49323.5, 49353, 49382.5, ...])
        list_dt = arr_dt.tolist() # numpy array -> list
    del arr_dt
    
    nc.close()
    
    return list_dt


def get_list_dates2(ifile_list, type_dates):
    
    '''
    Returns list of dates from a list of files.
    
    :param ifile_list: list of NetCDF files
    :type ifile: list of str
    :param type_dates: type of dates ('dt' for datetime objects, 'num' for float objects) 
    :type type_dates: str

    :rtype: list of datetime/float 
    
    '''
    
    list_dates_glob = []
    for filename in ifile_list:
        list_dates_current = get_list_dates(filename, type_dates)
        list_dates_glob = list_dates_glob + list_dates_current
    list_dates_glob.sort()
    
    return list_dates_glob


def date2num(dt, calend, units):   
    '''
    Converts datetime object to numerical date.    
    
    :param dt: datetime object
    :type dt: datetime.datetime object
    :param calend: calendar attribute of variable "time" in netCDF file
    :type calend: str
    :param units: units of variable "time" in netCDF file
    :type units: str
    
    :rtype: float
    '''
    t = utime(units, calend)
    dt_num = t.date2num(dt)
    return dt_num


def num2date(num, calend, units):
    '''
    Converts numerical date to datetime object.    
    
    :param num: numerical date
    :type num: float
    :param calend: calendar attribute of variable "time" in netCDF file
    :type calend: str
    :param units: units of variable "time" in netCDF file
    :type units: str
    
    :rtype: datetime.datetime object
    '''   
    t = utime(units, calend) 
    dt = t.num2date(num) 
    return dt


def get_time_range(files, temporal_var_name='time'):
    
    '''
    :param files: netCDF file(s) (including OPeNDAP URL(s))
    :type files: list of str
    
    :param temporal_var_name: name of temporal variable from netCDF file (default: "time")
    :type temporal_var_name: str
    
    :rtype
    
    
    Returns a time range: a list two datetime objects: [begin, end], where "begin" is the first date, and "end" is the last.
    '''
    
    nc = Dataset(files[0],'r')
    time = nc.variables[temporal_var_name]
    
    try:
        calend = time.calendar
    except:
        calend = 'gregorian'
    
    units = time.units
    
    nc.close()
    
    time_arr = numpy.array([])
    for f in files:
        nc = Dataset(f, 'r')
        time_arr_f = nc.variables[temporal_var_name][:]
        time_arr = numpy.concatenate([time_arr, time_arr_f])       
        nc.close()
    
    begin_num = min(time_arr)
    end_num = max(time_arr)
        
    del time_arr
    
    begin_dt = num2date(begin_num, calend, units)
    end_dt = num2date(end_num, calend, units)
    
    return [begin_dt, end_dt]

def get_year_list(dt_arr):
    '''
    Just to get a list of all years conteining in time steps vector (dt_arr).
    '''

    year_list = []
    for dt in dt_arr:
        year_list.append(dt.year)
        
    year_list = list(set(year_list))
    
    return year_list


def adjust_time_range(time_range, dt):
    '''
    Adjust the ``time_range`` by setting hour value to datetime.datetime objects.
    
    :param time_range: time range selected by user   
    :type time_range: list of two datetime.datetime objects
    
    :param dt: one datetime step of input datetime vector
    :type dt: datetime.datetime object
    
    :rtype: list of two datetime.datetime objects
    
    WHY:
    if input time steps vector is from 1990-01-01 12:00 to 2000-12-31 12:00,
    and user's time_range is [datetime.datetime(1900, 1, 1), datetime.datetime(1905, 12, 31)],
    i.e. [datetime.datetime(1900, 1, 1, 0, 0), datetime.datetime(1905, 12, 31, 0, 0)],
    it will be not included in the input time steps (there will be the error message "The time range is not included in the input time steps array.").
    Thus, this function will adjust the hour of the user's time_range: [datetime.datetime(1900, 1, 1, 12, 0), datetime.datetime(1905, 12, 31, 12, 0)]

    '''
    
    hour = dt.hour
    time_range_begin = datetime(time_range[0].year, time_range[0].month, time_range[0].day, dt.hour)
    time_range_end = datetime(time_range[1].year, time_range[1].month, time_range[1].day, dt.hour)
    
    return [time_range_begin, time_range_end]


def get_indices_subset(dt_arr, time_range):
    '''
    Returns indices for time subset.
    
    :param dt_arr: time steps vector
    :type dt_arr: numpy.ndarray of datetime objects
    :param time_range: time range
    :type time_range: [datetime1, datetime2]
    
    '''
    
    dt1 = time_range[0]
    dt2 = time_range[1]
   
    
    if dt1 >= dt_arr[0] and dt2 <= dt_arr[-1]:

        mask_dt_arr = numpy.logical_or(dt_arr<dt1, dt_arr>dt2)
        
        indices_non_masked = numpy.where(mask_dt_arr==False)[0]
       
        return indices_non_masked
        
    else:    
        print 'The time range is not included in the input time steps array.'
        sys.exit()