import unittest
from datetime import datetime, timedelta
from functools import partial
from unittest.mock import patch

from app.include import OmniDatabase
from app.include.OmniDatabase.MSSQL import MSSQL
from app.models import Connection, Technology
from app.tests.utils_testing import USERS, execute_client_login
from app.utils.crypto import encrypt
from app.views.tree_mssql import (
    get_checks,
    get_columns,
    get_databases,
    get_database_roles,
    get_fks,
    get_fks_columns,
    get_function_fields,
    get_functions,
    get_indexes,
    get_indexes_columns,
    get_logins,
    get_pk,
    get_pk_columns,
    get_procedure_fields,
    get_procedures,
    get_properties,
    get_schemas,
    get_server_roles,
    get_statistics,
    get_table_definition,
    get_tables,
    get_triggers,
    get_tree_info,
    get_types,
    get_uniques,
    get_uniques_columns,
    get_users,
    get_views,
    get_views_columns,
    template_select,
)
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

User = get_user_model()

# Every DDL template the get_tree_info_mssql endpoint should expose, mapped to
# a keyword expected in its text. A substring check is used instead of exact
# whole-template equality (see test_postgresql12.py) so that documentation or
# whitespace tweaks to the template text don't break dozens of tests at once.
EXPECTED_TEMPLATE_KEYWORDS = {
    "create_user": "CREATE USER",
    "alter_user": "ALTER USER",
    "drop_user": "DROP USER",
    "create_login": "CREATE LOGIN",
    "alter_login": "ALTER LOGIN",
    "drop_login": "DROP LOGIN",
    "create_database_role": "CREATE ROLE",
    "alter_database_role": "ALTER ROLE",
    "drop_database_role": "DROP ROLE",
    "create_server_role": "CREATE SERVER ROLE",
    "alter_server_role": "ALTER SERVER ROLE",
    "drop_server_role": "DROP SERVER ROLE",
    "create_database": "CREATE DATABASE",
    "alter_database": "ALTER DATABASE",
    "drop_database": "DROP DATABASE",
    "create_schema": "CREATE SCHEMA",
    "drop_schema": "DROP SCHEMA",
    "create_function": "CREATE",
    "alter_function": "ALTER FUNCTION",
    "drop_function": "DROP FUNCTION",
    "create_procedure": "CREATE",
    "alter_procedure": "ALTER",
    "drop_procedure": "DROP PROCEDURE",
    "create_view": "CREATE",
    "alter_view": "ALTER VIEW",
    "drop_view": "DROP VIEW",
    "drop_table": "DROP TABLE",
    "create_trigger": "CREATE",
    "drop_trigger": "DROP TRIGGER",
    "create_statistics": "CREATE STATISTICS",
    "drop_statistics": "DROP STATISTICS",
    "create_type": "CREATE TYPE",
    "drop_type": "DROP TYPE",
}


class MSSQLTreeURLTests(TestCase):
    """URL wiring and auth-boundary checks. These don't touch a real MSSQL
    connection, so they run (and provide coverage) even when the MSSQL test
    container isn't up - unlike MSSQLTreeTests below, which needs it.
    """

    URLS = {
        "get_tree_info_mssql": ("/get_tree_info_mssql/", get_tree_info),
        "get_databases_mssql": ("/get_databases_mssql/", get_databases),
        "get_schemas_mssql": ("/get_schemas_mssql/", get_schemas),
        "get_tables_mssql": ("/get_tables_mssql/", get_tables),
        "get_columns_mssql": ("/get_columns_mssql/", get_columns),
        "get_pk_mssql": ("/get_pk_mssql/", get_pk),
        "get_pk_columns_mssql": ("/get_pk_columns_mssql/", get_pk_columns),
        "get_fks_mssql": ("/get_fks_mssql/", get_fks),
        "get_fks_columns_mssql": ("/get_fks_columns_mssql/", get_fks_columns),
        "get_uniques_mssql": ("/get_uniques_mssql/", get_uniques),
        "get_uniques_columns_mssql": ("/get_uniques_columns_mssql/", get_uniques_columns),
        "get_checks_mssql": ("/get_checks_mssql/", get_checks),
        "get_views_mssql": ("/get_views_mssql/", get_views),
        "get_views_columns_mssql": ("/get_views_columns_mssql/", get_views_columns),
        "get_procedures_mssql": ("/get_procedures_mssql/", get_procedures),
        "get_procedure_fields_mssql": ("/get_procedure_fields_mssql/", get_procedure_fields),
        "get_statistics_mssql": ("/get_statistics_mssql/", get_statistics),
        "get_functions_mssql": ("/get_functions_mssql/", get_functions),
        "get_function_fields_mssql": ("/get_function_fields_mssql/", get_function_fields),
        "get_indexes_mssql": ("/get_indexes_mssql/", get_indexes),
        "get_indexes_columns_mssql": ("/get_indexes_columns_mssql/", get_indexes_columns),
        "get_triggers_mssql": ("/get_triggers_mssql/", get_triggers),
        "get_server_roles_mssql": ("/get_server_roles_mssql/", get_server_roles),
        "get_database_roles_mssql": ("/get_database_roles_mssql/", get_database_roles),
        "get_logins_mssql": ("/get_logins_mssql/", get_logins),
        "get_users_mssql": ("/get_users_mssql/", get_users),
        "template_select_mssql": ("/template_select_mssql/", template_select),
        "get_properties_mssql": ("/get_properties_mssql/", get_properties),
        "get_table_definition_mssql": ("/get_table_definition_mssql/", get_table_definition),
        "get_types_mssql": ("/get_types_mssql/", get_types),
    }

    def test_urls_resolve_to_expected_views(self):
        for url_name, (path, view_func) in self.URLS.items():
            with self.subTest(url_name=url_name):
                match = resolve(path)
                self.assertEqual(match.func.__name__, view_func.__name__)

    def test_unauthenticated_access_denied(self):
        response = self.client.post(
            reverse("get_tree_info_mssql"),
            data={"database_index": 0, "workspace_id": 0},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)


class MSSQLTreeTests(TestCase):
    """Integration tests against a live MSSQL server + Northwind fixture (see
    docker-compose.yml / fetch-test-data.sh). Skipped as a whole class if that
    server isn't reachable.
    """

    HOST = "127.0.0.1"
    PORT = "1434"
    SERVICE = "northwind_test"
    ROLE = "sa"
    PASSWORD = "Audax_2026!"

    @classmethod
    def setUpClass(cls):
        cls.db_type = "mssql"

        # Probe connectivity before calling super().setUpClass(): Django's
        # TestCase.setUpClass() opens a class-level atomic block that's only
        # unwound by tearDownClass(), which unittest does NOT call if
        # setUpClass() raises (including via SkipTest) - so skipping after
        # entering that block would leave it open and contaminate later
        # test classes. Doing the check first means there's nothing to unwind.
        database = OmniDatabase.Generic.InstantiateDatabase(
            cls.db_type, cls.HOST, cls.PORT, cls.SERVICE, cls.ROLE, 0, 0
        )
        database.connection.password = cls.PASSWORD

        # MSSQL.GetVersion()/major_version swallow connection errors internally
        # and just return None instead of raising, so a failed connection has
        # to be detected by checking the result rather than catching an exception
        database.GetVersion()
        if database.major_version is None:
            raise unittest.SkipTest(
                f"MSSQL test database is not reachable at {cls.HOST}:{cls.PORT} - "
                f"start it with `docker compose up` in app/tests (see fetch-test-data.sh "
                f"to fetch the Northwind fixture first)."
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
            alias="PgManage MSSQL Tests",
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

    def test_get_tree_info_mssql(self):
        response = self.client.post(reverse("get_tree_info_mssql"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("version", data)
        self.assertIn("major_version", data)
        self.assertEqual(data["major_version"], self.database.major_version)

        templates = data["templates"]
        self.assertEqual(sorted(templates.keys()), sorted(EXPECTED_TEMPLATE_KEYWORDS.keys()))

        for key, keyword in EXPECTED_TEMPLATE_KEYWORDS.items():
            with self.subTest(template=key):
                text = templates[key]
                self.assertIsInstance(text, str)
                self.assertGreater(len(text), 0)
                self.assertIn(keyword, text)

    def test_get_databases_mssql(self):
        response = self.client.post(reverse("get_databases_mssql"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn(self.SERVICE, [d["name"] for d in data])

    def test_get_schemas_mssql(self):
        response = self.client.post(reverse("get_schemas_mssql"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("dbo", [s["name"] for s in data])

    def test_get_tables_mssql(self):
        response = self.client.post(reverse("get_tables_mssql"), data={"schema": "dbo", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        tables = response.json()
        self.assertIsInstance(tables, list)
        for name in ("Customers", "Orders", "Products", "Categories"):
            self.assertIn(name, tables)

    def test_get_columns_mssql(self):
        response = self.client.post(
            reverse("get_columns_mssql"), data={"table": "Customers", "schema": "dbo", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        cols_by_name = {c["column_name"]: c for c in response.json()}
        self.assertIn("CustomerID", cols_by_name)
        self.assertIn("CompanyName", cols_by_name)

        self.assertEqual(cols_by_name["CustomerID"]["data_type"], "nchar")
        self.assertEqual(cols_by_name["CustomerID"]["nullable"], "False")
        self.assertEqual(cols_by_name["ContactName"]["nullable"], "True")

    def test_get_pk_mssql(self):
        response = self.client.post(
            reverse("get_pk_mssql"), data={"table": "Customers", "schema": "dbo", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual([pk["constraint_name"] for pk in data], ["PK_Customers"])

    def test_get_pk_columns_mssql(self):
        response = self.client.post(
            reverse("get_pk_columns_mssql"),
            data={"key": "PK_Customers", "table": "Customers", "schema": "dbo", **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["CustomerID"])

    def test_get_fks_mssql(self):
        response = self.client.post(
            reverse("get_fks_mssql"), data={"table": "Orders", "schema": "dbo", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        fks_by_name = {fk["constraint_name"]: fk for fk in response.json()}
        self.assertIn("FK_Orders_Customers", fks_by_name)

        fk = fks_by_name["FK_Orders_Customers"]
        self.assertEqual(fk["column_name"], "CustomerID")
        self.assertEqual(fk["table_name"], "Orders")
        self.assertEqual(fk["r_table_name"], "Customers")
        self.assertEqual(fk["r_column_name"], "CustomerID")

    def test_get_fks_columns_mssql(self):
        response = self.client.post(
            reverse("get_fks_columns_mssql"),
            data={
                "fkey": "FK_Orders_Customers",
                "table": "Orders",
                "schema": "dbo",
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["column_name"], "CustomerID")
        self.assertEqual(data[0]["r_column_name"], "CustomerID")
        self.assertEqual(data[0]["r_table_name"], "Customers")

    def test_get_uniques_mssql(self):
        self.database.connection.Execute(
            "IF EXISTS (SELECT * FROM sys.key_constraints WHERE name = 'UQ_test_mssql') "
            "ALTER TABLE dbo.Categories DROP CONSTRAINT UQ_test_mssql"
        )
        self.database.connection.Execute(
            "ALTER TABLE dbo.Categories ADD CONSTRAINT UQ_test_mssql UNIQUE (CategoryName)"
        )
        try:
            response = self.client.post(
                reverse("get_uniques_mssql"), data={"table": "Categories", "schema": "dbo", **self.tab_data}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual([u["constraint_name"] for u in data], ["UQ_test_mssql"])
        finally:
            self.database.connection.Execute("ALTER TABLE dbo.Categories DROP CONSTRAINT UQ_test_mssql")

    def test_get_uniques_columns_mssql(self):
        self.database.connection.Execute(
            "IF EXISTS (SELECT * FROM sys.key_constraints WHERE name = 'UQ_test_mssql') "
            "ALTER TABLE dbo.Categories DROP CONSTRAINT UQ_test_mssql"
        )
        self.database.connection.Execute(
            "ALTER TABLE dbo.Categories ADD CONSTRAINT UQ_test_mssql UNIQUE (CategoryName)"
        )
        try:
            response = self.client.post(
                reverse("get_uniques_columns_mssql"),
                data={
                    "unique": "UQ_test_mssql",
                    "table": "Categories",
                    "schema": "dbo",
                    **self.tab_data,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), ["CategoryName"])
        finally:
            self.database.connection.Execute("ALTER TABLE dbo.Categories DROP CONSTRAINT UQ_test_mssql")

    def test_get_checks_mssql(self):
        response = self.client.post(
            reverse("get_checks_mssql"), data={"table": "Products", "schema": "dbo", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        checks_by_name = {c["constraint_name"]: c for c in response.json()}
        self.assertIn("CK_Products_UnitPrice", checks_by_name)
        self.assertIn("UnitPrice", checks_by_name["CK_Products_UnitPrice"]["check_clause"])

    def test_get_views_mssql(self):
        response = self.client.post(reverse("get_views_mssql"), data={"schema": "dbo", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("Invoices", [v["name"] for v in data])

    def test_get_views_columns_mssql(self):
        response = self.client.post(
            reverse("get_views_columns_mssql"), data={"table": "Invoices", "schema": "dbo", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        cols = response.json()
        self.assertGreater(len(cols), 0)
        self.assertIn("ShipName", [c["column_name"] for c in cols])

    def test_get_procedures_mssql(self):
        response = self.client.post(reverse("get_procedures_mssql"), data={"schema": "dbo", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        procs_by_name = {p["name"]: p for p in data}
        self.assertIn("CustOrdersDetail", procs_by_name)
        self.assertIn("oid", procs_by_name["CustOrdersDetail"])

    def test_get_procedure_fields_mssql(self):
        response = self.client.post(
            reverse("get_procedure_fields_mssql"),
            data={"procedure": "CustOrdersDetail", "schema": "dbo", **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data, [{"name": "@OrderID int", "type": "I"}])

    def test_get_statistics_mssql(self):
        self.database.connection.Execute(
            "IF EXISTS (SELECT * FROM sys.stats WHERE name = 'ST_test_mssql' "
            "AND object_id = OBJECT_ID('dbo.Categories')) DROP STATISTICS dbo.Categories.ST_test_mssql"
        )
        self.database.connection.Execute("CREATE STATISTICS ST_test_mssql ON dbo.Categories(CategoryName)")
        try:
            response = self.client.post(
                reverse("get_statistics_mssql"), data={"table": "Categories", "schema": "dbo", **self.tab_data}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("ST_test_mssql", [s["statistic_name"] for s in data])
        finally:
            self.database.connection.Execute("DROP STATISTICS dbo.Categories.ST_test_mssql")

    def test_get_functions_mssql(self):
        self.database.connection.Execute(
            "IF OBJECT_ID('dbo.fn_test_mssql', 'FN') IS NOT NULL DROP FUNCTION dbo.fn_test_mssql"
        )
        self.database.connection.Execute(
            "CREATE FUNCTION dbo.fn_test_mssql(@Param1 int) RETURNS int AS BEGIN RETURN @Param1 END"
        )
        try:
            response = self.client.post(reverse("get_functions_mssql"), data={"schema": "dbo", **self.tab_data})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("fn_test_mssql", [f["name"] for f in data])
        finally:
            self.database.connection.Execute("DROP FUNCTION dbo.fn_test_mssql")

    def test_get_function_fields_mssql(self):
        self.database.connection.Execute(
            "IF OBJECT_ID('dbo.fn_test_mssql', 'FN') IS NOT NULL DROP FUNCTION dbo.fn_test_mssql"
        )
        self.database.connection.Execute(
            "CREATE FUNCTION dbo.fn_test_mssql(@Param1 int) RETURNS int AS BEGIN RETURN @Param1 END"
        )
        try:
            response = self.client.post(
                reverse("get_function_fields_mssql"),
                data={"function": "fn_test_mssql", "schema": "dbo", **self.tab_data},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn({"name": "@Param1 int", "type": "I"}, data)
        finally:
            self.database.connection.Execute("DROP FUNCTION dbo.fn_test_mssql")

    def test_get_indexes_mssql(self):
        response = self.client.post(
            reverse("get_indexes_mssql"), data={"table": "Orders", "schema": "dbo", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        indexes_by_name = {idx["index_name"]: idx for idx in response.json()}
        self.assertIn("CustomersOrders", indexes_by_name)
        self.assertEqual(indexes_by_name["CustomersOrders"]["columns"], ["CustomerID"])

        self.assertIn("PK_Orders", indexes_by_name)
        self.assertTrue(indexes_by_name["PK_Orders"]["is_primary"])
        self.assertTrue(indexes_by_name["PK_Orders"]["unique"])

    def test_get_indexes_columns_mssql(self):
        response = self.client.post(
            reverse("get_indexes_columns_mssql"),
            data={"index": "CustomersOrders", "table": "Orders", "schema": "dbo", **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["CustomerID"])

    def test_get_triggers_mssql(self):
        self.database.connection.Execute(
            "IF OBJECT_ID('dbo.trg_test_mssql', 'TR') IS NOT NULL DROP TRIGGER dbo.trg_test_mssql"
        )
        self.database.connection.Execute(
            "CREATE TRIGGER dbo.trg_test_mssql ON dbo.Categories AFTER INSERT AS BEGIN SET NOCOUNT ON; END"
        )
        try:
            response = self.client.post(
                reverse("get_triggers_mssql"), data={"table": "Categories", "schema": "dbo", **self.tab_data}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            triggers_by_name = {t["trigger_name"]: t for t in data}
            self.assertIn("trg_test_mssql", triggers_by_name)
            self.assertTrue(triggers_by_name["trg_test_mssql"]["enabled"])
        finally:
            self.database.connection.Execute("DROP TRIGGER dbo.trg_test_mssql")

    def test_get_server_roles_mssql(self):
        response = self.client.post(reverse("get_server_roles_mssql"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]
        self.assertIn("sysadmin", [r["name"] for r in data])

    def test_get_database_roles_mssql(self):
        response = self.client.post(reverse("get_database_roles_mssql"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]
        self.assertIn("db_owner", [r["name"] for r in data])

    def test_get_logins_mssql(self):
        response = self.client.post(reverse("get_logins_mssql"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]
        self.assertIn("sa", [r["name"] for r in data])

    def test_get_users_mssql(self):
        response = self.client.post(reverse("get_users_mssql"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()["data"]
        self.assertIn("dbo", [r["name"] for r in data])

    def test_template_select_mssql(self):
        response = self.client.post(
            reverse("template_select_mssql"),
            data={"table": "Customers", "schema": "dbo", "kind": "t", **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("template", data)
        self.assertIn("SELECT", data["template"].upper())
        self.assertIn("Customers", data["template"])

    def test_get_properties_mssql(self):
        response = self.client.post(
            reverse("get_properties_mssql"),
            data={
                "data": {"table": "Customers", "object": "Customers", "type": "table", "schema": "dbo"},
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        properties = dict(data["properties"])
        self.assertEqual(properties["Schema Name"], "dbo")
        self.assertEqual(properties["Table Name"], "Customers")
        self.assertIn("CREATE TABLE", data["ddl"])

    def test_get_table_definition_mssql(self):
        response = self.client.post(
            reverse("get_table_definition_mssql"), data={"table": "Customers", "schema": "dbo", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        cols_by_name = {c["name"]: c for c in response.json()["data"]}
        self.assertTrue(cols_by_name["CustomerID"]["is_primary"])
        self.assertFalse(cols_by_name["ContactName"]["is_primary"])
        self.assertTrue(cols_by_name["ContactName"]["nullable"])

    def test_get_types_mssql(self):
        self.database.connection.Execute("IF TYPE_ID('dbo.tp_test_mssql') IS NOT NULL DROP TYPE dbo.tp_test_mssql")
        self.database.connection.Execute("CREATE TYPE dbo.tp_test_mssql FROM int NOT NULL")
        try:
            response = self.client.post(reverse("get_types_mssql"), data={"schema": "dbo", **self.tab_data})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("tp_test_mssql", [t["type_name"] for t in data])
        finally:
            self.database.connection.Execute("DROP TYPE dbo.tp_test_mssql")

    def test_get_columns_error_response(self):
        with patch.object(MSSQL, "QueryTablesFields", side_effect=Exception("test error")):
            response = self.client.post(
                reverse("get_columns_mssql"), data={"table": "Customers", "schema": "dbo", **self.tab_data}
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "test error"})

    def test_get_schemas_error_response_uses_500(self):
        with patch.object(MSSQL, "QuerySchemas", side_effect=Exception("test error")):
            response = self.client.post(reverse("get_schemas_mssql"), data=self.tab_data)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"data": "test error"})

    def test_get_properties_error_response(self):
        with patch.object(MSSQL, "GetProperties", side_effect=Exception("test error")):
            response = self.client.post(
                reverse("get_properties_mssql"),
                data={
                    "data": {"table": "Customers", "object": "Customers", "type": "table", "schema": "dbo"},
                    **self.tab_data,
                },
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "test error"})
