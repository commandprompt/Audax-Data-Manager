"""
This python script is responsible for executing a process, and logs its output,
and error in the given output directory.

We will create a detached process, which executes this script.

This script will:
* Fetch the configuration from the given database.
* Run the given executable specified in the configuration with the arguments.
* Create log files for both stdout, and stdout.
* Update the start time, end time, exit code, etc in the configuration
  database.

Args:
  list of program and arguments passed to it.

It also depends on the following environment variable for proper execution.
JOB_ID - Job-id
OUTDIR - Output directory
"""
import json
import logging
import os
import re
import secrets
import signal
import subprocess
import sys
from datetime import datetime
from threading import Thread
from typing import Any, Dict, List, Optional

_IS_WIN = os.name == "nt"
sys_encoding = None
out_dir = None
log_file = None

# meta-commands with real OS/shell/file impact; never emitted by pg_dump/pg_dumpall
_BLOCKED_META_COMMANDS = {
    b"\\!",
    b"\\o",
    b"\\g",
    b"\\gx",
    b"\\copy",
    b"\\i",
    b"\\ir",
    b"\\include",
    b"\\include_relative",
    b"\\e",
    b"\\edit",
    b"\\ef",
    b"\\ev",
    b"\\w",
    b"\\write",
    b"\\lo_import",
    b"\\lo_export",
}
_COPY_FROM_STDIN_RE = re.compile(rb"(?im)^\s*COPY\s+.+\sFROM\s+STDIN\b")
_DOLLAR_TAG_RE = re.compile(rb"\$([A-Za-z_][A-Za-z0-9_]*)?\$")


def psql_supports_restrict(psql_path):
    #checks if psql executable supports restrict natively"
    try:
        result = subprocess.run(
            [psql_path, "--help=commands"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        return b"\\restrict" in result.stdout
    except Exception:
        return False


def inject_restrict_args(command, dash_f_index, is_pigz_into_psql):
    # restrict with a random key, so nobody can unrestrict
    key = secrets.token_hex(16)
    restrict_args = ["-c", f"\\restrict {key}"]
    if is_pigz_into_psql:
        # "-f -" keeps psql reading from stdin (fed by pigz) after the -c command
        return command[:-1] + restrict_args + ["-f", "-"] + command[-1:]
    return command[:dash_f_index] + restrict_args + command[dash_f_index:]


def update_dollar_quote_state(line, state):
    count = len(_DOLLAR_TAG_RE.findall(line))
    if count % 2 == 1:
        state["in_dollar_quote"] = not state["in_dollar_quote"]


def filter_psql_line(line, state):
    # COPY data and dollar-quoted bodies can legitimately start with `\`
    # (e.g. NULL is literally `\N`), so leave them untouched
    if state["in_dollar_quote"]:
        update_dollar_quote_state(line, state)
        return line

    if state["in_copy"]:
        if line.rstrip(b"\r\n") == b"\\.":
            state["in_copy"] = False
        return line

    stripped = line.lstrip()
    if stripped.startswith(b"\\"):
        token = stripped.split(None, 1)[0].rstrip(b"\r\n").lower()
        if token in _BLOCKED_META_COMMANDS:
            return b"-- " + line.rstrip(b"\r\n") + b"\n"
        return line

    if _COPY_FROM_STDIN_RE.search(line):
        state["in_copy"] = True
        return line

    update_dollar_quote_state(line, state)
    return line


def unescape_dquotes_process_arg(arg):
    # Double quotes has special meaning for shell command line and they are
    # run without the double quotes.
    #
    # Remove the saviour #DQ#

    dq_id = "#DQ#"

    if arg.startswith(dq_id) and arg.endswith(dq_id):
        return "{0}".format(arg[len(dq_id) : -len(dq_id)])
    else:
        return arg


class ProcessLogger(Thread):
    def __init__(self, stream_type):
        Thread.__init__(self)
        self.processes = []
        self.streams = []
        self.logger = open(os.path.join(out_dir, stream_type), "wb", buffering=0)

    def attach_process_stream(self, process, stream):
        self.processes.append(process)
        self.streams.append(stream)

    def log(self, msg):
        """
        This function will update log file

        Args:
            msg: message

        Returns:
            None
        """
        if self.logger:
            if msg:
                self.logger.write(
                    datetime.now().strftime("%Y%m%d%H%M%S%f").encode("utf-8")
                )
                self.logger.write(b",")
                self.logger.write(msg.lstrip(b"\r\n" if _IS_WIN else b"\n"))

            return True
        return False

    def run(self):
        for process, stream in zip(self.processes, self.streams):
            if process and stream:
                while True:
                    nextline = stream.readline()

                    if nextline:
                        self.log(nextline)
                    else:
                        if process.poll() is not None:
                            break

    def release(self):
        if self.logger:
            self.logger.close()
            self.logger = None


class ProcessExecutor:
    """Class for executing and managing processes."""

    def __init__(self) -> None:
        self.process_stdout = None
        self.process_stderr = None
        self.status_args = {}

    def execute(self, argv: List[str]) -> None:
        """
        Execute the command specified in argv.

        Args:
            argv: List of command line arguments.

        Returns:
            None
        """
        command = argv[1:]

        self.status_args = {
            "start_time": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "pid": os.getpid(),
        }

        logging.info("Initialize the process execution: %s", command)

        self._create_loggers()

        try:
            self._update_process_status()
            logging.info("Status updated.")

            kwargs = {
                "close_fds": False,
                "shell": True if _IS_WIN else False,
                "env": os.environ.copy(),
            }

            logging.info("Starting the command execution...")

            is_psql = "psql" in os.path.basename(command[0]).lower()
            dash_f_index = None
            if is_psql:
                for i, arg in enumerate(command):
                    if arg == "-f" and i + 1 < len(command):
                        dash_f_index = i
                        break
            pigz_tail = len(command[-1].split()) >= 3
            is_pigz_into_psql = is_psql and pigz_tail and "-dc" in command[-1].split()
            # this block handles filtering of psql slash commands
            # if psql supports \restrict - use it
            # otherwise process executor will strip dangerous slash commands
            # and pipe the sanitized plain dump into psql
            if is_psql and (dash_f_index is not None or is_pigz_into_psql):
                if psql_supports_restrict(command[0]):
                    command = inject_restrict_args(
                        command, dash_f_index, is_pigz_into_psql
                    )
                    if is_pigz_into_psql:
                        self._execute_with_pigz(command, kwargs)
                    else:
                        self._execute_without_pigz(command, kwargs)
                elif is_pigz_into_psql:
                    self._execute_psql_filtered_from_pigz(command, kwargs)
                else:
                    self._execute_psql_filtered_from_file(command, dash_f_index, kwargs)
            elif pigz_tail:
                self._execute_with_pigz(command, kwargs)
            else:
                self._execute_without_pigz(command, kwargs)
        except OSError as exc:
            self._handle_execute_exception(exc, exit_code=None)
        except Exception as exc:
            self._handle_execute_exception(exc, exit_code=-1)
        finally:
            self._update_process_status()
            logging.info("Exiting the process executor...")
            self._cleanup_loggers()
            logging.info("Job is finished.")

    def _create_loggers(self) -> None:
        """Create loggers for process stdout and stderr."""
        self.process_stdout = ProcessLogger("out")
        self.process_stderr = ProcessLogger("err")

    def _cleanup_loggers(self) -> None:
        if self.process_stdout:
            self.process_stdout.release()
        if self.process_stderr:
            self.process_stderr.release()

    def _update_process_status(self) -> None:
        if out_dir:
            status = dict(
                (k, v)
                for k, v in self.status_args.items()
                if k in ("start_time", "end_time", "exit_code", "pid")
            )
            json_status = json.dumps(status)
            logging.info("Updating the status:\n %s", json_status)
            with open(os.path.join(out_dir, "status"), "w") as fp:
                json.dump(status, fp)
        else:
            raise ValueError("Please verify pid and db_file arguments.")

    def _update_process_info(self, process: subprocess.Popen) -> None:
        self.status_args.update(
            {
                "start_time": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "pid": process.pid,
            }
        )
        self._update_process_status()

    def _execute_without_pigz(self, command: List[str], kwargs: Dict[str, Any]) -> None:
        """Execute the command without pigz compression."""
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )

        self._update_process_info(process)

        logging.info("Status updated after starting child process...")

        logging.info("Attaching the loggers to stdout, and stderr...")
        self.process_stdout.attach_process_stream(process, process.stdout)
        self.process_stdout.start()
        self.process_stderr.attach_process_stream(process, process.stderr)
        self.process_stderr.start()

        self.process_stdout.join()
        self.process_stderr.join()

        logging.info("Waiting for the process to finish...")
        exit_code = process.wait()

        if exit_code is None:
            exit_code = process.poll()

        logging.info("Process exited with code: %s", exit_code)

        self.status_args.update({"exit_code": exit_code})

        self.status_args.update({"end_time": datetime.now().strftime("%Y%m%d%H%M%S%f")})

        self._fetch_execute_output(process)

    def _execute_psql_filtered_from_file(
        self, command: List[str], dash_f_index: int, kwargs: Dict[str, Any]
    ) -> None:
        # no native \\restrict support: stream the file through the filter into stdin instead of -f ...
        file_path = command[dash_f_index + 1]
        psql_command = command[:dash_f_index] + command[dash_f_index + 2 :]

        process = subprocess.Popen(
            psql_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kwargs,
        )

        def source():
            with open(file_path, "rb") as f:
                yield from f

        self._run_filtered_restore(process, source())

    def _execute_psql_filtered_from_pigz(
        self, command: List[str], kwargs: Dict[str, Any]
    ) -> None:
        # Same as _execute_psql_filtered_from_file, but sourced from pigz's decompressed output
        pigz_command = command[-1].split()
        psql_command = command[:-1]

        pigz_process = subprocess.Popen(
            pigz_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )
        process = subprocess.Popen(
            psql_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kwargs,
        )

        def source():
            try:
                yield from pigz_process.stdout
            finally:
                pigz_process.stdout.close()
                pigz_process.wait()

        self._run_filtered_restore(process, source())

    def _run_filtered_restore(self, process: subprocess.Popen, line_source) -> None:
        writer = Thread(target=self._write_filtered_stdin, args=(process, line_source))
        writer.start()

        self._update_process_info(process)

        self.process_stdout.attach_process_stream(process, process.stdout)
        self.process_stdout.start()
        self.process_stderr.attach_process_stream(process, process.stderr)
        self.process_stderr.start()

        self.process_stdout.join()
        self.process_stderr.join()
        writer.join()

        # already closed by the writer thread; communicate() would raise trying to flush it otherwise
        process.stdin = None

        exit_code = process.wait()

        if exit_code is None:
            exit_code = process.poll()

        self.status_args.update(
            {
                "exit_code": exit_code,
                "end_time": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            }
        )

        self._fetch_execute_output(process)

    @staticmethod
    def _write_filtered_stdin(process: subprocess.Popen, line_source) -> None:
        state = {"in_copy": False, "in_dollar_quote": False}
        buffer = bytearray()
        flush_threshold = 256 * 1024
        try:
            for raw_line in line_source:
                buffer += filter_psql_line(raw_line, state)
                if len(buffer) >= flush_threshold:
                    process.stdin.write(buffer)
                    buffer.clear()
            if buffer:
                process.stdin.write(buffer)
        except Exception:
            pass
        finally:
            try:
                process.stdin.close()
            except Exception:
                pass

    def _execute_with_pigz(self, command: List[str], kwargs: Dict[str, Any]):
        """Execute the command with pigz compression."""

        pigz_command = command[-1].split()
        utility_command = command[:-1]

        if "-dc" in pigz_command:
            self._execute_decompress_restore(utility_command, pigz_command, kwargs)
        else:
            self._execute_dump_compress(utility_command, pigz_command, kwargs)

    def _execute_dump_compress(
        self,
        utility_command: List[str],
        pigz_command: List[str],
        kwargs: Dict[str, Any],
    ) -> None:
        """Execute dump and compress process."""
        process = subprocess.Popen(
            utility_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )

        pigz_command = [arg for arg in pigz_command if arg not in ["|", ">"]]

        with open(pigz_command[-1], "wb") as output_file:
            second_process = subprocess.Popen(
                pigz_command[:-1],
                stdin=process.stdout,
                stdout=output_file,
                stderr=subprocess.PIPE,
                **kwargs
            )

        process.stdout.close()  # Allow process to receive a SIGPIPE if second_process exits.

        self._update_process_info(process=second_process)

        logging.info("Status updated after starting dump/compress child process...")

        self.process_stderr.attach_process_stream(process, process.stderr)
        self.process_stderr.attach_process_stream(second_process, second_process.stderr)
        self.process_stderr.start()

        self.process_stderr.join()

        logging.info("Waiting for the dump/compress process to finish...")

        exit_code = second_process.wait()

        if exit_code is None:
            exit_code = second_process.poll()

        logging.info("Process exited with code: %s", exit_code)

        self.status_args.update(
            {
                "exit_code": exit_code,
                "end_time": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            }
        )

        self._fetch_execute_output(second_process)

    def _execute_decompress_restore(
        self,
        utility_command: List[str],
        pigz_command: List[str],
        kwargs: Dict[str, Any],
    ) -> None:
        """Execute decompress and restore process."""
        process = subprocess.Popen(
            pigz_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )

        second_process = subprocess.Popen(
            utility_command,
            stdin=process.stdout,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            **kwargs
        )

        process.stdout.close()  # Allow process to receive a SIGPIPE if second_process exits.

        self._update_process_info(second_process)

        logging.info(
            "Status updated after starting decompress/restore child process..."
        )

        self.process_stderr.attach_process_stream(second_process, second_process.stderr)
        self.process_stderr.start()

        self.process_stderr.join()

        exit_code = second_process.wait()

        if exit_code is None:
            exit_code = second_process.poll()

        logging.info("Process exited with code: %s", exit_code)

        self.status_args.update(
            {
                "exit_code": exit_code,
                "end_time": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            }
        )

        self._fetch_execute_output(second_process)

    def _handle_execute_exception(
        self, exc: Exception, exit_code: Optional[int] = None
    ):
        logging.exception("Exception occurred")

        if self.process_stderr:
            self.process_stderr.log(str(exc).encode())

        self.status_args.update(
            {
                "end_time": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "exit_code": exc.errno if exit_code is None else exit_code,
            }
        )

    def _fetch_execute_output(self, process: subprocess.Popen) -> None:
        data = process.communicate()

        if data:
            if data[0]:
                self.process_stdout.log(data[0])
            if data[1]:
                self.process_stderr.log(data[1])


def signal_handler(signal, msg):
    # Let's ignore all the signal comming to us.
    pass


if __name__ == "__main__":
    argv = [unescape_dquotes_process_arg(arg) for arg in sys.argv]

    sys_encoding = sys.getdefaultencoding()
    if not sys_encoding or sys_encoding == "ascii":
        sys_encoding = "utf-8"

    out_dir = os.environ["OUTDIR"]
    log_file = os.path.join(out_dir, ("log_%s" % os.getpid()))

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s  %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
    )

    logging.info("Starting the process executor...")

    executor = ProcessExecutor()

    # Ignore any signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logging.info("Disabled the SIGINT, SIGTERM signals...")

    if _IS_WIN:
        logging.info("Disable the SIGBREAKM signal (windows)...")
        signal.signal(signal.SIGBREAK, signal_handler)

        logging.info("Disabled the SIGBREAKM signal (windows)...")

        logging.info("[CHILD] Start process execution...")
        # This is a child process running as the daemon process.
        # Let's do the job assigning to it.
        try:
            logging.info("Executing the command now from the detached child...")
            executor.execute(argv)
        except Exception:
            logging.exception("Exception occurred")
    else:
        r, w = os.pipe()

        if os.fork() == 0:
            logging.info("[CHILD] Forked the child process...")
            try:
                os.close(r)

                logging.info("[CHILD] Make the child process leader...")
                os.setsid()
                os.umask(0)

                logging.info("[CHILD] Make the child process leader...")
                w = os.fdopen(w, "w")

                logging.info("[CHILD] Inform parent about successful child forking...")
                w.write("1")
                w.close()
                logging.info("[CHILD] Start executing the background process...")
                executor.execute(argv)
            except Exception as error:
                logging.exception("Exception occurred")
                sys.exit(1)
        else:
            os.close(w)
            r = os.fdopen(r)

            r.read()
            logging.info("[PARENT] Got message from the child...")
            r.close()

            logging.info("[PARENT] Exiting...")
            sys.exit(0)
