import unittest
from datetime import datetime, timedelta
from functools import partial
from types import SimpleNamespace
from unittest.mock import patch

from app.include import OmniDatabase
from app.include.OmniDatabase.Oracle import Oracle
from app.models import Connection, Technology
from app.tests.utils_testing import USERS, execute_client_login
from app.utils.crypto import encrypt
from app.views.tree_oracle import (
    get_columns,
    get_fks,
    get_fks_columns,
    get_function_definition,
    get_function_fields,
    get_functions,
    get_indexes,
    get_indexes_columns,
    get_pk,
    get_pk_columns,
    get_procedure_definition,
    get_procedure_fields,
    get_procedures,
    get_properties,
    get_roles,
    get_sequences,
    get_table_definition,
    get_tables,
    get_tablespaces,
    get_tree_info,
    get_types,
    get_uniques,
    get_uniques_columns,
    get_view_definition,
    get_views,
    get_views_columns,
    kill_backend,
    template_insert,
    template_select,
    template_update,
)
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

User = get_user_model()

EXPECTED_TEMPLATE_KEYWORDS = {
    "create_role": "ROLE",
    "alter_role": "ALTER",
    "drop_role": "DROP",
    "create_tablespace": "CREATE",
    "alter_tablespace": "ALTER",
    "drop_tablespace": "DROP",
    "create_sequence": "CREATE SEQUENCE",
    "alter_sequence": "ALTER SEQUENCE",
    "drop_sequence": "DROP SEQUENCE",
    "create_function": "CREATE OR REPLACE FUNCTION",
    "drop_function": "DROP FUNCTION",
    "create_procedure": "CREATE OR REPLACE PROCEDURE",
    "drop_procedure": "DROP PROCEDURE",
    "create_view": "VIEW",
    "drop_view": "DROP VIEW",
    "create_table": "TABLE",
    "alter_table": "ALTER TABLE",
    "drop_table": "DROP TABLE",
    "create_column": "ADD",
    "alter_column": "ALTER TABLE",
    "drop_column": "DROP COLUMN",
    "create_primarykey": "PRIMARY KEY",
    "drop_primarykey": "DROP",
    "create_unique": "UNIQUE",
    "drop_unique": "DROP",
    "create_foreignkey": "FOREIGN KEY",
    "drop_foreignkey": "DROP",
    "create_index": "INDEX",
    "alter_index": "INDEX",
    "drop_index": "DROP INDEX",
    "delete": "DELETE FROM",
}


class OracleTreeURLTests(TestCase):
    """URL wiring and auth-boundary checks. These do not open an Oracle
    connection, so they run even when the Oracle test container is down.
    """

    URLS = {
        "get_tree_info_oracle": ("/get_tree_info_oracle/", get_tree_info),
        "get_tables_oracle": ("/get_tables_oracle/", get_tables),
        "get_columns_oracle": ("/get_columns_oracle/", get_columns),
        "get_pk_oracle": ("/get_pk_oracle/", get_pk),
        "get_pk_columns_oracle": ("/get_pk_columns_oracle/", get_pk_columns),
        "get_fks_oracle": ("/get_fks_oracle/", get_fks),
        "get_fks_columns_oracle": ("/get_fks_columns_oracle/", get_fks_columns),
        "get_uniques_oracle": ("/get_uniques_oracle/", get_uniques),
        "get_uniques_columns_oracle": ("/get_uniques_columns_oracle/", get_uniques_columns),
        "get_indexes_oracle": ("/get_indexes_oracle/", get_indexes),
        "get_indexes_columns_oracle": ("/get_indexes_columns_oracle/", get_indexes_columns),
        "get_tablespaces_oracle": ("/get_tablespaces_oracle/", get_tablespaces),
        "get_roles_oracle": ("/get_roles_oracle/", get_roles),
        "get_functions_oracle": ("/get_functions_oracle/", get_functions),
        "get_function_fields_oracle": ("/get_function_fields_oracle/", get_function_fields),
        "get_function_definition_oracle": ("/get_function_definition_oracle/", get_function_definition),
        "get_procedures_oracle": ("/get_procedures_oracle/", get_procedures),
        "get_procedure_fields_oracle": ("/get_procedure_fields_oracle/", get_procedure_fields),
        "get_procedure_definition_oracle": ("/get_procedure_definition_oracle/", get_procedure_definition),
        "get_sequences_oracle": ("/get_sequences_oracle/", get_sequences),
        "get_views_oracle": ("/get_views_oracle/", get_views),
        "get_views_columns_oracle": ("/get_views_columns_oracle/", get_views_columns),
        "get_view_definition_oracle": ("/get_view_definition_oracle/", get_view_definition),
        "kill_backend_oracle": ("/kill_backend_oracle/", kill_backend),
        "get_properties_oracle": ("/get_properties_oracle/", get_properties),
        "template_select_oracle": ("/template_select_oracle/", template_select),
        "template_insert_oracle": ("/template_insert_oracle/", template_insert),
        "template_update_oracle": ("/template_update_oracle/", template_update),
        "get_types_oracle": ("/get_types_oracle/", get_types),
        "get_table_definition_oracle": ("/get_table_definition_oracle/", get_table_definition),
    }

    def test_urls_resolve_to_expected_views(self):
        for url_name, (path, view_func) in self.URLS.items():
            with self.subTest(url_name=url_name):
                match = resolve(path)
                self.assertEqual(match.func.__name__, view_func.__name__)
                self.assertEqual(match.func.__module__, "app.views.tree_oracle")

    def test_url_names_point_at_the_oracle_paths(self):
        for url_name, (path, _) in self.URLS.items():
            with self.subTest(url_name=url_name):
                self.assertEqual(reverse(url_name), path)

    def test_unauthenticated_access_denied(self):
        for url_name, (path, _) in self.URLS.items():
            with self.subTest(url_name=url_name):
                response = self.client.post(path, data={}, content_type="application/json")
                self.assertEqual(response.status_code, 401)


class OracleTreeTests(TestCase):
    """Integration tests against a live Oracle server with the HR sample schema
    (see docker-compose.yml / init-oracle.sh). The whole class is skipped when
    that server is not reachable.

    The tests log in as HR, the owner of the schema, because Oracle resolves
    DBMS_METADATA and some constraint views against the connected user. A
    SYSTEM connection makes get_table_definition, get_fks_columns and
    get_procedure_definition come back empty or fail.
    """

    HOST = "127.0.0.1"
    PORT = "1522"
    SERVICE = "FREEPDB1"
    ROLE = "hr"
    PASSWORD = "hr"
    SCHEMA = "HR"

    @classmethod
    def setUpClass(cls):
        cls.db_type = "oracle"

        database = OmniDatabase.Generic.InstantiateDatabase(
            cls.db_type, cls.HOST, cls.PORT, cls.SERVICE, cls.ROLE, 0, 0
        )
        database.connection.password = cls.PASSWORD

        try:
            database.GetVersion()
        except Exception:
            raise unittest.SkipTest(
                f"Oracle test database is not reachable at {cls.HOST}:{cls.PORT} - "
                f"start it with `docker compose up` in app/tests (the "
                f"oracle_test_db_init sidecar loads the HR sample schema)."
            )

        super().setUpClass()

        encrypted_password = encrypt(cls.PASSWORD, key=USERS["ADMIN"]["PASSWORD"])
        cls.test_connection = Connection.objects.create(
            user=User.objects.get(username="admin"),
            technology=Technology.objects.filter(name=cls.db_type).first(),
            server=cls.HOST,
            port=cls.PORT,
            database=cls.SERVICE,
            username=cls.ROLE,
            password=encrypted_password,
            alias="PgManage Oracle Tests",
        )
        database.conn_id = cls.test_connection.id
        cls.database = database

        cls.tab_data = {"database_index": 0, "workspace_id": 0}

    def setUp(self):
        execute_client_login(
            p_client=self.client,
            p_username=USERS["ADMIN"]["USER"],
            p_password=USERS["ADMIN"]["PASSWORD"],
        )
        session = self.client.session
        session["pgmanage_session"].databases = [
            {
                "database": self.database,
                "prompt_password": False,
                "prompt_timeout": datetime.now() + timedelta(seconds=60000),
            }
        ]
        session["pgmanage_session"].tab_connections = {0: self.database}
        session["pgmanage_session"].tabs_databases = {0: self.SERVICE}
        session.save()

        self.client.post = partial(self.client.post, content_type="application/json")

    def post(self, url_name, **payload):
        return self.client.post(reverse(url_name), data={**self.tab_data, **payload})

    def test_get_tree_info(self):
        response = self.post("get_tree_info_oracle")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["database"], self.SERVICE)
        self.assertEqual(body["username"], self.SCHEMA)
        self.assertTrue(body["version"].startswith("23."))
        self.assertIn("formatted_version", body)
        self.assertIn("express", body)

    def test_get_tree_info_gives_every_ddl_template(self):
        body = self.post("get_tree_info_oracle").json()

        for key, keyword in EXPECTED_TEMPLATE_KEYWORDS.items():
            with self.subTest(template=key):
                self.assertIn(key, body)
                self.assertIn(keyword, body[key])

    def test_get_tables(self):
        response = self.post("get_tables_oracle", schema=self.SCHEMA)

        self.assertEqual(response.status_code, 200)
        tables = [table["name_raw"] for table in response.json()]
        self.assertEqual(
            sorted(tables),
            ["COUNTRIES", "DEPARTMENTS", "EMPLOYEES", "JOBS", "JOB_HISTORY", "LOCATIONS", "REGIONS"],
        )

    def test_get_columns(self):
        response = self.post("get_columns_oracle", schema=self.SCHEMA, table="EMPLOYEES")

        self.assertEqual(response.status_code, 200)
        columns = response.json()
        self.assertEqual(len(columns), 11)

        first = columns[0]
        self.assertEqual(first["column_name"], "EMPLOYEE_ID")
        self.assertEqual(first["data_type"], "INTEGER")
        self.assertEqual(first["nullable"], "NO")

    def test_get_pk(self):
        response = self.post("get_pk_oracle", schema=self.SCHEMA, table="EMPLOYEES")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["EMP_EMP_ID_PK"])

    def test_get_pk_columns(self):
        response = self.post(
            "get_pk_columns_oracle", schema=self.SCHEMA, table="EMPLOYEES", key="EMP_EMP_ID_PK"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["EMPLOYEE_ID"])

    def test_get_fks(self):
        response = self.post("get_fks_oracle", schema=self.SCHEMA, table="EMPLOYEES")

        self.assertEqual(response.status_code, 200)
        fks = {fk["constraint_name"]: fk for fk in response.json()}
        self.assertEqual(set(fks), {"EMP_DEPT_FK", "EMP_JOB_FK", "EMP_MANAGER_FK"})

        department = fks["EMP_DEPT_FK"]
        self.assertEqual(department["column_name"], "DEPARTMENT_ID")
        self.assertEqual(department["r_table_name"], "DEPARTMENTS")
        self.assertEqual(department["r_column_name"], "DEPARTMENT_ID")
        self.assertEqual(department["table_schema"], self.SCHEMA)

    def test_get_fks_columns(self):
        response = self.post(
            "get_fks_columns_oracle",
            schema=self.SCHEMA,
            table="EMPLOYEES",
            fkey="EMP_DEPT_FK",
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["column_name"], "DEPARTMENT_ID")
        self.assertEqual(body["r_table_name"], "DEPARTMENTS")
        self.assertEqual(body["r_column_name"], "DEPARTMENT_ID")

    def test_get_uniques(self):
        response = self.post("get_uniques_oracle", schema=self.SCHEMA, table="EMPLOYEES")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["EMP_EMAIL_UK"])

    def test_get_uniques_columns(self):
        response = self.post(
            "get_uniques_columns_oracle",
            schema=self.SCHEMA,
            table="EMPLOYEES",
            unique="EMP_EMAIL_UK",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["EMAIL"])

    def test_get_indexes(self):
        response = self.post("get_indexes_oracle", schema=self.SCHEMA, table="EMPLOYEES")

        self.assertEqual(response.status_code, 200)
        indexes = {index["index_name"]: index for index in response.json()}
        self.assertEqual(
            set(indexes),
            {
                "EMP_DEPARTMENT_IX",
                "EMP_EMAIL_UK",
                "EMP_EMP_ID_PK",
                "EMP_JOB_IX",
                "EMP_MANAGER_IX",
                "EMP_NAME_IX",
            },
        )

        primary = indexes["EMP_EMP_ID_PK"]
        self.assertTrue(primary["is_primary"])
        self.assertTrue(primary["unique"])
        self.assertEqual(primary["columns"], ["EMPLOYEE_ID"])

        composite = indexes["EMP_NAME_IX"]
        self.assertFalse(composite["is_primary"])
        self.assertFalse(composite["unique"])
        self.assertEqual(composite["columns"], ["LAST_NAME", "FIRST_NAME"])

    def test_get_indexes_columns(self):
        response = self.post(
            "get_indexes_columns_oracle",
            schema=self.SCHEMA,
            table="EMPLOYEES",
            index="EMP_NAME_IX",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["LAST_NAME", "FIRST_NAME"])

    def test_get_tablespaces(self):
        response = self.post("get_tablespaces_oracle")

        self.assertEqual(response.status_code, 200)
        names = [tablespace["name"] for tablespace in response.json()]
        self.assertIn("USERS", names)
        self.assertIn("SYSTEM", names)

    def test_get_roles(self):
        response = self.post("get_roles_oracle")

        self.assertEqual(response.status_code, 200)
        roles = response.json()
        self.assertTrue(roles)
        self.assertIn(self.SCHEMA, [role["name"] for role in roles])

    def test_get_sequences(self):
        response = self.post("get_sequences_oracle", schema=self.SCHEMA)

        self.assertEqual(response.status_code, 200)
        names = [sequence["sequence_name"] for sequence in response.json()]
        self.assertEqual(
            sorted(names), ["DEPARTMENTS_SEQ", "EMPLOYEES_SEQ", "LOCATIONS_SEQ"]
        )

    def test_get_views(self):
        response = self.post("get_views_oracle", schema=self.SCHEMA)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([view["name"] for view in response.json()], ["EMP_DETAILS_VIEW"])

    def test_get_views_columns(self):
        response = self.post(
            "get_views_columns_oracle", schema=self.SCHEMA, table="EMP_DETAILS_VIEW"
        )

        self.assertEqual(response.status_code, 200)
        columns = response.json()
        self.assertEqual(len(columns), 16)
        self.assertEqual(columns[0]["column_name"], "EMPLOYEE_ID")

    def test_get_view_definition(self):
        response = self.post(
            "get_view_definition_oracle", schema=self.SCHEMA, view="EMP_DETAILS_VIEW"
        )

        self.assertEqual(response.status_code, 200)
        definition = response.json()["data"]
        self.assertIn("EMP_DETAILS_VIEW", definition)
        self.assertIn("SELECT", definition.upper())

    def test_get_procedures(self):
        response = self.post("get_procedures_oracle", schema=self.SCHEMA)

        self.assertEqual(response.status_code, 200)
        names = [procedure["name"] for procedure in response.json()]
        self.assertEqual(sorted(names), ["ADD_JOB_HISTORY", "SECURE_DML"])

    def test_get_procedure_fields(self):
        response = self.post(
            "get_procedure_fields_oracle", schema=self.SCHEMA, procedure="ADD_JOB_HISTORY"
        )

        self.assertEqual(response.status_code, 200)
        fields = response.json()
        self.assertEqual(len(fields), 5)
        self.assertTrue(any("P_EMP_ID" in field["name"] for field in fields))

    def test_get_procedure_definition(self):
        response = self.post(
            "get_procedure_definition_oracle", procedure="ADD_JOB_HISTORY"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("ADD_JOB_HISTORY", response.json()["data"])

    def test_get_functions(self):
        # The HR sample schema holds no functions, packages or types.
        response = self.post("get_functions_oracle", schema=self.SCHEMA)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_function_fields_of_an_unknown_function(self):
        response = self.post(
            "get_function_fields_oracle", schema=self.SCHEMA, function="MISSING"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_function_definition_of_an_unknown_function(self):
        response = self.post("get_function_definition_oracle", function="MISSING")

        self.assertEqual(response.status_code, 400)

    def test_get_functions_maps_each_row(self):
        # The HR schema holds no functions, so a stub row drives the mapping.
        rows = [{"name": "GET_BONUS", "id": "GET_BONUS"}]
        with patch.object(Oracle, "QueryFunctions", return_value=SimpleNamespace(Rows=rows)):
            response = self.post("get_functions_oracle", schema=self.SCHEMA)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"name": "GET_BONUS", "id": "GET_BONUS"}])

    def test_get_function_fields_maps_each_row(self):
        rows = [{"name": "P_SALARY NUMBER", "type": "I"}]
        with patch.object(Oracle, "QueryFunctionFields", return_value=SimpleNamespace(Rows=rows)):
            response = self.post(
                "get_function_fields_oracle", schema=self.SCHEMA, function="GET_BONUS"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"name": "P_SALARY NUMBER", "type": "I"}])

    def test_get_types_maps_each_row(self):
        rows = [{"type_name": "ADDRESS_TYPE"}]
        with patch.object(Oracle, "QueryTypes", return_value=SimpleNamespace(Rows=rows)):
            response = self.post("get_types_oracle", schema=self.SCHEMA)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"type_name": "ADDRESS_TYPE"}])

    def test_get_types(self):
        response = self.post("get_types_oracle", schema=self.SCHEMA)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_properties(self):
        response = self.post(
            "get_properties_oracle",
            data={
                "schema": self.SCHEMA,
                "table": "EMPLOYEES",
                "object": "EMPLOYEES",
                "type": "table",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        properties = dict(body["properties"])
        self.assertEqual(properties["Owner"], self.SCHEMA)
        self.assertEqual(properties["Object Name"], "EMPLOYEES")
        self.assertEqual(properties["Object Type"], "TABLE")
        self.assertIn("CREATE TABLE", body["ddl"])

    def test_get_table_definition(self):
        response = self.post(
            "get_table_definition_oracle", schema=self.SCHEMA, table="EMPLOYEES"
        )

        self.assertEqual(response.status_code, 200)
        columns = response.json()["data"]
        self.assertEqual(len(columns), 11)

        first = columns[0]
        self.assertEqual(first["name"], "EMPLOYEE_ID")
        self.assertEqual(first["data_type"], "number(6,0)")
        self.assertTrue(first["is_primary"])
        self.assertFalse(first["nullable"])
        self.assertIn("Primary key", first["comment"])

    def test_template_select(self):
        response = self.post("template_select_oracle", schema=self.SCHEMA, table="EMPLOYEES")

        self.assertEqual(response.status_code, 200)
        template = response.json()["template"]
        self.assertIn("SELECT", template)
        self.assertIn("EMPLOYEE_ID", template)

    def test_template_insert(self):
        response = self.post("template_insert_oracle", schema=self.SCHEMA, table="EMPLOYEES")

        self.assertEqual(response.status_code, 200)
        template = response.json()["template"]
        self.assertIn(f"INSERT INTO {self.SCHEMA}.EMPLOYEES", template)

    def test_template_update(self):
        response = self.post("template_update_oracle", schema=self.SCHEMA, table="EMPLOYEES")

        self.assertEqual(response.status_code, 200)
        template = response.json()["template"]
        self.assertIn(f"UPDATE {self.SCHEMA}.EMPLOYEES", template)
        self.assertIn("SET", template)

    def test_kill_backend_without_the_privilege(self):
        # HR owns the sample schema but holds no ALTER SYSTEM privilege.
        response = self.post("kill_backend_oracle", pid=999999)

        self.assertEqual(response.status_code, 400)
        self.assertIn("ORA-", response.json()["data"])

    def test_get_tables_error_response(self):
        with patch.object(Oracle, "QueryTables", side_effect=Exception("test error")):
            response = self.post("get_tables_oracle", schema=self.SCHEMA)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "test error"})

    def test_get_columns_error_response(self):
        with patch.object(Oracle, "QueryTablesFields", side_effect=Exception("test error")):
            response = self.post("get_columns_oracle", schema=self.SCHEMA, table="EMPLOYEES")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "test error"})

    def test_get_tree_info_error_response(self):
        with patch.object(Oracle, "GetName", side_effect=Exception("test error")):
            response = self.post("get_tree_info_oracle")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "test error"})
