import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from functools import partial

from app.include import OmniDatabase
from app.models import Connection, Technology
from app.tests.utils_testing import USERS, execute_client_login
from app.views.tree_sqlite import (get_columns, get_fks, get_fks_columns,
                                   get_indexes, get_indexes_columns, get_pk,
                                   get_pk_columns, get_properties,
                                   get_table_definition, get_tables,
                                   get_tree_info, get_triggers, get_uniques,
                                   get_uniques_columns, get_view_definition,
                                   get_views, get_views_columns,
                                   template_insert, template_select,
                                   template_update)
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import resolve, reverse


class SQLiteTreeTests(TestCase):

    URLS = {
        "get_tree_info_sqlite": ("/get_tree_info_sqlite/", get_tree_info),
        "get_tables_sqlite": ("/get_tables_sqlite/", get_tables),
        "get_columns_sqlite": ("/get_columns_sqlite/", get_columns),
        "get_pk_sqlite": ("/get_pk_sqlite/", get_pk),
        "get_pk_columns_sqlite": ("/get_pk_columns_sqlite/", get_pk_columns),
        "get_fks_sqlite": ("/get_fks_sqlite/", get_fks),
        "get_fks_columns_sqlite": ("/get_fks_columns_sqlite/", get_fks_columns),
        "get_uniques_sqlite": ("/get_uniques_sqlite/", get_uniques),
        "get_uniques_columns_sqlite": ("/get_uniques_columns_sqlite/", get_uniques_columns),
        "get_indexes_sqlite": ("/get_indexes_sqlite/", get_indexes),
        "get_indexes_columns_sqlite": ("/get_indexes_columns_sqlite/", get_indexes_columns),
        "get_views_sqlite": ("/get_views_sqlite/", get_views),
        "get_views_columns_sqlite": ("/get_views_columns_sqlite/", get_views_columns),
        "get_triggers_sqlite": ("/get_triggers_sqlite/", get_triggers),
        "template_select_sqlite": ("/template_select_sqlite/", template_select),
        "template_insert_sqlite": ("/template_insert_sqlite/", template_insert),
        "template_update_sqlite": ("/template_update_sqlite/", template_update),
        "get_properties_sqlite": ("/get_properties_sqlite/", get_properties),
        "get_table_definition_sqlite": ("/get_table_definition_sqlite/", get_table_definition),
        "get_view_definition_sqlite": ("/get_view_definition_sqlite/", get_view_definition),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.sqlite_path = os.path.join(cls._tmpdir.name, "tree_sqlite_tests.db")

        con = sqlite3.connect(cls.sqlite_path)
        try:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE test_users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER
                );
            """
            )
            cur.execute(
                """
                CREATE TABLE test_posts (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    FOREIGN KEY(user_id) REFERENCES test_users(id)
                );
            """
            )
            cur.execute("INSERT INTO test_users(name, age) VALUES ('Alice', 30), ('Bob', NULL);")
            cur.execute("INSERT INTO test_posts(user_id, title) VALUES (1, 'Hello'), (1, 'Second');")

            cur.execute(
                """
                CREATE VIEW v_test_users AS
                SELECT id, name FROM test_users;
                """
            )

            cur.execute(
                """
                CREATE TRIGGER trg_test_posts_ai
                AFTER INSERT ON test_posts
                BEGIN
                  UPDATE test_users SET age = age WHERE id = NEW.user_id;
                END;
                """
            )
            con.commit()
        finally:
            con.close()

        cls.db_type = "sqlite"

        cls.test_connection = Connection.objects.create(
            user=User.objects.get(username="admin"),
            technology=Technology.objects.filter(name=cls.db_type).first(),
            server="",
            port="",
            database=cls.sqlite_path,
            alias="SQLite Tree Tests",
        )

        cls.database = OmniDatabase.Generic.InstantiateDatabase(
            cls.db_type, "", "", cls.sqlite_path, "", 0, cls.test_connection.id
        )

        cls.database.GetVersion()
        cls.tab_data = {"database_index": 0, "workspace_id": 0}

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            cls._tmpdir.cleanup()
        except Exception:
            pass

    def setUp(self):
        self.user = {
            "user": USERS["ADMIN"]["USER"],
            "password": USERS["ADMIN"]["PASSWORD"],
        }

        execute_client_login(
            p_client=self.client,
            p_username=self.user["user"],
            p_password=self.user["password"],
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
        session["pgmanage_session"].tabs_databases = {0: self.sqlite_path}
        session.save()

        self.client.post = partial(self.client.post, content_type="application/json")

    def test_urls_resolve_to_expected_views(self):
        for url_name, (path, view_func) in self.URLS.items():
            with self.subTest(url_name=url_name):
                match = resolve(path)
                self.assertEqual(match.func.__name__, view_func.__name__)

    def test_get_tree_info_sqlite(self):
        response = self.client.post(reverse("get_tree_info_sqlite"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        expected_keys = [
            "version",
            "create_view",
            "drop_view",
            "create_table",
            "alter_table",
            "drop_table",
            "create_column",
            "create_index",
            "reindex",
            "drop_index",
            "delete",
            "create_trigger",
            "alter_trigger",
            "drop_trigger",
        ]

        self.assertEqual(sorted(list(data.keys())), sorted(expected_keys))
        self.assertTrue(isinstance(data["version"], str) and len(data["version"]) > 0)
        self.assertTrue(isinstance(data["create_table"], str) and len(data["create_table"]) > 0)

    def test_get_tables_sqlite(self):
        response = self.client.post(reverse("get_tables_sqlite"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        tables = response.json()
        self.assertIsInstance(tables, list)

        names = sorted([t["name"] for t in tables])
        self.assertIn("test_users", names)
        self.assertIn("test_posts", names)

        self.assertIn("name", tables[0])
        self.assertIn("name_raw", tables[0])

    def test_get_columns_sqlite(self):
        response = self.client.post(reverse("get_columns_sqlite"), data={"table": "test_users", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        cols = response.json()
        self.assertIsInstance(cols, list)
        self.assertGreaterEqual(len(cols), 3)

        cols_by_name = {c["column_name"]: c for c in cols}
        self.assertIn("id", cols_by_name)
        self.assertIn("name", cols_by_name)
        self.assertIn("age", cols_by_name)

        for cname in ("id", "name", "age"):
            self.assertIn("data_type", cols_by_name[cname])
            self.assertIn("data_length", cols_by_name[cname])
            self.assertIn("nullable", cols_by_name[cname])

    def test_get_pk_sqlite(self):
        response = self.client.post(reverse("get_pk_sqlite"), data={"table": "test_users", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        pks = response.json()
        self.assertIsInstance(pks, list)

    def test_get_pk_columns_sqlite(self):
        response = self.client.post(reverse("get_pk_columns_sqlite"), data={"table": "test_users", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        cols = response.json()
        self.assertIsInstance(cols, list)
        self.assertIn("id", cols)

    def test_get_fks_sqlite(self):
        response = self.client.post(reverse("get_fks_sqlite"), data={"table": "test_posts", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        fks = response.json()
        self.assertIsInstance(fks, list)
        self.assertGreaterEqual(len(fks), 1)

        fk0 = fks[0]
        for key in (
            "constraint_name",
            "column_name",
            "table_name",
            "r_table_name",
            "r_column_name",
            "on_update",
            "on_delete",
        ):
            self.assertIn(key, fk0)

    def test_get_fks_columns_sqlite(self):
        response_fks = self.client.post(
            reverse("get_fks_sqlite"),
            data={"table": "test_posts", **self.tab_data},
        )
        self.assertEqual(response_fks.status_code, 200)
        fks = response_fks.json()
        self.assertGreaterEqual(len(fks), 1)

        constraint = fks[0]["constraint_name"]

        response = self.client.post(
            reverse("get_fks_columns_sqlite"), data={"table": "test_posts", "fkey": constraint, **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        fk = response.json()
        self.assertIsInstance(fk, dict)
        self.assertTrue(len(fk.keys()) >= 0)

    def test_get_uniques_sqlite(self):
        response = self.client.post(reverse("get_uniques_sqlite"), data={"table": "test_users", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        uniques = response.json()
        self.assertIsInstance(uniques, list)

    def test_get_indexes_sqlite(self):
        response = self.client.post(reverse("get_indexes_sqlite"), data={"table": "test_users", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        indexes = response.json()
        self.assertIsInstance(indexes, list)

        for idx in indexes:
            for key in ("index_name", "unique", "type", "is_primary", "columns", "predicate"):
                self.assertIn(key, idx)

    def test_get_views_sqlite(self):
        response = self.client.post(reverse("get_views_sqlite"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)

        views = response.json()
        self.assertIsInstance(views, list)

        names = sorted([v["name"] for v in views])
        self.assertIn("v_test_users", names)

        self.assertIn("name", views[0])
        self.assertIn("name_raw", views[0])

    def test_get_views_columns_sqlite(self):
        response = self.client.post(
            reverse("get_views_columns_sqlite"), data={"table": "v_test_users", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        cols = response.json()
        self.assertIsInstance(cols, list)
        self.assertGreaterEqual(len(cols), 1)

        col0 = cols[0]
        for key in ("column_name", "data_type", "data_length"):
            self.assertIn(key, col0)

    def test_get_triggers_sqlite(self):
        response = self.client.post(reverse("get_triggers_sqlite"), data={"table": "test_posts", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        triggers = response.json()
        self.assertIsInstance(triggers, list)
        self.assertIn("trg_test_posts_ai", triggers)

    def test_template_select_sqlite(self):
        response = self.client.post(
            reverse("template_select_sqlite"), data={"table": "test_users", "kind": "t", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("template", data)
        self.assertIsInstance(data["template"], str)
        self.assertGreater(len(data["template"]), 0)

    def test_template_insert_sqlite(self):
        response = self.client.post(reverse("template_insert_sqlite"), data={"table": "test_users", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("template", data)
        self.assertIsInstance(data["template"], str)
        self.assertGreater(len(data["template"]), 0)

    def test_template_update_sqlite(self):
        response = self.client.post(reverse("template_update_sqlite"), data={"table": "test_users", **self.tab_data})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("template", data)
        self.assertIsInstance(data["template"], str)
        self.assertGreater(len(data["template"]), 0)

    def test_get_properties_sqlite(self):
        response = self.client.post(
            reverse("get_properties_sqlite"),
            data={
                "data": {"table": "test_users", "object": "test_users", "type": "table"},
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("properties", data)
        self.assertIn("ddl", data)
        self.assertIsInstance(data["properties"], list)
        self.assertIsInstance(data["ddl"], str)

    def test_get_table_definition_sqlite(self):
        response = self.client.post(
            reverse("get_table_definition_sqlite"), data={"table": "test_users", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("data", data)
        cols = data["data"]
        self.assertIsInstance(cols, list)
        self.assertGreaterEqual(len(cols), 1)

        col0 = cols[0]
        for key in ("name", "data_type", "default_value", "nullable", "is_primary"):
            self.assertIn(key, col0)

        by_name = {c["name"]: c for c in cols}
        self.assertIn("id", by_name)
        self.assertTrue(by_name["id"]["is_primary"])

    def test_get_view_definition_sqlite(self):
        response = self.client.post(
            reverse("get_view_definition_sqlite"), data={"view": "v_test_users", **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("data", data)
        self.assertIsInstance(data["data"], str)
        self.assertIn("SELECT", data["data"].upper())
