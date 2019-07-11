### mysql 笔记
---
#### 计算数据文件，索引文件大小SQL
```
SELECT    table_name,   CONCAT(FORMAT(SUM(data_length) / 1024 / 1024,2),'M') AS dbdata_size,   CONCAT(FORMAT(SUM(index_length) / 1024 / 1024,2),'M') AS dbindex_size,   CONCAT(FORMAT(SUM(data_length + index_length) / 1024 / 1024 / 1024,2),'G') AS `db_size(G)`,   AVG_ROW_LENGTH,table_rows,update_time FROM   information_schema.tables WHERE table_schema = DATABASE() and table_name='xxx';
```