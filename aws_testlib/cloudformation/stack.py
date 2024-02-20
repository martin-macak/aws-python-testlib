import time
from typing import Any, Callable, Optional


class HandleContext:
    def __init__(self,
                 stack: "Stack",
                 handle_id: str,
                 ):
        self._stack = stack
        self._handle_id = handle_id

    def __del__(self):
        self._stack.stop_event_loop()

    def signal(
        self,
        resource_name: str,
        signal_type: str,
        event: Any,
    ):
        self._stack.signal(
            resource_name=resource_name,
            signal_type=signal_type,
            event=event,
        )

    def add_state(
        self,
        name: str,
        value: Any,
    ):
        self._stack.add_state(
            handle_id=self._handle_id,
            name=name,
            value=value,

        )

    def get_state(
        self,
        name: str,
    ) -> Any:
        return self._stack.get_state(
            handle_id=self._handle_id,
            name=name,
        )


class Stack:
    def __init__(self):
        self._handles: dict[str, tuple[str, Callable]] = {}
        self._signal_handlers: dict[str, tuple[str, Callable]] = {}
        self._state = {
            "handles": {

            },
        }
        self._loop_thread = None
        self._is_running = False
        self._signals_emitted = 0

    def process_event_loop(
        self,
        on_background: Optional[bool] = False
    ):
        def do_loop():
            for handle_id, (resource_name, resource_handle) in self._handles.items():
                resource_handle(
                    HandleContext(
                        stack=self,
                        handle_id=handle_id,
                    )
                )

        def do_background_loop():
            while self._is_running:
                do_loop()
                time.sleep(0.1)

        if on_background is False:
            do_loop()
        else:
            import threading
            thread = threading.Thread(target=do_background_loop, daemon=True)
            self._loop_thread = thread
            thread.start()

    def wait_for_empty_loop(self):
        is_done = False
        while not is_done:
            self._signals_emitted = 0
            for handle_id, (resource_name, resource_handle) in self._handles.items():
                resource_handle(
                    HandleContext(
                        stack=self,
                        handle_id=handle_id,
                    )
                )
            is_done = self._signals_emitted == 0

    def stop_event_loop(self):
        if self._loop_thread is not None:
            self._loop_thread.join()
            self._loop_thread = None

    def register_signal_handler(
        self,
        resource_name: str,
        signal_type: str,
        handler: Callable,
    ):
        handler_id = f"{resource_name}:{signal_type}"
        self._signal_handlers[handler_id] = (resource_name, handler)

    def signal(
        self,
        resource_name: str,
        signal_type: str,
        event: Any,
    ):
        handler_id = f"{resource_name}:{signal_type}"
        handler = self._signal_handlers.get(handler_id)
        if handler is not None:
            handler[1](event)
        self._signals_emitted += 1

    def register_to_event_loop(
        self,
        handle_id: str,
        resource_name: str,
        resource_handle: Any,
    ):
        self._handles[handle_id] = (resource_name, resource_handle)

    def add_state(
        self,
        handle_id: str,
        name: str,
        value: Any,
    ):
        if self._state["handles"].get(handle_id) is None:
            self._state["handles"][handle_id] = {}

        self._state["handles"][handle_id][name] = value

    def get_state(
        self,
        handle_id: str,
        name: str,
    ) -> Any:
        if self._state["handles"].get(handle_id) is None:
            return None

        return self._state["handles"][handle_id].get(name)
