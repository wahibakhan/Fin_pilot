"""A minimal test double standing in for a real chat model. It implements
just enough of BaseChatModel's interface (`bind_tools`, `ainvoke`) for the
graph's `interpret` node, always returning a pre-programmed tool call —
deterministic by construction, since the whole point of these tests is to
verify the graph's dispatch/execution logic, not an LLM's extraction
accuracy (that needs a live provider and is out of scope for this suite)."""

from langchain_core.messages import AIMessage


class FakeToolCallingModel:
    def __init__(self, tool_call: dict) -> None:
        self._tool_call = tool_call

    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        return AIMessage(content="", tool_calls=[self._tool_call])


class FakeNoToolCallModel:
    """Simulates the model replying in plain text instead of picking a tool —
    the interpret node's other clarification path."""

    def __init__(self, content: str) -> None:
        self._content = content

    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        return AIMessage(content=self._content, tool_calls=[])
