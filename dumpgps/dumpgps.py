import os
from datetime import datetime, timedelta
from math import atan2, cos, radians, sin, sqrt

import piexif


def files_in_current_dir(dir_name):
    """list all files in a dir.

    Args:
        dir_name (str): path to a dir

    Returns:
        list: files in a dir.
    """
    return [os.path.abspath(os.path.join(dir_name, x))
            for x in os.listdir(dir_name)
            if os.path.isfile(os.path.abspath(os.path.join(dir_name, x)))]


def files_in_subdirs(dir_name):
    """list all files in a dir with all sub dirs.

    Args:
        dir_name (str): path to a dir

    Returns:
        list: files in a dir.
    """
    ret = []
    for r, _, f in os.walk(dir_name):
        for file in f:
            ret.append(os.path.abspath(os.path.join(r, file)))
    return ret


def list_files(dir_name, file_name, recursive=False):
    if recursive:
        files = files_in_subdirs(dir_name)
    else:
        files = files_in_current_dir(dir_name)

    gps_info = []
    for i in files:
        try:
            gps_info.append(exif(i))
        except piexif.InvalidImageDataError:
            pass

    gps_info = distance_threashold(sorted(gps_info), 10)
    flat_list = [item for sublist in gps_info for item in sublist]
    save(flat_list, file_name)


def save(gps_info, file_name):
    with open(file_name, 'w') as f:
        counter = 1
        header = 'INDEX,TAG,DATE,TIME,LATITUDE N/S,'
        header += 'LONGITUDE E/W,HEIGHT,SPEED,HEADING,VOX\n'
        f.write(header)
        for i in gps_info:
            f.write('{},T,{},{},{},{},{},0,0\n'.format(counter, i[0][0],
                                                       i[0][1], i[1][0],
                                                       i[1][1], i[1][2]))
            counter += 1


def distance_threashold(gps_info, km):
    if len(gps_info) == 1:
        gps_info = [gps_info[0], gps_info[0]]
        return gps_info

    start = 0
    end = 1
    ret = []
    while end < len(gps_info):
        if distance(gps_info[end - 1][1], gps_info[end][1]) < km:
            end += 1
        else:
            ret.append(gps_info[start:end])
            start = end
            end += 1
    ret.append(gps_info[start:end])

    for index, item in enumerate(ret):
        if len(item) == 1:
            new_record = item[0]
            new_time = datetime.strptime(new_record[0][0] + new_record[0][1],
                                         '%y%m%d%H%M%S')
            new_time += timedelta(seconds=1)
            new_record = ((new_time.strftime('%y%m%d'),
                           new_time.strftime('%H%M%S')), new_record[1])
            ret[index] = [item[0], new_record]
    return ret


def distance(loc1, loc2):
    """calc distance between two locations.

       each location store in a tuple as (latitude, longitude, altitude),
       in which each element is a string.

       latitude & longitude follow this format XXX.XXXXXXY,
       where X are numbers, Y is either S and N or W and E respectively

       altitude is a integer

    Args:
        loc1 (tuple): first location
        loc2 (tuple): second location

    Returns:
        float: distance in km
    """
    R = 6371
    latitude1 = float(loc1[0][:-1])
    if loc1[0][-1] == 'S':
        latitude1 = -latitude1
    longitude1 = float(loc1[1][:-1])
    if loc1[1][-1] == 'W':
        longitude1 = -longitude1

    latitude2 = float(loc2[0][:-1])
    if loc2[0][-1] == 'S':
        latitude2 = -latitude2
    longitude2 = float(loc2[1][:-1])
    if loc2[1][-1] == 'W':
        longitude2 = -longitude2

    latitude1 = radians(latitude1)
    longitude1 = radians(longitude1)
    latitude2 = radians(latitude2)
    longitude2 = radians(longitude2)

    a = (sin((latitude2 - latitude1) / 2) ** 2 +
         cos(latitude1) * cos(latitude2) *
         sin((longitude2 - longitude1) / 2) ** 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    d = R * c
    return d


def exif(img_filename):
    exif_dict = piexif.load(img_filename)
    gps_info = exif_dict['GPS']
    if 2 not in gps_info or 4 not in gps_info:
        raise piexif.InvalidImageDataError

    shot_time = get_photo_time(img_filename)
    return shot_time, convert_gps2decimal(gps_info)


def get_photo_time(img_filename):
    exif_dict = piexif.load(img_filename)
    try:
        exif_ifd = exif_dict['Exif']
        shot_time = min(exif_ifd[36867], exif_ifd[36868]).decode('ascii')
        ret = datetime.strptime(shot_time, '%Y:%m:%d %H:%M:%S')
    except piexif.InvalidImageDataError:
        try:
            gps_info = exif_dict['GPS']
            ret = convert_gpstime2UTC(gps_info)
        except KeyError:
            ret = guess_shot_time(img_filename)
    return ret.strftime('%y%m%d'), ret.strftime('%H%M%S')


def guess_shot_time(img_filename):
    file_time = os.stat(img_filename)
    earliest = min(file_time.st_ctime, file_time.st_mtime, file_time.st_atime)
    return datetime.fromtimestamp(earliest)


def convert_gps2decimal(gps_info):
    GPSLatitude = gps_info[2]
    latitude = (GPSLatitude[0][0] / GPSLatitude[0][1] +
                GPSLatitude[1][0] / 60 / GPSLatitude[1][1] +
                GPSLatitude[2][0] / 3600 / GPSLatitude[2][1])
    latitude = '{:f}'.format(latitude) + gps_info[1].decode('ascii')

    GPSLongitude = gps_info[4]
    longitude = (GPSLongitude[0][0] / GPSLongitude[0][1] +
                 GPSLongitude[1][0] / 60 / GPSLongitude[1][1] +
                 GPSLongitude[2][0] / 3600 / GPSLongitude[2][1])
    longitude = '{:f}'.format(longitude) + gps_info[3].decode('ascii')

    if 6 in gps_info:
        altitude = '{:.0f}'.format(gps_info[6][0] / gps_info[6][1])
    else:
        altitude = 0
    return (latitude, longitude, altitude)


def convert_gpstime2UTC(gps_info):
    ret = datetime.strptime(gps_info[29].decode('ascii'), '%Y:%m:%d')
    hour = gps_info[7][0][0]
    minute = gps_info[7][1][0]
    second = round(gps_info[7][2][0] / gps_info[7][2][1])
    ret = ret.replace(hour=hour, minute=minute, second=second)
    return ret
