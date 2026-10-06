"""
Session state for the chat tutor.

The SDK's `Entity` base class was removed in 0.4. Session-scoped state
(`ctx.session.state`) replaces it: values persist across workflow runs that
share a session_id, which is what the tutor needs for its conversation.
"""

import time


class TutorConversation:
    """A chat tutor conversation kept in the session's state."""

    def __init__(self, ctx):
        self._state = ctx.session.state

    async def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        messages = await self._state.get("messages", [])
        messages.append({"role": role, "content": content, "timestamp": time.time()})
        await self._state.set("messages", messages)
        await self._state.set("message_count", await self.get_message_count() + 1)

    async def get_messages(self) -> list:
        """Get conversation message history."""
        return await self._state.get("messages", [])

    async def get_topic(self) -> str:
        """Get conversation topic."""
        return await self._state.get("topic", "general")

    async def set_topic(self, topic: str) -> None:
        """Set conversation topic."""
        await self._state.set("topic", topic)

    async def get_message_count(self) -> int:
        """Get total message count."""
        return await self._state.get("message_count", 0)


__all__ = ["TutorConversation"]
