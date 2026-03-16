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
    def setUpClass(self):
        super(PostgreSQL, self).setUpClass()
        self.host = '127.0.0.1'
        self.port = '5433'
        self.service = 'dellstore'
        self.role = 'postgres'
        self.password = 'postgres'
        self.encrypted_password = encrypt(self.password, key=USERS["ADMIN"]["PASSWORD"])
        self.db_type = "postgresql"
        self.test_connection = Connection.objects.create(
            user=User.objects.get(username="admin"),
            technology=Technology.objects.filter(name=self.db_type).first(),
            server=self.host,
            port=self.port,
            database=self.service,
            username=self.role,
            password=self.encrypted_password,
            alias="Pgmanage Tests",
        )
        self.database = OmniDatabase.Generic.InstantiateDatabase(
            self.db_type,
            self.host,
            self.port,
            self.service,
            self.role,
            0,
            self.test_connection.id
        )
        self.database.connection.password = self.password
        self.database.GetVersion()
        self.major_version = self.database.major_version

        self.client_nosession = Client()
        self.client_session = Client()

        success, response = execute_client_login(p_client=self.client_session, p_username='admin', p_password='admin')
        get_client_omnidb_session(p_client=self.client_session)

        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert 0 <= data['data']
        session = self.client_session.session
        assert 'admin' == session['pgmanage_session'].user_name

        session['pgmanage_session'].databases = [{
            'database': self.database,
            'prompt_password': False,
            'prompt_timeout': datetime.now() + timedelta(0,60000)
        }]
        session['pgmanage_session'].tab_connections = {0: self.database}
        session['pgmanage_session'].tabs_databases = {0: 'dellstore'}
        session.save()

    @classmethod
    def lists_equal(self, p_list_a, p_list_b):
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
        assert 401 == response.status_code

    def test_get_tree_info_postgresql_session(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code

        data = response.json()
        keys = list(data["templates"].keys())
        keys.sort()
        keys_l = ['add_pubtable', 'alter_aggregate', 'alter_column', 'alter_database', 'alter_domain', 'alter_eventtrigger', 'alter_eventtriggerfunction', 'alter_fdw', 'alter_foreign_column', 'alter_foreign_server', 'alter_foreign_table', 'alter_function', 'alter_index', 'alter_mview', 'alter_procedure', 'alter_publication', 'alter_rule', 'alter_schema', 'alter_sequence', 'alter_statistics', 'alter_subscription', 'alter_tablespace', 'alter_trigger', 'alter_triggerfunction', 'alter_type', 'alter_user_mapping', 'alter_view', 'analyze', 'analyze_table', 'cluster_index', 'create_aggregate', 'create_check', 'create_column', 'create_database', 'create_domain', 'create_eventtrigger', 'create_eventtriggerfunction', 'create_exclude', 'create_fdw', 'create_foreign_column', 'create_foreign_server', 'create_foreign_table', 'create_foreignkey', 'create_function', 'create_index', 'create_inherited', 'create_logicalreplicationslot', 'create_mview', 'create_partition', 'create_physicalreplicationslot', 'create_primarykey', 'create_procedure', 'create_publication', 'create_rule', 'create_schema', 'create_sequence', 'create_statistics', 'create_subscription', 'create_tablespace', 'create_trigger', 'create_triggerfunction', 'create_type', 'create_unique', 'create_user_mapping', 'create_view', 'create_view_trigger', 'delete', 'detach_partition', 'disable_eventtrigger', 'disable_trigger', 'drop_aggregate', 'drop_check', 'drop_column', 'drop_database', 'drop_domain', 'drop_eventtrigger', 'drop_eventtriggerfunction', 'drop_exclude', 'drop_fdw', 'drop_foreign_column', 'drop_foreign_server', 'drop_foreign_table', 'drop_foreignkey', 'drop_function', 'drop_index', 'drop_logicalreplicationslot', 'drop_mview', 'drop_partition', 'drop_physicalreplicationslot', 'drop_primarykey', 'drop_procedure', 'drop_publication', 'drop_pubtable', 'drop_role', 'drop_rule', 'drop_schema', 'drop_sequence', 'drop_statistics', 'drop_subscription', 'drop_table', 'drop_tablespace', 'drop_trigger', 'drop_triggerfunction', 'drop_type', 'drop_unique', 'drop_user_mapping', 'drop_view', 'enable_eventtrigger', 'enable_trigger', 'import_foreign_schema', 'noinherit_partition', 'refresh_mview', 'reindex', 'truncate', 'vacuum', 'vacuum_table']
        assert keys == keys_l

    def test_template_create_tablespace(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createtablespace.html
CREATE TABLESPACE name
LOCATION 'directory'
--OWNER new_owner | CURRENT_USER | SESSION_USER
--WITH ( tablespace_option = value [, ... ] )
''' == template_data['create_tablespace']

    def test_template_alter_tablespace(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertablespace.html
ALTER TABLESPACE #tablespace_name#
--RENAME TO new_name
--OWNER TO {{ new_owner | CURRENT_USER | SESSION_USER }}
--SET seq_page_cost = value
--RESET seq_page_cost
--SET random_page_cost = value
--RESET random_page_cost
--SET effective_io_concurrency = value
--RESET effective_io_concurrency
''' == template_data['alter_tablespace']

    def test_template_drop_tablespace(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'-- https://www.postgresql.org/docs/{self.major_version}/sql-droptablespace.html\nDROP TABLESPACE #tablespace_name#' == template_data['drop_tablespace']


    def test_template_drop_role(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert 'DROP ROLE #role_name#' == template_data['drop_role']

    def test_template_create_database(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createdatabase.html
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
''' == template_data['create_database']

    def test_template_alter_database(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterdatabase.html
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
''' == template_data['alter_database']

    def test_template_drop_database(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropdatabase.html
DROP DATABASE #database_name#
--WITH ( FORCE )
''' == template_data['drop_database']

    def test_template_create_schema(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createschema.html
CREATE SCHEMA schema_name
--AUTHORIZATION [ GROUP ] user_name | CURRENT_USER | SESSION_USER
''' == template_data['create_schema']

    def test_template_alter_schema(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterschema.html
ALTER SCHEMA #schema_name#
--RENAME TO new_name
--OWNER TO {{ new_owner | CURRENT_USER | SESSION_USER }}
''' == template_data['alter_schema']

    def test_template_drop_schema(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropschema.html
DROP SCHEMA #schema_name#
--CASCADE
''' == template_data['drop_schema']

    def test_template_drop_table(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-droptable.html
DROP TABLE #table_name#
--CASCADE
''' == template_data['drop_table']

    def test_template_create_sequence(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createsequence.html
CREATE SEQUENCE #schema_name#.name
--INCREMENT BY increment
--MINVALUE minvalue | NO MINVALUE
--MAXVALUE maxvalue | NO MAXVALUE
--START WITH start
--CACHE cache
--CYCLE
--OWNED BY {{ table_name.column_name | NONE }}
''' == template_data['create_sequence']

    def test_template_alter_sequence(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altersequence.html
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
''' == template_data['alter_sequence']

    def test_template_drop_sequence(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropsequence.html
DROP SEQUENCE #sequence_name#
--CASCADE
''' == template_data['drop_sequence']

    def test_template_create_function(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createfunction.html
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
''' == template_data['create_function']

    def test_template_drop_function(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropfunction.html
DROP FUNCTION #function_name#
--CASCADE
''' == template_data['drop_function']

    def test_template_create_triggerfunction(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createfunction.html
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
''' == template_data['create_triggerfunction']

    def test_template_drop_triggerfunction(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropfunction.html
DROP FUNCTION #function_name#
--CASCADE
''' == template_data['drop_triggerfunction']

    def test_template_create_view(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createview.html
CREATE [ OR REPLACE ] [ TEMP | TEMPORARY ] [ RECURSIVE ] VIEW #schema_name#.name
--WITH ( check_option = local | cascaded )
--WITH ( security_barrier = true | false )
AS
SELECT ...
''' == template_data['create_view']

    def test_template_drop_view(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropview.html
DROP VIEW #view_name#
--CASCADE
''' == template_data['drop_view']

    def test_template_create_mview(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-creatematerializedview.html
CREATE MATERIALIZED VIEW #schema_name#.name AS
SELECT ...
--WITH NO DATA
''' == template_data['create_mview']

    def test_template_refresh_mview(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-refreshmaterializedview.html
REFRESH MATERIALIZED VIEW
--CONCURRENTLY
#view_name#
--WITH NO DATA
''' == template_data['refresh_mview']

    def test_template_drop_mview(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropmaterializedview.html
DROP MATERIALIZED VIEW #view_name#
--CASCADE
''' == template_data['drop_mview']

    def test_template_create_column(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD COLUMN name data_type
--COLLATE collation
--column_constraint [ ... ] ]
''' == template_data['create_column']

    def test_template_alter_column(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
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
''' == template_data['alter_column']

    def test_template_drop_column(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP COLUMN #column_name#
--CASCADE
''' == template_data['drop_column']

    def test_template_create_primarykey(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD CONSTRAINT name
PRIMARY KEY ( column_name [, ... ] )
--WITH ( storage_parameter [= value] [, ... ] )
--WITH OIDS
--WITHOUT OIDS
--USING INDEX TABLESPACE tablespace_name
''' == template_data['create_primarykey']

    def test_template_drop_primarykey(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''' == template_data['drop_primarykey']

    def test_template_create_unique(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD CONSTRAINT name
UNIQUE ( column_name [, ... ] )
--WITH ( storage_parameter [= value] [, ... ] )
--WITH OIDS
--WITHOUT OIDS
--USING INDEX TABLESPACE tablespace_name
''' == template_data['create_unique']

    def test_template_drop_unique(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''' == template_data['drop_unique']

    def test_template_create_foreignkey(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD CONSTRAINT name
FOREIGN KEY ( column_name [, ... ] )
REFERENCES reftable [ ( refcolumn [, ... ] ) ]
--MATCH {{ FULL | PARTIAL | SIMPLE }}
--ON DELETE {{ NO ACTION | RESTRICT | CASCADE | SET NULL | SET DEFAULT }}
--ON UPDATE {{ NO ACTION | RESTRICT | CASCADE | SET NULL | SET DEFAULT }}
--NOT VALID
''' == template_data['create_foreignkey']

    def test_template_drop_foreignkey(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''' == template_data['drop_foreignkey']

    def test_template_create_index(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createindex.html
CREATE [ UNIQUE ] INDEX [ CONCURRENTLY ] name
ON [ ONLY ] #table_name#
--USING method
( {{ column_name | ( expression ) }} [ COLLATE collation ] [ opclass [ ( opclass_parameter = value [, ... ] ) ] ] [ ASC | DESC ] [ NULLS {{ FIRST | LAST }} ] [, ...] )
--INCLUDE ( column_name [, ...] )
--WITH ( storage_parameter = value [, ... ] )
--WHERE predicate
''' == template_data['create_index']

    def test_template_alter_index(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterindex.html
ALTER INDEX #index_name#
--RENAME to new_name
--SET TABLESPACE tablespace_name
--ATTACH PARTITION index_name
--DEPENDS ON EXTENSION extension_name
--NO DEPENDS ON EXTENSION extension_name
--SET ( storage_parameter = value [, ... ] )
--RESET ( storage_parameter [, ... ] )
''' == template_data['alter_index']

    def test_template_drop_index(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropindex.html
DROP INDEX
--CONCURRENTLY
#index_name#
--CASCADE
''' == template_data['drop_index']

    def test_template_create_check(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
ADD CONSTRAINT name
CHECK ( expression )
''' == template_data['create_check']

    def test_template_drop_check(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''' == template_data['drop_check']

    def test_template_create_exclude(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/ddl-constraints.html#DDL-CONSTRAINTS-EXCLUSION
ALTER TABLE #table_name#
ADD CONSTRAINT name
--USING index_method
EXCLUDE ( exclude_element WITH operator [, ... ] )
--index_parameters
--WHERE ( predicate )
''' == template_data['create_exclude']

    def test_template_drop_exclude(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertable.html
ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''' == template_data['drop_exclude']

    def test_template_create_rule(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createrule.html
CREATE RULE name
AS ON {{ SELECT | INSERT | UPDATE | DELETE }}
TO #table_name#
--WHERE condition
--DO ALSO {{ NOTHING | command | ( command ; command ... ) }}
--DO INSTEAD {{ NOTHING | command | ( command ; command ... ) }}
''' == template_data['create_rule']

    def test_template_alter_rule(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterrule.html 
ALTER RULE #rule_name# ON #table_name# RENAME TO new_name''' == template_data['alter_rule']

    def test_template_drop_rule(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-droprule.html 
DROP RULE #rule_name# ON #table_name#
--CASCADE
''' == template_data['drop_rule']

    def test_template_create_trigger(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createtrigger.html
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
''' == template_data['create_trigger']

    def test_template_create_view_trigger(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createtrigger.html
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
''' == template_data['create_view_trigger']

    def test_template_alter_trigger(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altertrigger.html
ALTER TRIGGER #trigger_name# ON #table_name#
--RENAME TO new_name
--DEPENDS ON EXTENSION extension_name
--NO DEPENDS ON EXTENSION extension_name
''' == template_data['alter_trigger']

    def test_template_enable_trigger(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert '''ALTER TABLE #table_name# ENABLE
--REPLICA
--ALWAYS
TRIGGER #trigger_name#
''' == template_data['enable_trigger']

    def test_template_disable_trigger(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert 'ALTER TABLE #table_name# DISABLE TRIGGER #trigger_name#' == template_data['disable_trigger']

    def test_template_drop_trigger(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-droptrigger.html 
DROP TRIGGER #trigger_name# ON #table_name#
--CASCADE
''' == template_data['drop_trigger']

    def test_template_create_inherited(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert '''CREATE TABLE name (
    CHECK ( condition )
) INHERITS (#table_name#)
''' == template_data['create_inherited']

    def test_template_noinherit_partition(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert 'ALTER TABLE #partition_name# NO INHERIT #table_name#' == template_data['noinherit_partition']

    def test_template_drop_partition(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert 'DROP TABLE #partition_name#' == template_data['drop_partition']

    def test_template_vacuum(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-vacuum.html
VACUUM
--FULL
--FREEZE
--ANALYZE
--DISABLE_PAGE_SKIPPING
--SKIP_LOCKED
--INDEX_CLEANUP
--TRUNCATE
--PARALLEL number_of_parallel_workers
''' == template_data['vacuum']

    def test_template_vacuum_table(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-vacuum.html
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
''' == template_data['vacuum_table']

    def test_template_analyze(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'-- https://www.postgresql.org/docs/{self.major_version}/sql-analyze.html \nANALYZE' == template_data['analyze']

    def test_template_analyze_table(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-analyze.html
ANALYZE #table_name#
--(column_name, [, ...])
''' == template_data['analyze_table']

    def test_template_truncate(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-truncate.html
TRUNCATE
--ONLY
#table_name#
--RESTART IDENTITY
--CASCADE
''' == template_data['truncate']

    def test_template_create_physicalreplicationslot(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/functions-admin.html#FUNCTIONS-REPLICATION-TABLE 
SELECT * FROM pg_create_physical_replication_slot('slot_name')''' == template_data['create_physicalreplicationslot']

    def test_template_drop_physicalreplicationslot(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/functions-admin.html#FUNCTIONS-REPLICATION-TABLE 
SELECT pg_drop_replication_slot('#slot_name#')''' == template_data['drop_physicalreplicationslot']

    def test_template_create_logicalreplicationslot(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/functions-admin.html#FUNCTIONS-REPLICATION-TABLE 
SELECT * FROM pg_create_logical_replication_slot('slot_name', 'pgoutput')''' == template_data['create_logicalreplicationslot']

    def test_template_drop_logicalreplicationslot(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/functions-admin.html#FUNCTIONS-REPLICATION-TABLE 
SELECT pg_drop_replication_slot('#slot_name#')''' == template_data['drop_logicalreplicationslot']

    def test_template_create_publication(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createpublication.html
CREATE PUBLICATION name
--FOR TABLE [ ONLY ] table_name [ * ] [, ...]
--FOR ALL TABLES
--WITH ( publish = 'insert, update, delete, truncate' )
--WITH ( publish_via_partition_root = true | false )
''' == template_data['create_publication']

    def test_template_alter_publication(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterpublication.html
ALTER PUBLICATION #pub_name#
--ADD TABLE [ ONLY ] table_name [ * ] [, ...]
--SET TABLE [ ONLY ] table_name [ * ] [, ...]
--DROP TABLE [ ONLY ] table_name [ * ] [, ...]
--SET ( publish = 'insert, update, delete, truncate' )
--SET ( publish_via_partition_root = true | false )
--OWNER TO {{ new_owner | CURRENT_USER | SESSION_USER }}
--RENAME TO new_name
''' == template_data['alter_publication']

    def test_template_drop_publication(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-droppublication.html 
DROP PUBLICATION #pub_name#
--CASCADE
''' == template_data['drop_publication']

    def test_template_add_pubtable(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-alterpublication.html 
ALTER PUBLICATION #pub_name# ADD TABLE table_name''' == template_data['add_pubtable']

    def test_template_drop_pubtable(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'-- https://www.postgresql.org/docs/{self.major_version}/sql-alterpublication.html \nALTER PUBLICATION #pub_name# DROP TABLE #table_name#' == template_data['drop_pubtable']

    def test_template_create_subscription(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-createsubscription.html
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
''' == template_data['create_subscription']

    def test_template_alter_subscription(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-altersubscription.html
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
''' == template_data['alter_subscription']

    def test_template_drop_subscription(self):
        response = self.client_session.post('/get_tree_info_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        template_data = data['templates']
        assert f'''-- https://www.postgresql.org/docs/{self.major_version}/sql-dropsubscription.html 
DROP SUBSCRIPTION #sub_name#
--CASCADE
''' == template_data['drop_subscription']


    def test_get_tables_postgresql_nosession(self):
        response = self.client_nosession.post('/get_tables_postgresql/')
        assert 401 == response.status_code

    def test_get_tables_postgresql_session(self):
        response = self.client_session.post('/get_tables_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['name'] for a in data], [
            'categories',
            'cust_hist',
            'customers',
            'inventory',
            'orderlines',
            'orders',
            'products',
            'reorder'
        ])


    def test_get_table_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_table_definition_postgresql/')
        assert 401 == response.status_code

    def test_get_table_definition_postgresql_session(self):
        response = self.client_session.post('/get_table_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "inventory"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['name'] for a in data['data']], ['prod_id', 'quan_in_stock', 'sales'])


    def test_get_schemas_postgresql_nosession(self):
        response = self.client_nosession.post('/get_schemas_postgresql/')
        assert 401 == response.status_code

    def test_get_schemas_postgresql_session_with_system_catalogs(self):
        user = User.objects.get(username="admin")
        user.userdetails.show_system_catalogs = True
        user.userdetails.save()

        response = self.client_session.post('/get_schemas_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = response.json()
        assert self.lists_equal([a['name'] for a in data], [
            'public',
            'pg_catalog',
            'information_schema'
        ])
    
    def test_get_schemas_postgresql_session_without_system_catalogs(self):
        user = User.objects.get(username="admin")
        user.userdetails.show_system_catalogs = False
        user.userdetails.save()

        response = self.client_session.post('/get_schemas_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert response.status_code == 200

        data = json.loads(response.content.decode())

        assert self.lists_equal(
            [a['name'] for a in data],
            ['public']
        )

    def test_get_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_columns_postgresql/')
        assert 401 == response.status_code

    def test_get_columns_postgresql_session(self):
        response = self.client_session.post('/get_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "orders"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['column_name'] for a in data], [
            'orderid',
            'orderdate',
            'customerid',
            'netamount',
            'tax',
            'totalamount'
        ])

    def test_get_pk_postgresql_nosession(self):
        response = self.client_nosession.post('/get_pk_postgresql/')
        assert 401 == response.status_code

    def test_get_pk_postgresql_session(self):
        response = self.client_session.post('/get_pk_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "orders"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['constraint_name'] for a in data], ['orders_pkey'])

    def test_get_pk_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_pk_columns_postgresql/')
        assert 401 == response.status_code

    def test_get_pk_columns_postgresql_session(self):
        response = self.client_session.post('/get_pk_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "key": "orders_pkey", "schema": "public", "table": "orders"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a for a in data], ['orderid'])

    def test_get_fks_postgresql_nosession(self):
        response = self.client_nosession.post('/get_fks_postgresql/')
        assert 401 == response.status_code

    def test_get_fks_postgresql_session(self):
        response = self.client_session.post('/get_fks_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "orders"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['constraint_name'] for a in data], ['fk_customerid'])

    def test_get_fks_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_fks_columns_postgresql/')
        assert 401 == response.status_code

    def test_get_fks_columns_postgresql_session(self):
        response = self.client_session.post('/get_fks_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "fkey": "fk_customerid", "schema": "public", "table": "orders"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['column_name'] for a in data], ['customerid'])

    def test_get_uniques_postgresql_nosession(self):
        response = self.client_nosession.post('/get_uniques_postgresql/')
        assert 401 == response.status_code

    def test_get_uniques_postgresql_session(self):
        self.database.connection.Execute('alter table public.categories drop constraint if exists un_test')
        self.database.connection.Execute('alter table public.categories add constraint un_test unique (categoryname)')
        response = self.client_session.post('/get_uniques_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['constraint_name'] for a in data], ['un_test'])
        self.database.connection.Execute('alter table public.categories drop constraint un_test')

    def test_get_uniques_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_uniques_columns_postgresql/')
        assert 401 == response.status_code

    def test_get_uniques_columns_postgresql_session(self):
        self.database.connection.Execute('alter table public.categories drop constraint if exists un_test')
        self.database.connection.Execute('alter table public.categories add constraint un_test unique (categoryname)')
        response = self.client_session.post('/get_uniques_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "unique": "un_test", "schema": "public", "table": "categories"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a for a in data], ['categoryname'])
        self.database.connection.Execute('alter table public.categories drop constraint un_test')

    def test_get_indexes_postgresql_nosession(self):
        response = self.client_nosession.post('/get_indexes_postgresql/')
        assert 401 == response.status_code

    def test_get_indexes_postgresql_session(self):
        response = self.client_session.post('/get_indexes_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "orders"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['index_name'] for a in data], ['ix_order_custid', 'orders_pkey'])

    def test_get_indexes_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_indexes_columns_postgresql/')
        assert 401 == response.status_code

    def test_get_indexes_columns_postgresql_session(self):
        response = self.client_session.post('/get_indexes_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "index": "ix_order_custid", "schema": "public", "table": "orders"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal(data, ['customerid'])

    def test_get_functions_postgresql_nosession(self):
        response = self.client_nosession.post('/get_functions_postgresql/')
        assert 401 == response.status_code

    def test_get_functions_postgresql_session(self):
        response = self.client_session.post('/get_functions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert 'new_customer' in [a['name'] for a in data]

    def test_get_function_fields_postgresql_nosession(self):
        response = self.client_nosession.post('/get_function_fields_postgresql/')
        assert 401 == response.status_code

    def test_get_function_fields_postgresql_session(self):
        response = self.client_session.post('/get_function_fields_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "function": "new_customer(character varying, character varying, character varying, character varying, character varying, character varying, integer, character varying, integer, character varying, character varying, integer, character varying, character varying, character varying, character varying, integer, integer, character varying)"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['name'] for a in data], [
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
        ])

    def test_get_function_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_function_definition_postgresql/')
        assert 401 == response.status_code

    def test_get_function_definition_postgresql_session(self):
        response = self.client_session.post('/get_function_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "function": "new_customer(character varying, character varying, character varying, character varying, character varying, character varying, integer, character varying, integer, character varying, character varying, integer, character varying, character varying, character varying, character varying, integer, integer, character varying)"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert '''CREATE OR REPLACE FUNCTION public.new_customer(firstname_in character varying, lastname_in character varying, address1_in character varying, address2_in character varying, city_in character varying, state_in character varying, zip_in integer, country_in character varying, region_in integer, email_in character varying, phone_in character varying, creditcardtype_in integer, creditcard_in character varying, creditcardexpiration_in character varying, username_in character varying, password_in character varying, age_in integer, income_in integer, gender_in character varying, OUT customerid_out integer)
 RETURNS integer
 LANGUAGE plpgsql''' in data['data']

    def test_get_sequences_postgresql_nosession(self):
        response = self.client_nosession.post('/get_sequences_postgresql/')
        assert 401 == response.status_code

    def test_get_sequences_postgresql_session(self):
        response = self.client_session.post('/get_sequences_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['sequence_name'] for a in data], [
            'categories_category_seq',
            'customers_customerid_seq',
            'orders_orderid_seq',
            'products_prod_id_seq'
        ])

    def test_get_views_postgresql_nosession(self):
        response = self.client_nosession.post('/get_views_postgresql/')
        assert 401 == response.status_code

    def test_get_views_postgresql_session(self):
        self.database.connection.Execute('create or replace view vw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_views_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['name'] for a in data], ['vw_omnidb_test'])
        self.database.connection.Execute('drop view vw_omnidb_test')

    def test_get_views_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_views_columns_postgresql/')
        assert 401 == response.status_code

    def test_get_views_columns_postgresql_session(self):
        self.database.connection.Execute('create or replace view vw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_views_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "vw_omnidb_test"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['column_name'] for a in data], [
            'customerid',
            'firstname',
            'lastname',
            'totalamount'
        ])
        self.database.connection.Execute('drop view vw_omnidb_test')

    def test_get_view_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_view_definition_postgresql/')
        assert 401 == response.status_code

    def test_get_view_definition_postgresql_session(self):
        self.database.connection.Execute('create or replace view vw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_view_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "view": "vw_omnidb_test"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert '''CREATE OR REPLACE VIEW public.vw_omnidb_test AS
 SELECT c.customerid,
    c.firstname,
    c.lastname,
    sum(o.totalamount) AS totalamount
   FROM (customers c
     JOIN orders o ON ((o.customerid = c.customerid)))
  GROUP BY c.customerid, c.firstname, c.lastname''' in data['data']
        self.database.connection.Execute('drop view vw_omnidb_test')

    def test_get_databases_postgresql_nosession(self):
        response = self.client_nosession.post('/get_databases_postgresql/')
        assert 401 == response.status_code

    def test_get_databases_postgresql_session(self):
        response = self.client_session.post('/get_databases_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.service in [a['name'] for a in data]

    def test_get_tablespaces_postgresql_nosession(self):
        response = self.client_nosession.post('/get_tablespaces_postgresql/')
        assert 401 == response.status_code

    def test_get_tablespaces_postgresql_session(self):
        response = self.client_session.post('/get_tablespaces_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert 'pg_default' in [a['name'] for a in data]

    def test_get_roles_postgresql_nosession(self):
        response = self.client_nosession.post('/get_roles_postgresql/')
        assert 401 == response.status_code

    def test_get_roles_postgresql_session(self):
        response = self.client_session.post('/get_roles_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.role in [a['name'] for a in data['data']]

    def test_get_checks_postgresql_nosession(self):
        response = self.client_nosession.post('/get_checks_postgresql/')
        assert 401 == response.status_code

    def test_get_checks_postgresql_session(self):
        self.database.connection.Execute('alter table public.categories drop constraint if exists ch_test')
        self.database.connection.Execute("alter table public.categories add constraint ch_test check ( position(' ' in categoryname) = 0 )")
        response = self.client_session.post('/get_checks_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['constraint_name'] for a in data], ['ch_test'])
        self.database.connection.Execute('alter table public.categories drop constraint ch_test')

    def test_get_excludes_postgresql_nosession(self):
        response = self.client_nosession.post('/get_excludes_postgresql/')
        assert 401 == response.status_code


    def test_get_excludes_postgresql_session(self):
        self.database.connection.Execute('alter table public.categories drop constraint if exists ex_test')
        self.database.connection.Execute('alter table public.categories add constraint ex_test exclude (categoryname with = )')
        response = self.client_session.post('/get_excludes_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert data[0]['constraint_name'] == 'ex_test'
        self.database.connection.Execute('alter table public.categories drop constraint ex_test')

    def test_get_rules_postgresql_nosession(self):
        response = self.client_nosession.post('/get_rules_postgresql/')
        assert 401 == response.status_code

    def test_get_rules_postgresql_session(self):
        self.database.connection.Execute('create or replace rule ru_test as on delete to public.categories do instead nothing')
        response = self.client_session.post('/get_rules_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['rule_name'] for a in data], ['ru_test'])
        self.database.connection.Execute('drop rule ru_test on public.categories')

    def test_get_rule_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_rule_definition_postgresql/')
        assert 401 == response.status_code

    def test_get_rule_definition_postgresql_session(self):
        self.database.connection.Execute('create or replace rule ru_test as on delete to public.categories do instead nothing')
        response = self.client_session.post('/get_rule_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories", "rule": "ru_test"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert '''CREATE OR REPLACE RULE ru_test AS
    ON DELETE TO public.categories DO INSTEAD NOTHING;''' in data['data']
        self.database.connection.Execute('drop rule ru_test on public.categories')

    def test_get_triggerfunctions_postgresql_nosession(self):
        response = self.client_nosession.post('/get_triggerfunctions_postgresql/')
        assert 401 == response.status_code

    def test_get_triggerfunctions_postgresql_session(self):
        self.database.connection.Execute("create or replace function public.tg_ins_category() returns trigger language plpgsql as $function$begin new.categoryname := old.categoryname || ' modified'; end;$function$")
        response = self.client_session.post('/get_triggerfunctions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['name'] for a in data], ['tg_ins_category'])
        self.database.connection.Execute('drop function tg_ins_category()')

    def test_get_triggerfunction_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_triggerfunction_definition_postgresql/')
        assert 401 == response.status_code

    def test_get_triggerfunction_definition_postgresql_session(self):
        self.database.connection.Execute("create or replace function public.tg_ins_category() returns trigger language plpgsql as $function$begin new.categoryname := old.categoryname || ' modified'; end;$function$")
        response = self.client_session.post('/get_triggerfunction_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "function": "public.tg_ins_category()"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert '''CREATE OR REPLACE FUNCTION public.tg_ins_category()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$begin new.categoryname := old.categoryname || ' modified'; end;$function$''' in data['data']

    def test_get_triggers_postgresql_nosession(self):
        response = self.client_nosession.post('/get_triggers_postgresql/')
        assert 401 == response.status_code

    def test_get_triggers_postgresql_session(self):
        self.database.connection.Execute("create or replace function public.tg_ins_category() returns trigger language plpgsql as $function$begin new.categoryname := old.categoryname || ' modified'; end;$function$")
        self.database.connection.Execute('create or replace trigger tg_ins before insert on public.categories for each statement execute procedure public.tg_ins_category()')
        response = self.client_session.post('/get_triggers_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['trigger_name'] for a in data], ['tg_ins'])
        self.database.connection.Execute('drop trigger tg_ins on public.categories')
        self.database.connection.Execute('drop function public.tg_ins_category()')

    def test_get_inheriteds_postgresql_nosession(self):
        response = self.client_nosession.post('/get_inheriteds_postgresql/')
        assert 401 == response.status_code

    def test_get_inheriteds_postgresql_session(self):
        self.database.connection.Execute('create table if not exists public.categories_p1 (check ( category < 100 )) inherits (public.categories)')
        response = self.client_session.post('/get_inheriteds_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "categories"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal(data, ['public.categories_p1'])
        self.database.connection.Execute('alter table public.categories_p1 no inherit public.categories')
        self.database.connection.Execute('drop table public.categories_p1')

    def test_get_mviews_postgresql_nosession(self):
        response = self.client_nosession.post('/get_mviews_postgresql/')
        assert 401 == response.status_code

    def test_get_mviews_postgresql_session(self):
        self.database.connection.Execute('create materialized view if not exists public.mvw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_mviews_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['name'] for a in data], ['mvw_omnidb_test'])
        self.database.connection.Execute('drop materialized view public.mvw_omnidb_test')

    def test_get_mviews_columns_postgresql_nosession(self):
        response = self.client_nosession.post('/get_mviews_columns_postgresql/')
        assert 401 == response.status_code

    def test_get_mviews_columns_postgresql_session(self):
        self.database.connection.Execute('create materialized view if not exists public.mvw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_mviews_columns_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "table": "mvw_omnidb_test"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['column_name'] for a in data], [
            'customerid',
            'firstname',
            'lastname',
            'totalamount'
        ])
        self.database.connection.Execute('drop materialized view public.mvw_omnidb_test')

    def test_get_mview_definition_postgresql_nosession(self):
        response = self.client_nosession.post('/get_mview_definition_postgresql/')
        assert 401 == response.status_code

    def test_get_mview_definition_postgresql_session(self):
        self.database.connection.Execute('create materialized view if not exists public.mvw_omnidb_test as select c.customerid, c.firstname, c.lastname, sum(o.totalamount) as totalamount from customers c inner join orders o on o.customerid = c.customerid group by c.customerid, c.firstname, c.lastname')
        response = self.client_session.post('/get_mview_definition_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public", "view": "mvw_omnidb_test"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert '''DROP MATERIALIZED VIEW public.mvw_omnidb_test;

CREATE MATERIALIZED VIEW public.mvw_omnidb_test AS
 SELECT c.customerid,
    c.firstname,
    c.lastname,
    sum(o.totalamount) AS totalamount
   FROM (customers c
     JOIN orders o ON ((o.customerid = c.customerid)))
  GROUP BY c.customerid, c.firstname, c.lastname;
''' in data['data']
        self.database.connection.Execute('drop materialized view public.mvw_omnidb_test')

    def test_get_extensions_postgresql_nosession(self):
        response = self.client_nosession.post('/get_extensions_postgresql/')
        assert 401 == response.status_code

    def test_get_extensions_postgresql_session(self):
        response = self.client_session.post('/get_extensions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert 'plpgsql' in [a['name'] for a in data], ['plpgsql']

    def test_get_physicalreplicationslots_postgresql_nosession(self):
        response = self.client_nosession.post('/get_physicalreplicationslots_postgresql/')
        assert 401 == response.status_code

    def test_get_physicalreplicationslots_postgresql_session(self):
        self.database.connection.Execute("select * from pg_create_physical_replication_slot('test_slot')")
        response = self.client_session.post('/get_physicalreplicationslots_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['name'] for a in data], ['test_slot'])
        self.database.connection.Execute("select pg_drop_replication_slot('test_slot')")

    def test_get_logicalreplicationslots_postgresql_nosession(self):
        response = self.client_nosession.post('/get_logicalreplicationslots_postgresql/')
        assert 401 == response.status_code

    def test_get_logicalreplicationslots_postgresql_session(self):
        self.database.connection.Execute("select * from pg_create_logical_replication_slot('test_slot', 'pgoutput')")
        response = self.client_session.post('/get_logicalreplicationslots_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert self.lists_equal([a['name'] for a in data], ['test_slot'])
        self.database.connection.Execute("select pg_drop_replication_slot('test_slot')")

    def test_get_extension_details_postgresql_nosession(self):
        response = self.client_nosession.post('/get_extension_details/')
        assert 401 == response.status_code

    def test_get_extension_details_postgresql_session(self):
        response = self.client_session.post('/get_extension_details/', {'data': '{"database_index": 0, "ext_name": "nonexistentextension", "workspace_id": 0}'})
        assert 400 == response.status_code
        data = json.loads(response.content.decode())
        assert "does not exist" in data['data']

        response = self.client_session.post('/get_extension_details/', {'data': '{"database_index": 0, "ext_name": "plpgsql", "workspace_id": 0}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert data['name'] == 'plpgsql'

    # TODO: extract these tests into separate test set
    def test_execute_query_postgresql_session(self):
        response = self.client_session.post('/execute_query/', {'data': '{"database_index": 0, "workspace_id": 0, "query": "select 1=1"}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert data['status'] == 'success'

    def test_execute_query_postgresql_nosession(self):
        response = self.client_nosession.post('/execute_query/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 401 == response.status_code

    def test_get_available_extensions_postgresql_session(self):
        response = self.client_session.post('/get_available_extensions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert len(data['available_extensions']) > 0

    def test_get_available_extensions_postgresql_nosession(self):
        response = self.client_nosession.post('/get_available_extensions_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 401 == response.status_code

    def test_get_object_description_postgresql_session(self):
        # just get something with a valid oid to run tests on
        response = self.client_session.post('/get_tables_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0, "schema": "public"}'})
        data = json.loads(response.content.decode())
        table_data = data[0]
        request_params = '{"database_index": 0, "workspace_id": 0, "object_type": "table", "position": 0, "oid":' + table_data['oid'] + '}'
        response = self.client_session.post('/get_object_description_postgresql/', {'data': request_params})
        assert 200 == response.status_code
        data = json.loads(response.content.decode())
        assert "COMMENT" in data['data']

    def test_get_object_description_postgresql_nosession(self):
        response = self.client_nosession.post('/get_object_description_postgresql/', {'data': '{"database_index": 0, "workspace_id": 0}'})
        assert 401 == response.status_code
