from datetime import datetime, timedelta
from functools import partial
from unittest.mock import Mock, patch

from app.include import OmniDatabase
from app.include.OmniDatabase import PostgreSQL
from app.models.main import Connection, Technology
from app.tests.utils_testing import USERS, execute_client_login
from app.utils.crypto import encrypt
from app.views.pgextras import (
    delete_pgcron_job,
    delete_pgcron_job_logs,
    get_pgcron_job_details,
    get_pgcron_job_logs,
    get_pgcron_jobs,
    save_pgcron_job,
)
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from django.urls import resolve, reverse


class PgCronJobViewsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.host = "127.0.0.1"
        cls.port = "5433"
        cls.service = "dellstore"
        cls.role = "postgres"
        cls.password = "postgres"
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
            db_type=cls.db_type,
            server=cls.host,
            port=cls.port,
            service=cls.service,
            user=cls.role,
            password=cls.password,
            conn_id=cls.test_connection.id,
            application_name="Pgmanage Tests",
        )

        cls.tab_data = {"database_index": cls.test_connection.id, "tab_id": 0}
        cls.invalid_tab_data = {"database_index": 999, "tab_id": 0}

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

        session["pgmanage_session"].databases = {
            self.test_connection.id: {
                "database": self.database,
                "prompt_password": False,
                "prompt_timeout": datetime.now() + timedelta(0, 60000),
            }
        }
        session["pgmanage_session"].tab_connections = {
            self.test_connection.id: self.database
        }
        session["pgmanage_session"].tabs_databases = {0: "dellstore"}
        session.save()

        self.client.post = partial(self.client.post, content_type="application/json")

    @patch.object(PostgreSQL, "QueryPgCronJobs")
    def test_get_pgcron_jobs_view(self, query_mock):
        query_mock.return_value = Mock(Rows=[[1, "Job 1"], [2, "Job 2"]])
        response = self.client.post(reverse("get_pgcron_jobs"), data=self.tab_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("jobs")[0], {"id": 1, "name": "Job 1"})

    @patch.object(PostgreSQL, "QueryPgCronJobs")
    def test_get_pgcron_jobs_view_with_error_response(self, query_mock):
        query_mock.side_effect = DatabaseError("mocked error")
        response = self.client.post(reverse("get_pgcron_jobs"), data=self.tab_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("data"), "mocked error")

    def test_get_pgcron_jobs_url_resolves_get_pgcron_jobs_view(self):
        view = resolve("/get_pgcron_jobs/")

        self.assertEqual(view.func.__name__, get_pgcron_jobs.__name__)

    @patch.object(PostgreSQL, "GetPgCronJob")
    def test_get_pgcron_job_details_view(self, mock_get_pgcron_job_details):
        mock_get_pgcron_job_details.return_value = Mock(
            Rows=[{"jobid": 1, "jobname": "test job"}]
        )
        response = self.client.post(
            reverse("get_pgcron_job_details"),
            data={"job_meta": {"id": 1}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("jobname"), "test job")

    @patch.object(PostgreSQL, "GetPgCronJob")
    def test_get_pgcron_job_details_view_with_empty_pgcron_job_detail(
        self, mock_get_pgcron_job_details
    ):
        mock_get_pgcron_job_details.return_value = Mock(Rows=[])
        response = self.client.post(
            reverse("get_pgcron_job_details"),
            data={"job_meta": {"id": 1}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("data"), "Job does not exist.")

    def test_get_pgcron_job_details_view_without_job_meta(self):
        response = self.client.post(
            reverse("get_pgcron_job_details"), data=self.tab_data
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("data"), "invalid job details supplied")

    def test_get_pgcron_job_details_url_resolves_get_pgcron_job_details_view(self):
        view = resolve("/get_pgcron_job_details/")
        self.assertEqual(view.func.__name__, get_pgcron_job_details.__name__)

    @patch.object(PostgreSQL, "GetPgCronJobLogs")
    @patch.object(PostgreSQL, "GetPgCronJobStats")
    def test_get_pgcron_job_logs_view(self, mock_stats, mock_logs):
        mock_stats.return_value = Mock(Rows=[{"succeeded": 1, "failed": 1}])
        mock_logs.return_value = Mock(Rows=[{"runid": 1, "job_pid": 2}])

        response = self.client.post(
            reverse("get_pgcron_job_logs"),
            data={"job_meta": {"id": 1}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("logs"), [{"runid": 1, "job_pid": 2}])
        self.assertEqual(response.json().get("stats"), {"succeeded": 1, "failed": 1})

    def test_get_pgcron_job_logs_view_without_job_meta(self):
        response = self.client.post(reverse("get_pgcron_job_logs"), data=self.tab_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("data"), "invalid job details supplied")

    def test_get_pgcron_job_logs_url_resolves_get_pgcron_job_logs_view(self):
        view = resolve("/get_pgcron_job_logs/")
        self.assertEqual(view.func.__name__, get_pgcron_job_logs.__name__)

    @patch.object(PostgreSQL, "SavePgCronJob")
    def test_save_pgcron_job_view(self, mock_save_pgcron_job):
        mock_save_pgcron_job.return_value = None
        response = self.client.post(
            reverse("save_pgcron_job"),
            data={
                "jobName": "Test Job",
                "schedule": "*/5 * * * *",
                "command": "test",
                "inDatabase": False,
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 200)

    @patch.object(PostgreSQL, "SavePgCronJob")
    def test_save_pgcron_job_view_with_database_error(self, mock_save_pgcron_job):
        mock_save_pgcron_job.side_effect = DatabaseError("mocked error")
        response = self.client.post(
            reverse("save_pgcron_job"),
            data={
                "jobName": "Test Job",
                "schedule": "*/5 * * * *",
                "command": "test",
                "inDatabase": False,
                **self.tab_data,
            },
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json().get("data"), "mocked error")

    def test_save_pgcron_job_url_resolves_save_pgcron_job_view(self):
        view = resolve("/save_pgcron_job/")
        self.assertEqual(view.func.__name__, save_pgcron_job.__name__)

    @patch.object(PostgreSQL, "DeletePgCronJob")
    def test_delete_pgcron_job_view(self, mock_delete_pgcron_job):
        mock_delete_pgcron_job.return_value = None
        response = self.client.post(
            reverse("delete_pgcron_job"), data={"job_meta": {"id": 1}, **self.tab_data}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "success")

    @patch.object(PostgreSQL, "DeletePgCronJob")
    def test_delete_pgcron_job_view_with_database_error(self, mock_delete_pgcron_job):
        mock_delete_pgcron_job.side_effect = DatabaseError("mocked error")
        response = self.client.post(
            reverse("delete_pgcron_job"), data={"job_meta": {"id": 1}, **self.tab_data}
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json().get("data"), "mocked error")

    def test_delete_pgcron_job_view_without_job_meta(self):
        response = self.client.post(reverse("delete_pgcron_job"), data=self.tab_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("data"), "invalid job details supplied")

    def test_delete_pgcron_job_url_resolves_delete_pgcron_job_view(self):
        view = resolve("/delete_pgcron_job/")
        self.assertEqual(view.func.__name__, delete_pgcron_job.__name__)

    @patch.object(PostgreSQL, "DeletePgCronJobLogs")
    def test_delete_pgcron_job_logs_view(self, mock_delete_pgcron_job_logs):
        mock_delete_pgcron_job_logs.return_value = None
        response = self.client.post(
            reverse("delete_pgcron_job_logs"),
            data={"job_meta": {"id": 1}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "success")

    @patch.object(PostgreSQL, "DeletePgCronJobLogs")
    def test_delete_pgcron_job_logs_view_with_database_error(
        self, mock_delete_pgcron_job_logs
    ):
        mock_delete_pgcron_job_logs.side_effect = DatabaseError("mocked error")
        response = self.client.post(
            reverse("delete_pgcron_job_logs"),
            data={"job_meta": {"id": 1}, **self.tab_data},
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json().get("data"), "mocked error")

    def test_delete_pgcron_job_logs_view_without_job_meta(self):
        response = self.client.post(
            reverse("delete_pgcron_job_logs"), data=self.tab_data
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("data"), "invalid job details supplied")

    def test_delete_pgcron_job_logs_url_resolves_delete_pgcron_job_logs_view(self):
        view = resolve("/delete_pgcron_job_logs/")
        self.assertEqual(view.func.__name__, delete_pgcron_job_logs.__name__)
