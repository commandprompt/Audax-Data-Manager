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
            if len(command[-1].split()) >= 3:
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
