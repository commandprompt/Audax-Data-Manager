import copy
import io
import logging
import os
import threading
import time
import traceback
from collections import defaultdict
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Optional

import paramiko
import sqlparse
from app.client_manager import Client, client_manager
from app.include import OmniDatabase
from app.include.custom_paramiko_expect import SSHClientInteraction
from app.include.Session import Session
from app.include.Spartacus import Utils
from app.models.main import Connection, ConsoleHistory, QueryHistory, Tab
from app.utils.decorators import session_required, user_authenticated
from django.contrib.auth.models import User
from django.db import DatabaseError
from django.http import HttpRequest, JsonResponse

from pgmanage import settings
from pgmanage.startup import clean_temp_folder

logger = logging.getLogger("app.QueryServer")


class QueryModes(IntEnum):
    DATA_OPERATION = 0
    FETCH_MORE = 1
    FETCH_ALL = 2
    COMMIT = 3
    ROLLBACK = 4


class ConsoleModes(IntEnum):
    DATA_OPERATION = 0
    FETCH_MORE = 1
    FETCH_ALL = 2
    SKIP_FETCH = 3


class RequestType(IntEnum):
    LOGIN = 0
    QUERY = 1
    EXECUTE = 2
    SCRIPT = 3
    QUERY_EDIT_DATA = 4
    SAVE_EDIT_DATA = 5
    CANCEL_THREAD = 6
    DEBUG = 7
    CLOSE_TAB = 8
    ADVANCED_OBJECT_SEARCH = 9
    CONSOLE = 10
    TERMINAL = 11
    PING = 12
    SCHEMA_EDIT_DATA = 13


class ResponseType(IntEnum):
    LOGIN_RESULT = 0
    QUERY_RESULT = 1
    QUERY_EDIT_DATA_RESULT = 2
    SAVE_EDIT_DATA_RESULT = 3
    SESSION_MISSING = 4
    PASSWORD_REQUIRED = 5
    QUERY_ACK = 6
    MESSAGE_EXCEPTION = 7
    DEBUG_RESPONSE = 8
    REMOVE_CONTEXT = 9
    ADVANCED_OBJECT_SEARCH_RESULT = 10
    CONSOLE_RESULT = 11
    TERMINAL_RESULT = 12
    PONG = 13
    OPERATION_CANCELLED = 14
    SCHEMA_EDIT_RESULT = 15


class DebugState(IntEnum):
    INITIAL = 0
    STARTING = 1
    READY = 2
    STEP = 3
    FINISHED = 4
    CANCEL = 5


class StoppableThread(threading.Thread):
    def __init__(self, p1, p2):
        super().__init__(
            name=f"{p1.__name__}-{p2.get('tab_id')}",
            target=p1,
            args=(
                self,
                p2,
            ),
        )
        self.cancel = False

    def stop(self):
        self.cancel = True


def get_duration(start, end) -> str:
    duration = ""
    time_diff = end - start
    if time_diff.days == 0 and time_diff.seconds == 0:
        duration = str(time_diff.microseconds / 1000) + " ms"
    else:
        days, seconds = time_diff.days, time_diff.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        duration = "{0}:{1}:{2}".format(
            "%02d" % (hours,), "%02d" % (minutes,), "%02d" % (seconds,)
        )

    return duration


def log_history(
    user_id: int,
    sql: str,
    start: datetime,
    end: datetime,
    duration: str,
    status: str,
    conn_id: int,
    database: str,
) -> None:

    try:
        query_db = QueryHistory.objects.filter(
            user=User.objects.get(id=user_id),
            connection=Connection.objects.get(id=conn_id),
            database=database,
        ).last()
        if query_db and query_db.snippet == sql:
            query_db.start_time = start
            query_db.end_time = end
            query_db.duration = duration
            query_db.status = status
            query_db.save()
        else:
            query_object = QueryHistory(
                user=User.objects.get(id=user_id),
                connection=Connection.objects.get(id=conn_id),
                start_time=start,
                end_time=end,
                duration=duration,
                status=status,
                snippet=sql,
                database=database,
            )
            query_object.save()
    except Exception as exc:
        logger.error("""*** Exception ***\n{0}""".format(traceback.format_exc()))


def export_data(
    sql_cmd: str, database, encoding: str, delimiter: str, cmd_type: str
) -> tuple[str, str]:
    skip_headers: bool = False
    # cleaning temp folder
    clean_temp_folder()

    extension: str
    if 'csv' in cmd_type:
        extension = "csv"
    elif 'xlsx' in cmd_type:
        extension = "xlsx"
    else:
        extension = "json"

    export_dir: str = settings.TEMP_DIR

    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    database.connection.Open()

    file_name: str = f'${str(time.time()).replace(".", "_")}.{extension}'

    data = database.connection.QueryBlock(sql_cmd, 1000, False, True)

    name_count = defaultdict(int)
    columns = []
    for column in data.Columns:
        name_count[column] += 1
        if name_count[column] > 1:
            columns.append(f"{column}_{name_count[column]}")
        else:
            columns.append(column)

    data.Columns = columns

    file_path: str = os.path.join(export_dir, file_name)
    skip_headers = cmd_type in ['export_xlsx-no_headers', 'export_csv-no_headers']
    file = Utils.DataFileWriter(
        file_path, data.Columns, encoding, delimiter, skip_headers=skip_headers
    )

    file.Open()

    has_more_records: bool
    if database.connection.start:
        file.Write(data)
        has_more_records = False
    elif len(data.Rows) > 0:
        file.Write(data)
        has_more_records = True
    else:
        has_more_records = False

    while has_more_records:
        data = database.connection.QueryBlock(sql_cmd, 1000, False, True)

        if database.connection.start:
            file.Write(data)
            has_more_records = False
        elif len(data.Rows) > 0:
            file.Write(data)
            has_more_records = True
        else:
            has_more_records = False
    database.connection.Close()

    file.Flush()

    return file_name, extension


@user_authenticated
@session_required(include_session=False)
def clear_client(request: HttpRequest) -> JsonResponse:
    client_manager.clear_client(request.session.session_key)
    return JsonResponse({})


@user_authenticated
@session_required(include_session=False)
def client_keep_alive(request: HttpRequest) -> JsonResponse:
    client: Client = client_manager.get_or_create_client(
        client_id=request.session.session_key
    )
    client.last_update = datetime.now()

    return JsonResponse({})


@session_required(include_session=False)
def long_polling(request: HttpRequest) -> JsonResponse:
    startup: bool = request.data["startup"]

    client_object: Client = client_manager.get_or_create_client(
        client_id=request.session.session_key
    )

    if startup:
        client_object.release_polling_lock()

    # Acquire client polling lock to read returning data
    client_object.polling_lock.acquire()

    returning_data: list[dict[Any, Any]] = []

    client_object.returning_data_lock.acquire()

    while len(client_object.returning_data) > 0:
        try:
            returning_data.append(client_object.returning_data.popleft())
        except IndexError:
            pass

    client_object.release_returning_data_lock()
    return JsonResponse({"returning_rows": returning_data})


def queue_response(client: Client, data: dict[str, Any]) -> None:

    client.returning_data_lock.acquire()

    client.returning_data.append(data)

    # Attempt to release client polling lock so that the polling thread can read data
    client.release_polling_lock()

    client.release_returning_data_lock()


@session_required
def create_request(request: HttpRequest, session: Session) -> JsonResponse:
    json_object: dict[str, Any] = request.data
    request_type: RequestType = json_object["request_type"]
    context_code: str = json_object["context_code"]
    request_data: dict[str, Any] = json_object["data"]

    client_object: Client = client_manager.get_or_create_client(
        client_id=request.session.session_key
    )

    # Release lock to avoid dangling ajax polling requests
    client_object.release_polling_lock()

    # Cancel thread
    if request_type == RequestType.CANCEL_THREAD:
        try:
            workspace_context: Optional[dict[str, Any]] = client_object.get_tab(
                tab_id=request_data.get("tab_id"),
                workspace_id=request_data.get("workspace_id"),
            )
            if workspace_context:
                if workspace_context.get("type") == "advancedobjectsearch":

                    def callback(self):
                        try:
                            self.tag["lock"].acquire()

                            for active_connection in self.tag["activeConnections"]:
                                active_connection.Cancel(False)
                        finally:
                            self.tag["lock"].release()

                    workspace_context["thread_pool"].stop(p_callback=callback)
                else:
                    if workspace_context["thread"]:
                        workspace_context["thread"].stop()
                    try:
                        workspace_context["omnidatabase"].connection.Cancel(keep_connection=True)
                    except Exception as exc:
                        logger.error(exc)

                    response_data = {
                        "response_type": ResponseType.OPERATION_CANCELLED,
                        "context_code": context_code,
                    }
                    queue_response(client_object, response_data)
        except Exception:
            pass

    # Close Tab
    elif request_type == RequestType.CLOSE_TAB:
        for tab_close_data in request_data:
            client_object.close_tab(
                tab_id=tab_close_data.get("tab_id"),
                workspace_id=tab_close_data.get("workspace_id"),
            )
            # remove from tabs table if db_tab_id is not null
            if tab_close_data.get("tab_db_id"):
                try:
                    tab = Tab.objects.get(id=tab_close_data.get("tab_db_id"))
                    tab.delete()
                except Exception:
                    pass
    else:
        # Check database prompt timeout
        if request_data["db_index"] is not None:
            timeout: dict[str, Any] = session.DatabaseReachPasswordTimeout(
                request_data["db_index"]
            )
            if timeout["timeout"]:
                response_data = {
                    "response_type": ResponseType.PASSWORD_REQUIRED,
                    "context_code": context_code,
                    "data": timeout.get("message"),
                }
                queue_response(client_object, response_data)
                return JsonResponse({})

        if request_type == RequestType.TERMINAL:
            workspace_context: Optional[dict[str, Any]] = client_object.get_tab(
                workspace_id=request_data["workspace_id"]
            )

            if (
                workspace_context is None
                or not workspace_context.get("terminal_transport").is_active()
            ):
                workspace_context: dict[str, Any] = client_object.create_main_tab(
                    workspace_id=request_data["workspace_id"],
                    tab={"thread": None, "terminal_object": None},
                )
                start_thread: bool = True

                conn = Connection.objects.get(id=request_data["ssh_id"])
                conn.last_access_date = datetime.now(tz=timezone.utc)
                conn.save()

                try:
                    conn_object: dict[str, Any] = session.databases[
                        request_data["ssh_id"]
                    ]

                    client = paramiko.SSHClient()
                    client.load_system_host_keys()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    # ssh key provided
                    if conn_object["tunnel"]["key"].strip() != "":
                        key = paramiko.RSAKey.from_private_key(
                            io.StringIO(conn_object["tunnel"]["key"]),
                            password=conn_object["tunnel"]["password"] or None,
                        )
                        client.connect(
                            hostname=conn_object["tunnel"]["server"],
                            username=conn_object["tunnel"]["user"],
                            pkey=key,
                            passphrase=conn_object["tunnel"]["password"],
                            port=int(conn_object["tunnel"]["port"]),
                        )
                    else:
                        client.connect(
                            hostname=conn_object["tunnel"]["server"],
                            username=conn_object["tunnel"]["user"],
                            password=conn_object["tunnel"]["password"],
                            port=int(conn_object["tunnel"]["port"]),
                        )

                    transport = client.get_transport()
                    transport.set_keepalive(120)

                    resize: Optional[dict[str, Any]] = request_data.get("resize")

                    workspace_context["terminal_ssh_client"] = client
                    workspace_context["terminal_transport"] = transport
                    workspace_context["terminal_object"] = SSHClientInteraction(
                        client,
                        timeout=60,
                        display=False,
                        tty_width=resize["cols"] if resize else 80,
                        tty_height=resize["rows"] if resize else 24,
                    )

                    workspace_context["terminal_type"] = "remote"

                except Exception as exc:
                    start_thread = False
                    response_data = {
                        "response_type": ResponseType.MESSAGE_EXCEPTION,
                        "context_code": context_code,
                        "data": str(exc),
                    }
                    queue_response(client_object, response_data)

                if start_thread:
                    request_data["context_code"] = context_code
                    request_data["workspace_context"] = workspace_context
                    request_data["client_object"] = client_object
                    request_data["session"] = session
                    t = StoppableThread(thread_terminal, request_data)
                    workspace_context["thread"] = t
                    workspace_context["type"] = "terminal"
                    workspace_context["workspace_id"] = request_data["workspace_id"]
                    t.start()
            else:
                try:
                    workspace_context["last_update"] = datetime.now()
                    resize: Optional[dict[str, Any]] = request_data.get("resize")
                    if resize:
                        workspace_context["terminal_object"].resize(
                            width=resize["cols"], height=resize["rows"]
                        )
                    else:
                        workspace_context["terminal_object"].send(request_data["cmd"])
                except OSError:
                    pass

        elif request_type in [
            RequestType.QUERY,
            RequestType.QUERY_EDIT_DATA,
            RequestType.SAVE_EDIT_DATA,
            RequestType.ADVANCED_OBJECT_SEARCH,
            RequestType.CONSOLE,
            RequestType.SCHEMA_EDIT_DATA
        ]:
            # create tab object if it doesn't exist
            workspace_context: Optional[dict[str, Any]] = client_object.get_tab(
                workspace_id=request_data["workspace_id"], tab_id=request_data["tab_id"]
            )
            if workspace_context is None:
                workspace_context = client_object.create_tab(
                    workspace_id=request_data["workspace_id"],
                    tab_id=request_data["tab_id"],
                    tab={"thread": None, "omnidatabase": None, "inserted_tab": False},
                )

            try:
                client_object.get_database(
                    session=session,
                    tab=workspace_context,
                    workspace_id=request_data["workspace_id"],
                    database_index=request_data["db_index"],
                    attempt_to_open_connection=True,
                    current_database=request_data.get("database_name"),
                )
            except Exception as exc:
                response_data = {
                    "response_type": ResponseType.PASSWORD_REQUIRED,
                    "context_code": context_code,
                    "data": str(exc),
                }
                queue_response(client_object, response_data)
                return JsonResponse({})

            request_data["context_code"] = context_code
            request_data["database"] = workspace_context["omnidatabase"]
            request_data["client_object"] = client_object
            request_data["session"] = session
            # Query request
            if request_type == RequestType.QUERY:
                workspace_context["tab_db_id"] = request_data["tab_db_id"]
                request_data["workspace_context"] = workspace_context
                t = StoppableThread(thread_query, request_data)
                workspace_context["thread"] = t
                workspace_context["type"] = "query"
                workspace_context["sql_cmd"] = request_data["sql_cmd"]
                workspace_context["sql_save"] = request_data["sql_save"]
                workspace_context["tab_id"] = request_data["tab_id"]
                # t.setDaemon(True)
                t.start()

            # Console request
            elif request_type == RequestType.CONSOLE:
                request_data["workspace_context"] = workspace_context
                t = StoppableThread(thread_console, request_data)
                workspace_context["thread"] = t
                workspace_context["type"] = "console"
                workspace_context["sql_cmd"] = request_data["sql_cmd"]
                # t.setDaemon(True)
                t.start()

            # Query edit data
            elif request_type == RequestType.QUERY_EDIT_DATA:
                t = StoppableThread(thread_query_edit_data, request_data)
                workspace_context["thread"] = t
                workspace_context["type"] = "edit"
                # t.setDaemon(True)
                t.start()

            # Save edit data
            elif request_type == RequestType.SAVE_EDIT_DATA:
                t = StoppableThread(thread_save_edit_data, request_data)
                workspace_context["thread"] = t
                workspace_context["type"] = "edit"
                # t.setDaemon(True)
                t.start()
            
            # Schema edit data
            elif request_type == RequestType.SCHEMA_EDIT_DATA:
                t = StoppableThread(thread_schema_edit_data, request_data)
                workspace_context["thread"] = t
                workspace_context["type"] = "schema_edit"
                t.start()

        # Debugger
        elif request_type == RequestType.DEBUG:

            # create tab object if it doesn't exist
            workspace_context: Optional[dict[str, Any]] = client_object.get_tab(
                workspace_id=request_data.get("workspace_id"),
                tab_id=request_data.get("v_tab_id"),
            )

            if workspace_context is None:
                workspace_context = client_object.create_tab(
                    workspace_id=request_data.get("workspace_id"),
                    tab_id=request_data.get("v_tab_id"),
                    tab={
                        "thread": None,
                        "omnidatabase_debug": None,
                        "omnidatabase_control": None,
                        "port": None,
                        "debug_pid": -1,
                        "cancelled": False,
                        "tab_id": request_data["v_tab_id"],
                        "type": "debug",
                    },
                )

            # New debugger, create connections
            if request_data["v_state"] == DebugState.STARTING:
                try:
                    v_conn_tab_connection = session.databases[
                        request_data["v_db_index"]
                    ]["database"]

                    v_database_debug = OmniDatabase.Generic.InstantiateDatabase(
                        v_conn_tab_connection.db_type,
                        v_conn_tab_connection.connection.host,
                        str(v_conn_tab_connection.connection.port),
                        v_conn_tab_connection.active_service,
                        v_conn_tab_connection.active_user,
                        v_conn_tab_connection.connection.password,
                        v_conn_tab_connection.conn_id,
                        v_conn_tab_connection.alias,
                        conn_string=v_conn_tab_connection.conn_string,
                        parse_conn_string=False,
                    )
                    v_database_control = OmniDatabase.Generic.InstantiateDatabase(
                        v_conn_tab_connection.db_type,
                        v_conn_tab_connection.connection.host,
                        str(v_conn_tab_connection.connection.port),
                        v_conn_tab_connection.active_service,
                        v_conn_tab_connection.active_user,
                        v_conn_tab_connection.connection.password,
                        v_conn_tab_connection.conn_id,
                        v_conn_tab_connection.alias,
                        conn_string=v_conn_tab_connection.conn_string,
                        parse_conn_string=False,
                    )
                    workspace_context["omnidatabase_debug"] = v_database_debug
                    workspace_context["cancelled"] = False
                    workspace_context["omnidatabase_control"] = v_database_control
                    workspace_context["port"] = v_database_debug.connection.ExecuteScalar(
                        "show port"
                    )
                except Exception as exc:
                    logger.error(
                        """*** Exception ***\n{0}""".format(traceback.format_exc())
                    )

                    response_data = {
                        "response_code": ResponseType.MESSAGE_EXCEPTION,
                        "context_code": context_code,
                        "data": traceback.format_exc().replace("\n", "<br>"),
                    }
                    queue_response(client_object, response_data)

            request_data["context_code"] = context_code
            request_data["workspace_context"] = workspace_context
            request_data["client_object"] = client_object

            t = StoppableThread(thread_debug, request_data)
            workspace_context["thread"] = t
            # t.setDaemon(True)
            t.start()

    return JsonResponse({})


def thread_debug(self, args):
    v_response = {
        "v_code": -1,
        "v_context_code": args["v_context_code"],
        "v_error": False,
        "v_data": 1,
    }
    v_state = args["v_state"]
    v_tab_object = args["v_tab_object"]
    v_client_object = args["v_client_object"]
    v_database_debug = v_tab_object["omnidatabase_debug"]
    v_database_control = v_tab_object["omnidatabase_control"]

    try:

        if v_state == DebugState.STARTING:

            # Start debugger and return ready state
            v_database_debug.connection.Open()
            v_database_control.connection.Open()

            # Cleaning contexts table
            v_database_debug.connection.Execute(
                "delete from omnidb.contexts t where t.pid not in (select pid from pg_stat_activity where pid = t.pid)"
            )

            connections_details = v_database_debug.connection.Query(
                "select pg_backend_pid()", True
            )
            pid = connections_details.Rows[0][0]

            v_database_debug.connection.Execute(
                "insert into omnidb.contexts (pid, function, hook, lineno, stmttype, breakpoint, finished) values ({0}, null, null, null, null, 0, false)".format(
                    pid
                )
            )

            # lock row for current pid
            v_database_control.connection.Execute(
                "select pg_advisory_lock({0}) from omnidb.contexts where pid = {0}".format(
                    pid
                )
            )

            # updating pid and port in tab object
            v_tab_object["debug_pid"] = pid

            # Run thread that will execute the function
            t = StoppableThread(
                thread_debug_run_func,
                {
                    "v_tab_object": v_tab_object,
                    "v_context_code": args["v_context_code"],
                    "v_function": args["v_function"],
                    "v_type": args["v_type"],
                    "v_client_object": v_client_object,
                },
            )
            v_tab_object["thread"] = t
            # t.setDaemon(True)
            t.start()

            # ws_object.v_list_tab_objects[v_tab_id] = v_tab_object

            v_lineno = None
            # wait for context to be ready or thread ends
            while v_lineno == None and t.is_alive():
                time.sleep(0.5)
                v_lineno = v_database_control.connection.ExecuteScalar(
                    "select lineno from omnidb.contexts where pid = {0} and lineno is not null".format(
                        pid
                    )
                )

            # Function ended instantly
            if not t.is_alive():
                v_database_control.connection.Close()
            else:
                v_variables = v_database_control.connection.Query(
                    "select name,attribute,vartype,value from omnidb.variables where pid = {0}".format(
                        pid
                    ),
                    True,
                )

                v_response["v_code"] = ResponseType.DEBUG_RESPONSE
                v_response["v_data"] = {
                    "v_state": DebugState.READY,
                    "v_remove_context": False,
                    "v_variables": v_variables.Rows,
                    "v_lineno": v_lineno,
                }
                queue_response(v_client_object, v_response)

        elif v_state == DebugState.STEP:

            v_database_control.connection.Execute(
                "update omnidb.contexts set breakpoint = {0} where pid = {1}".format(
                    args["v_next_breakpoint"], v_tab_object["debug_pid"]
                )
            )

            try:
                v_database_control.connection.Execute(
                    "select pg_advisory_unlock({0}) from omnidb.contexts where pid = {0}; select pg_advisory_lock({0}) from omnidb.contexts where pid = {0};".format(
                        v_tab_object["debug_pid"]
                    )
                )

                # acquired the lock, get variables and lineno
                v_variables = v_database_control.connection.Query(
                    "select name,attribute,vartype,value from omnidb.variables where pid = {0}".format(
                        v_tab_object["debug_pid"]
                    ),
                    True,
                )
                v_context_data = v_database_control.connection.Query(
                    "select lineno,finished from omnidb.contexts where pid = {0}".format(
                        v_tab_object["debug_pid"]
                    ),
                    True,
                )

                # not last statement
                if v_context_data.Rows[0][1] != "True":
                    v_response["v_code"] = ResponseType.DEBUG_RESPONSE
                    v_response["v_data"] = {
                        "v_state": DebugState.READY,
                        "v_remove_context": True,
                        "v_variables": v_variables.Rows,
                        "v_lineno": v_context_data.Rows[0][0],
                    }
                    queue_response(v_client_object, v_response)
                else:
                    v_database_control.connection.Execute(
                        "select pg_advisory_unlock({0}) from omnidb.contexts where pid = {0};".format(
                            v_tab_object["debug_pid"]
                        )
                    )
                    v_database_control.connection.Close()
                    v_response["v_code"] = ResponseType.REMOVE_CONTEXT
                    queue_response(v_client_object, v_response)

            except Exception:
                v_response["v_code"] = ResponseType.REMOVE_CONTEXT
                queue_response(v_client_object, v_response)

        # Cancelling debugger, the thread executing the function will return the cancel status
        elif v_state == DebugState.CANCEL:
            v_tab_object["cancelled"] = True
            v_database_control.connection.Cancel(False)
            v_database_control.connection.Terminate(v_tab_object["debug_pid"])
            v_database_control.connection.Close()

    except Exception as exc:
        v_response["v_code"] = ResponseType.DEBUG_RESPONSE
        v_response["v_data"] = {
            "v_state": DebugState.FINISHED,
            "v_remove_context": True,
            "v_error": True,
            "v_error_msg": str(exc),
        }

        try:
            v_database_debug.connection.Close()
            v_database_control.connection.Close()
        except Exception:
            None

        queue_response(v_client_object, v_response)


def thread_debug_run_func(self, args):
    v_response = {
        "v_code": -1,
        "v_context_code": args["v_context_code"],
        "v_error": False,
        "v_data": 1,
    }
    v_tab_object = args["v_tab_object"]
    v_client_object = args["v_client_object"]
    v_database_debug = v_tab_object["omnidatabase_debug"]
    v_database_control = v_tab_object["omnidatabase_control"]

    try:
        # enable debugger for current connection
        conn_string = (
            "host=''localhost'' port={0} dbname=''{1}'' user=''{2}''".format(
                v_tab_object["port"],
                v_database_debug.v_service,
                v_database_debug.v_user,
            )
        )

        v_database_debug.connection.Execute(
            "select omnidb.omnidb_enable_debugger('{0}')".format(conn_string)
        )

        # run function it will lock until the function ends
        if args["v_type"] == "f":
            v_func_return = v_database_debug.connection.Query(
                "select * from {0} limit 1000".format(args["v_function"]), True
            )
        else:
            v_func_return = v_database_debug.connection.Query(
                "call {0}".format(args["v_function"]), True
            )

        # Not cancelled, return all data
        if not v_tab_object["cancelled"]:

            # retrieve variables
            v_variables = v_database_debug.connection.Query(
                "select name,attribute,vartype,value from omnidb.variables where pid = {0}".format(
                    v_tab_object["debug_pid"]
                ),
                True,
            )

            # retrieve statistics
            v_statistics = v_database_debug.connection.Query(
                'select lineno,coalesce(trunc((extract("epoch" from tend)  - extract("epoch" from tstart))::numeric,4),0) as msec from omnidb.statistics where pid = {0} order by step'.format(
                    v_tab_object["debug_pid"]
                ),
                True,
            )

            # retrieve statistics summary
            v_statistics_summary = v_database_debug.connection.Query(
                """
            select lineno, max(msec) as msec
            from (select lineno,coalesce(trunc((extract("epoch" from tend) - extract("epoch" from tstart))::numeric,4),0) as msec from omnidb.statistics where pid = {0}) t
            group by lineno
            order by lineno
            """.format(
                    v_tab_object["debug_pid"]
                ),
                True,
            )

            # retrieve notices
            v_notices = v_database_debug.connection.GetNotices()
            v_notices_text = ""
            if len(v_notices) > 0:
                for v_notice in v_notices:
                    v_notices_text += v_notice.replace("\n", "<br/>")

            v_response["v_data"] = {
                "v_state": DebugState.FINISHED,
                "v_remove_context": True,
                "v_result_rows": v_func_return.Rows,
                "v_result_columns": v_func_return.Columns,
                "v_result_statistics": v_statistics.Rows,
                "v_result_statistics_summary": v_statistics_summary.Rows,
                "v_result_notices": v_notices_text,
                "v_result_notices_length": len(v_notices),
                "v_variables": v_variables.Rows,
                "v_error": False,
            }

            v_database_debug.connection.Close()

            # send debugger finished message
            v_response["v_code"] = ResponseType.DEBUG_RESPONSE

            queue_response(v_client_object, v_response)
        # Cancelled, return cancelled status
        else:
            v_response["v_code"] = ResponseType.DEBUG_RESPONSE
            v_response["v_data"] = {
                "v_state": DebugState.CANCEL,
                "v_remove_context": True,
                "v_error": False,
            }
            queue_response(v_client_object, v_response)

    except Exception as exc:
        # Not cancelled
        if not v_tab_object["cancelled"]:
            v_response["v_code"] = ResponseType.DEBUG_RESPONSE
            v_response["v_data"] = {
                "v_state": DebugState.FINISHED,
                "v_remove_context": True,
                "v_error": True,
                "v_error_msg": str(exc),
            }
            try:
                v_database_debug.connection.Close()
            except Exception:
                None
            try:
                v_database_control.connection.Close()
            except Exception:
                None

            queue_response(v_client_object, v_response)
        else:
            v_response["v_code"] = ResponseType.DEBUG_RESPONSE
            v_response["v_data"] = {
                "v_state": DebugState.CANCEL,
                "v_remove_context": True,
                "v_error": False,
            }
            queue_response(v_client_object, v_response)


def thread_terminal(self, args) -> None:

    try:
        workspace_context: dict[str, Any] = args["workspace_context"]
        terminal_object: SSHClientInteraction = workspace_context["terminal_object"]
        terminal_ssh_client: paramiko.SSHClient = workspace_context["terminal_ssh_client"]
        client_object: Client = args["client_object"]

        while not self.cancel:
            try:
                if workspace_context["terminal_type"] == "local":
                    data_return = terminal_object.read_nonblocking(size=1024)
                else:
                    data_return = terminal_object.read_current()

                # send data in chunks to avoid blocking the websocket server
                chunks = [
                    data_return[x : x + 10000]
                    for x in range(0, len(data_return), 10000)
                ]

                if len(chunks) > 0:
                    for i, chunk in enumerate(chunks):
                        if self.cancel:
                            break

                        response_data = {
                            "response_type": ResponseType.TERMINAL_RESULT,
                            "context_code": args["context_code"],
                            "error": False,
                            "data": 1,
                        }

                        if not i == len(chunks) - 1:
                            response_data["data"] = {
                                "data": chunk,
                                "last_block": False,
                            }
                        else:
                            response_data["data"] = {
                                "data": chunk,
                                "last_block": True,
                            }
                        if not self.cancel:
                            queue_response(client_object, response_data)
                else:
                    if not self.cancel:
                        queue_response(client_object, response_data)

            except Exception as exc:
                transport = terminal_ssh_client.get_transport()
                if transport is None or transport.is_active() is False:
                    break
                if "EOF" in str(exc):
                    break

    except Exception as exc:
        logger.error("""*** Exception ***\n{0}""".format(traceback.format_exc()))
        response_data["data"] = {"data": str(exc), "duration": ""}
        if not self.cancel:
            queue_response(client_object, response_data)


def thread_query(self, args) -> None:
    response_data = {
        "response_type": ResponseType.QUERY_RESULT,
        "context_code": args["context_code"],
        "error": False,
        "data": 1,
    }

    try:
        sql_cmd: str = args.get("sql_cmd")
        cmd_type: Optional[str] = args.get("cmd_type")
        workspace_context: dict = args.get("workspace_context")
        mode: QueryModes = args.get("mode")
        all_data: bool = args.get("all_data")
        log_query: bool = args.get("log_query")
        tab_title: str = args.get("tab_title")
        autocommit: bool = args.get("autocommit")
        client_object: Client = args.get("client_object")
        block_size: int = args.get("block_size", 50)

        session: Session = args.get("session")
        database = args.get("database")

        log_start_time = datetime.now(timezone.utc)
        log_status: str = "success"

        inserted_id: Optional[int] = None
        if (
            not workspace_context.get("tab_db_id")
            and not workspace_context.get("inserted_tab")
            and log_query
        ):
            db_tab = Tab(
                user=User.objects.get(id=session.user_id),
                connection=Connection.objects.get(id=database.conn_id),
                title=tab_title,
                snippet=workspace_context.get("sql_save"),
                database=database.active_service,
            )
            db_tab.save()
            inserted_id = db_tab.id
            workspace_context["inserted_tab"] = True

        log_end_time = datetime.now(timezone.utc)
        duration = get_duration(log_start_time, log_end_time)

        if cmd_type in [
            "export_csv",
            "export_xlsx",
            "export_csv-no_headers",
            "export_xlsx-no_headers",
            "export_json"
        ]:
            file_name, extension = export_data(
                sql_cmd=sql_cmd,
                database=database,
                encoding=session.csv_encoding,
                delimiter=session.csv_delimiter,
                cmd_type=cmd_type,
            )

            log_end_time = datetime.now(timezone.utc)
            duration = get_duration(log_start_time, log_end_time)
            file_suffix = log_end_time.strftime("%Y-%m-%d_%H-%M-%S")
            response_data["data"] = {
                "file_name": f"{settings.PATH}/static/temp/{file_name}",
                "download_name": f"pgmanage_exported-{file_suffix}.{extension}",
                "duration": duration,
                "inserted_id": inserted_id,
                "con_status": database.connection.GetConStatus(),
                "chunks": False,
            }

            if not self.cancel:
                queue_response(client_object, response_data)
        else:
            if mode == QueryModes.DATA_OPERATION:
                database.connection.autocommit = autocommit
                if (
                    not database.connection.con
                    or database.connection.GetConStatus() == 0
                ):
                    database.connection.Open()
                else:
                    database.connection.start = True

            if (
                mode in (QueryModes.DATA_OPERATION, QueryModes.FETCH_MORE)
                and not all_data
            ):
                block_size = block_size if mode == QueryModes.FETCH_MORE else 50
                if database.db_type == "oracle" and len(sql_cmd.split(";\n")) >= 2:
                    list_sql: list[str] = sqlparse.split(sql_cmd,  strip_semicolon=True)
                    for el in list_sql:
                        data = database.connection.QueryBlock(el, block_size, True, True)
                else:
                    data = database.connection.QueryBlock(sql_cmd, block_size, True, True)

                notices = database.connection.GetNotices()[:]

                database.connection.ClearNotices()

                log_end_time = datetime.now(timezone.utc)
                duration = get_duration(log_start_time, log_end_time)

                response_data["data"] = {
                    "col_names": data.Columns,
                    "col_types": [
                        database.connection.ResolveType(c)
                        for c in data.ColumnTypeCodes
                    ],
                    "data": data.Rows,
                    "last_block": True,
                    "duration": duration,
                    "notices": notices,
                    "inserted_id": inserted_id,
                    "status": database.connection.GetStatus(),
                    "con_status": database.connection.GetConStatus(),
                    "chunks": True,
                }

                if not self.cancel:
                    queue_response(client_object, response_data)
            elif mode == QueryModes.FETCH_ALL or all_data:
                has_more_records = True

                while has_more_records:

                    data = database.connection.QueryBlock(sql_cmd, 10000, True, True)

                    notices = database.connection.GetNotices()

                    database.connection.ClearNotices()

                    log_end_time = datetime.now(timezone.utc)

                    duration = get_duration(log_start_time, log_end_time)

                    response_data["data"] = {
                        "col_names": data.Columns,
                        "col_types": [
                            database.connection.ResolveType(c)
                            for c in data.ColumnTypeCodes
                        ],
                        "data": data.Rows,
                        "last_block": False,
                        "duration": duration,
                        "notices": notices,
                        "inserted_id": inserted_id,
                        "status": "",
                        "con_status": 0,
                        "chunks": True,
                    }

                    if database.connection.start:
                        has_more_records = False
                    elif len(data.Rows) > 0:
                        has_more_records = True
                    else:
                        has_more_records = False

                    if self.cancel:
                        break
                    if has_more_records:
                        queue_response(client_object, response_data)

                if not self.cancel:

                    notices = database.connection.GetNotices()

                    log_end_time = datetime.now(timezone.utc)
                    duration = get_duration(log_start_time, log_end_time)

                    response_data["data"] = {
                        "col_names": data.Columns,
                        "col_types": [
                            database.connection.ResolveType(c)
                            for c in data.ColumnTypeCodes
                        ],
                        "data": data.Rows,
                        "last_block": True,
                        "duration": duration,
                        "notices": notices,
                        "inserted_id": inserted_id,
                        "status": database.connection.GetStatus(),
                        "con_status": database.connection.GetConStatus(),
                        "chunks": True,
                    }
                    queue_response(client_object, response_data)
            elif mode in (QueryModes.COMMIT, QueryModes.ROLLBACK):
                duration = get_duration(log_start_time, log_end_time)

                if mode == QueryModes.COMMIT:
                    database.connection.Query("COMMIT;", True)
                else:
                    database.connection.Query("ROLLBACK;", True)

                response_data["data"] = {
                    "col_names": None,
                    "data": [],
                    "last_block": True,
                    "duration": duration,
                    "notices": [],
                    "inserted_id": inserted_id,
                    "status": database.connection.GetStatus(),
                    "con_status": database.connection.GetConStatus(),
                    "chunks": False,
                }
                queue_response(client_object, response_data)
    except Exception as exc:
        if not self.cancel:
            notices = database.connection.GetNotices()[:]
            database.connection.ClearNotices()

            log_end_time = datetime.now(timezone.utc)
            duration = get_duration(log_start_time, log_end_time)

            log_status = "error"
            response_data["data"] = {
                "position": database.GetErrorPosition(str(exc), sql_cmd),
                "message": str(exc),
                "duration": duration,
                "notices": notices,
                "inserted_id": inserted_id,
                "status": 0,
                "con_status": database.connection.GetConStatus(),
                "chunks": False,
            }

            response_data["error"] = True

            queue_response(client_object, response_data)

    if mode == QueryModes.DATA_OPERATION and log_query:
        log_history(
            user_id=session.user_id,
            sql=sql_cmd,
            start=log_start_time,
            end=log_end_time,
            duration=duration,
            status=log_status,
            conn_id=database.conn_id,
            database=database.active_service,
        )

    if mode == QueryModes.DATA_OPERATION and workspace_context.get("tab_db_id") and log_query:
        tab = Tab.objects.filter(id=workspace_context.get("tab_db_id")).first()
        if tab:
            tab.snippet = workspace_context.get("sql_save")
            tab.title = tab_title
            tab.save()


def thread_console(self, args) -> None:
    response_data = {
        "response_type": ResponseType.CONSOLE_RESULT,
        "context_code": args.get("context_code"),
        "error": False,
        "data": 1,
    }
    try:
        sql_cmd: str = args.get("sql_cmd")
        workspace_context: dict[str, Any] = args.get("workspace_context")
        autocommit: bool = args.get("autocommit")
        mode: ConsoleModes = args.get("mode")
        client_object: Client = args.get("client_object")
        block_size: int = args.get("block_size", 50)

        session: Session = args.get("session")
        database = args.get("database")

        # Removing last character if it is a semi-colon
        if sql_cmd[-1:] == ";":
            sql_cmd = sql_cmd[:-1]

        log_start_time = datetime.now(timezone.utc)
        show_fetch_button: bool = False

        try:
            list_sql: list[str] = sqlparse.split(sql_cmd)

            data_return: str = ""
            run_command_list: bool = True

            if mode == ConsoleModes.DATA_OPERATION:
                database.connection.autocommit = autocommit
                if (
                    not database.connection.con
                    or database.connection.GetConStatus() == 0
                ):
                    database.connection.Open()
                else:
                    database.connection.start = True

            if mode == ConsoleModes.FETCH_MORE:
                table = database.connection.QueryBlock("", block_size, True, True)
                # need to stop again
                if not database.connection.start or len(table.Rows) >= block_size:
                    data_return += (
                        "\n"
                        + table.Pretty(database.connection.expanded)
                        + "\n"
                        + database.connection.GetStatus()
                    )
                    run_command_list = False
                    show_fetch_button = True
                else:
                    data_return += (
                        "\n"
                        + table.Pretty(database.connection.expanded)
                        + "\n"
                        + database.connection.GetStatus()
                    )
                    run_command_list = True
                    list_sql = workspace_context["remaining_commands"]
            elif mode == ConsoleModes.FETCH_ALL:
                has_more_records = True
                run_command_list = False
                while has_more_records:

                    data = database.connection.QueryBlock("", 10000, True, True)
                    data_return = (
                        "\n" + data.Pretty(database.connection.expanded) + "\n"
                    )
                    data_return = data_return.replace("\n", "\r\n")

                    log_end_time = datetime.now(timezone.utc)
                    duration = get_duration(log_start_time, log_end_time)

                    response_data["data"] = {
                        "data": data_return,
                        "last_block": False,
                        "duration": duration,
                        "show_fetch_button": show_fetch_button,
                        "con_status": "",
                    }

                    if database.connection.start:
                        has_more_records = False
                    elif len(data.Rows) > 0:
                        has_more_records = True
                    else:
                        has_more_records = False

                    if self.cancel:
                        break

                    if has_more_records:
                        queue_response(client_object, response_data)

            if mode == ConsoleModes.SKIP_FETCH:
                run_command_list = True
                list_sql = workspace_context["remaining_commands"]

            if run_command_list:
                counter = 0
                show_fetch_button = False
                for sql in list_sql:
                    counter = counter + 1
                    try:
                        formated_sql = sql.strip()
                        data_return += (
                            "\n"
                            + database.active_service
                            + "=# "
                            + formated_sql
                            + "\n"
                        )

                        database.connection.ClearNotices()
                        database.connection.start = True
                        data1 = database.connection.Special(sql)

                        notices = database.connection.GetNotices()
                        notices_text = ""
                        if len(notices) > 0:
                            for notice in notices:
                                notices_text += notice
                            data_return += notices_text

                        data_return += data1

                        if database.use_server_cursor:
                            if database.connection.last_fetched_size == 50:
                                workspace_context["remaining_commands"] = list_sql[counter:]
                                show_fetch_button = True
                                break
                    except Exception as exc:
                        try:
                            notices = database.connection.GetNotices()
                            notices_text = ""
                            if len(notices) > 0:
                                for notice in notices:
                                    notices_text += notice
                                data_return += notices_text
                        except Exception as exc:
                            None
                        response_data["error"] = True
                        data_return += str(exc)
                    workspace_context["remaining_commands"] = []

            log_end_time = datetime.now(timezone.utc)
            duration = get_duration(log_start_time, log_end_time)

            data_return = data_return.replace("\n", "\r\n")

            response_data["data"] = {
                "data": data_return,
                "last_block": True,
                "duration": duration,
                "con_status": database.connection.GetConStatus(),
            }

            # send data in chunks to avoid blocking the websocket server
            chunks = (
                [data_return[x : x + 10000] for x in range(0, len(data_return), 10000)]
                if not mode == ConsoleModes.FETCH_ALL
                else []
            )
            if len(chunks) > 0:
                for idx, chunk in enumerate(chunks, 1):
                    response_data_copy = copy.deepcopy(response_data)
                    if self.cancel:
                        break
                    if idx != len(chunks):
                        response_data_copy["data"] = {
                            "data": chunk,
                            "last_block": False,
                            "duration": duration,
                            "show_fetch_button": show_fetch_button,
                            "con_status": "",
                        }
                    else:
                        response_data_copy["data"] = {
                            "data": chunk,
                            "last_block": True,
                            "duration": duration,
                            "show_fetch_button": show_fetch_button,
                            "con_status": database.connection.GetConStatus(),
                            "status": database.connection.GetStatus(),
                        }
                    if not self.cancel:
                        queue_response(client_object, response_data_copy)
            else:
                if not self.cancel:
                    queue_response(client_object, response_data)

            try:
                database.connection.ClearNotices()
            except Exception:
                None
        except Exception as exc:
            # try:
            #    v_database.connection.Close()
            # except:
            #    pass
            log_end_time = datetime.now(timezone.utc)
            duration = get_duration(log_start_time, log_end_time)
            response_data["error"] = True
            response_data["data"] = {"data": str(exc), "duration": duration}

            if not self.cancel:
                queue_response(client_object, response_data)

        if mode == ConsoleModes.DATA_OPERATION:
            query_db = ConsoleHistory.objects.filter(
                user=User.objects.get(id=session.user_id),
                connection=Connection.objects.get(id=database.conn_id),
                database=database.active_service,
            ).last()
            if query_db and query_db.snippet == sql_cmd.replace("'", "''"):
                query_db.start_time = datetime.now(timezone.utc)
                query_db.save()
            else:
                # logging to console history
                query_object = ConsoleHistory(
                    user=User.objects.get(id=session.user_id),
                    connection=Connection.objects.get(id=database.conn_id),
                    start_time=datetime.now(timezone.utc),
                    snippet=sql_cmd.replace("'", "''"),
                    database=database.active_service,
                )

                query_object.save()

    except Exception as exc:
        logger.error("""*** Exception ***\n{0}""".format(traceback.format_exc()))
        response_data["error"] = True
        response_data["data"] = {"data": str(exc), "duration": ""}
        if not self.cancel:
            queue_response(client_object, response_data)


def thread_query_edit_data(self, args) -> None:
    response_data = {
        "response_type": ResponseType.QUERY_EDIT_DATA_RESULT,
        "context_code": args["context_code"],
        "error": False,
        "data": {
            "rows": [],
        },
    }

    try:
        database = args["database"]
        table: str = args["table"]
        schema: Optional[str] = args["schema"]
        query_filter: str = args["query_filter"]
        count: str = str(args["count"])
        client_object: Client = args["client_object"]

        try:
            if database.has_schema:
                table_data = database.QueryTableRecords(
                    "*", table, schema, query_filter, count
                )
            else:
                table_data = database.QueryTableRecords("*", table, query_filter, count)

            table_rows = []
            for row in table_data.Rows:
                row_data = []

                for col in table_data.Columns:
                    if row[col] is None:
                        row_data.append(None)
                    else:
                        row_data.append(str(row[col]))
                table_rows.append(row_data)
            response_data["data"]["rows"] = table_rows

        except Exception as exc:
            response_data["data"] = str(exc)
            response_data["error"] = True

        if not self.cancel:
            queue_response(client_object, response_data)
    except Exception as exc:
        logger.error("""*** Exception ***\n{0}""".format(traceback.format_exc()))
        response_data["error"] = True
        response_data["data"] = traceback.format_exc().replace("\n", "<br>")
        if not self.cancel:
            queue_response(client_object, response_data)


def thread_save_edit_data(self, args) -> None:
    response_data = {
        "response_type": ResponseType.SAVE_EDIT_DATA_RESULT,
        "context_code": args["context_code"],
        "error": False,
        "data": [],
    }

    try:
        database = args["database"]
        client_object: Client = args["client_object"]
        command: str = args["sql_cmd"]
        if database.db_type in ["sqlite","mysql"] and len(command.split(";\n")) >= 2:
            try:
                database.connection.Open(False)
                database.connection.Execute("BEGIN")
                for sql in command.split(";\n"):
                    database.connection.Execute(sql)
                database.connection.Commit()
            except Exception as exc:
                database.connection.con.rollback()
                raise DatabaseError(str(exc)) from exc
        elif database.db_type == "oracle" and len(command.split(";\n")) >= 2:
            try:
                database.connection.Open(False)
                database.connection.Execute(f"BEGIN\n{command};\nEND;")
                database.connection.Commit()
            except Exception as exc:
                database.connection.con.rollback()
                raise DatabaseError(str(exc)) from exc
        else:
            database.connection.Execute(command)

        if not self.cancel:
            queue_response(client_object, response_data)
    except Exception as exc:
        logger.error("""*** Exception ***\n{0}""".format(traceback.format_exc()))
        response_data["error"] = True
        response_data["data"] = str(exc)
        if not self.cancel:
            queue_response(client_object, response_data)


def thread_schema_edit_data(self, args) -> None:
    response_data = {
        "response_type": ResponseType.SCHEMA_EDIT_RESULT,
        "context_code": args["context_code"],
        "error": False,
        "data": 1,
    }

    try:
        client_object: Client = args.get("client_object")
        sql_cmd: str = args.get("sql_cmd")
        autocommit: bool = args.get("autocommit")
        database = args.get("database")

        database.connection.autocommit = autocommit

        if not database.connection.con or database.connection.GetConStatus() == 0:
            database.connection.Open()
        else:
            database.connection.start = True

        if database.db_type == "sqlite" and len(sql_cmd.split(";\n")) >= 2:
            try:
                database.connection.Execute("BEGIN")
                for sql in sql_cmd.split(";\n"):
                    database.connection.Execute(sql)
                database.connection.Commit()
            except Exception as exc:
                database.connection.con.rollback()
                raise DatabaseError(str(exc))
        elif database.db_type == "oracle" and len(sql_cmd.split(";\n")) >= 2:
            list_sql: list[str] = sqlparse.split(sql_cmd,  strip_semicolon=True)
            for sql in list_sql:
                database.connection.QueryBlock(sql, 50, True, True)
        else:
            database.connection.QueryBlock(sql_cmd, 50, True, True)

        database.connection.ClearNotices()

        response_data["data"] = {
            "status": database.connection.GetStatus(),
        }

        if not self.cancel:
            queue_response(client_object, response_data)

    except Exception as exc:
        if not self.cancel:
            response_data["data"] = {
                "message": str(exc),
            }

            response_data["error"] = True

            queue_response(client_object, response_data)
