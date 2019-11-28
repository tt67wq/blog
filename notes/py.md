## python 相关
---

### utils合集

```
import pymysql
import contextlib
import csv
import time


def connect_mysql(config):
    return pymysql.connect(**config)


@contextlib.contextmanager
def get_conn(config):
    conn = None
    try:
        conn = connect_mysql(config)
        yield conn
    finally:
        if conn:
            conn.close()


def write2csv(filename, headers, rows):
    with open(filename, 'w') as f:
        f_csv = csv.DictWriter(f, headers)
        f_csv.writeheader()
        f_csv.writerows(rows)


# 把时间戳转成字符串形式
def timestamp_toString(sp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(sp))

```