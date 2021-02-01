#!/usr/bin/env python
# -*- coding: utf-8 -*-

from contextlib import contextmanager
from typing import List

import csv
import pymysql

DB_CFG = {
    "host": "xx.xx.xx.xx",
    "port": 3306,
    "user": "xxx",
    "password": "password",
    "db": "xxx",
}


def group_by(elems: List[dict], key: any) -> dict:
    res = {}
    for elem in elems:
        k = elem[key]
        res.setdefault(k, [])
        res[k].append(elem)

    return res

# -------------- DB ---------------

@contextmanager
def connect_db():
    conn = None
    try:
        conn = pymysql.connect(**DB_CFG)
        yield conn
    finally:
        if conn:
            conn.commit()
            conn.close()



def get_all(cz) -> List[dict]:
    names = [d[0] for d in cz.description]
    return [dict(zip(names, row)) for row in cz.fetchall()]


def get_one(cz):
    names = [d[0] for d in cz.description]
    return dict(zip(names, cz.fetchone()))
