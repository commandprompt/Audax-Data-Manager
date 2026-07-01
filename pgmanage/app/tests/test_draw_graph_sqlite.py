import json
import os
import tempfile
from datetime import datetime, timedelta

import app.include.OmniDatabase as OmniDatabase
from app.models.main import Connection, Technology
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from .utils_testing import execute_client_login, get_client_omnidb_session

User = get_user_model()


class DrawGraphSQLite(TestCase):
    """ER Diagram generation against a throwaway SQLite database file.

    SQLite is the only backend whose QueryTables returns name_raw (always
    quoted, for every table) while its foreign-key metadata carries unquoted
    table names, so these tests cover the label-based edge endpoint
    resolution in draw_graph. No live database server is required.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        fd, cls.db_path = tempfile.mkstemp(
            suffix='.db', prefix='pgmanage_erd_test_'
        )
        os.close(fd)

        # draw_graph resolves the saved ERD layout by treating database_index
        # as a Connection id; the session below posts database_index 0, so a
        # Connection row with that id must exist for the request to succeed.
        cls.test_connection = Connection.objects.create(
            id=0,
            user=User.objects.get(username="admin"),
            technology=Technology.objects.filter(name="sqlite").first(),
            database=cls.db_path,
            alias="ERD sqlite test",
        )
        cls.database = OmniDatabase.Generic.InstantiateDatabase(
            'sqlite',
            '',
            '',
            cls.db_path,
            '',
            '',
            cls.test_connection.id
        )
        cls.database.connection.Execute(
            'CREATE TABLE "TestTable882" (id integer PRIMARY KEY)'
        )
        cls.database.connection.Execute(
            'CREATE TABLE child_882 ('
            'id integer PRIMARY KEY, '
            'parent_id integer REFERENCES "TestTable882" (id))'
        )

        cls.client_session = Client()
        success, response = execute_client_login(
            p_client=cls.client_session, p_username='admin', p_password='admin'
        )
        get_client_omnidb_session(p_client=cls.client_session)
        assert 200 == response.status_code

        session = cls.client_session.session
        session['pgmanage_session'].databases = [{
            'database': cls.database,
            'prompt_password': False,
            'prompt_timeout': datetime.now() + timedelta(0, 60000)
        }]
        session['pgmanage_session'].tab_connections = {0: cls.database}
        session['pgmanage_session'].tabs_databases = {0: cls.db_path}
        session.save()

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.db_path)
        except OSError:
            pass
        super().tearDownClass()

    def test_draw_graph_sqlite_fk_edges_session(self):
        # The SQLite ERD tab is opened without a schema (see createERDTab()
        # in TreeSqlite.vue), so the frontend posts an empty schema string.
        response = self.client_session.post(
            '/draw_graph/',
            {'data': '{"database_index": 0, "workspace_id": 0, "schema": ""}'},
        )
        assert 200 == response.status_code
        data = json.loads(response.content.decode())

        labels = {node['label']: node for node in data['nodes']}
        assert 'TestTable882' in labels
        assert 'child_882' in labels

        # every edge endpoint must reference an existing node
        node_ids = {node['id'] for node in data['nodes']}
        for edge in data['edges']:
            assert edge['from'] in node_ids, \
                "edge source {!r} is not a known node".format(edge['from'])
            assert edge['to'] in node_ids, \
                "edge target {!r} is not a known node".format(edge['to'])

        # the FK edge is present even though SQLite reports unquoted table
        # names in its foreign-key metadata while node ids are quoted
        child_id = labels['child_882']['id']
        parent_id = labels['TestTable882']['id']
        assert any(
            edge['from'] == child_id and edge['to'] == parent_id
            for edge in data['edges']
        ), 'expected FK edge child_882 -> TestTable882 in graph'

        # the FK/PK column flags are resolved despite the name mismatch
        assert any(
            column['name'] == 'parent_id' and column['is_fk']
            for column in labels['child_882']['columns']
        ), 'expected parent_id to be flagged as a foreign key column'
        assert any(
            column['name'] == 'id' and column['is_pk']
            for column in labels['TestTable882']['columns']
        ), 'expected TestTable882.id to be flagged as a primary key column'
