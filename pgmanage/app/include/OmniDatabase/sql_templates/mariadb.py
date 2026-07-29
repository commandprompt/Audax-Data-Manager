from string import Template

TEMPLATES = {
    "create_role": Template(
        """CREATE USER name
-- IDENTIFIED BY password
-- REQUIRE NONE
-- REQUIRE SSL
-- REQUIRE X509
-- REQUIRE CIPHER 'cipher'
-- REQUIRE ISSUER 'issuer'
-- REQUIRE SUBJECT 'subject'
-- WITH MAX_QUERIES_PER_HOUR count
-- WITH MAX_UPDATES_PER_HOUR count
-- WITH MAX_CONNECTIONS_PER_HOUR count
-- WITH MAX_USER_CONNECTIONS count
-- PASSWORD EXPIRE
-- ACCOUNT { LOCK | UNLOCK }
"""
    ),
    "alter_role": Template(
        """ALTER USER #role_name#
-- IDENTIFIED BY password
-- REQUIRE NONE
-- REQUIRE SSL
-- REQUIRE X509
-- REQUIRE CIPHER 'cipher'
-- REQUIRE ISSUER 'issuer'
-- REQUIRE SUBJECT 'subject'
-- WITH MAX_QUERIES_PER_HOUR count
-- WITH MAX_UPDATES_PER_HOUR count
-- WITH MAX_CONNECTIONS_PER_HOUR count
-- WITH MAX_USER_CONNECTIONS count
-- PASSWORD EXPIRE
-- ACCOUNT { LOCK | UNLOCK }
-- RENAME USER #role_name# TO new_name
-- SET PASSWORD FOR #role_name# = password
"""
    ),
    "drop_role": Template("DROP USER #role_name#"),
    "create_database": Template(
        """CREATE DATABASE name
-- CHARACTER SET charset
-- COLLATE collate
"""
    ),
    "alter_database": Template(
        """ALTER DATABASE #database_name#
-- CHARACTER SET charset
-- COLLATE collate
"""
    ),
    "drop_database": Template("DROP DATABASE #database_name#"),
    "create_sequence": Template(
        """CREATE SEQUENCE #schema_name#.name
--INCREMENT BY increment
--MINVALUE minvalue | NOMINVALUE
--MAXVALUE maxvalue | NOMAXVALUE
--START WITH start
--CACHE cache | NOCACHE
--CYCLE | NOCYCLE
"""
    ),
    "alter_sequence": Template(
        """ALTER SEQUENCE #sequence_name#
--INCREMENT BY increment
--MINVALUE minvalue | NOMINVALUE
--MAXVALUE maxvalue | NOMAXVALUE
--START WITH start
--CACHE cache | NOCACHE
--CYCLE | NOCYCLE
--RESTART WITH restart
"""
    ),
    "drop_sequence": Template("DROP SEQUENCE #sequence_name#"),
    "create_function": Template(
        """CREATE FUNCTION #schema_name#.name
(
-- argname argtype
)
RETURNS rettype
BEGIN
-- DECLARE variables
-- definition
-- RETURN variable | value
END;
"""
    ),
    "drop_function": Template("DROP FUNCTION #function_name#"),
    "create_procedure": Template(
        """CREATE PROCEDURE #schema_name#.name
(
-- [argmode] argname argtype
)
BEGIN
-- DECLARE variables
-- definition
END;
"""
    ),
    "drop_procedure": Template("DROP PROCEDURE #function_name#"),
    "create_view": Template(
        """CREATE OR REPLACE VIEW #schema_name#.name AS
SELECT ...
"""
    ),
    "drop_view": Template(
        """DROP VIEW #view_name#
-- RESTRICT
-- CASCADE
"""
    ),
    "create_table": Template(
        """CREATE
-- TEMPORARY
TABLE #schema_name#.table_name
-- AS query
(
    column_name data_type
    -- NOT NULL
    -- NULL
    -- DEFAULT default_value
    -- AUTO_INCREMENT
    -- UNIQUE
    -- PRIMARY KEY
    -- COMMENT 'string'
    -- COLUMN_FORMAT { FIXED | DYNAMIC | DEFAULT }
    -- STORAGE { DISK | MEMORY | DEFAULT }
    -- [ GENERATED ALWAYS ] AS (expression) [ VIRTUAL | STORED ]
    -- [ CONSTRAINT [ symbol ] ] PRIMARY KEY [ USING { BTREE | HASH } ] ( column_name, ... )
    -- { INDEX | KEY } [ index_name ] [ USING { BTREE | HASH } ] ( column_name, ... )
    -- [ CONSTRAINT [ symbol ] ] UNIQUE [ INDEX | KEY ] [ index_name ] [ USING { BTREE | HASH } ] ( column_name, ... )
    -- { FULLTEXT | SPATIAL } [ INDEX | KEY ] [ index_name ] [ USING { BTREE | HASH } ] ( column_name, ... )
    -- [ CONSTRAINT [ symbol ] ] FOREIGN KEY [ index_name ]  ( column_name, ... ) REFERENCES reftable ( refcolumn, ... ) [MATCH FULL | MATCH PARTIAL | MATCH SIMPLE] [ON DELETE { RESTRICT | CASCADE | SET NULL | NO ACTION | SET DEFAULT }] [ON UPDATE { RESTRICT | CASCADE | SET NULL | NO ACTION | SET DEFAULT }]
    -- CHECK ( expr )
)
-- AUTO_INCREMENT value
-- AVG_ROW_LENGTH value
-- [ DEFAULT ] CHARACTER SET charset_name
-- CHECKSUM { 0 | 1 }
-- [ DEFAULT ] COLLATE collation_name
-- COMMENT 'string'
-- COMPRESSION { 'ZLIB' | 'LZ4' | 'NONE' }
-- CONNECTION 'connect_string'
-- { DATA | INDEX } DIRECTORY 'absolute path to directory'
-- DELAY_KEY_WRITE { 0 | 1 }
-- ENCRYPTION { 'Y' | 'N' }
-- ENGINE engine_name
-- INSERT_METHOD { NO | FIRST | LAST }
-- KEY_BLOCK_SIZE value
-- MAX_ROWS value
-- MIN_ROWS value
-- PACK_KEYS { 0 | 1 | DEFAULT }
-- PASSWORD 'string'
-- ROW_FORMAT { DEFAULT | DYNAMIC | FIXED | COMPRESSED | REDUNDANT | COMPACT }
-- STATS_AUTO_RECALC { DEFAULT | 0 | 1 }
-- STATS_PERSISTENT { DEFAULT | 0 | 1 }
-- STATS_SAMPLE_PAGES value
-- TABLESPACE tablespace_name [STORAGE { DISK | MEMORY | DEFAULT } ]
"""
    ),
    "alter_table": Template(
        """ALTER TABLE #table_name#
-- ADD [ COLUMN ] col_name column_definition  [ FIRST | AFTER col_name ]
-- ADD [ COLUMN ] ( col_name column_definition , ... )
-- ADD { INDEX | KEY } [ index_name ] USING { BTREE | HASH } (index_col_name , ... )
-- ADD [ CONSTRAINT [ symbol ] ] PRIMARY KEY USING { BTREE | HASH } ( index_col_name , ... )
-- ADD [ CONSTRAINT [ symbol ] ] UNIQUE [ INDEX | KEY ] [ index_name ] USING { BTREE | HASH } ( index_col_name , ... )
-- ADD FULLTEXT [ INDEX | KEY ] ( index_col_name , ... )
-- ADD SPATIAL [ INDEX | KEY ] [ index_name ] (index_col_name , ... )
-- ADD [ CONSTRAINT [ symbol ] ] FOREIGN KEY [ index_name ] ( index_col_name , ... ) reference_definition
-- ALGORITHM { DEFAULT | INPLACE | COPY }
-- ALTER [ COLUMN ] col_name { SET DEFAULT literal | DROP DEFAULT }
-- CHANGE [ COLUMN ] old_col_name new_col_name column_definition [ FIRST | AFTER col_name ]
-- [DEFAULT] CHARACTER SET charset_name [ COLLATE collation_name ]
-- CONVERT TO CHARACTER SET charset_name [ COLLATE collation_name ]
-- { DISABLE | ENABLE } KEYS
-- { DISCARD | IMPORT } TABLESPACE
-- DROP [ COLUMN ] col_name
-- DROP { INDEX | KEY } index_name
-- DROP PRIMARY KEY
-- DROP FOREIGN KEY fk_symbol
-- FORCE
-- LOCK { DEFAULT | NONE | SHARED | EXCLUSIVE }
-- MODIFY [ COLUMN ] col_name column_definition [ FIRST | AFTER col_name ]
-- ORDER BY col_name [, col_name] ...
-- RENAME { INDEX | KEY } old_index_name TO new_index_name
-- RENAME [ TO | AS ] new_tbl_name
-- { WITHOUT | WITH } VALIDATION
-- ADD PARTITION ( partition_definition )
-- DROP PARTITION partition_names
-- DISCARD PARTITION { partition_names | ALL } TABLESPACE
-- IMPORT PARTITION { partition_names | ALL } TABLESPACE
-- TRUNCATE PARTITION { partition_names | ALL }
-- COALESCE PARTITION number
-- REORGANIZE PARTITION partition_names INTO ( partition_definitions )
-- EXCHANGE PARTITION partition_name WITH TABLE tbl_name [ { WITH | WITHOUT } VALIDATION ]
-- ANALYZE PARTITION { partition_names | ALL }
-- CHECK PARTITION { partition_names | ALL }
-- OPTIMIZE PARTITION { partition_names | ALL }
-- REBUILD PARTITION { partition_names | ALL }
-- REPAIR PARTITION { partition_names | ALL }
-- REMOVE PARTITIONING
-- UPGRADE PARTITIONING
-- AUTO_INCREMENT value
-- AVG_ROW_LENGTH value
-- [ DEFAULT ] CHARACTER SET charset_name
-- CHECKSUM { 0 | 1 }
-- [ DEFAULT ] COLLATE collation_name
-- COMMENT 'string'
-- COMPRESSION { 'ZLIB' | 'LZ4' | 'NONE' }
-- CONNECTION 'connect_string'
-- { DATA | INDEX } DIRECTORY 'absolute path to directory'
-- DELAY_KEY_WRITE { 0 | 1 }
-- ENCRYPTION { 'Y' | 'N' }
-- ENGINE engine_name
-- INSERT_METHOD { NO | FIRST | LAST }
-- KEY_BLOCK_SIZE value
-- MAX_ROWS value
-- MIN_ROWS value
-- PACK_KEYS { 0 | 1 | DEFAULT }
-- PASSWORD 'string'
-- ROW_FORMAT { DEFAULT | DYNAMIC | FIXED | COMPRESSED | REDUNDANT | COMPACT }
-- STATS_AUTO_RECALC { DEFAULT | 0 | 1 }
-- STATS_PERSISTENT { DEFAULT | 0 | 1 }
-- STATS_SAMPLE_PAGES value
-- TABLESPACE tablespace_name [STORAGE { DISK | MEMORY | DEFAULT } ]
"""
    ),
    "drop_table": Template(
        """DROP TABLE #table_name#
-- RESTRICT
-- CASCADE
"""
    ),
    "create_column": Template(
        """ALTER TABLE #table_name#
ADD name data_type
--DEFAULT expr
--NOT NULL
"""
    ),
    "alter_column": Template(
        """ALTER TABLE #table_name#
-- ALTER #column_name# { datatype | DEFAULT expr | [ NULL | NOT NULL ]}
-- CHANGE COLUMN #column_name# TO new_name
"""
    ),
    "drop_column": Template(
        """ALTER TABLE #table_name#
DROP COLUMN #column_name#
"""
    ),
    "create_primarykey": Template(
        """ALTER TABLE #table_name#
ADD CONSTRAINT name
PRIMARY KEY ( column_name [, ... ] )
"""
    ),
    "drop_primarykey": Template(
        """ALTER TABLE #table_name#
DROP PRIMARY KEY
"""
    ),
    "create_unique": Template(
        """ALTER TABLE #table_name#
ADD CONSTRAINT name
UNIQUE ( column_name [, ... ] )
"""
    ),
    "drop_unique": Template(
        """ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
"""
    ),
    "create_foreignkey": Template(
        """ALTER TABLE #table_name#
ADD CONSTRAINT name
FOREIGN KEY ( column_name [, ... ] )
REFERENCES reftable [ ( refcolumn [, ... ] ) ]
"""
    ),
    "drop_foreignkey": Template(
        """ALTER TABLE #table_name#
DROP FOREIGN KEY #constraint_name#
"""
    ),
    "create_index": Template(
        """CREATE [ UNIQUE ] INDEX name
ON #table_name#
( { column_name | ( expression ) } [ ASC | DESC ] )
"""
    ),
    "drop_index": Template("DROP INDEX #index_name# ON #table_name#"),
    "delete": Template(
        """DELETE FROM #table_name#
WHERE condition
"""
    ),
}


def get_template(key, version=None):
    tpl = TEMPLATES.get(key)
    if tpl is None:
        raise KeyError(f"No such template: {key}")
    return tpl
