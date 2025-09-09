"""
Unit tests for TUI screen components.

Tests HelpScreen, DebugScreen, TemplateInspectorScreen, and TuiLogHandler
functionality including screen composition, navigation, and log handling.
"""

import logging
import pytest
from collections import deque
from unittest.mock import Mock, patch


from haproxy_template_ic.tui.screens import (
    HelpScreen,
    DebugScreen,
    TemplateInspectorScreen,
    TuiLogHandler,
    get_tui_log_handler,
)
from haproxy_template_ic.tui.models import TemplateInfo

from datetime import datetime, timezone


class TestTuiLogHandler:
    """Test the TuiLogHandler class."""

    @pytest.fixture
    def log_handler(self):
        """Create a TuiLogHandler instance."""
        return TuiLogHandler()

    @pytest.fixture
    def log_record(self):
        """Create a sample log record."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        return record

    @pytest.fixture
    def error_record(self):
        """Create a sample error log record."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/path/to/file.py",
            lineno=456,
            msg="Test error",
            args=(),
            exc_info=None,
        )
        return record

    def test_log_handler_initialization(self, log_handler):
        """Test TuiLogHandler initialization."""
        assert isinstance(log_handler.logs, deque)
        assert isinstance(log_handler.log_records, deque)
        assert log_handler.debug_screen is None
        assert log_handler.min_log_level == logging.INFO
        assert log_handler.formatter is not None

    def test_emit_info_record(self, log_handler, log_record):
        """Test emitting INFO level log record."""
        log_handler.emit(log_record)

        assert len(log_handler.logs) == 1
        assert len(log_handler.log_records) == 1
        assert "Test message" in log_handler.logs[0]
        assert log_handler.log_records[0] == log_record

    def test_emit_error_record_without_exc_info(self, log_handler, error_record):
        """Test emitting ERROR level log record without exception info."""
        log_handler.emit(error_record)

        assert len(log_handler.logs) == 1
        assert "Test error" in log_handler.logs[0]

    def test_emit_error_record_with_exc_info(self, log_handler):
        """Test emitting ERROR level log record with exception info."""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/path/to/file.py",
                lineno=789,
                msg="Test error with exception",
                args=(),
                exc_info=(type(e), e, e.__traceback__),
            )

            with patch.object(
                log_handler,
                "_format_filtered_traceback",
                return_value="Filtered traceback",
            ):
                log_handler.emit(record)

                assert len(log_handler.logs) == 1
                assert "Test error with exception" in log_handler.logs[0]
                assert "Filtered traceback" in log_handler.logs[0]

    def test_emit_writes_to_debug_screen(self, log_handler, log_record):
        """Test that emit writes to debug screen when active."""
        mock_debug_screen = Mock()
        log_handler.set_debug_screen(mock_debug_screen)

        log_handler.emit(log_record)

        mock_debug_screen.add_log_line.assert_called_once()

    def test_emit_respects_min_log_level(self, log_handler):
        """Test that emit respects minimum log level filter."""
        mock_debug_screen = Mock()
        log_handler.set_debug_screen(mock_debug_screen)
        log_handler.set_min_log_level(logging.WARNING)

        # INFO level should not be written to debug screen
        info_record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Info message",
            args=(),
            exc_info=None,
        )
        log_handler.emit(info_record)

        # Should be stored but not written to debug screen
        assert len(log_handler.logs) == 1
        mock_debug_screen.add_log_line.assert_not_called()

    def test_emit_exception_handling(self, log_handler, log_record):
        """Test that emit handles exceptions gracefully."""
        with patch.object(log_handler, "format", side_effect=Exception("Format error")):
            # Should not raise exception
            log_handler.emit(log_record)

            # Log should not be added due to exception
            assert len(log_handler.logs) == 0

    def test_set_debug_screen(self, log_handler):
        """Test setting debug screen."""
        mock_debug_screen = Mock()
        log_handler.set_debug_screen(mock_debug_screen)

        assert log_handler.debug_screen == mock_debug_screen

    def test_get_recent_logs(self, log_handler):
        """Test getting recent logs."""
        # Add multiple logs
        for i in range(5):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i}",
                args=(),
                exc_info=None,
            )
            log_handler.emit(record)

        recent = log_handler.get_recent_logs(3)
        assert len(recent) == 3
        assert "Message 2" in recent[0]
        assert "Message 4" in recent[-1]

    def test_get_filtered_logs(self, log_handler):
        """Test getting filtered logs by level."""
        # Add logs of different levels
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
        for i, level in enumerate(levels):
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="",
                lineno=0,
                msg=f"Message {i} level {level}",
                args=(),
                exc_info=None,
            )
            log_handler.emit(record)

        # Filter for WARNING and above
        filtered = log_handler.get_filtered_logs(count=10, min_level=logging.WARNING)
        assert len(filtered) == 2
        assert "WARNING" in filtered[0] or "ERROR" in filtered[0]
        assert "WARNING" in filtered[1] or "ERROR" in filtered[1]

    def test_set_min_log_level(self, log_handler):
        """Test setting minimum log level."""
        log_handler.set_min_log_level(logging.ERROR)
        assert log_handler.min_log_level == logging.ERROR

    def test_set_min_log_level_refreshes_debug_screen(self, log_handler):
        """Test that setting min log level refreshes debug screen."""
        mock_debug_screen = Mock()
        log_handler.set_debug_screen(mock_debug_screen)

        log_handler.set_min_log_level(logging.ERROR)

        mock_debug_screen.refresh_log_display.assert_called_once()

    def test_should_add_stack_trace(self, log_handler):
        """Test stack trace decision logic."""
        # Should add stack trace for regular errors
        regular_record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Unexpected error",
            args=(),
            exc_info=None,
        )
        assert log_handler._should_add_stack_trace(regular_record) is True

        # Should not add stack trace for expected errors
        expected_record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Connection refused",
            args=(),
            exc_info=None,
        )
        assert log_handler._should_add_stack_trace(expected_record) is False

    def test_get_filtered_stack_trace(self, log_handler):
        """Test filtered stack trace generation."""
        with patch("traceback.format_stack") as mock_format_stack:
            mock_format_stack.return_value = [
                '  File "/some/external/path.py", line 10, in external_func\n    external_code()\n',
                '  File "/path/haproxy_template_ic/module.py", line 20, in our_func\n    our_code()\n',
            ]

            result = log_handler._get_filtered_stack_trace()

            # Method should handle this gracefully and return a string
            assert isinstance(result, str)

    def test_format_filtered_traceback(self, log_handler):
        """Test filtered traceback formatting."""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Error with traceback",
                args=(),
                exc_info=(type(e), e, e.__traceback__),
            )

            result = log_handler._format_filtered_traceback(record)
            assert isinstance(result, str)
            assert len(result) > 0


class TestHelpScreen:
    """Test the HelpScreen class."""

    @pytest.fixture
    def help_screen(self):
        """Create a HelpScreen instance."""
        return HelpScreen()

    def test_help_screen_initialization(self, help_screen):
        """Test HelpScreen initialization."""
        assert isinstance(help_screen, HelpScreen)

    def test_help_screen_compose(self, help_screen):
        """Test HelpScreen composition."""
        with patch("textual.containers.Container") as mock_container:
            with patch("textual.widgets.Markdown") as mock_markdown:
                mock_container.return_value = Mock()
                mock_markdown.return_value = Mock()

                # This would normally return a ComposeResult
                compose_result = help_screen.compose()

                # Verify that compose method exists and can be called
                assert compose_result is not None


class TestDebugScreen:
    """Test the DebugScreen class."""

    @pytest.fixture
    def debug_screen(self):
        """Create a DebugScreen instance."""
        return DebugScreen()

    @pytest.fixture
    def mock_log_handler(self):
        """Create a mock TuiLogHandler."""
        handler = Mock(spec=TuiLogHandler)
        handler.get_filtered_logs.return_value = ["Log line 1", "Log line 2"]
        handler.min_log_level = logging.INFO
        return handler

    def test_debug_screen_initialization(self, debug_screen):
        """Test DebugScreen initialization."""
        assert isinstance(debug_screen, DebugScreen)
        assert debug_screen.log_widget is None
        assert debug_screen.log_level_select is None

    def test_debug_screen_compose(self, debug_screen):
        """Test DebugScreen composition."""
        with (
            patch("textual.containers.Container") as mock_container,
            patch("textual.widgets.Log") as mock_log,
            patch("textual.widgets.Select") as mock_select,
        ):
            mock_container.return_value = Mock()
            mock_log.return_value = Mock()
            mock_select.return_value = Mock()

            compose_result = debug_screen.compose()
            assert compose_result is not None

    def test_on_mount_sets_up_log_handler(self, debug_screen):
        """Test that on_mount sets up the log handler."""
        # Mock the widgets that on_mount tries to query
        mock_log_widget = Mock()
        mock_select_widget = Mock()

        with patch.object(
            debug_screen, "query_one", side_effect=[mock_log_widget, mock_select_widget]
        ):
            with patch(
                "haproxy_template_ic.tui.screens.get_tui_log_handler"
            ) as mock_get_handler:
                mock_handler = Mock(spec=TuiLogHandler)
                mock_get_handler.return_value = mock_handler

                with patch.object(debug_screen, "refresh_log_display") as mock_refresh:
                    debug_screen.on_mount()

                    # Verify widgets were assigned
                    assert debug_screen.log_widget == mock_log_widget
                    assert debug_screen.log_level_select == mock_select_widget

                    # Verify handler setup
                    mock_handler.set_debug_screen.assert_called_once_with(debug_screen)
                    mock_handler.set_min_log_level.assert_called_once()
                    mock_refresh.assert_called_once()

    def test_on_screen_suspend_cleans_up_handler(self, debug_screen):
        """Test that on_screen_suspend cleans up the log handler."""
        with patch(
            "haproxy_template_ic.tui.screens.get_tui_log_handler"
        ) as mock_get_handler:
            mock_handler = Mock(spec=TuiLogHandler)
            mock_handler.min_log_level = logging.INFO
            mock_get_handler.return_value = mock_handler

            # Set up initial state
            debug_screen.current_log_level = logging.INFO

            debug_screen.on_screen_suspend()

            mock_handler.set_debug_screen.assert_called_once_with(None)

    def test_add_log_line(self, debug_screen):
        """Test adding log line to debug screen."""
        mock_log_widget = Mock()
        debug_screen.log_widget = mock_log_widget

        debug_screen.add_log_line("Test log message")

        mock_log_widget.write_line.assert_called_once_with("Test log message")

    def test_add_log_line_without_widget(self, debug_screen):
        """Test adding log line when widget is not available."""
        debug_screen.log_widget = None

        # Should not raise exception
        debug_screen.add_log_line("Test log message")

    def test_refresh_log_display(self, debug_screen, mock_log_handler):
        """Test refreshing log display."""
        mock_log_widget = Mock()
        debug_screen.log_widget = mock_log_widget

        with patch(
            "haproxy_template_ic.tui.screens.get_tui_log_handler",
            return_value=mock_log_handler,
        ):
            debug_screen.refresh_log_display()

            mock_log_widget.clear.assert_called_once()
            # Should write header, separator, and log lines
            assert mock_log_widget.write_line.call_count >= 2

    def test_on_log_level_changed(self, debug_screen, mock_log_handler):
        """Test log level selection change."""
        # Create a mock Select.Changed event
        mock_event = Mock()
        mock_event.value = logging.ERROR

        with patch(
            "haproxy_template_ic.tui.screens.get_tui_log_handler",
            return_value=mock_log_handler,
        ):
            debug_screen.on_log_level_changed(mock_event)

            mock_log_handler.set_min_log_level.assert_called_once_with(logging.ERROR)
            # Verify current log level was updated
            assert debug_screen.current_log_level == logging.ERROR

    def test_screen_resume_restores_state(self, debug_screen, mock_log_handler):
        """Test that on_screen_resume restores handler state."""
        # Mock the widgets
        mock_log_widget = Mock()
        mock_select_widget = Mock()

        debug_screen.log_widget = mock_log_widget
        debug_screen.log_level_select = mock_select_widget
        debug_screen.current_log_level = logging.ERROR

        with patch(
            "haproxy_template_ic.tui.screens.get_tui_log_handler",
            return_value=mock_log_handler,
        ):
            with patch.object(debug_screen, "refresh_log_display") as mock_refresh:
                debug_screen.on_screen_resume(None)

                # Verify handler is re-registered
                mock_log_handler.set_debug_screen.assert_called_once_with(debug_screen)
                # Verify log level is restored
                mock_log_handler.set_min_log_level.assert_called_once_with(
                    logging.ERROR
                )
                # Verify refresh was called
                mock_refresh.assert_called_once()


class TestTemplateInspectorScreen:
    """Test the TemplateInspectorScreen class."""

    @pytest.fixture
    def template_info(self):
        """Create sample template info."""
        return TemplateInfo(
            name="test.cfg",
            type="haproxy_config",
            status="rendered",
            size=1024,
            last_modified=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def inspector_screen(self, template_info):
        """Create a TemplateInspectorScreen instance."""
        templates_data = {"test.cfg": template_info}
        return TemplateInspectorScreen(
            data_provider=Mock(),
            templates_data=templates_data,
            selected_template="test.cfg",
        )

    def test_template_inspector_initialization(self, inspector_screen, template_info):
        """Test TemplateInspectorScreen initialization."""
        assert inspector_screen.templates_data == {"test.cfg": template_info}
        assert inspector_screen.selected_template == "test.cfg"
        assert inspector_screen.data_provider is not None

    def test_template_inspector_compose(self, inspector_screen):
        """Test TemplateInspectorScreen composition."""
        with patch(
            "haproxy_template_ic.tui.widgets.inspector.TemplateInspectorWidget"
        ) as mock_widget:
            mock_widget.return_value = Mock()

            compose_result = inspector_screen.compose()
            assert compose_result is not None

    def test_on_mount_initializes_widget(self, inspector_screen):
        """Test that on_mount initializes the inspector widget."""
        mock_widget = Mock()

        with patch.object(inspector_screen, "query_one", return_value=mock_widget):
            # Set up some test data
            test_template = Mock()
            inspector_screen.templates_data = {"test.cfg": test_template}
            inspector_screen.selected_template = "test.cfg"

            with patch.object(
                inspector_screen, "call_after_refresh"
            ) as mock_call_after:
                inspector_screen.on_mount()

                # Verify widget properties were set
                assert mock_widget.templates_data == {"test.cfg": test_template}
                assert mock_widget.selected_template == "test.cfg"

                # Verify async content loading was scheduled
                mock_call_after.assert_called_once()

    def test_on_template_content_changed(self, inspector_screen):
        """Test template content change handling."""
        # This tests the message handler structure
        from haproxy_template_ic.tui.widgets.inspector import TemplateContentChanged

        message = Mock(spec=TemplateContentChanged)
        message.content = "new template content"

        # Should not raise exception (message is handled)
        inspector_screen.on_template_content_changed(message)


class TestGetTuiLogHandler:
    """Test the get_tui_log_handler function."""

    def test_get_tui_log_handler_creates_handler(self):
        """Test that get_tui_log_handler creates and returns a handler."""
        with patch(
            "haproxy_template_ic.tui.screens.logging.getLogger"
        ) as mock_get_logger:
            mock_logger = Mock()
            mock_logger.handlers = []
            mock_get_logger.return_value = mock_logger

            handler = get_tui_log_handler()

            assert isinstance(handler, TuiLogHandler)

    def test_get_tui_log_handler_reuses_existing(self):
        """Test that get_tui_log_handler reuses existing handler."""
        # Mock the global variable to have an existing handler
        existing_handler = TuiLogHandler()

        with patch(
            "haproxy_template_ic.tui.screens._tui_log_handler", existing_handler
        ):
            handler = get_tui_log_handler()

            # Should return the existing handler
            assert handler == existing_handler

    def test_get_tui_log_handler_adds_to_logger(self):
        """Test that get_tui_log_handler adds handler to logger."""
        # Reset global state to None
        with patch("haproxy_template_ic.tui.screens._tui_log_handler", None):
            with patch(
                "haproxy_template_ic.tui.screens.logging.getLogger"
            ) as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                handler = get_tui_log_handler()

                # Should add the new handler to the root logger
                mock_logger.addHandler.assert_called_once()
                mock_logger.setLevel.assert_called_once_with(logging.DEBUG)
                assert isinstance(handler, TuiLogHandler)


class TestScreenIntegration:
    """Test integration between screens and related components."""

    def test_debug_screen_log_handler_integration(self):
        """Test integration between DebugScreen and TuiLogHandler."""
        debug_screen = DebugScreen()
        log_handler = TuiLogHandler()

        # Mock the log widget
        mock_log_widget = Mock()
        debug_screen.log_widget = mock_log_widget

        # Set up the relationship
        log_handler.set_debug_screen(debug_screen)

        # Emit a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Integration test",
            args=(),
            exc_info=None,
        )

        log_handler.emit(record)

        # Verify the log was written to the debug screen
        mock_log_widget.write_line.assert_called_once()

    def test_template_inspector_with_different_templates(self):
        """Test TemplateInspectorScreen with different template types."""
        templates = [
            TemplateInfo(
                name="haproxy.cfg",
                type="haproxy_config",
                status="rendered",
                size=2048,
                last_modified=datetime.now(timezone.utc),
            ),
            TemplateInfo(
                name="host.map",
                type="map",
                status="rendered",
                size=512,
                last_modified=datetime.now(timezone.utc),
            ),
            TemplateInfo(
                name="cert.pem",
                type="certificate",
                status="error",
                size=0,
                last_modified=datetime.now(timezone.utc),
            ),
        ]

        templates_data = {t.name: t for t in templates}
        screen = TemplateInspectorScreen(
            data_provider=Mock(),
            templates_data=templates_data,
            selected_template="haproxy.cfg",
        )
        assert screen.templates_data == templates_data
        assert screen.selected_template == "haproxy.cfg"

    def test_screen_lifecycle_methods(self):
        """Test screen lifecycle methods."""
        debug_screen = DebugScreen()

        # Test mount lifecycle
        mock_log_widget = Mock()
        mock_select_widget = Mock()

        with patch.object(
            debug_screen, "query_one", side_effect=[mock_log_widget, mock_select_widget]
        ):
            with patch(
                "haproxy_template_ic.tui.screens.get_tui_log_handler"
            ) as mock_get_handler:
                mock_handler = Mock(spec=TuiLogHandler)
                mock_get_handler.return_value = mock_handler

                with patch.object(debug_screen, "refresh_log_display"):
                    debug_screen.on_mount()
                    mock_handler.set_debug_screen.assert_called_once_with(debug_screen)
                    assert debug_screen.log_widget == mock_log_widget
                    assert debug_screen.log_level_select == mock_select_widget

        # Test suspend/resume lifecycle
        with patch(
            "haproxy_template_ic.tui.screens.get_tui_log_handler"
        ) as mock_get_handler:
            mock_handler = Mock(spec=TuiLogHandler)
            mock_handler.min_log_level = 20  # INFO level
            mock_handler.get_filtered_logs.return_value = []  # Return empty list
            mock_get_handler.return_value = mock_handler

            # Mock the query_one method for the log widget
            mock_log_widget = Mock()
            with patch.object(debug_screen, "query_one", return_value=mock_log_widget):
                debug_screen.on_screen_suspend()
                debug_screen.on_screen_resume(None)

    def test_log_handler_get_filtered_logs_edge_cases(self):
        """Test get_filtered_logs method edge cases."""
        log_handler = TuiLogHandler()

        # Test with min_level=None (should use self.min_log_level) - line 84
        log_handler.min_log_level = logging.WARNING
        result = log_handler.get_filtered_logs(count=100, min_level=None)
        assert result == []

        # Test early break condition when count is reached - line 92
        # Add some logs to test the break condition
        for i in range(5):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"Message {i}",
                args=(),
                exc_info=None,
            )
            log_handler.emit(record)

        # Request only 2 logs to trigger the break condition
        result = log_handler.get_filtered_logs(count=2, min_level=logging.INFO)
        assert len(result) == 2

    def test_log_handler_stack_trace_filtering(self):
        """Test stack trace filtering edge cases."""
        log_handler = TuiLogHandler()

        # Test _should_add_stack_trace with expected errors - should skip stack trace
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Connection refused",
            args=(),
            exc_info=None,
        )
        result = log_handler._should_add_stack_trace(record)
        assert result is False

        # Test with unexpected error - should add stack trace
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Unexpected error occurred",
            args=(),
            exc_info=None,
        )
        result = log_handler._should_add_stack_trace(record)
        assert result is True

    def test_log_handler_traceback_formatting_edge_cases(self):
        """Test traceback formatting edge cases."""
        log_handler = TuiLogHandler()

        # Test _format_filtered_traceback with no exc_info - line 167
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=None,
        )
        result = log_handler._format_filtered_traceback(record)
        assert result == ""

        # Test with real exception to cover more lines
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error with exception",
                args=(),
                exc_info=True,
            )
            # Get the exc_info for the record
            import sys

            record.exc_info = sys.exc_info()

            result = log_handler._format_filtered_traceback(record)
            # Should return something (empty string or formatted traceback)
            assert isinstance(result, str)

    def test_get_tui_log_handler_logger_configuration(self):
        """Test that get_tui_log_handler properly configures logging."""
        # Import the global variable
        import haproxy_template_ic.tui.screens as screens_module

        # Clear any existing handler
        original_handler = screens_module._tui_log_handler
        screens_module._tui_log_handler = None

        try:
            root_logger = logging.getLogger()

            # Get the handler which should configure logging
            handler = get_tui_log_handler()

            # Verify logger configuration
            assert root_logger.level == logging.DEBUG
            assert handler in root_logger.handlers
            assert handler.level == logging.DEBUG

            # Calling again should return the same instance
            handler2 = get_tui_log_handler()
            assert handler is handler2

        finally:
            # Restore original state
            screens_module._tui_log_handler = original_handler
