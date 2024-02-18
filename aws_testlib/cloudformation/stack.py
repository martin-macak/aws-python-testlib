from typing import Any, Callable


class HandleContext:
    def __init__(self,
                 stack: "Stack",
                 handle_id: str,
                 ):
        self._stack = stack
        self._handle_id = handle_id

    def signal(
        self,
        resource_name: str,
        signal_type: str,
        event: Any,
    ):
        pass

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
        self._state = {
            "handles": {

            },
        }

    def process_event_loop(self):
        for handle_id, (resource_name, resource_handle) in self._handles.items():
            resource_handle(
                HandleContext(
                    stack=self,
                    handle_id=handle_id,
                )
            )

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
