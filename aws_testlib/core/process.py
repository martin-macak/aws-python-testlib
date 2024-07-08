import os
import select
import subprocess
import sys
import threading
import time
from typing import Callable

Finalizer = Callable


def run_cmd(
    cmd: list[str],
    exception_on_error: bool = False,
    print_output: bool = True,
    wait: bool = True,
    wait_timeout: int = 3000,
    env: dict[str, str] = None,
    prompt: str = "",
    finalizer: Finalizer = None,
) -> (int, subprocess.Popen):
    """
    Runs a command in a subprocess and returns the exit code and the process object.
    Whenever possible, pass the finalizer function to ensure the process is terminated properly when the
    outer context reaches the end of its life. Finalizer is called with another Callable that's supposed
    to be called once the process is no longer needed. This is useful for terminating the process.

    :param cmd: The command to run. This is standard array of arguments passed to subprocess.Popen.
    :param exception_on_error: If True, raises an exception if the command fails.
    :param print_output: If True, prints the output of the command to stdout.
    :param wait: If True, waits for the command to finish before returning.
    :param wait_timeout: The maximum time to wait for the command to finish.
    :param env: The environment variables to pass to the subprocess.
    :param prompt: The prompt to prepend to each line of output.
    :param finalizer: The finalizer function to call when the process is no longer needed.

    """

    process_env = dict(os.environ, **{k: str(v) for k, v in (env or {}).items()})

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
        env=process_env,
    )

    state = {
        "p_exit_code": None,
    }

    semaphore = threading.Semaphore(0)

    def run_process_guard():
        try:
            while True:
                if print_output:
                    ready_dfs, _, _ = select.select([p.stdout, p.stderr], [], [], 1)
                    for fd in ready_dfs:
                        if fd == p.stdout:
                            line = p.stdout.readline()
                            if line:
                                print(prompt + line, end="")
                        elif fd == p.stderr:
                            line = p.stderr.readline()
                            if line:
                                print(prompt + line, end="")

                exit_code = p.poll()
                state["p_exit_code"] = exit_code
                if exit_code is not None:
                    break

                sys.stdout.flush()
                time.sleep(0.1)

            if print_output:
                remaining_stdout = p.stdout.read()
                remaining_stderr = p.stderr.read()
                if remaining_stdout:
                    print(prompt + remaining_stdout, end="")
                if remaining_stderr:
                    print(prompt + remaining_stderr, end="")
                sys.stdout.flush()
        finally:
            semaphore.release(1)
            p.stdout.close()
            p.stderr.close()

    if finalizer:
        finalizer(p.terminate)

    thread = threading.Thread(target=run_process_guard)
    thread.daemon = True
    thread.start()

    if wait:
        semaphore.acquire(blocking=True, timeout=wait_timeout)

        p_exit_code = int(state.get("p_exit_code", "0"))
        if p_exit_code != 0 and exception_on_error:
            raise Exception(f"Command failed with exit code {p_exit_code}")

        return p_exit_code, None
    else:
        return None, p
