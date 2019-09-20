#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# author: wq
# description: ""

import os
import os.path
import time
import datetime

FILE_DIR = "/data/logs/apps/"


# 注意这里的time_diff 为天数
def file_filter(files, time_diff):
    list = []
    for filename in files:
        date = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
        now = datetime.datetime.now()
        if (now - date).days > time_diff:
            if os.path.exists(filename):
                list.append(filename)

    return list


def catch_file(dir, fmt):
    list = []
    items = os.listdir(dir)
    for item in items:
        if os.path.isdir(dir + item):
            list.extend(catch_file(dir + item + "/", fmt))
        elif item.endswith(".{}".format(fmt)):
            list.append(dir + item)
    return list


def main():
    print('Script is running...')

    while True:
        list = catch_file(FILE_DIR, "log")
        files2rm = file_filter(list, 2 * 30)
        print("total file num: ", len(list))
        print("need rm file num: ", len(files2rm))
        for file in files2rm:
            print("removing {}".format(file))
            os.remove(file)

        time.sleep(5)

    print("never arrive...")


if __name__ == '__main__':
    main()
