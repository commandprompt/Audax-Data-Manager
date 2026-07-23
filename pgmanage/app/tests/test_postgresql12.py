import json
from datetime import datetime, timedelta

import app.include.OmniDatabase as OmniDatabase
from app.models.main import Connection, Technology
from app.utils.crypto import encrypt
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from .utils_testing import (USERS, execute_client_login,
                            get_client_omnidb_session)

User = get_user_model()


class PostgreSQL(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.host = '127.0.0.1'
        cls.port = '5433'
        cls.service = 'dellstore'
        cls.role = 'postgres'
        cls.password = 'postgres'
        cls.encrypted_password = encrypt(cls.password, key=USERS["ADMIN"]["PASSWORD"])
        cls.db_type = "postgresql"
        cls.test_connection = Connection.objects.create(
            user=User.objects.get(username="admin"),
            technology=Technology.objects.filter(name=cls.db_type).first(),
            server=cls.host,
            port=cls.port,
            database=cls.service,
            username=cls.role,
            password=cls.encrypted_password,
            alias="Pgmanage Tests",
        )
        cls.database = OmniDatabase.Generic.InstantiateDatabase(
            cls.db_type,
            cls.host,
            cls.port,
            cls.service,
            cls.role,
            0,
            cls.test_connection.id
        )
        cls.database.connection.password = cls.password
        cls.database.GetVersion()
        cls.major_version = cls.database.major_version

        cls.client_nosession = Client()
        cls.client_session = Client()

        success, response = execute_client_login(p_client=cls.client_session, p_username='admin', p_password='admin')
        get_client_omnidb_session(p_client=cls.client_session)

        # sanity checks on the shared fixture, not a per-test assertion - no
        # TestCase instance exists yet in setUpClass, so self.assert* can't be used
        assert response.status_code == 200
        data = json.loads(response.content.decode())
        assert data['data'] >= 0
        session = cls.client_session.session
        assert session['pgmanage_session'].user_name == 'admin'

        session['pgmanage_session'].databases = [{
            'database': cls.database,
            'prompt_password': False,
            'prompt_timeout': datetime.now() + timedelta(0,60000)
        }]
        session['pgmanage_session'].tab_connections = {0: cls.database}
        session['pgmanage_session'].tabs_databases = {0: 'dellstore'}
        session.save()

        # DDL templates are static per connection - fetched once here instead of
        # once per test, since dozens of tests below only check one dict key each
        tree_info_response = cls.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert tree_info_response.status_code == 200
        cls.templates = tree_info_response.json()['templates']

    @classmethod
    def lists_equal(cls, p_list_a, p_list_b):
        equal = True
        equal = len(p_list_a) == len(p_list_b)
        k = 0
        while k < len(p_list_a) and equal:
            if p_list_a[k] != p_list_b[k]:
                equal = False
            k = k + 1
        return equal

    def test_get_tree_info_postgresql_nosession(self):
        response = self.client_nosession.post('/get_tree_info_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_tree_info_postgresql_session(self):
        keys = list(self.templates.keys())
        keys.sort()
        keys_l = ['add_pubtable', 'alter_aggregate', 'alter_column', 'alter_database', 'alter_domain', 'alter_eventtrigger', 'alter_eventtriggerfunction', 'alter_fdw', 'alter_foreign_column', 'alter_foreign_server', 'alter_foreign_table', 'alter_function', 'alter_index', 'alter_mview', 'alter_procedure', 'alter_publication', 'alter_rule', 'alter_schema', 'alter_sequence', 'alter_statistics', 'alter_subscription', 'alter_tablespace', 'alter_trigger', 'alter_triggerfunction', 'alter_type', 'alter_user_mapping', 'alter_view', 'analyze', 'analyze_table', 'cluster_index', 'create_aggregate', 'create_check', 'create_column', 'create_database', 'create_domain', 'create_eventtrigger', 'create_eventtriggerfunction', 'create_exclude', 'create_fdw', 'create_foreign_column', 'create_foreign_server', 'create_foreign_table', 'create_foreignkey', 'create_function', 'create_index', 'create_inherited', 'create_logicalreplicationslot', 'create_mview', 'create_partition', 'create_physicalreplicationslot', 'create_primarykey', 'create_procedure', 'create_publication', 'create_rule', 'create_schema', 'create_sequence', 'create_statistics', 'create_subscription', 'create_tablespace', 'create_trigger', 'create_triggerfunction', 'create_type', 'create_unique', 'create_user_mapping', 'create_view', 'create_view_trigger', 'delete', 'detach_partition', 'disable_eventtrigger', 'disable_trigger', 'drop_aggregate', 'drop_check', 'drop_column', 'drop_database', 'drop_domain', 'drop_eventtrigger', 'drop_eventtriggerfunction', 'drop_exclude', 'drop_fdw', 'drop_foreign_column', 'drop_foreign_server', 'drop_foreign_table', 'drop_foreignkey', 'drop_function', 'drop_index', 'drop_logicalreplicationslot', 'drop_mview', 'drop_partition', 'drop_physicalreplicationslot', 'drop_primarykey', 'drop_procedure', 'drop_publication', 'drop_pubtable', 'drop_role', 'drop_rule', 'drop_schema', 'drop_sequence', 'drop_statistics', 'drop_subscription', 'drop_table', 'drop_tablespace', 'drop_trigger', 'drop_triggerfunction', 'drop_type', 'drop_unique', 'drop_user_mapping', 'drop_view', 'enable_eventtrigger', 'enable_trigger', 'import_foreign_schema', 'noinherit_partition', 'refresh_mview', 'reindex', 'truncate', 'vacuum', 'vacuum_table']
        self.assertEqual(keys, keys_l)

    def test_template_create_tablespace(self):
        self.assertEqual(self.templates['create_tablespace'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createtablespace.html
CREATE TABLESPACE name
LOCATION 'directory'
--OWNER new_owner | CURRENT_USER | SESSION_USER
--WITH ( tablespace_option = value [, ... ] )
''')

    def test_template_alter_tablespace(self):
        self.assertEqual(self.templates['alter_tablespace'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertablespace.html
ALTER TABLESPACE #tablespace_name#
--RENAME TO new_name
--OWNER TO {{ new_owner | CURRENT_USER | SESSION_USER }}
--SET seq_page_cost = value
--RESET seq_page_cost
--SET random_page_cost = value
--RESET random_page_cost
--SET effective_io_concurrency = value
--RESET effective_io_concurrency
''')

    def test_template_drop_tablespace(self):
        self.assertEqual(self.templates['drop_tablespace'], f'-- https://www.postgresql.org/docs/{self.major_version}/sql-droptablespace.html\nDROP TABLESPACE #tablespace_name#')


    def test_template_drop_role(self):
        self.assertEqual(self.templates['drop_role'], 'DROP ROLE #role_name#')

    def test_template_create_database(self):
        self.assertEqual(self.templates['create_database'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createdatabase.html
CREATE DATABASE name
--OWNER user_name
--TEMPLATE template
--ENCODING encoding
--STRATEGY strategy
--LOCALE locale
--LC_COLLATE lc_collate
--LC_CTYPE lc_ctype
--ICU_LOCALE icu_locale
--LOCALE_PROVIDER locale_provider
--COLLATION_VERSION collation_version
--TABLESPACE tablespace
--ALLOW_CONNECTIONS allowconn
--CONNECTION LIMIT connlimit
--IS_TEMPLATE istemplate
--OID oid
''')

    def test_template_alter_database(self):
        self.assertEqual(self.templates['alter_database'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterdatabase.html
ALTER DATABASE #database_name#
--ALLOW_CONNECTIONS allowconn
--CONNECTION LIMIT connlimit
--IS_TEMPLATE istemplate
--RENAME TO new_name
--OWNER TO {{ new_owner | CURRENT_USER | SESSION_USER }}
--SET TABLESPACE new_tablespace
--SET configuration_parameter TO {{ value | DEFAULT }}
--SET configuration_parameter FROM CURRENT
--RESET configuration_parameter
--RESET ALL
''')

    def test_template_drop_database(self):
        self.assertEqual(self.templates['drop_database'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropdatabase.html
DROP DATABASE #database_name#
--WITH ( FORCE )
''')

    def test_template_create_schema(self):
        self.assertEqual(self.templates['create_schema'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createschema.html
CREATE SCHEMA schema_name
--AUTHORIZATION [ GROUP ] user_name | CURRENT_USER | SESSION_USER
''')

    def test_template_alter_schema(self):
        self.assertEqual(self.templates['alter_schema'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterschema.html
ALTER SCHEMA #schema_name#
--RENAME TO new_name
--OWNER TO {{ new_owner | CURRENT_USER | SESSION_USER }}
''')

    def test_template_drop_schema(self):
        self.assertEqual(self.templates['drop_schema'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropschema.html
DROP SCHEMA #schema_name#
--CASCADE
''')

    def test_template_drop_table(self):
        self.assertEqual(self.templates['drop_table'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-droptable.html
DROP TABLE #table_name#
--CASCADE
''')

    def test_template_create_sequence(self):
        self.assertEqual(self.templates['create_sequence'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createsequence.html
CREATE SEQUENCE #schema_name#.name
--INCREMENT BY increment
--MINVALUE minvalue | NO MINVALUE
--MAXVALUE maxvalue | NO MAXVALUE
--START WITH start
--CACHE cache
--CYCLE
--OWNED BY {{ table_name.column_name | NONE }}
''')

    def test_template_alter_sequence(self):
        self.assertEqual(self.templates['alter_sequence'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altersequence.html
ALTER SEQUENCE #sequence_name#
--INCREMENT BY increment
--MINVALUE minvalue | NO MINVALUE
--MAXVALUE maxvalue | NO MAXVALUE
--START WITH start
--RESTART
--RESTART WITH restart
--CACHE cache
--CYCLE
--NO CYCLE
--OWNED BY {{ table_name.column_name | NONE }}
--OWNER TO {{ new_owner | CURRENT_USER | SESSION_USER }}
--RENAME TO new_name
--SET SCHEMA new_schema
''')

    def test_template_drop_sequence(self):
        self.assertEqual(self.templates['drop_sequence'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropsequence.html
DROP SEQUENCE #sequence_name#
--CASCADE
''')

    def test_template_create_function(self):
        self.assertEqual(self.templates['create_function'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createfunction.html
CREATE OR REPLACE FUNCTION #schema_name#.name
--(
--    [ argmode ] [ argname ] argtype [ {{ DEFAULT | = }} default_expr ]
--)
--RETURNS rettype
--RETURNS TABLE ( column_name column_type )
LANGUAGE plpgsql
--IMMUTABLE | STABLE | VOLATILE
--STRICT
--SECURITY DEFINER
--COST execution_cost
--ROWS result_rows
AS
$function$
--DECLARE
-- variables
BEGIN
-- definition
END;
$function$
''')

    def test_template_drop_function(self):
        self.assertEqual(self.templates['drop_function'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropfunction.html
DROP FUNCTION #function_name#
--CASCADE
''')

    def test_template_create_triggerfunction(self):
        self.assertEqual(self.templates['create_triggerfunction'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createfunction.html
CREATE OR REPLACE FUNCTION #schema_name#.name()
RETURNS trigger
LANGUAGE plpgsql
--IMMUTABLE | STABLE | VOLATILE
--COST execution_cost
AS
$function$
--DECLARE
-- variables
BEGIN
-- definition
END;
$function$
''')

    def test_template_drop_triggerfunction(self):
        self.assertEqual(self.templates['drop_triggerfunction'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropfunction.html
DROP FUNCTION #function_name#
--CASCADE
''')

    def test_template_create_view(self):
        self.assertEqual(self.templates['create_view'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createview.html
CREATE [ OR REPLACE ] [ TEMP | TEMPORARY ] [ RECURSIVE ] VIEW #schema_name#.name
--WITH ( check_option = local | cascaded )
--WITH ( security_barrier = true | false )
AS
SELECT ...
''')

    def test_template_drop_view(self):
        self.assertEqual(self.templates['drop_view'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropview.html
DROP VIEW #view_name#
--CASCADE
''')

    def test_template_create_mview(self):
        self.assertEqual(self.templates['create_mview'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-creatematerializedview.html
CREATE MATERIALIZED VIEW #schema_name#.name AS
SELECT ...
--WITH NO DATA
''')

    def test_template_refresh_mview(self):
        self.assertEqual(self.templates['refresh_mview'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-refreshmaterializedview.html
REFRESH MATERIALIZED VIEW
--CONCURRENTLY
#view_name#
--WITH NO DATA
''')

    def test_template_drop_mview(self):
        self.assertEqual(self.templates['drop_mview'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropmaterializedview.html
DROP MATERIALIZED VIEW #view_name#
--CASCADE
''')

    def test_template_create_column(self):
        self.assertEqual(self.templates['create_column'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD COLUMN name data_type
--COLLATE collation
--column_constraint [ ... ] ]
''')

    def test_template_alter_column(self):
        self.assertEqual(self.templates['alter_column'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
--ALTER COLUMN #column_name#
--RENAME COLUMN #column_name# TO new_column
--TYPE data_type [ COLLATE collation ] [ USING expression ]
--SET DEFAULT expression
--DROP DEFAULT
--SET NOT NULL
--DROP NOT NULL
--SET STATISTICS integer
--SET ( attribute_option = value [, ... ] )
--RESET ( attribute_option [, ... ] )
--SET STORAGE {{ PLAIN | EXTERNAL | EXTENDED | MAIN }}
''')

    def test_template_drop_column(self):
        self.assertEqual(self.templates['drop_column'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP COLUMN #column_name#
--CASCADE
''')

    def test_template_create_primarykey(self):
        self.assertEqual(self.templates['create_primarykey'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD CONSTRAINT name
PRIMARY KEY ( column_name [, ... ] )
--WITH ( storage_parameter [= value] [, ... ] )
--WITH OIDS
--WITHOUT OIDS
--USING INDEX TABLESPACE tablespace_name
''')

    def test_template_drop_primarykey(self):
        self.assertEqual(self.templates['drop_primarykey'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''')

    def test_template_create_unique(self):
        self.assertEqual(self.templates['create_unique'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD CONSTRAINT name
UNIQUE ( column_name [, ... ] )
--WITH ( storage_parameter [= value] [, ... ] )
--WITH OIDS
--WITHOUT OIDS
--USING INDEX TABLESPACE tablespace_name
''')

    def test_template_drop_unique(self):
        self.assertEqual(self.templates['drop_unique'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''')

    def test_template_create_foreignkey(self):
        self.assertEqual(self.templates['create_foreignkey'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD CONSTRAINT name
FOREIGN KEY ( column_name [, ... ] )
REFERENCES reftable [ ( refcolumn [, ... ] ) ]
--MATCH {{ FULL | PARTIAL | SIMPLE }}
--ON DELETE {{ NO ACTION | RESTRICT | CASCADE | SET NULL | SET DEFAULT }}
--ON UPDATE {{ NO ACTION | RESTRICT | CASCADE | SET NULL | SET DEFAULT }}
--NOT VALID
''')

    def test_template_drop_foreignkey(self):
        self.assertEqual(self.templates['drop_foreignkey'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''')

    def test_template_create_index(self):
        self.assertEqual(self.templates['create_index'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createindex.html
CREATE [ UNIQUE ] INDEX [ CONCURRENTLY ] name
ON [ ONLY ] #table_name#
--USING method
( {{ column_name | ( expression ) }} [ COLLATE collation ] [ opclass [ ( opclass_parameter = value [, ... ] ) ] ] [ ASC | DESC ] [ NULLS {{ FIRST | LAST }} ] [, ...] )
--INCLUDE ( column_name [, ...] )
--WITH ( storage_parameter = value [, ... ] )
--WHERE predicate
''')

    def test_template_alter_index(self):
        self.assertEqual(self.templates['alter_index'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterindex.html
ALTER INDEX #index_name#
--RENAME to new_name
--SET TABLESPACE tablespace_name
--ATTACH PARTITION index_name
--DEPENDS ON EXTENSION extension_name
--NO DEPENDS ON EXTENSION extension_name
--SET ( storage_parameter = value [, ... ] )
--RESET ( storage_parameter [, ... ] )
''')

    def test_template_drop_index(self):
        self.assertEqual(self.templates['drop_index'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropindex.html
DROP INDEX
--CONCURRENTLY
#index_name#
--CASCADE
''')

    def test_template_create_check(self):
        self.assertEqual(self.templates['create_check'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD CONSTRAINT name
CHECK ( expression )
''')

    def test_template_drop_check(self):
        self.assertEqual(self.templates['drop_check'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''')

    def test_template_create_exclude(self):
        self.assertEqual(self.templates['create_exclude'], f'''-- https://www.postgresql.org/docs/{self.major_version}/ddl-constraints.html#DDL-CONSTRAINTS-EXCLUSION
ALTER TABLE #table_name#
ADD CONSTRAINT name
--USING index_method
EXCLUDE ( exclude_element WITH operator [, ... ] )
--index_parameters
--WHERE ( predicate )
''')

    def test_template_drop_exclude(self):
        self.assertEqual(self.templates['drop_exclude'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''')

    def test_template_create_rule(self):
        self.assertEqual(self.templates['create_rule'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createrule.html
CREATE RULE name
AS ON {{ SELECT | INSERT | UPDATE | DELETE }}
TO #table_name#
--WHERE condition
--DO ALSO {{ NOTHING | command | ( command ; command ... ) }}
--DO INSTEAD {{ NOTHING | command | ( command ; command ... ) }}
''')

    def test_template_alter_rule(self):
        self.assertEqual(self.templates['alter_rule'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterrule.html 
ALTER RULE #rule_name# ON #table_name# RENAME TO new_name''')

    def test_template_drop_rule(self):
        self.assertEqual(self.templates['drop_rule'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-droprule.html 
DROP RULE #rule_name# ON #table_name#
--CASCADE
''')

    def test_template_create_trigger(self):
        self.assertEqual(self.templates['create_trigger'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createtrigger.html
CREATE TRIGGER name
--BEFORE {{ INSERT [ OR ] | UPDATE [ OF column_name [, ... ] ] [ OR ] | DELETE [ OR ] | TRUNCATE }}
--AFTER {{ INSERT [ OR ] | UPDATE [ OF column_name [, ... ] ] [ OR ] | DELETE [ OR ] | TRUNCATE }}
ON #table_name#
--FROM referenced_table_name
--NOT DEFERRABLE | [ DEFERRABLE ] {{ INITIALLY IMMEDIATE | INITIALLY DEFERRED }}
--FOR EACH ROW
--FOR EACH STATEMENT
--WHEN ( condition )
--EXECUTE PROCEDURE function_name ( arguments )
''')

    def test_template_create_view_trigger(self):
        self.assertEqual(self.templates['create_view_trigger'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createtrigger.html
CREATE TRIGGER name
--BEFORE {{ INSERT [ OR ] | UPDATE [ OF column_name [, ... ] ] [ OR ] | DELETE }}
--AFTER {{ INSERT [ OR ] | UPDATE [ OF column_name [, ... ] ] [ OR ] | DELETE }}
--INSTEAD OF {{ INSERT [ OR ] | UPDATE [ OF column_name [, ... ] ] [ OR ] | DELETE }}
ON #table_name#
--FROM referenced_table_name
--NOT DEFERRABLE | [ DEFERRABLE ] {{ INITIALLY IMMEDIATE | INITIALLY DEFERRED }}
--FOR EACH ROW
--FOR EACH STATEMENT
--WHEN ( condition )
--EXECUTE PROCEDURE function_name ( arguments )
''')

    def test_template_alter_trigger(self):
        self.assertEqual(self.templates['alter_trigger'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertrigger.html
ALTER TRIGGER #trigger_name# ON #table_name#
--RENAME TO new_name
--DEPENDS ON EXTENSION extension_name
--NO DEPENDS ON EXTENSION extension_name
''')

    def test_template_enable_trigger(self):
        self.assertEqual(self.templates['enable_trigger'], '''ALTER TABLE #table_name# ENABLE
--REPLICA
--ALWAYS
TRIGGER #trigger_name#
''')

    def test_template_disable_trigger(self):
        self.assertEqual(self.templates['disable_trigger'], 'ALTER TABLE #table_name# DISABLE TRIGGER #trigger_name#')

    def test_template_drop_trigger(self):
        self.assertEqual(self.templates['drop_trigger'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-droptrigger.html 
DROP TRIGGER #trigger_name# ON #table_name#
--CASCADE
''')

    def test_template_create_inherited(self):
        self.assertEqual(self.templates['create_inherited'], '''CREATE TABLE name (
    CHECK ( condition )
) INHERITS (#table_name#)
''')

    def test_template_noinherit_partition(self):
        self.assertEqual(self.templates['noinherit_partition'], 'ALTER TABLE #partition_name# NO INHERIT #table_name#')

    def test_template_drop_partition(self):
        self.assertEqual(self.templates['drop_partition'], 'DROP TABLE #partition_name#')

    def test_template_vacuum(self):
        self.assertEqual(self.templates['vacuum'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-vacuum.html
VACUUM
--FULL
--FREEZE
--ANALYZE
--DISABLE_PAGE_SKIPPING
--SKIP_LOCKED
--INDEX_CLEANUP
--TRUNCATE
--PARALLEL number_of_parallel_workers
''')

    def test_template_vacuum_table(self):
        self.assertEqual(self.templates['vacuum_table'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-vacuum.html
VACUUM
--FULL
--FREEZE
--ANALYZE
--DISABLE_PAGE_SKIPPING
--SKIP_LOCKED
--INDEX_CLEANUP
--TRUNCATE
--PARALLEL number_of_parallel_workers
#table_name#
--(column_name, [, ...])
''')

    def test_template_analyze(self):
        self.assertEqual(self.templates['analyze'], f'-- https://www.postgresql.org/docs/{self.major_version}/sql-analyze.html \nANALYZE')

    def test_template_analyze_table(self):
        self.assertEqual(self.templates['analyze_table'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-analyze.html
ANALYZE #table_name#
--(column_name, [, ...])
''')

    def test_template_truncate(self):
        self.assertEqual(self.templates['truncate'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-truncate.html
TRUNCATE
--ONLY
#table_name#
--RESTART IDENTITY
--CASCADE
''')

    def test_template_create_physicalreplicationslot(self):
        self.assertEqual(self.templates['create_physicalreplicationslot'], f'''-- https://www.postgresql.org/docs/{self.major_version}/functions-admin.html#FUNCTIONS-REPLICATION-TABLE 
SELECT * FROM pg_create_physical_replication_slot('slot_name')''')

    def test_template_drop_physicalreplicationslot(self):
        self.assertEqual(self.templates['drop_physicalreplicationslot'], f'''-- https://www.postgresql.org/docs/{self.major_version}/functions-admin.html#FUNCTIONS-REPLICATION-TABLE 
SELECT pg_drop_replication_slot('#slot_name#')''')

    def test_template_create_logicalreplicationslot(self):
        self.assertEqual(self.templates['create_logicalreplicationslot'], f'''-- https://www.postgresql.org/docs/{self.major_version}/functions-admin.html#FUNCTIONS-REPLICATION-TABLE 
SELECT * FROM pg_create_logical_replication_slot('slot_name', 'pgoutput')''')

    def test_template_drop_logicalreplicationslot(self):
        self.assertEqual(self.templates['drop_logicalreplicationslot'], f'''-- https://www.postgresql.org/docs/{self.major_version}/functions-admin.html#FUNCTIONS-REPLICATION-TABLE 
SELECT pg_drop_replication_slot('#slot_name#')''')

    def test_template_create_publication(self):
        self.assertEqual(self.templates['create_publication'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createpublication.html
CREATE PUBLICATION name
--FOR TABLE [ ONLY ] table_name [ * ] [, ...]
--FOR ALL TABLES
--WITH ( publish = 'insert, update, delete, truncate' )
--WITH ( publish_via_partition_root = true | false )
''')

    def test_template_alter_publication(self):
        self.assertEqual(self.templates['alter_publication'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterpublication.html
ALTER PUBLICATION #pub_name#
--ADD TABLE [ ONLY ] table_name [ * ] [, ...]
--SET TABLE [ ONLY ] table_name [ * ] [, ...]
--DROP TABLE [ ONLY ] table_name [ * ] [, ...]
--SET ( publish = 'insert, update, delete, truncate' )
--SET ( publish_via_partition_root = true | false )
--OWNER TO {{ new_owner | CURRENT_USER | SESSION_USER }}
--RENAME TO new_name
''')

    def test_template_drop_publication(self):
        self.assertEqual(self.templates['drop_publication'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-droppublication.html 
DROP PUBLICATION #pub_name#
--CASCADE
''')

    def test_template_add_pubtable(self):
        self.assertEqual(self.templates['add_pubtable'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterpublication.html 
ALTER PUBLICATION #pub_name# ADD TABLE table_name''')

    def test_template_drop_pubtable(self):
        self.assertEqual(self.templates['drop_pubtable'], f'-- https://www.postgresql.org/docs/{self.major_version}/sql-alterpublication.html \nALTER PUBLICATION #pub_name# DROP TABLE #table_name#')

    def test_template_create_subscription(self):
        self.assertEqual(self.templates['create_subscription'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createsubscription.html
CREATE SUBSCRIPTION name
CONNECTION 'conninfo'
PUBLICATION pub_name [, ...]
--WITH (
--copy_data = {{ true | false }}
--, create_slot = {{ true | false }}
--, enabled = {{ true | false }}
--, slot_name = 'name'
--, synchronous_commit = {{ on | remote_apply | remote_write | local | off }}
--, connect = {{ true | false }}
--)
''')

    def test_template_alter_subscription(self):
        self.assertEqual(self.templates['alter_subscription'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altersubscription.html
ALTER SUBSCRIPTION #sub_name#
--CONNECTION 'conninfo'
--SET PUBLICATION pub_name [, ...] [ WITH ( refresh = {{ true | false }} ) ]
--REFRESH PUBLICATION [ WITH ( copy_data = {{ true | false }} ) ]
--ENABLE
--DISABLE
--SET (
--slot_name = 'name'
--, synchronous_commit = {{ on | remote_apply | remote_write | local | off }}
--)
--OWNER TO {{ new_owner | CURRENT_USER | SESSION_USER }}
--RENAME TO new_name
''')

    def test_template_drop_subscription(self):
        self.assertEqual(self.templates['drop_subscription'], f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropsubscription.html 
DROP SUBSCRIPTION #sub_name#
--CASCADE
''')


    def test_get_tables_postgresql_nosession(self):
        response = self.client_nosession.post('/get_tables_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_tables_postgresql_session(self):
        response = self.client_session.post('/get_tables_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['name'] for a in data], [
            'categories',
            'cust_hist',
            'customers',
            'inventory',
            'orderlines',
            'orders',
            'products',
            'reorder'
        ]))


    def test_get_table_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_table_definition_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_table_definition_postgresql_session(self):
        response = self.client_session.post('/get_table_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "inventory"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['name'] for a in data['data']], ['prod_id', 'quan_in_stock', 'sales']))


    def test_get_schemas_postgresql_nosession(self):
        response = self.client_nosession.post('/get_schemas_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_schemas_postgresql_session(self):
        response = self.client_session.post('/get_schemas_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['name'] for a in data], [
            'public',
            'pg_catalog',
            'information_schema'
        ]))

    def test_get_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_columns_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_columns_postgresql_session(self):
        response = self.client_session.post('/get_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "orders"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['column_name'] for a in data], [
            'orderid',
            'orderdate',
            'customerid',
            'netamount',
            'tax',
            'totalamount'
        ]))

    def test_get_pk_postgresql_nosession(self):
        response = self.client_nosession.post('/get_pk_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_pk_postgresql_session(self):
        response = self.client_session.post('/get_pk_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "orders"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['constraint_name'] for a in data], ['orders_pkey']))

    def test_get_pk_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_pk_columns_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_pk_columns_postgresql_session(self):
        response = self.client_session.post('/get_pk_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "key": "orders_pkey", "schema": "public", "table": "orders"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a for a in data], ['orderid']))

    def test_get_fks_postgresql_nosession(self):
        response = self.client_nosession.post('/get_fks_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_fks_postgresql_session(self):
        response = self.client_session.post('/get_fks_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "orders"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['constraint_name'] for a in data], ['fk_customerid']))

    def test_get_fks_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_fks_columns_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_fks_columns_postgresql_session(self):
        response = self.client_session.post('/get_fks_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "fkey": "fk_customerid", "schema": "public", "table": "orders"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['column_name'] for a in data], ['customerid']))

    def test_get_uniques_postgresql_nosession(self):
        response = self.client_nosession.post('/get_uniques_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_uniques_postgresql_session(self):
        self.database.connection.Execute('alter table public.categories drop constraint if exists un_test')
        self.database.connection.Execute('alter table public.categories add constraint un_test unique (categoryname)')
        response = self.client_session.post('/get_uniques_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['constraint_name'] for a in data], ['un_test']))
        self.database.connection.Execute('alter table public.categories drop constraint un_test')

    def test_get_uniques_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_uniques_columns_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_uniques_columns_postgresql_session(self):
        self.database.connection.Execute('alter table public.categories drop constraint if exists un_test')
        self.database.connection.Execute('alter table public.categories add constraint un_test unique (categoryname)')
        response = self.client_session.post('/get_uniques_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "unique": "un_test", "schema": "public", "table": "categories"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a for a in data], ['categoryname']))
        self.database.connection.Execute('alter table public.categories drop constraint un_test')

    def test_get_indexes_postgresql_nosession(self):
        response = self.client_nosession.post('/get_indexes_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_indexes_postgresql_session(self):
        response = self.client_session.post('/get_indexes_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "orders"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['index_name'] for a in data], ['ix_order_custid', 'orders_pkey']))

    def test_get_indexes_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_indexes_columns_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_indexes_columns_postgresql_session(self):
        response = self.client_session.post('/get_indexes_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "index": "ix_order_custid", "schema": "public", "table": "orders"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal(data, ['customerid']))

    def test_get_functions_postgresql_nosession(self):
        response = self.client_nosession.post('/get_functions_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_functions_postgresql_session(self):
        response = self.client_session.post('/get_functions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn('new_customer', [a['name'] for a in data])

    def test_get_function_fields_postgresql_nosession(self):
        response = self.client_nosession.post('/get_function_fields_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_function_fields_postgresql_session(self):
        response = self.client_session.post('/get_function_fields_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "function": "new_customer(character varying, character varying, character varying, character varying, character varying, character varying, integer, character varying, integer, character varying, character varying, integer, character varying, character varying, character varying, character varying, integer, integer, character varying)"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['name'] for a in data], [
            'firstname_in character varying',
            'lastname_in character varying',
            'address1_in character varying',
            'address2_in character varying',
            'city_in character varying',
            'state_in character varying',
            'zip_in integer',
            'country_in character varying',
            'region_in integer',
            'email_in character varying',
            'phone_in character varying',
            'creditcardtype_in integer',
            'creditcard_in character varying',
            'creditcardexpiration_in character varying',
            'username_in character varying',
            'password_in character varying',
            'age_in integer',
            'income_in integer',
            'gender_in character varying',
            'OUT customerid_out integer'
        ]))

    def test_get_function_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_function_definition_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_function_definition_postgresql_session(self):
        response = self.client_session.post('/get_function_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "function": "new_customer(character varying, character varying, character varying, character varying, character varying, character varying, integer, character varying, integer, character varying, character varying, integer, character varying, character varying, character varying, character varying, integer, integer, character varying)"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn('''CREATE OR REPLACE FUNCTION public.new_customer(firstname_in character varying, lastname_in character varying, address1_in character varying, address2_in character varying, city_in character varying, state_in character varying, zip_in integer, country_in character varying, region_in integer, email_in character varying, phone_in character varying, creditcardtype_in integer, creditcard_in character varying, creditcardexpiration_in character varying, username_in character varying, password_in character varying, age_in integer, income_in integer, gender_in character varying, OUT customerid_out integer)
 RETURNS integer
 LANGUAGE plpgsql''', data['data'])

    def test_get_sequences_postgresql_nosession(self):
        response = self.client_nosession.post('/get_sequences_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_sequences_postgresql_session(self):
        response = self.client_session.post('/get_sequences_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['sequence_name'] for a in data], [
            'categories_category_seq',
            'customers_customerid_seq',
            'orders_orderid_seq',
            'products_prod_id_seq'
        ]))

    def test_get_views_postgresql_nosession(self):
        response = self.client_nosession.post('/get_views_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_views_postgresql_session(self):
        self.database.connection.Execute('create or replace view vw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_views_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['name'] for a in data], ['vw_omnidb_test']))
        self.database.connection.Execute('drop view vw_omnidb_test')

    def test_get_views_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_views_columns_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_views_columns_postgresql_session(self):
        self.database.connection.Execute('create or replace view vw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_views_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "vw_omnidb_test"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['column_name'] for a in data], [
            'customerid',
            'firstname',
            'lastname',
            'totalamount'
        ]))
        self.database.connection.Execute('drop view vw_omnidb_test')

    def test_get_view_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_view_definition_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_view_definition_postgresql_session(self):
        self.database.connection.Execute('create or replace view vw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_view_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "view": "vw_omnidb_test"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn('''CREATE OR REPLACE VIEW public.vw_omnidb_test AS
 SELECT c.customerid,
    c.firstname,
    c.lastname,
    sum(o.totalamount) AS totalamount
   FROM (customers c
     JOIN orders o ON ((o.customerid = c.customerid)))
  GROUP BY c.customerid, c.firstname, c.lastname''', data['data'])
        self.database.connection.Execute('drop view vw_omnidb_test')

    def test_get_databases_postgresql_nosession(self):
        response = self.client_nosession.post('/get_databases_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_databases_postgresql_session(self):
        response = self.client_session.post('/get_databases_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn(self.service, [a['name'] for a in data])

    def test_get_tablespaces_postgresql_nosession(self):
        response = self.client_nosession.post('/get_tablespaces_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_tablespaces_postgresql_session(self):
        response = self.client_session.post('/get_tablespaces_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn('pg_default', [a['name'] for a in data])

    def test_get_roles_postgresql_nosession(self):
        response = self.client_nosession.post('/get_roles_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_roles_postgresql_session(self):
        response = self.client_session.post('/get_roles_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn(self.role, [a['name'] for a in data['data']])

    def test_get_checks_postgresql_nosession(self):
        response = self.client_nosession.post('/get_checks_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_checks_postgresql_session(self):
        self.database.connection.Execute('alter table public.categories drop constraint if exists ch_test')
        self.database.connection.Execute("alter table public.categories add constraint ch_test check ( position(' ' in categoryname) = 0 )")
        response = self.client_session.post('/get_checks_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['constraint_name'] for a in data], ['ch_test']))
        self.database.connection.Execute('alter table public.categories drop constraint ch_test')

    def test_get_excludes_postgresql_nosession(self):
        response = self.client_nosession.post('/get_excludes_postgresql/')
        self.assertEqual(response.status_code, 401)


    def test_get_excludes_postgresql_session(self):
        self.database.connection.Execute('alter table public.categories drop constraint if exists ex_test')
        self.database.connection.Execute('alter table public.categories add constraint ex_test exclude (categoryname with = )')
        response = self.client_session.post('/get_excludes_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data[0]['constraint_name'], 'ex_test')
        self.database.connection.Execute('alter table public.categories drop constraint ex_test')

    def test_get_rules_postgresql_nosession(self):
        response = self.client_nosession.post('/get_rules_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_rules_postgresql_session(self):
        self.database.connection.Execute('create or replace rule ru_test as on delete to public.categories do instead nothing')
        response = self.client_session.post('/get_rules_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['rule_name'] for a in data], ['ru_test']))
        self.database.connection.Execute('drop rule ru_test on public.categories')

    def test_get_rule_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_rule_definition_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_rule_definition_postgresql_session(self):
        self.database.connection.Execute('create or replace rule ru_test as on delete to public.categories do instead nothing')
        response = self.client_session.post('/get_rule_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories", "rule": "ru_test"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn('''CREATE OR REPLACE RULE ru_test AS
    ON DELETE TO public.categories DO INSTEAD NOTHING;''', data['data'])
        self.database.connection.Execute('drop rule ru_test on public.categories')

    def test_get_triggerfunctions_postgresql_nosession(self):
        response = self.client_nosession.post('/get_triggerfunctions_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_triggerfunctions_postgresql_session(self):
        self.database.connection.Execute("create or replace function public.tg_ins_category() returns trigger language plpgsql as $function$begin new.categoryname := old.categoryname || ' modified'; end;$function$")
        response = self.client_session.post('/get_triggerfunctions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['name'] for a in data], ['tg_ins_category']))
        self.database.connection.Execute('drop function tg_ins_category()')

    def test_get_triggerfunction_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_triggerfunction_definition_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_triggerfunction_definition_postgresql_session(self):
        self.database.connection.Execute("create or replace function public.tg_ins_category() returns trigger language plpgsql as $function$begin new.categoryname := old.categoryname || ' modified'; end;$function$")
        response = self.client_session.post('/get_triggerfunction_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "function": "public.tg_ins_category()"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn('''CREATE OR REPLACE FUNCTION public.tg_ins_category()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$begin new.categoryname := old.categoryname || ' modified'; end;$function$''', data['data'])

    def test_get_triggers_postgresql_nosession(self):
        response = self.client_nosession.post('/get_triggers_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_triggers_postgresql_session(self):
        self.database.connection.Execute("create or replace function public.tg_ins_category() returns trigger language plpgsql as $function$begin new.categoryname := old.categoryname || ' modified'; end;$function$")
        self.database.connection.Execute('create or replace trigger tg_ins before insert on public.categories for each statement execute procedure public.tg_ins_category()')
        response = self.client_session.post('/get_triggers_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['trigger_name'] for a in data], ['tg_ins']))
        self.database.connection.Execute('drop trigger tg_ins on public.categories')
        self.database.connection.Execute('drop function public.tg_ins_category()')

    def test_get_inheriteds_postgresql_nosession(self):
        response = self.client_nosession.post('/get_inheriteds_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_inheriteds_postgresql_session(self):
        self.database.connection.Execute('create table if not exists public.categories_p1 (check ( category < 100 )) inherits (public.categories)')
        response = self.client_session.post('/get_inheriteds_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal(data, ['public.categories_p1']))
        self.database.connection.Execute('alter table public.categories_p1 no inherit public.categories')
        self.database.connection.Execute('drop table public.categories_p1')

    def test_get_mviews_postgresql_nosession(self):
        response = self.client_nosession.post('/get_mviews_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_mviews_postgresql_session(self):
        self.database.connection.Execute('create materialized view if not exists public.mvw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_mviews_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['name'] for a in data], ['mvw_omnidb_test']))
        self.database.connection.Execute('drop materialized view public.mvw_omnidb_test')

    def test_get_mviews_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_mviews_columns_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_mviews_columns_postgresql_session(self):
        self.database.connection.Execute('create materialized view if not exists public.mvw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_mviews_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "mvw_omnidb_test"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['column_name'] for a in data], [
            'customerid',
            'firstname',
            'lastname',
            'totalamount'
        ]))
        self.database.connection.Execute('drop materialized view public.mvw_omnidb_test')

    def test_get_mview_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_mview_definition_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_mview_definition_postgresql_session(self):
        self.database.connection.Execute('create materialized view if not exists public.mvw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_mview_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "view": "mvw_omnidb_test"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn('''DROP MATERIALIZED VIEW public.mvw_omnidb_test;

CREATE MATERIALIZED VIEW public.mvw_omnidb_test AS
 SELECT c.customerid,
    c.firstname,
    c.lastname,
    sum(o.totalamount) AS totalamount
   FROM (customers c
     JOIN orders o ON ((o.customerid = c.customerid)))
  GROUP BY c.customerid, c.firstname, c.lastname;
''', data['data'])
        self.database.connection.Execute('drop materialized view public.mvw_omnidb_test')

    def test_get_extensions_postgresql_nosession(self):
        response = self.client_nosession.post('/get_extensions_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_extensions_postgresql_session(self):
        response = self.client_session.post('/get_extensions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn('plpgsql', [a['name'] for a in data], ['plpgsql'])

    def test_get_physicalreplicationslots_postgresql_nosession(self):
        response = self.client_nosession.post('/get_physicalreplicationslots_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_physicalreplicationslots_postgresql_session(self):
        self.database.connection.Execute("select * from pg_create_physical_replication_slot('test_slot')")
        response = self.client_session.post('/get_physicalreplicationslots_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['name'] for a in data], ['test_slot']))
        self.database.connection.Execute("select pg_drop_replication_slot('test_slot')")

    def test_get_logicalreplicationslots_postgresql_nosession(self):
        response = self.client_nosession.post('/get_logicalreplicationslots_postgresql/')
        self.assertEqual(response.status_code, 401)

    def test_get_logicalreplicationslots_postgresql_session(self):
        self.database.connection.Execute("select * from pg_create_logical_replication_slot('test_slot', 'pgoutput')")
        response = self.client_session.post('/get_logicalreplicationslots_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(self.lists_equal([a['name'] for a in data], ['test_slot']))
        self.database.connection.Execute("select pg_drop_replication_slot('test_slot')")

    def test_get_extension_details_postgresql_nosession(self):
        response = self.client_nosession.post('/get_extension_details/')
        self.assertEqual(response.status_code, 401)

    def test_get_extension_details_postgresql_session(self):
        response = self.client_session.post('/get_extension_details/', {'data': '{"database_index": 0, "ext_name": "nonexistentextension", "workspace_id": 0}'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content.decode())
        self.assertIn("does not exist", data['data'])

        response = self.client_session.post('/get_extension_details/', {'data': '{"database_index": 0, "ext_name": "plpgsql", "workspace_id": 0}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data['name'], 'plpgsql')

    # TODO: extract these tests into separate test set
    def test_execute_query_postgresql_session(self):
        response = self.client_session.post('/execute_query/', {'data': '{"database_index": 0, "workspace_id": 0, "query": "select 1=1"}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertEqual(data['status'], 'success')

    def test_execute_query_postgresql_nosession(self):
        response = self.client_nosession.post('/execute_query/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 401)

    def test_get_available_extensions_postgresql_session(self):
        response = self.client_session.post('/get_available_extensions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertGreater(len(data['available_extensions']), 0)

    def test_get_available_extensions_postgresql_nosession(self):
        response = self.client_nosession.post('/get_available_extensions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 401)

    def test_get_object_description_postgresql_session(self):
        # just get something with a valid oid to run tests on
        response = self.client_session.post('/get_tables_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        data = json.loads(response.content.decode())
        table_data = data[0]
        request_params = '{"database_index": 0, "workspace_id": 0, "object_type": "table", "position": 0, "oid":' + table_data['oid'] + '}'
        response = self.client_session.post('/get_object_description_postgresql/', {'data': request_params})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertIn("COMMENT", data['data'])

    def test_get_object_description_postgresql_nosession(self):
        response = self.client_nosession.post('/get_object_description_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        self.assertEqual(response.status_code, 401)
