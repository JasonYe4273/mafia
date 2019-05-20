# -*- coding: utf-8 -*-
"""
Created on Tue May  7 13:01:13 2019

@author: krist
"""


def DMS_to_dec(loc):
    '''
    takes a loc in DMS and converts to decimal
    assumes format "intdint'int" letter" as a string
    '''
    if type(loc) == 'list':
        return loc[0] + loc[1]/60 + loc[2]/3600
#    otherwise, assumes you have a string
    deg, other = loc.split('d')
    m, sec = other.split("'")
    sec = int(sec[:2])
    m = int(m)
    deg = int(deg)
    if loc[-1] == 'N' or loc[-1] == 'E':
        sign = 1
    else:
        sign = -1
    return (deg + m/60 + sec/3600)*sign
     
def dec_to_DMS(loc,direction,return_kind = 'li'):
    '''
    takes a loc in decimal as a float and returns it in DMS
    direction: either lat or lon
    returns as a list if return_kind is li
    returns as a str in format for DMS_to_dec otherwise
    '''
    if loc >= 0:
        if direction == 'lat':
            sign = 'N'
        else:
            sign = 'E'
    else:
        if direction == 'lat':
            sign = 'S'
        else:
            sign = 'W'
    loc = abs(loc)
    deg = int(loc)
    m = int((loc-deg)*60)
    sec = int((loc-deg-m/60)*3600)
    if return_kind == 'li':
        return [deg,m,sec,sign]
    return '''{}d{}'{}" {}'''.format(deg,m,sec,sign)