### MySql 笔记 
---
#### 计算数据文件，索引文件大小SQL
```
SELECT
    'table_name',
    CONCAT(FORMAT(SUM(data_length) / 1024 / 1024,2),'M') AS dbdata_size,
    CONCAT(FORMAT(SUM(index_length) / 1024 / 1024,2),'M') AS dbindex_size,
    CONCAT(FORMAT(SUM(data_length + index_length) / 1024 / 1024 / 1024,2),'G') AS `db_size(G)`,
    AVG_ROW_LENGTH, table_rows, update_time
FROM
    information_schema.tables
WHERE
    table_schema = DATABASE() and table_name='xxx';
```

#### 文本体积

```
      Type | Maximum length
-----------+-------------------------------------
  TINYTEXT |           255 (2 8−1) bytes
      TEXT |        65,535 (216−1) bytes = 64 KiB
MEDIUMTEXT |    16,777,215 (224−1) bytes = 16 MiB
  LONGTEXT | 4,294,967,295 (232−1) bytes =  4 GiB
```

#### 用户和权限
```
create user zhangsan identified by 'zhangsan';
grant all privileges on zhangsanDb.* to zhangsan@'%' identified by 'zhangsan';
flush privileges;
show grants for 'zhangsan';
```


#### 库/表导出/入
```
mysqldump --host={host} -u{user} -p{password} --databases {database} --tables {tables} --where="{where}" --skip-lock-tables --result-file={result}.sql

mycli -h{host} -u{user} -D{database} -p{password} < {result}.sql
```
