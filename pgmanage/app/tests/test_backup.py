import os
import unittest
from datetime import datetime, timedelta
from functools import partial
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock, patch

from app.include import OmniDatabase
from app.models import Connection, Technology
from app.tests.utils_testing import USERS, execute_client_login
from app.utils.crypto import encrypt
from app.views.backup import (Backup, BackupMessage, GlobalsBackup,
                               ObjectBackup, ServerBackup, create_backup,
                               get_args_params_values, preview_command)
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

User = get_user_model()


class BackupClassesTests(TestCase):

    def test_get_backup_type_valid_strings(self):
        self.assertEqual(Backup.get_backup_type("globals"), Backup.GLOBALS)
        self.assertEqual(Backup.get_backup_type("server"), Backup.SERVER)
        self.assertEqual(Backup.get_backup_type("objects"), Backup.OBJECT)

    def test_get_backup_type_invalid_raises_value_error(self):
        with self.assertRaises(ValueError):
            Backup.get_backup_type("bogus")

    def test_create_dispatches_to_correct_subclass(self):
        self.assertIsInstance(Backup.create(Backup.GLOBALS), GlobalsBackup)
        self.assertIsInstance(Backup.create(Backup.SERVER), ServerBackup)
        self.assertIsInstance(Backup.create(Backup.OBJECT), ObjectBackup)

    def test_globals_backup_properties(self):
        b = GlobalsBackup()
        self.assertEqual(b.type_desc, "Backing up the global objects")
        self.assertEqual(b.backup_type, "Backup Globals")
        self.assertEqual(b.get_message("myconn"), "Backing up the global objects on the server 'myconn'")

    def test_server_backup_properties(self):
        b = ServerBackup()
        self.assertEqual(b.type_desc, "Backing up the server")
        self.assertEqual(b.backup_type, "Backup Server")
        self.assertEqual(b.get_message("myconn"), "Backing up the server 'myconn'")

    def test_object_backup_properties(self):
        b = ObjectBackup()
        self.assertEqual(b.type_desc, "Backing up an object on the server")
        self.assertEqual(b.backup_type, "Backup Object")
        self.assertEqual(
            b.get_message("myconn", "mydb"),
            "Backing up an object on the server 'myconn' from database 'mydb'",
        )

    def test_base_class_cannot_be_instantiated_directly(self):
        with self.assertRaises(TypeError):
            Backup()


class BackupMessageTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.get(username="admin")
        cls.technology = Technology.objects.filter(name="postgresql").first()
        cls.connection = Connection.objects.create(
            user=cls.owner,
            technology=cls.technology,
            server="db.example.com",
            port=5432,
            database="mydb",
            username="dbuser",
            alias="Backup Test Connection",
        )

    def test_get_connection_name_direct(self):
        msg = BackupMessage(ObjectBackup(), self.connection.id, "/tmp/backup.dump")
        self.assertEqual(msg.get_connection_name(), "mydb (db.example.com:5432)")

    def test_get_connection_name_via_ssh_tunnel(self):
        self.connection.use_tunnel = True
        self.connection.ssh_server = "bastion.example.com"
        self.connection.ssh_port = "2222"
        self.connection.save()
        try:
            msg = BackupMessage(ObjectBackup(), self.connection.id, "/tmp/backup.dump")
            self.assertEqual(msg.get_connection_name(), "mydb (bastion.example.com:2222)")
        finally:
            self.connection.use_tunnel = False
            self.connection.save()

    def test_get_connection_name_missing_connection(self):
        msg = BackupMessage(ObjectBackup(), 999999, "/tmp/backup.dump")
        self.assertEqual(msg.get_connection_name(), "Not available")

    def test_message_and_type_desc_object_backup(self):
        msg = BackupMessage(ObjectBackup(), self.connection.id, "/tmp/backup.dump", database="mydb")
        self.assertEqual(
            msg.message,
            "Backing up an object on the server 'mydb (db.example.com:5432)' from database 'mydb'",
        )
        self.assertEqual(msg.type_desc, "Backing up an object on the server")

    def test_message_and_type_desc_globals_backup(self):
        msg = BackupMessage(GlobalsBackup(), self.connection.id, "/tmp/backup.dump")
        self.assertEqual(msg.message, "Backing up the global objects on the server 'mydb (db.example.com:5432)'")
        self.assertEqual(msg.type_desc, "Backing up the global objects")

    def test_cmd_building_flags_and_quoted_values(self):
        msg = BackupMessage(
            ObjectBackup(), self.connection.id, "/tmp/backup.dump",
            "--host", "db.example.com", "--dbname", "my db",
        )
        self.assertEqual(msg.cmd, ' --host "db.example.com" --dbname "my db"')

    def test_cmd_arg_escapes_quotes_and_backslashes(self):
        msg = BackupMessage(ObjectBackup(), self.connection.id, "/tmp/backup.dump", 'weird\\path"name')
        self.assertEqual(msg.cmd, ' "weird\\\\path\\"name"')

    def test_four_word_value_is_correctly_quoted(self):
        msg = BackupMessage(
            ObjectBackup(),
            self.connection.id,
            "/tmp/backup.dump",
            "--schema",
            "My Very Weird Schema",
        )
        self.assertEqual(msg.cmd, ' --schema "My Very Weird Schema"')

    def test_cmd_building_pigz_suffix_is_appended_not_prepended(self):
        msg = BackupMessage(
            ObjectBackup(), self.connection.id, "/tmp/backup.dump",
            "--dbname", "mydb", "| pigz -p4 -6 > /tmp/backup.dump.gz",
        )
        self.assertEqual(msg.cmd, ' --dbname "mydb" | pigz -p4 -6 > /tmp/backup.dump.gz')

    def test_details_cmd_concatenation(self):
        msg = BackupMessage(ObjectBackup(), self.connection.id, "/tmp/backup.dump", "--dbname", "mydb")
        details = msg.details("pg_dump")
        self.assertEqual(details["cmd"], 'pg_dump --dbname "mydb"')
        self.assertEqual(details["server"], "mydb (db.example.com:5432)")
        self.assertEqual(details["type"], "Backup Object")

class GetArgsParamsValuesTests(TestCase):
    """get_args_params_values is a pure function of (data, conn, backup_obj_type,
    backup_file) - no database access at all, hence a plain duck-typed conn
    stand-in.
    """

    def setUp(self):
        self.conn = SimpleNamespace(server="db.example.com", port=5432, user="dbuser", active_service="mydb")

    def base_args(self, backup_file="/tmp/backup.dump"):
        return [
            "--file", backup_file, "--host", "db.example.com", "--port", "5432",
            "--username", "dbuser", "--no-password",
        ]

    def test_objects_type_appends_database_name_at_end(self):
        args = get_args_params_values({"database": "mydb"}, self.conn, "objects", "/tmp/backup.dump")
        self.assertEqual(args, self.base_args() + ["--dbname", "mydb"])

    def test_globals_type_uses_active_service_for_database_flag(self):
        args = get_args_params_values({}, self.conn, "globals", "/tmp/backup.dump")
        self.assertEqual(args, self.base_args() + ["--database", "mydb"])

    def test_verbose_and_quote_all_identifiers_flags(self):
        args = get_args_params_values(
            {"database": "mydb", "verbose": True, "dqoute": True}, self.conn, "objects", "/tmp/backup.dump"
        )
        self.assertEqual(args, self.base_args() + ["--verbose", "--quote-all-identifiers", "--dbname", "mydb"])

    def test_role_value(self):
        args = get_args_params_values({"database": "mydb", "role": "myrole"}, self.conn, "objects", "/tmp/backup.dump")
        self.assertEqual(args, self.base_args() + ["--role", "myrole", "--dbname", "mydb"])

    def test_format_custom_with_blobs_and_compress(self):
        args = get_args_params_values(
            {"database": "mydb", "format": "custom", "blobs": True, "compression_ratio": 6},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertEqual(args, self.base_args() + ["--format=c", "--blobs", "--compress", "6", "--dbname", "mydb"])

    def test_format_tar_allows_blobs_but_not_compress(self):
        args = get_args_params_values(
            {"database": "mydb", "format": "tar", "blobs": True, "compression_ratio": 6},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertEqual(args, self.base_args() + ["--format=t", "--blobs", "--dbname", "mydb"])

    def test_format_plain_allows_compress_but_not_blobs(self):
        args = get_args_params_values(
            {"database": "mydb", "format": "plain", "blobs": True, "compression_ratio": 6},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertEqual(args, self.base_args() + ["--format=p", "--compress", "6", "--dbname", "mydb"])

    def test_format_directory_with_number_of_jobs(self):
        args = get_args_params_values(
            {"database": "mydb", "format": "directory", "number_of_jobs": 4},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertEqual(args, self.base_args() + ["--format=d", "--jobs", "4", "--dbname", "mydb"])

    def test_number_of_jobs_ignored_for_non_directory_format(self):
        args = get_args_params_values(
            {"database": "mydb", "format": "custom", "number_of_jobs": 4}, self.conn, "objects", "/tmp/backup.dump"
        )
        self.assertNotIn("--jobs", args)

    def test_number_of_jobs_ignored_when_pigz_enabled(self):
        args = get_args_params_values(
            {
                "database": "mydb", "format": "directory", "number_of_jobs": 4,
                "pigz": True, "compression_ratio": 6,
            },
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertNotIn("--jobs", args)

    def test_only_data_and_disable_trigger_requires_plain_format(self):
        args = get_args_params_values(
            {"database": "mydb", "format": "plain", "only_data": True, "disable_trigger": True},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertEqual(args, self.base_args() + ["--format=p", "--data-only", "--disable-triggers", "--dbname", "mydb"])

    def test_disable_trigger_ignored_for_non_plain_format(self):
        args = get_args_params_values(
            {"database": "mydb", "format": "custom", "only_data": True, "disable_trigger": True},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertNotIn("--disable-triggers", args)

    def test_only_schema_requires_not_only_data(self):
        args = get_args_params_values(
            {"database": "mydb", "only_schema": True}, self.conn, "objects", "/tmp/backup.dump"
        )
        self.assertIn("--schema-only", args)

    def test_only_schema_ignored_when_only_data_also_set(self):
        args = get_args_params_values(
            {"database": "mydb", "only_schema": True, "only_data": True}, self.conn, "objects", "/tmp/backup.dump"
        )
        self.assertNotIn("--schema-only", args)

    def test_only_globals_tablespaces_roles_apply_to_non_objects_type(self):
        args = get_args_params_values(
            {"only_globals": True, "only_tablespaces": True, "only_roles": True},
            self.conn, "globals", "/tmp/backup.dump",
        )
        self.assertEqual(
            args, self.base_args() + ["--database", "mydb", "--globals-only", "--tablespaces-only", "--roles-only"]
        )

    def test_only_globals_tablespaces_roles_never_apply_to_objects_type(self):
        args = get_args_params_values(
            {"database": "mydb", "only_globals": True, "only_tablespaces": True, "only_roles": True},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertNotIn("--globals-only", args)
        self.assertNotIn("--tablespaces-only", args)
        self.assertNotIn("--roles-only", args)

    def test_remaining_boolean_flags(self):
        data = {
            "database": "mydb",
            "owner": True,
            "include_create_database": True,
            "include_drop_commands": True,
            "pre_data": True,
            "data": True,
            "post_data": True,
            "privilege": True,
            "tablespace": True,
            "unlogged_tbl_data": True,
            "use_insert_commands": True,
            "use_column_inserts": True,
            "disable_quoting": True,
            "use_set_session_auth": True,
            "comments": True,
            "load_via_partition_root": True,
        }
        args = get_args_params_values(data, self.conn, "objects", "/tmp/backup.dump")
        self.assertEqual(
            args,
            self.base_args()
            + [
                "--no-owner",
                "--create",
                "--clean",
                "--section=pre-data",
                "--section=data",
                "--section=post-data",
                "--no-privileges",
                "--no-tablespaces",
                "--no-unlogged-table-data",
                "--inserts",
                "--column-inserts",
                "--disable-dollar-quoting",
                "--use-set-session-authorization",
                "--no-comments",
                "--load-via-partition-root",
                "--dbname",
                "mydb",
            ],
        )

    def test_encoding_value(self):
        args = get_args_params_values(
            {"database": "mydb", "encoding": "UTF8"}, self.conn, "objects", "/tmp/backup.dump"
        )
        self.assertEqual(args, self.base_args() + ["--encoding", "UTF8", "--dbname", "mydb"])

    def test_schemas_and_tables_lists(self):
        args = get_args_params_values(
            {"database": "mydb", "schemas": ["public", "sales"], "tables": ["orders"]},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertEqual(
            args,
            self.base_args()
            + ["--schema", "public", "--schema", "sales", "--table", "orders", "--dbname", "mydb"],
        )

    def test_pigz_drops_file_flag_and_appends_pipe_suffix(self):
        args = get_args_params_values(
            {"database": "mydb", "pigz": True, "number_of_jobs": "4", "compression_ratio": 6},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertEqual(
            args,
            [
                "--host", "db.example.com", "--port", "5432", "--username", "dbuser", "--no-password",
                "--dbname", "mydb", "| pigz -p4 -6 > /tmp/backup.dump.gz",
            ],
        )
        self.assertNotIn("--file", args)

    def test_pigz_auto_jobs_omits_dash_p(self):
        args = get_args_params_values(
            {"database": "mydb", "pigz": True, "number_of_jobs": "auto", "compression_ratio": 6},
            self.conn, "objects", "/tmp/backup.dump",
        )
        self.assertEqual(args[-1], "| pigz  -6 > /tmp/backup.dump.gz")

    def test_pigz_does_not_double_append_gz_suffix(self):
        args = get_args_params_values(
            {"database": "mydb", "pigz": True, "compression_ratio": 6},
            self.conn, "objects", "/tmp/backup.dump.gz",
        )
        self.assertTrue(args[-1].endswith("/tmp/backup.dump.gz"))
        self.assertFalse(args[-1].endswith(".gz.gz"))

    def test_objects_missing_database_key_raises_clear_value_error(self):
        with self.assertRaises(ValueError):
            get_args_params_values({}, self.conn, "objects", "/tmp/backup.dump")


class BackupURLTests(TestCase):

    def test_create_backup_url_resolves_to_view(self):
        match = resolve("/backup/")
        self.assertEqual(match.func.__name__, create_backup.__name__)

    def test_preview_command_url_resolves_to_view(self):
        match = resolve("/backup/preview_command/")
        self.assertEqual(match.func.__name__, preview_command.__name__)

    def test_create_backup_unauthenticated_access_denied(self):
        response = self.client.post(
            reverse("create_backup"), data={"data": {}}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)

    def test_preview_command_unauthenticated_access_denied(self):
        response = self.client.post(
            reverse("backup_preview_command"), data={"data": {}}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)


class BackupViewTests(TestCase):
    """Integration tests for create_backup/preview_command. These views need
    a live, connectable database (see docker-compose.yml/fetch-test-data.sh)
    because @database_required(open_connection=True) attempts a real
    connection before the view body runs - but the view logic itself
    (FileManager, get_utility_path, BatchJob) is mocked so no real backup
    files, dump binaries, or subprocesses are needed.
    """

    HOST = "127.0.0.1"
    PORT = "5433"
    SERVICE = "dellstore"
    ROLE = "postgres"
    PASSWORD = "postgres"

    @classmethod
    def setUpClass(cls):
        cls.db_type = "postgresql"

        database = OmniDatabase.Generic.InstantiateDatabase(
            cls.db_type, cls.HOST, cls.PORT, cls.SERVICE, cls.ROLE, 0, 0
        )
        database.connection.password = cls.PASSWORD

        database.GetVersion()
        if database.major_version is None:
            raise unittest.SkipTest(
                f"Postgres test database is not reachable at {cls.HOST}:{cls.PORT} - "
                f"start it with `docker compose up` in app/tests."
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
            alias="PgManage Backup Tests",
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

    @patch("app.views.backup.BatchJob")
    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_create_backup_objects_success(self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_dump"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.return_value = None

        mock_job = MagicMock()
        mock_job.id = 42
        mock_job.description.message = "Backing up an object on the server 'dellstore'"
        mock_batch_job_cls.return_value = mock_job

        response = self.client.post(
            reverse("create_backup"),
            data={
                "backup_type": "objects",
                "data": {"fileName": "backup.dump", "database": "dellstore"},
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["job_id"], 42)
        self.assertEqual(body["Success"], 1)
        self.assertEqual(body["description"], mock_job.description.message)
        mock_job.start.assert_called_once()

        # the DB password is handed to the subprocess via a per-job env dict
        # (BatchJob.env, merged into that one Popen call only), not the
        # shared/persistent os.environ - same fix as views/restore.py
        mock_job.env.__setitem__.assert_called_once_with("PGPASSWORD", self.PASSWORD)
        self.assertNotIn(str(mock_job.id), os.environ)

        call_kwargs = mock_batch_job_cls.call_args.kwargs
        self.assertIsInstance(call_kwargs["description"], BackupMessage)
        self.assertEqual(call_kwargs["description"].bfile, "/data/backup.dump")
        self.assertEqual(call_kwargs["description"].database, "dellstore")
        self.assertEqual(call_kwargs["cmd"], "/usr/bin/pg_dump")

        args = call_kwargs["args"]
        self.assertIn("dellstore", args)
        self.assertEqual(args[args.index("dellstore") - 1], "--dbname")

    @patch("app.views.backup.BatchJob")
    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_create_backup_globals_success(self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_dumpall"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/globals.dump"
        mock_batch_job_cls.return_value = MagicMock(id=1, description=MagicMock(message="backing up globals"))

        response = self.client.post(
            reverse("create_backup"),
            data={"backup_type": "globals", "data": {"fileName": "globals.dump"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        mock_get_utility_path.assert_called_once_with("pg_dumpall", ANY, None)
        call_kwargs = mock_batch_job_cls.call_args.kwargs
        self.assertIsInstance(call_kwargs["description"], BackupMessage)
        self.assertIsInstance(call_kwargs["description"].backup_type, GlobalsBackup)

    @patch("app.views.backup.BatchJob")
    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_create_backup_server_success(self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_dumpall"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/server.dump"
        mock_batch_job_cls.return_value = MagicMock(id=1, description=MagicMock(message="backing up server"))

        response = self.client.post(
            reverse("create_backup"),
            data={"backup_type": "server", "data": {"fileName": "server.dump"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        call_kwargs = mock_batch_job_cls.call_args.kwargs
        self.assertIsInstance(call_kwargs["description"].backup_type, ServerBackup)

    @patch("app.views.backup.BatchJob")
    @patch("app.views.backup.FileManager")
    @patch(
        "app.views.backup.get_utility_path",
        side_effect=["/usr/bin/pg_dump", "/usr/bin/pigz"],
    )
    def test_create_backup_success_with_pigz(self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_job = MagicMock()
        mock_job.id = 7
        mock_job.description.message = "Backing up an object on the server 'dellstore'"
        mock_batch_job_cls.return_value = mock_job

        response = self.client.post(
            reverse("create_backup"),
            data={
                "backup_type": "objects",
                "data": {
                    "fileName": "backup.dump",
                    "database": "dellstore",
                    "pigz": True,
                    "number_of_jobs": "4",
                    "compression_ratio": 6,
                },
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job_id"], 7)
        args = mock_batch_job_cls.call_args.kwargs["args"]
        # pigz_path resolves to the full path returned by get_utility_path
        # ("/usr/bin/pigz"), not the bare "pigz" name
        self.assertIn("| /usr/bin/pigz -p4 -6 > /data/backup.dump.gz", args)

    @patch("app.views.backup.get_utility_path", side_effect=FileNotFoundError("pg_dump not found"))
    def test_create_backup_missing_utility(self, mock_get_utility_path):
        response = self.client.post(
            reverse("create_backup"),
            data={"backup_type": "objects", "data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "pg_dump not found"})

    @patch(
        "app.views.backup.get_utility_path",
        side_effect=["/usr/bin/pg_dump", FileNotFoundError("pigz not found")],
    )
    def test_create_backup_missing_pigz(self, mock_get_utility_path):
        response = self.client.post(
            reverse("create_backup"),
            data={
                "backup_type": "objects",
                "data": {"fileName": "backup.dump", "database": "dellstore", "pigz": True},
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "pigz not found"})

    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_create_backup_permission_denied(self, mock_get_utility_path, mock_file_manager_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_dump"
        mock_file_manager_cls.return_value.resolve_path.side_effect = PermissionError("access denied")

        response = self.client.post(
            reverse("create_backup"),
            data={"backup_type": "objects", "data": {"fileName": "../../etc/passwd"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"data": "access denied"})

    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_create_backup_check_access_permission_denied(self, mock_get_utility_path, mock_file_manager_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_dump"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.side_effect = PermissionError(
            "outside storage directory"
        )

        response = self.client.post(
            reverse("create_backup"),
            data={"backup_type": "objects", "data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"data": "outside storage directory"})

    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_create_backup_invalid_backup_type_returns_410(self, mock_get_utility_path, mock_file_manager_cls):
        # Unlike preview_command (see below), create_backup calls
        # Backup.get_backup_type() *inside* its try/except, so an invalid
        # backup_type is caught and reported cleanly here.
        mock_get_utility_path.return_value = "/usr/bin/pg_dump"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"

        response = self.client.post(
            reverse("create_backup"),
            data={"backup_type": "bogus", "data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json(), {"data": "Invalid backup type: bogus"})

    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_create_backup_objects_missing_database_key_returns_410(
        self, mock_get_utility_path, mock_file_manager_cls
    ):
        mock_get_utility_path.return_value = "/usr/bin/pg_dump"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"

        response = self.client.post(
            reverse("create_backup"),
            data={"backup_type": "objects", "data": {"fileName": "backup.dump"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json(), {"data": "Missing required field: database"})

    @patch("app.views.backup.BatchJob")
    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_create_backup_batch_job_start_failure(self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_dump"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_job = MagicMock()
        mock_job.id = 99
        mock_job.start.side_effect = Exception("failed to start job")
        mock_batch_job_cls.return_value = mock_job

        response = self.client.post(
            reverse("create_backup"),
            data={"backup_type": "objects", "data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json(), {"data": "failed to start job"})
        mock_job.start.assert_called_once()

    # --- preview_command ---

    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_preview_command_success(self, mock_get_utility_path, mock_file_manager_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_dump"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.return_value = None

        response = self.client.post(
            reverse("backup_preview_command"),
            data={"backup_type": "objects", "data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        command = response.json()["command"]
        self.assertIn("/usr/bin/pg_dump", command["cmd"])
        self.assertEqual(command["type"], "Backup Object")
        self.assertEqual(command["object"], "dellstore")

    @patch("app.views.backup.FileManager")
    def test_preview_command_permission_denied(self, mock_file_manager_cls):
        mock_file_manager_cls.return_value.resolve_path.side_effect = PermissionError("access denied")

        response = self.client.post(
            reverse("backup_preview_command"),
            data={"backup_type": "objects", "data": {"fileName": "../../etc/passwd"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"data": "access denied"})

    @patch("app.views.backup.FileManager")
    def test_preview_command_check_access_permission_denied(self, mock_file_manager_cls):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.side_effect = PermissionError(
            "outside storage directory"
        )

        response = self.client.post(
            reverse("backup_preview_command"),
            data={"backup_type": "objects", "data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"data": "outside storage directory"})

    @patch("app.views.backup.get_utility_path", side_effect=FileNotFoundError("pg_dump not found"))
    @patch("app.views.backup.FileManager")
    def test_preview_command_missing_utility(self, mock_file_manager_cls, mock_get_utility_path):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"

        response = self.client.post(
            reverse("backup_preview_command"),
            data={"backup_type": "objects", "data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "pg_dump not found"})

    @patch(
        "app.views.backup.get_utility_path",
        side_effect=["/usr/bin/pg_dump", FileNotFoundError("pigz not found")],
    )
    @patch("app.views.backup.FileManager")
    def test_preview_command_missing_pigz(self, mock_file_manager_cls, mock_get_utility_path):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump.gz"

        response = self.client.post(
            reverse("backup_preview_command"),
            data={
                "backup_type": "objects",
                "data": {"fileName": "backup.dump.gz", "database": "dellstore", "pigz": True},
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "pigz not found"})

    @patch(
        "app.views.backup.get_utility_path",
        side_effect=["/usr/bin/pg_dump", "/usr/bin/pigz"],
    )
    @patch("app.views.backup.FileManager")
    def test_preview_command_success_with_pigz(self, mock_file_manager_cls, mock_get_utility_path):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump.gz"

        response = self.client.post(
            reverse("backup_preview_command"),
            data={
                "backup_type": "objects",
                "data": {
                    "fileName": "backup.dump.gz",
                    "database": "dellstore",
                    "pigz": True,
                    "number_of_jobs": "4",
                    "compression_ratio": 6,
                },
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("| /usr/bin/pigz -p4 -6 > /data/backup.dump.gz", response.json()["command"]["cmd"])

    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_preview_command_invalid_backup_type_returns_400(
        self, mock_get_utility_path, mock_file_manager_cls
    ):
        mock_get_utility_path.return_value = "/usr/bin/pg_dump"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.return_value = None

        response = self.client.post(
            reverse("backup_preview_command"),
            data={"backup_type": "bogus", "data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "Invalid backup type: bogus"})

    @patch("app.views.backup.FileManager")
    @patch("app.views.backup.get_utility_path")
    def test_preview_command_objects_missing_database_key_returns_400(
        self, mock_get_utility_path, mock_file_manager_cls
    ):
        mock_get_utility_path.return_value = "/usr/bin/pg_dump"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.return_value = None

        response = self.client.post(
            reverse("backup_preview_command"),
            data={"backup_type": "objects", "data": {"fileName": "backup.dump"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "Missing required field: database"})
