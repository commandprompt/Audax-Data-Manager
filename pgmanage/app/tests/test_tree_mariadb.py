import unittest
from datetime import datetime, timedelta
from functools import partial
from types import SimpleNamespace
from unittest.mock import patch

from app.include import OmniDatabase
from app.include.OmniDatabase.MariaDB import MariaDB
from app.models import Connection, Technology
from app.tests.utils_testing import USERS, execute_client_login
from app.utils.crypto import encrypt
from app.views.tree_mariadb import (
    get_columns,
    get_databases,
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
    get_tables,
    get_tree_info,
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
    "create_role": "CREATE USER",
    "alter_role": "ALTER USER",
    "drop_role": "DROP USER",
    "create_database": "CREATE DATABASE",
    "alter_database": "ALTER DATABASE",
    "drop_database": "DROP DATABASE",
    "create_function": "CREATE FUNCTION",
    "drop_function": "DROP FUNCTION",
    "create_procedure": "CREATE PROCEDURE",
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
    "drop_primarykey": "DROP PRIMARY KEY",
    "create_unique": "UNIQUE",
    "drop_unique": "DROP CONSTRAINT",
    "create_foreignkey": "FOREIGN KEY",
    "drop_foreignkey": "DROP FOREIGN KEY",
    "create_index": "INDEX",
    "drop_index": "DROP INDEX",
    "delete": "DELETE FROM",
    "create_sequence": "CREATE SEQUENCE",
    "alter_sequence": "ALTER SEQUENCE",
    "drop_sequence": "DROP SEQUENCE",
}


class MariaDBTreeURLTests(TestCase):
    """URL wiring and auth-boundary checks. These do not open a MariaDB
    connection, so they run even when the MariaDB test container is down.
    """

    URLS = {
        "get_tree_info_mariadb": ("/get_tree_info_mariadb/", get_tree_info),
        "get_tables_mariadb": ("/get_tables_mariadb/", get_tables),
        "get_columns_mariadb": ("/get_columns_mariadb/", get_columns),
        "get_pk_mariadb": ("/get_pk_mariadb/", get_pk),
        "get_pk_columns_mariadb": ("/get_pk_columns_mariadb/", get_pk_columns),
        "get_fks_mariadb": ("/get_fks_mariadb/", get_fks),
        "get_fks_columns_mariadb": ("/get_fks_columns_mariadb/", get_fks_columns),
        "get_uniques_mariadb": ("/get_uniques_mariadb/", get_uniques),
        "get_uniques_columns_mariadb": ("/get_uniques_columns_mariadb/", get_uniques_columns),
        "get_indexes_mariadb": ("/get_indexes_mariadb/", get_indexes),
        "get_indexes_columns_mariadb": ("/get_indexes_columns_mariadb/", get_indexes_columns),
        "get_functions_mariadb": ("/get_functions_mariadb/", get_functions),
        "get_function_fields_mariadb": ("/get_function_fields_mariadb/", get_function_fields),
        "get_function_definition_mariadb": ("/get_function_definition_mariadb/", get_function_definition),
        "get_procedures_mariadb": ("/get_procedures_mariadb/", get_procedures),
        "get_procedure_fields_mariadb": ("/get_procedure_fields_mariadb/", get_procedure_fields),
        "get_procedure_definition_mariadb": ("/get_procedure_definition_mariadb/", get_procedure_definition),
        "get_sequences_mariadb": ("/get_sequences_mariadb/", get_sequences),
        "get_views_mariadb": ("/get_views_mariadb/", get_views),
        "get_views_columns_mariadb": ("/get_views_columns_mariadb/", get_views_columns),
        "get_view_definition_mariadb": ("/get_view_definition_mariadb/", get_view_definition),
        "get_databases_mariadb": ("/get_databases_mariadb/", get_databases),
        "get_roles_mariadb": ("/get_roles_mariadb/", get_roles),
        "kill_backend_mariadb": ("/kill_backend_mariadb/", kill_backend),
        "get_properties_mariadb": ("/get_properties_mariadb/", get_properties),
        "template_select_mariadb": ("/template_select_mariadb/", template_select),
        "template_insert_mariadb": ("/template_insert_mariadb/", template_insert),
        "template_update_mariadb": ("/template_update_mariadb/", template_update),
    }

    def test_urls_resolve_to_expected_views(self):
        for url_name, (path, view_func) in self.URLS.items():
            with self.subTest(url_name=url_name):
                match = resolve(path)
                self.assertEqual(match.func.__name__, view_func.__name__)
                self.assertEqual(match.func.__module__, "app.views.tree_mariadb")

    def test_url_names_point_at_the_mariadb_paths(self):
        for url_name, (path, _) in self.URLS.items():
            with self.subTest(url_name=url_name):
                self.assertEqual(reverse(url_name), path)

    def test_unauthenticated_access_denied(self):
        for url_name, (path, _) in self.URLS.items():
            with self.subTest(url_name=url_name):
                response = self.client.post(path, data={}, content_type="application/json")
                self.assertEqual(response.status_code, 401)


class MariaDBTreeTests(TestCase):
    """Integration tests against a live MariaDB server with the classicmodels
    fixture (see docker-compose.yml / fetch-test-data.sh). The whole class is
    skipped when that server is not reachable.
    """

    HOST = "127.0.0.1"
    PORT = "3308"
    SERVICE = "classicmodels"
    ROLE = "root"
    PASSWORD = "mariadb"

    @classmethod
    def setUpClass(cls):
        cls.db_type = "mariadb"

        database = OmniDatabase.Generic.InstantiateDatabase(
            cls.db_type, cls.HOST, cls.PORT, cls.SERVICE, cls.ROLE, 0, 0
        )
        database.connection.password = cls.PASSWORD

        try:
            database.GetVersion()
        except Exception:
            raise unittest.SkipTest(
                f"MariaDB test database is not reachable at {cls.HOST}:{cls.PORT} - "
                f"start it with `docker compose up` in app/tests (run "
                f"./fetch-test-data.sh classicmodels first to get the fixture)."
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
            alias="PgManage MariaDB Tests",
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
        response = self.post("get_tree_info_mariadb")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["database"], self.SERVICE)
        self.assertTrue(body["version"].startswith("MariaDB"))
        self.assertEqual(body["username"], self.ROLE)
        self.assertTrue(body["superuser"])

    def test_get_tree_info_gives_every_ddl_template(self):
        body = self.post("get_tree_info_mariadb").json()

        for key, keyword in EXPECTED_TEMPLATE_KEYWORDS.items():
            with self.subTest(template=key):
                self.assertIn(key, body)
                self.assertIn(keyword, body[key])

    def test_get_tables(self):
        response = self.post("get_tables_mariadb", schema=self.SERVICE)

        self.assertEqual(response.status_code, 200)
        tables = response.json()
        self.assertEqual(len(tables), 8)
        self.assertIn("customers", tables)
        self.assertIn("orderdetails", tables)

    def test_get_columns(self):
        response = self.post("get_columns_mariadb", schema=self.SERVICE, table="customers")

        self.assertEqual(response.status_code, 200)
        columns = response.json()
        self.assertEqual(len(columns), 13)

        first = columns[0]
        self.assertEqual(first["column_name"], "customerNumber")
        self.assertEqual(first["data_type"], "int")
        self.assertEqual(first["nullable"], "NO")
        self.assertIn("data_length", first)

    def test_get_pk(self):
        response = self.post("get_pk_mariadb", schema=self.SERVICE, table="customers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["pk_customers"])

    def test_get_pk_columns(self):
        response = self.post(
            "get_pk_columns_mariadb", schema=self.SERVICE, table="customers", key="pk_customers"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["customerNumber"])

    def test_get_pk_columns_of_a_composite_key(self):
        response = self.post(
            "get_pk_columns_mariadb",
            schema=self.SERVICE,
            table="orderdetails",
            key="pk_orderdetails",
        )

        self.assertEqual(response.json(), ["orderNumber", "productCode"])

    def test_get_fks(self):
        response = self.post("get_fks_mariadb", schema=self.SERVICE, table="orders")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["orders_ibfk_1"])

    def test_get_fks_columns(self):
        response = self.post(
            "get_fks_columns_mariadb",
            schema=self.SERVICE,
            table="orders",
            fkey="orders_ibfk_1",
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["column_name"], "customerNumber")
        self.assertEqual(body["r_column_name"], "customerNumber")
        self.assertEqual(body["r_table_name"], "customers")

    def test_get_fks_columns_of_an_unknown_key_gives_an_empty_object(self):
        response = self.post(
            "get_fks_columns_mariadb", schema=self.SERVICE, table="orders", fkey="missing"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_get_uniques(self):
        response = self.post("get_uniques_mariadb", schema=self.SERVICE, table="customers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_uniques_columns(self):
        response = self.post(
            "get_uniques_columns_mariadb",
            schema=self.SERVICE,
            table="customers",
            unique="missing",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_indexes(self):
        response = self.post("get_indexes_mariadb", schema=self.SERVICE, table="orders")

        self.assertEqual(response.status_code, 200)
        indexes = {index["index_name"]: index["uniqueness"] for index in response.json()}
        self.assertEqual(indexes, {"PRIMARY": "Unique", "customerNumber": "Non Unique"})

    def test_get_indexes_columns(self):
        response = self.post(
            "get_indexes_columns_mariadb",
            schema=self.SERVICE,
            table="orders",
            index="customerNumber",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["customerNumber"])

    def test_get_databases(self):
        response = self.post("get_databases_mariadb")

        self.assertEqual(response.status_code, 200)
        databases = response.json()
        names = [db["name"] for db in databases]
        self.assertIn(self.SERVICE, names)
        self.assertIn("mysql", names)
        self.assertFalse(any(db["pinned"] for db in databases))

    def test_get_databases_marks_a_pinned_database(self):
        self.test_connection.pinned_databases = [self.SERVICE]
        self.test_connection.save()
        self.addCleanup(self.reset_pinned_databases)

        databases = self.post("get_databases_mariadb").json()

        pinned = [db["name"] for db in databases if db["pinned"]]
        self.assertEqual(pinned, [self.SERVICE])

    def reset_pinned_databases(self):
        self.test_connection.pinned_databases = []
        self.test_connection.save()

    def test_get_roles(self):
        response = self.post("get_roles_mariadb")

        self.assertEqual(response.status_code, 200)
        roles = response.json()
        self.assertTrue(roles)
        self.assertTrue(all("name" in role for role in roles))
        self.assertTrue(any("root" in role["name"] for role in roles))

    def test_get_sequences(self):
        response = self.post("get_sequences_mariadb", schema=self.SERVICE)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_sequences_maps_each_row_to_its_name(self):
        rows = [{"sequence_name": "order_seq"}, {"sequence_name": "invoice_seq"}]
        with patch.object(MariaDB, "QuerySequences", return_value=SimpleNamespace(Rows=rows)):
            response = self.post("get_sequences_mariadb", schema=self.SERVICE)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [{"sequence_name": "order_seq"}, {"sequence_name": "invoice_seq"}],
        )

    def test_get_functions(self):
        response = self.post("get_functions_mariadb", schema=self.SERVICE)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_function_fields(self):
        response = self.post(
            "get_function_fields_mariadb", schema=self.SERVICE, function="missing"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_function_definition_of_an_unknown_function(self):
        response = self.post("get_function_definition_mariadb", function="missing")

        self.assertEqual(response.status_code, 400)

    def test_get_procedures(self):
        response = self.post("get_procedures_mariadb", schema=self.SERVICE)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_procedure_fields(self):
        response = self.post(
            "get_procedure_fields_mariadb", schema=self.SERVICE, procedure="missing"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_procedure_definition_of_an_unknown_procedure(self):
        response = self.post("get_procedure_definition_mariadb", procedure="missing")

        self.assertEqual(response.status_code, 400)

    def test_get_views(self):
        response = self.post("get_views_mariadb", schema=self.SERVICE)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_views_columns(self):
        response = self.post("get_views_columns_mariadb", schema=self.SERVICE, table="missing")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_view_definition_of_an_unknown_view(self):
        response = self.post("get_view_definition_mariadb", schema=self.SERVICE, view="missing")

        self.assertEqual(response.status_code, 400)

    def test_get_properties(self):
        response = self.post(
            "get_properties_mariadb",
            data={
                "schema": self.SERVICE,
                "table": "customers",
                "object": "customers",
                "type": "table",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        properties = dict(body["properties"])
        self.assertEqual(properties["Table Schema"], self.SERVICE)
        self.assertEqual(properties["Table Name"], "customers")
        self.assertEqual(properties["Table Type"], "BASE TABLE")
        self.assertIn("CREATE TABLE", body["ddl"])

    def test_get_properties_of_an_unknown_object(self):
        response = self.post(
            "get_properties_mariadb",
            data={
                "schema": self.SERVICE,
                "table": "customers",
                "object": "customers",
                "type": "bogus",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_template_select(self):
        response = self.post("template_select_mariadb", schema=self.SERVICE, table="customers")

        self.assertEqual(response.status_code, 200)
        template = response.json()["template"]
        self.assertIn("SELECT", template)
        self.assertIn("customerNumber", template)
        self.assertIn("customers", template)

    def test_template_insert(self):
        response = self.post("template_insert_mariadb", schema=self.SERVICE, table="customers")

        self.assertEqual(response.status_code, 200)
        template = response.json()["template"]
        self.assertIn(f"INSERT INTO {self.SERVICE}.customers", template)
        self.assertIn("customerName", template)

    def test_template_update(self):
        response = self.post("template_update_mariadb", schema=self.SERVICE, table="customers")

        self.assertEqual(response.status_code, 200)
        template = response.json()["template"]
        self.assertIn(f"UPDATE {self.SERVICE}.customers", template)
        self.assertIn("SET", template)

    def test_kill_backend(self):
        victim = OmniDatabase.Generic.InstantiateDatabase(
            self.db_type, self.HOST, self.PORT, self.SERVICE, self.ROLE, 0, 0
        )
        victim.connection.password = self.PASSWORD
        victim.connection.Open()
        self.addCleanup(self.close_quietly, victim)
        victim_pid = victim.connection.Query("select connection_id() as pid", True).Rows[0]["pid"]
        self.assertIn(victim_pid, self.live_backend_ids())

        response = self.post("kill_backend_mariadb", pid=victim_pid)

        self.assertEqual(response.status_code, 204)
        self.assertNotIn(victim_pid, self.live_backend_ids())

    def test_kill_backend_of_an_unknown_thread(self):
        response = self.post("kill_backend_mariadb", pid=999999)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown thread id", response.json()["data"])

    def live_backend_ids(self):
        return [row["Id"] for row in self.database.Query("show processlist", True).Rows]

    def close_quietly(self, database):
        try:
            database.connection.Close()
        except Exception:
            pass

    def test_get_tables_error_response(self):
        with patch.object(MariaDB, "QueryTables", side_effect=Exception("test error")):
            response = self.post("get_tables_mariadb", schema=self.SERVICE)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "test error"})

    def test_get_columns_error_response(self):
        with patch.object(MariaDB, "QueryTablesFields", side_effect=Exception("test error")):
            response = self.post("get_columns_mariadb", schema=self.SERVICE, table="customers")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "test error"})

    def test_get_tree_info_error_response(self):
        with patch.object(MariaDB, "GetName", side_effect=Exception("test error")):
            response = self.post("get_tree_info_mariadb")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "test error"})
