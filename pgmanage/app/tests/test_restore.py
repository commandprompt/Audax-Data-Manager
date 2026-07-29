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
from app.views.restore import RestoreMessage, create_restore, get_args_param_values, preview_command
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import resolve, reverse

User = get_user_model()


class RestoreMessageTests(TestCase):

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
            alias="Restore Test Connection",
        )

    def test_get_connection_name_direct(self):
        msg = RestoreMessage(self.connection.id, "/tmp/backup.dump")
        self.assertEqual(msg.get_connection_name(), "mydb (db.example.com:5432)")

    def test_get_connection_name_via_ssh_tunnel(self):
        self.connection.use_tunnel = True
        self.connection.ssh_server = "bastion.example.com"
        self.connection.ssh_port = "2222"
        self.connection.save()
        try:
            msg = RestoreMessage(self.connection.id, "/tmp/backup.dump")
            self.assertEqual(msg.get_connection_name(), "mydb (bastion.example.com:2222)")
        finally:
            self.connection.use_tunnel = False
            self.connection.save()

    def test_get_connection_name_missing_connection(self):
        msg = RestoreMessage(999999, "/tmp/backup.dump")
        self.assertEqual(msg.get_connection_name(), "Not available")

    def test_message_and_type_desc(self):
        msg = RestoreMessage(self.connection.id, "/tmp/backup.dump")
        self.assertEqual(msg.message, "Restoring backup on the server 'mydb (db.example.com:5432)'")
        self.assertEqual(msg.type_desc, "Restoring backup on the server")

    def test_cmd_building_flags_and_quoted_values(self):
        msg = RestoreMessage(
            self.connection.id,
            "/tmp/backup.dump",
            "--host",
            "db.example.com",
            "--dbname",
            "my db",
        )
        self.assertEqual(msg.cmd, ' --host "db.example.com" --dbname "my db"')

    def test_cmd_arg_escapes_quotes_and_backslashes(self):
        msg = RestoreMessage(self.connection.id, "/tmp/backup.dump", 'weird\\path"name')
        self.assertEqual(msg.cmd, ' "weird\\\\path\\"name"')

    def test_cmd_arg_empty_value_is_omitted(self):
        msg = RestoreMessage(self.connection.id, "/tmp/backup.dump", "--dbname", "")
        self.assertEqual(msg.cmd, " --dbname")

    def test_cmd_building_pigz_pipe_prefix(self):
        msg = RestoreMessage(
            self.connection.id,
            "/tmp/backup.dump",
            "--dbname",
            "mydb",
            "pigz -dc -p4 /tmp/backup.dump.gz",
        )
        self.assertEqual(msg.cmd, 'pigz -dc -p4 /tmp/backup.dump.gz |  --dbname "mydb"')

    def test_details_without_pipe(self):
        msg = RestoreMessage(self.connection.id, "/tmp/backup.dump", "--dbname", "mydb")
        details = msg.details("pg_restore")
        self.assertEqual(details["cmd"], 'pg_restore --dbname "mydb"')
        self.assertEqual(details["message"], "Restoring backup on the server 'mydb (db.example.com:5432)'")
        self.assertEqual(details["server"], "mydb (db.example.com:5432)")
        self.assertEqual(details["type"], "Restore")

    def test_details_with_pipe(self):
        msg = RestoreMessage(
            self.connection.id,
            "/tmp/backup.dump",
            "--dbname",
            "mydb",
            "pigz -dc -p4 /tmp/backup.dump.gz",
        )
        details = msg.details("pg_restore")
        self.assertEqual(details["cmd"], 'pigz -dc -p4 /tmp/backup.dump.gz | pg_restore  --dbname "mydb"')

    def test_details_object_uses_database_kwarg(self):
        msg = RestoreMessage(self.connection.id, "/tmp/backup.dump", database="mydb")
        self.assertEqual(msg.details("pg_restore")["object"], "mydb")


class GetArgsParamValuesTests(TestCase):

    def setUp(self):
        self.conn = SimpleNamespace(server="db.example.com", port=5432, user="dbuser")

    def base_args(self):
        return ["--host", "db.example.com", "--port", "5432", "--username", "dbuser", "--no-password"]

    def test_server_type_defaults_to_dash_f(self):
        args = get_args_param_values({"type": "server"}, self.conn, "/tmp/backup.sql")
        self.assertEqual(args, self.base_args() + ["-f", "/tmp/backup.sql"])

    def test_server_type_with_quiet_and_echo_queries(self):
        args = get_args_param_values(
            {"type": "server", "quiet": True, "echo_queries": True}, self.conn, "/tmp/backup.sql"
        )
        self.assertEqual(args, self.base_args() + ["--quiet", "--echo-queries", "-f", "/tmp/backup.sql"])

    def test_server_type_with_pigz(self):
        args = get_args_param_values(
            {"type": "server", "pigz": True, "pigz_number_of_jobs": "4"},
            self.conn,
            "/tmp/backup.sql.gz",
        )
        self.assertEqual(args, self.base_args() + ["pigz -dc -p4 /tmp/backup.sql.gz"])

    def test_server_type_with_pigz_auto_jobs_omits_dash_p(self):
        args = get_args_param_values(
            {"type": "server", "pigz": True, "pigz_number_of_jobs": "auto"},
            self.conn,
            "/tmp/backup.sql.gz",
        )
        self.assertEqual(args, self.base_args() + ["pigz -dc  /tmp/backup.sql.gz"])

    def test_pg_restore_default_appends_bare_backup_file(self):
        args = get_args_param_values({}, self.conn, "/tmp/backup.dump")
        self.assertEqual(args, self.base_args() + ["/tmp/backup.dump"])

    def test_pg_restore_role_and_database(self):
        args = get_args_param_values({"role": "myrole", "database": "mydb"}, self.conn, "/tmp/backup.dump")
        self.assertEqual(args, self.base_args() + ["--role", "myrole", "--dbname", "mydb", "/tmp/backup.dump"])

    def test_pg_restore_sections(self):
        args = get_args_param_values({"pre_data": True, "data": True, "post_data": True}, self.conn, "/tmp/backup.dump")
        self.assertEqual(
            args,
            self.base_args() + ["--section=pre-data", "--section=data", "--section=post-data", "/tmp/backup.dump"],
        )

    def test_pg_restore_only_data_excludes_owner_privilege_tablespace_flags(self):
        args = get_args_param_values(
            {
                "only_data": True,
                "dns_owner": True,
                "dns_privilege": True,
                "dns_tablespace": True,
            },
            self.conn,
            "/tmp/backup.dump",
        )
        self.assertEqual(args, self.base_args() + ["--data-only", "/tmp/backup.dump"])

    def test_pg_restore_owner_privilege_tablespace_flags_when_not_only_data(self):
        args = get_args_param_values(
            {"dns_owner": True, "dns_privilege": True, "dns_tablespace": True},
            self.conn,
            "/tmp/backup.dump",
        )
        self.assertEqual(
            args,
            self.base_args() + ["--no-owner", "--no-privileges", "--no-tablespaces", "/tmp/backup.dump"],
        )

    def test_pg_restore_only_schema_excludes_disable_trigger_flag(self):
        args = get_args_param_values({"only_schema": True, "disable_trigger": True}, self.conn, "/tmp/backup.dump")
        self.assertEqual(args, self.base_args() + ["--schema-only", "/tmp/backup.dump"])

    def test_pg_restore_disable_trigger_flag_when_not_only_schema(self):
        args = get_args_param_values({"disable_trigger": True}, self.conn, "/tmp/backup.dump")
        self.assertEqual(args, self.base_args() + ["--disable-triggers", "/tmp/backup.dump"])

    def test_pg_restore_remaining_boolean_flags(self):
        args = get_args_param_values(
            {
                "include_create_database": True,
                "clean": True,
                "single_transaction": True,
                "no_data_fail_table": True,
                "use_set_session_auth": True,
                "exit_on_error": True,
                "verbose": True,
                "no_comments": True,
            },
            self.conn,
            "/tmp/backup.dump",
        )
        self.assertEqual(
            args,
            self.base_args()
            + [
                "--no-comments",
                "--create",
                "--clean",
                "--single-transaction",
                "--no-data-for-failed-tables",
                "--use-set-session-authorization",
                "--exit-on-error",
                "--verbose",
                "/tmp/backup.dump",
            ],
        )

    def test_pg_restore_number_of_jobs_int_is_stringified(self):
        args = get_args_param_values({"number_of_jobs": 4}, self.conn, "/tmp/backup.dump")
        self.assertEqual(args, self.base_args() + ["--jobs", "4", "/tmp/backup.dump"])

    def test_pg_restore_schema_table_trigger_function_filters(self):
        args = get_args_param_values(
            {
                "schema": "public",
                "table": "orders",
                "trigger": "tg_ins",
                "function": "fn_test",
            },
            self.conn,
            "/tmp/backup.dump",
        )
        self.assertEqual(
            args,
            self.base_args()
            + [
                "--schema",
                "public",
                "--table",
                "orders",
                "--trigger",
                "tg_ins",
                "--function",
                "fn_test",
                "/tmp/backup.dump",
            ],
        )

    def test_pg_restore_with_pigz_appends_pipe_source_instead_of_backup_file(self):
        args = get_args_param_values({"pigz": True, "pigz_number_of_jobs": "2"}, self.conn, "/tmp/backup.dump.gz")
        self.assertEqual(args, self.base_args() + ["pigz -dc -p2 /tmp/backup.dump.gz"])


class RestoreURLTests(TestCase):
    """URL wiring and auth-boundary checks that don't need a live database
    connection - session_required/user_authenticated reject an unauthenticated
    request before @database_required ever attempts to open a connection.
    """

    def test_create_restore_url_resolves_to_view(self):
        match = resolve("/restore/")
        self.assertEqual(match.func.__name__, create_restore.__name__)

    def test_preview_command_url_resolves_to_view(self):
        match = resolve("/restore/preview_command/")
        self.assertEqual(match.func.__name__, preview_command.__name__)

    def test_create_restore_unauthenticated_access_denied(self):
        response = self.client.post(reverse("create_restore"), data={"data": {}}, content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_preview_command_unauthenticated_access_denied(self):
        response = self.client.post(
            reverse("restore_preview_command"), data={"data": {}}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)


class RestoreViewTests(TestCase):
    """Integration tests for create_restore/preview_command. These views need
    a live, connectable database (see docker-compose.yml/test-db.sh) because
    @database_required(open_connection=True) attempts a real connection
    before the view body runs - but the view logic itself (FileManager,
    get_utility_path, BatchJob) is mocked so no real backup files, restore
    binaries, or subprocesses are needed.
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
            alias="PgManage Restore Tests",
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

    @patch("app.views.restore.BatchJob")
    @patch("app.views.restore.FileManager")
    @patch("app.views.restore.get_utility_path")
    def test_create_restore_success(self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_restore"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.return_value = None

        mock_job = MagicMock()
        mock_job.id = 42
        mock_job.description.message = "Restoring backup on the server 'dellstore'"
        mock_batch_job_cls.return_value = mock_job

        response = self.client.post(
            reverse("create_restore"),
            data={"data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["job_id"], 42)
        self.assertEqual(body["Success"], 1)
        self.assertEqual(body["description"], mock_job.description.message)
        mock_job.start.assert_called_once()

        mock_job.env.__setitem__.assert_called_once_with("PGPASSWORD", self.PASSWORD)
        self.assertNotIn(str(mock_job.id), os.environ)

        call_kwargs = mock_batch_job_cls.call_args.kwargs
        self.assertIsInstance(call_kwargs["description"], RestoreMessage)
        self.assertEqual(call_kwargs["description"].backup_file, "/data/backup.dump")
        self.assertEqual(call_kwargs["description"].database, "dellstore")
        self.assertEqual(call_kwargs["cmd"], "/usr/bin/pg_restore")
        self.assertIn("--dbname", call_kwargs["args"])
        self.assertIn("dellstore", call_kwargs["args"])
        self.assertEqual(call_kwargs["user"].username, "admin")

    @patch("app.views.restore.BatchJob")
    @patch("app.views.restore.FileManager")
    @patch("app.views.restore.get_utility_path")
    def test_create_restore_success_server_mode(self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls):
        mock_get_utility_path.return_value = "/usr/bin/psql"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.sql"
        mock_batch_job_cls.return_value = MagicMock(id=1, description=MagicMock(message="restoring"))

        response = self.client.post(
            reverse("create_restore"),
            data={"data": {"fileName": "backup.sql", "type": "server"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        mock_get_utility_path.assert_called_once_with("psql", ANY, None)
        call_kwargs = mock_batch_job_cls.call_args.kwargs
        self.assertEqual(call_kwargs["cmd"], "/usr/bin/psql")
        self.assertIn("-f", call_kwargs["args"])
        self.assertIn("/data/backup.sql", call_kwargs["args"])

    @patch("app.views.restore.get_utility_path", side_effect=FileNotFoundError("pg_restore not found"))
    def test_create_restore_missing_utility(self, mock_get_utility_path):
        response = self.client.post(
            reverse("create_restore"), data={"data": {"fileName": "backup.dump"}, **self.tab_data}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "pg_restore not found"})

    @patch(
        "app.views.restore.get_utility_path",
        side_effect=["/usr/bin/pg_restore", FileNotFoundError("pigz not found")],
    )
    def test_create_restore_missing_pigz(self, mock_get_utility_path):
        response = self.client.post(
            reverse("create_restore"),
            data={"data": {"fileName": "backup.dump", "pigz": True}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "pigz not found"})

    @patch("app.views.restore.BatchJob")
    @patch("app.views.restore.FileManager")
    @patch(
        "app.views.restore.get_utility_path",
        side_effect=["/usr/bin/pg_restore", "/usr/bin/pigz"],
    )
    def test_create_restore_success_with_pigz(self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump.gz"
        mock_job = MagicMock()
        mock_job.id = 7
        mock_job.description.message = "Restoring backup on the server 'dellstore'"
        mock_batch_job_cls.return_value = mock_job

        response = self.client.post(
            reverse("create_restore"),
            data={
                "data": {"fileName": "backup.dump.gz", "pigz": True, "pigz_number_of_jobs": "4"},
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job_id"], 7)
        args = mock_batch_job_cls.call_args.kwargs["args"]
        self.assertIn("/usr/bin/pigz -dc -p4 /data/backup.dump.gz", args)

    @patch("app.views.restore.FileManager")
    @patch("app.views.restore.get_utility_path")
    def test_create_restore_permission_denied(self, mock_get_utility_path, mock_file_manager_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_restore"
        mock_file_manager_cls.return_value.resolve_path.side_effect = PermissionError("access denied")

        response = self.client.post(
            reverse("create_restore"),
            data={"data": {"fileName": "../../etc/passwd"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"data": "access denied"})

    @patch("app.views.restore.FileManager")
    @patch("app.views.restore.get_utility_path")
    def test_create_restore_check_access_permission_denied(self, mock_get_utility_path, mock_file_manager_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_restore"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.side_effect = PermissionError(
            "outside storage directory"
        )

        response = self.client.post(
            reverse("create_restore"), data={"data": {"fileName": "backup.dump"}, **self.tab_data}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"data": "outside storage directory"})

    @patch("app.views.restore.BatchJob", side_effect=Exception("failed to construct job"))
    @patch("app.views.restore.FileManager")
    @patch("app.views.restore.get_utility_path")
    def test_create_restore_batch_job_construction_failure(
        self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls
    ):
        mock_get_utility_path.return_value = "/usr/bin/pg_restore"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"

        response = self.client.post(
            reverse("create_restore"), data={"data": {"fileName": "backup.dump"}, **self.tab_data}
        )
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json(), {"data": "failed to construct job"})

    @patch("app.views.restore.BatchJob")
    @patch("app.views.restore.FileManager")
    @patch("app.views.restore.get_utility_path")
    def test_create_restore_batch_job_start_failure(
        self, mock_get_utility_path, mock_file_manager_cls, mock_batch_job_cls
    ):
        mock_get_utility_path.return_value = "/usr/bin/pg_restore"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_job = MagicMock()
        mock_job.id = 99
        mock_job.start.side_effect = Exception("failed to start job")
        mock_batch_job_cls.return_value = mock_job

        response = self.client.post(
            reverse("create_restore"), data={"data": {"fileName": "backup.dump"}, **self.tab_data}
        )
        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json(), {"data": "failed to start job"})
        mock_job.start.assert_called_once()

    @patch("app.views.restore.FileManager")
    @patch("app.views.restore.get_utility_path")
    def test_preview_command_success(self, mock_get_utility_path, mock_file_manager_cls):
        mock_get_utility_path.return_value = "/usr/bin/pg_restore"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.return_value = None

        response = self.client.post(
            reverse("restore_preview_command"),
            data={"data": {"fileName": "backup.dump", "database": "dellstore"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        command = response.json()["command"]
        self.assertIn("/usr/bin/pg_restore", command["cmd"])
        self.assertEqual(command["object"], "dellstore")
        self.assertEqual(command["type"], "Restore")

    @patch("app.views.restore.FileManager")
    @patch("app.views.restore.get_utility_path")
    def test_preview_command_success_server_mode(self, mock_get_utility_path, mock_file_manager_cls):
        mock_get_utility_path.return_value = "/usr/bin/psql"
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.sql"

        response = self.client.post(
            reverse("restore_preview_command"),
            data={"data": {"fileName": "backup.sql", "type": "server"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        mock_get_utility_path.assert_called_once_with("psql", ANY, None)
        command = response.json()["command"]
        self.assertIn("-f", command["cmd"])
        self.assertIn("/data/backup.sql", command["cmd"])

    @patch("app.views.restore.FileManager")
    def test_preview_command_permission_denied(self, mock_file_manager_cls):
        mock_file_manager_cls.return_value.resolve_path.side_effect = PermissionError("access denied")

        response = self.client.post(
            reverse("restore_preview_command"),
            data={"data": {"fileName": "../../etc/passwd"}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"data": "access denied"})

    @patch("app.views.restore.FileManager")
    def test_preview_command_check_access_permission_denied(self, mock_file_manager_cls):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"
        mock_file_manager_cls.return_value.check_access_permission.side_effect = PermissionError(
            "outside storage directory"
        )

        response = self.client.post(
            reverse("restore_preview_command"), data={"data": {"fileName": "backup.dump"}, **self.tab_data}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"data": "outside storage directory"})

    @patch("app.views.restore.get_utility_path", side_effect=FileNotFoundError("pg_restore not found"))
    @patch("app.views.restore.FileManager")
    def test_preview_command_missing_utility(self, mock_file_manager_cls, mock_get_utility_path):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump"

        response = self.client.post(
            reverse("restore_preview_command"), data={"data": {"fileName": "backup.dump"}, **self.tab_data}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "pg_restore not found"})

    @patch(
        "app.views.restore.get_utility_path",
        side_effect=["/usr/bin/pg_restore", FileNotFoundError("pigz not found")],
    )
    @patch("app.views.restore.FileManager")
    def test_preview_command_missing_pigz(self, mock_file_manager_cls, mock_get_utility_path):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump.gz"

        response = self.client.post(
            reverse("restore_preview_command"),
            data={"data": {"fileName": "backup.dump.gz", "pigz": True}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"data": "pigz not found"})

    @patch(
        "app.views.restore.get_utility_path",
        side_effect=["/usr/bin/pg_restore", "/usr/bin/pigz"],
    )
    @patch("app.views.restore.FileManager")
    def test_preview_command_success_with_pigz(self, mock_file_manager_cls, mock_get_utility_path):
        mock_file_manager_cls.return_value.resolve_path.return_value = "/data/backup.dump.gz"

        response = self.client.post(
            reverse("restore_preview_command"),
            data={
                "data": {"fileName": "backup.dump.gz", "pigz": True, "pigz_number_of_jobs": "4"},
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("/usr/bin/pigz -dc -p4 /data/backup.dump.gz", response.json()["command"]["cmd"])
