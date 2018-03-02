# -*- coding: utf-8 -*-
import time, math, re
import datetime
import pytz
try:
    datetime.timedelta().total_seconds()
except:
    #Fix for missing total_seconds() for python pre 2.7
    class new_timedelta(datetime.timedelta):
        def total_seconds(self):
            return timedelta_total_seconds(self)
    datetime.timedelta = new_timedelta

try:
    datetime.datetime.strptime('0','%H')
except TypeError:
    #Fix for datetime issues with XBMC/Kodi
    class new_datetime(datetime.datetime):
        @classmethod
        def strptime(cls,dstring,dformat):
            return datetime.datetime(*(time.strptime(dstring, dformat)[0:6]))

    datetime.datetime = new_datetime

def timedelta_total_seconds(td):
    try:
        return td.total_seconds()
    except:
        return ((float(td.seconds) + float(td.days) * 24 * 3600) * 10**6) / 10**6

def timezone_offset_check(tz_offset, timezones):
    timezone = ''
    for tz in timezones:
        x = datetime.datetime.now(pytz.timezone(tz)).strftime('%z')
        y = divmod(int(x), 100)
        if (math.fabs(y[0]) > 0) :
            offset = (y[0] * 3600) + (y[1] * 60 * y[0]/math.fabs(y[0]))
        else :
            offset = 0
        if (offset == tz_offset):
            timezone = tz
            break;

    return timezone

def timezone_guess(tz_offset):
    options = {'canada' : [], 'us' : [], 'rest' : []}
    for i in range(len(pytz.all_timezones)):
        zone = pytz.all_timezones[i]

        #sort timezone by canada, us, rest of the world
        if (re.search('^Canada', zone)):
            options['canada'].append(zone)
        elif (re.search('^US', zone)):
            options['us'].append(zone)
        else:
            options['rest'].append(zone)

    timezone = timezone_offset_check(tz_offset, options['us'])
    if (timezone != ''):
        return pytz.timezone(timezone)

    timezone = timezone_offset_check(tz_offset, options['canada'])
    if (timezone != ''):
        return pytz.timezone(timezone)

    timezone = timezone_offset_check(tz_offset, options['rest'])
    if (timezone != ''):
        return pytz.timezone(timezone)

    return pytz.FixedOffset(tz_offset/60)