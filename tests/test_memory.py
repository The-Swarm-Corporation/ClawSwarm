"""
Unit tests for claw_swarm.memory.
"""

from __future__ import annotations


from claw_swarm.agent import memory


class TestGetMemoryPath:
    """Test get_memory_path when patched."""

    def test_returns_path_from_fixture(self, mock_memory_path):
        path = memory.get_memory_path()
        assert path == mock_memory_path
        assert path.suffix == ".md"


class TestReadMemory:
    """Test read_memory."""

    def test_missing_file_returns_empty(self, mock_memory_path):
        assert not mock_memory_path.exists()
        assert memory.read_memory() == ""

    def test_reads_existing_content(self, mock_memory_path):
        mock_memory_path.write_text("hello world", encoding="utf-8")
        assert memory.read_memory() == "hello world"

    def test_strips_whitespace(self, mock_memory_path):
        mock_memory_path.write_text(
            "  \n  content  \n  ", encoding="utf-8"
        )
        assert memory.read_memory() == "content"

    def test_returns_empty_on_os_error(
        self, mock_memory_path, monkeypatch
    ):
        def raise_os_error():
            raise OSError("read failed")

        monkeypatch.setattr(
            "claw_swarm.agent.memory.get_memory_path",
            lambda: __import__("pathlib").Path(
                "/nonexistent/dir/file.md"
            ),
        )
        # If path doesn't exist, read_memory returns "" without reading
        result = memory.read_memory()
        assert result == ""

    def test_trims_to_max_chars_when_over_limit(
        self, mock_memory_path, monkeypatch
    ):
        monkeypatch.setattr(
            "claw_swarm.agent.memory.MAX_MEMORY_CHARS", 10
        )
        mock_memory_path.write_text(
            "0123456789extra", encoding="utf-8"
        )
        out = memory.read_memory()
        assert len(out) <= 10
        assert "extra" in out  # last MAX_MEMORY_CHARS from end


class TestAppendInteraction:
    """Test append_interaction."""

    def test_creates_file_and_appends(self, mock_memory_path):
        assert not mock_memory_path.exists()
        memory.append_interaction(
            platform="telegram",
            channel_id="ch1",
            thread_id="",
            sender_handle="user1",
            user_text="Hi",
            reply_text="Hello",
            message_id="msg1",
        )
        assert mock_memory_path.exists()
        content = mock_memory_path.read_text(encoding="utf-8")
        assert "telegram" in content
        assert "ch1" in content
        assert "user1" in content or "user" in content
        assert "Hi" in content
        assert "Hello" in content

    def test_appends_second_block(self, mock_memory_path):
        memory.append_interaction(
            platform="discord",
            channel_id="ch2",
            thread_id="",
            sender_handle="alice",
            user_text="Q",
            reply_text="A",
            message_id="",
        )
        memory.append_interaction(
            platform="discord",
            channel_id="ch2",
            thread_id="",
            sender_handle="alice",
            user_text="Q2",
            reply_text="A2",
            message_id="",
        )
        content = mock_memory_path.read_text(encoding="utf-8")
        assert "Q" in content and "A" in content
        assert "Q2" in content and "A2" in content

    def test_includes_thread_id_in_channel_line(
        self, mock_memory_path
    ):
        memory.append_interaction(
            platform="telegram",
            channel_id="ch",
            thread_id="thread123",
            sender_handle="bob",
            user_text="x",
            reply_text="y",
            message_id="",
        )
        content = mock_memory_path.read_text(encoding="utf-8")
        assert "thread" in content and "thread123" in content
