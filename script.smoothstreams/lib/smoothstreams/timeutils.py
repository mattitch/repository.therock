# -*- coding: utf-8 -*-
#
# With modified code originally by spline

from compat import datetime, timedelta_total_seconds
import time
import pytz
import tzlocal

LOCAL_TIMEZONE = None
TIMEZONE_OFFSET = 0

def setLocalTimezone(from_offset=None):
    global LOCAL_TIMEZONE
    global TIMEZONE_OFFSET
    if from_offset is not None:
        if from_offset == 0:
            LOCAL_TIMEZONE = pytz.UTC
        else:
            LOCAL_TIMEZONE = pytz.FixedOffset(from_offset)
    else:
        try:
            LOCAL_TIMEZONE = tzlocal.get_localzone()
        except:
            try:
                from dateutil.tz import tzlocal
                LOCAL_TIMEZONE = tzlocal()
            except:
                from compat import timezone_guess
                LOCAL_TIMEZONE = timezone_guess(int(timedelta_total_seconds(datetime.datetime.now() - datetime.datetime.utcnow())))

    TIMEZONE_OFFSET = int(round(time.mktime(datetime.datetime.now(tz=LOCAL_TIMEZONE).timetuple()) - time.mktime(datetime.datetime.now().timetuple())))

setLocalTimezone()

UTC_EPOCH = datetime.datetime(1970,1,1).replace(tzinfo=pytz.UTC)
LOCAL_EPOCH = datetime.datetime(1970,1,1).replace(tzinfo=LOCAL_TIMEZONE)

def UTCOffset():
    return int(timedelta_total_seconds((datetime.datetime.now() - datetime.datetime.utcnow()))/60)

def nowLocalTimestamp():
    now = datetime.datetime.now()
    return int(time.mktime(now.timetuple())) - TIMEZONE_OFFSET

def timezoneOffsetMinutes():
    return int(round(TIMEZONE_OFFSET/60.0))

def startOfDayLocalTimestamp():
    sod = startOfDayLocal()
    return int(time.mktime(sod.timetuple())) - TIMEZONE_OFFSET

def startOfDayLocal():
    now = datetime.datetime.now()
    sod = datetime.datetime(year=now.year,month=now.month,day=now.day)
    return sod

def timeInDayLocalSeconds():
    return int(nowLocalTimestamp() - startOfDayLocalTimestamp())

def nowLocal():
    return datetime.datetime.now()

def matchMinusOne(m):
    return str(int(m.group(0)) -1)

def fixWrongYear(year_string):
    import re
    return re.sub('\d\d\d\d',matchMinusOne,year_string,1)

def convertStringToUTCTimestamp(date_str):
    """Takes an XMLTV datetime string and converts it into epoch seconds (UTC)."""

    # returns a UTC datetime object based on offset of programs.
    if date_str.endswith('-0500'):  # conditional XMLTV vs JSONTV
        date_str_notz = date_str[:-6]  # strips -0500 offset.
    else:  # for JSONTV, just copy the variable.
        date_str_notz = date_str
    # two diff formats here. lets use a try/except.
    try:  # new JSONTV: '2014-10-24 00:00:00'
        dtobj = datetime.datetime.strptime(date_str_notz, '%Y-%m-%d %H:%M:%S')
    except:
        try:  # XMLTV.
            dtobj = datetime.datetime.strptime(date_str_notz, '%Y%m%d%H%M%S')  # create dtobj w/str.
        except Exception as e:
            print "ERROR: I could not parse date_str :: {0} :: {1}".format(date_str, e)
    dt = pytz.timezone("US/Eastern").localize(dtobj)  # localize since times expressed in eastern.
    utc_dt = pytz.utc.normalize(dt.astimezone(pytz.utc))  # convert to UTC, object is aware.
    # return "epoch seconds" from UTC.
    secs = timedelta_total_seconds(utc_dt - UTC_EPOCH)
    return int(secs)

def durationString(start, end):
    """Returns a relative time based on stop-start (duration) time."""

    seconds = end-start  # first math.
    seconds = long(round(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    minutes = long(minutes)
    hours = long(hours)
    days = long(days)
    # start to prepare output.
    duration = []
    if days > 0:
        duration.append('%dd' % days)
    if hours > 0:
        duration.append('%dh' % hours)
    if minutes > 0:
        duration.append('%dm' % minutes)
    if seconds > 0:
        duration.append('%ds' % seconds)
    # return w/o any spaces. 1m, 2h30m, etc.
    return ''.join(duration)

