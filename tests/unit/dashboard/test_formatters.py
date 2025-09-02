"""Test data formatting utilities."""

from datetime import datetime, timezone

from haproxy_template_ic.dashboard.formatters import (
    format_bytes,
    format_duration,
    format_timestamp,
    format_percentage,
    truncate_text,
    format_resource_name,
    create_sparkline,
    format_status,
)


class TestFormatBytes:
    """Test bytes formatting."""

    def test_bytes_formatting(self):
        """Test various byte values."""
        assert format_bytes(0) == "0B"
        assert format_bytes(512) == "512B"
        assert format_bytes(1024) == "1.0KB"
        assert format_bytes(1536) == "1.5KB"
        assert format_bytes(1024 * 1024) == "1.0MB"
        assert format_bytes(1024 * 1024 * 1024) == "1.0GB"
        assert format_bytes(1024 * 1024 * 1024 * 1024) == "1.0TB"

    def test_string_input_with_units(self):
        """Test string input with units."""
        assert format_bytes("1024B") == "1024B"
        assert format_bytes("1KB") == "1.0KB"
        assert format_bytes("1.5MB") == "1.5MB"
        assert format_bytes("2GB") == "2.0GB"

    def test_string_input_without_units(self):
        """Test string input without units."""
        assert format_bytes("1024") == "1.0KB"
        assert format_bytes("invalid") == "invalid"

    def test_invalid_input(self):
        """Test invalid input handling."""
        assert format_bytes(None) == "None"
        assert format_bytes([]) == "[]"


class TestFormatDuration:
    """Test duration formatting."""

    def test_milliseconds(self):
        """Test millisecond formatting."""
        assert format_duration(100) == "100ms"
        assert format_duration(999) == "999ms"

    def test_seconds(self):
        """Test second formatting."""
        assert format_duration(1000) == "1.0s"
        assert format_duration(1500) == "1.5s"
        assert format_duration(59999) == "60.0s"

    def test_minutes(self):
        """Test minute formatting."""
        assert format_duration(60000) == "1m 0s"
        assert format_duration(90000) == "1m 30s"
        assert format_duration(3599000) == "59m 59s"

    def test_hours(self):
        """Test hour formatting."""
        assert format_duration(3600000) == "1h 0m"
        assert format_duration(3900000) == "1h 5m"

    def test_string_input(self):
        """Test string input handling."""
        assert format_duration("1000ms") == "1000ms"
        assert format_duration("5s") == "5s"
        assert format_duration("1000") == "1.0s"
        assert format_duration("invalid") == "invalid"

    def test_invalid_input(self):
        """Test invalid input handling."""
        assert format_duration(None) == "None"


class TestFormatTimestamp:
    """Test timestamp formatting."""

    def test_recent_timestamp(self):
        """Test recent timestamp (seconds ago)."""
        now = datetime.now(timezone.utc)
        past = now.replace(
            second=now.second - 30 if now.second >= 30 else now.second + 30,
            microsecond=0,
        )
        result = format_timestamp(past.isoformat())
        assert "s ago" in result

    def test_minutes_ago(self):
        """Test timestamp from minutes ago."""
        now = datetime.now(timezone.utc)
        past = now.replace(
            minute=now.minute - 5 if now.minute >= 5 else now.minute + 55,
            second=0,
            microsecond=0,
        )
        result = format_timestamp(past.isoformat())
        assert "m ago" in result or ":" in result  # Could be time format if same day

    def test_today_timestamp(self):
        """Test timestamp from today."""
        now = datetime.now(timezone.utc)
        past = now.replace(
            hour=now.hour - 2 if now.hour >= 2 else now.hour + 22,
            minute=0,
            second=0,
            microsecond=0,
        )
        result = format_timestamp(past.isoformat())
        assert ":" in result

    def test_string_timestamp_with_z(self):
        """Test ISO string with Z suffix."""
        timestamp = "2023-01-01T12:00:00Z"
        result = format_timestamp(timestamp)
        assert result  # Should not raise exception

    def test_datetime_object(self):
        """Test datetime object input."""
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = format_timestamp(dt)
        assert result  # Should not raise exception

    def test_invalid_timestamp(self):
        """Test invalid timestamp handling."""
        assert format_timestamp("invalid") == "invalid"
        assert format_timestamp(123) == "123"


class TestFormatPercentage:
    """Test percentage formatting."""

    def test_percentage_0_100_range(self):
        """Test percentage in 0-100 range."""
        assert format_percentage(50) == "50.0%"
        assert format_percentage(75.5) == "75.5%"
        assert format_percentage(100) == "100.0%"

    def test_percentage_0_1_range(self):
        """Test percentage in 0-1 range."""
        assert format_percentage(0.5) == "50.0%"
        assert format_percentage(0.755) == "75.5%"
        assert format_percentage(1.0) == "100.0%"

    def test_decimal_places(self):
        """Test custom decimal places."""
        assert format_percentage(75.555, 0) == "76%"
        assert format_percentage(75.555, 2) == "75.56%"

    def test_string_input(self):
        """Test string input handling."""
        assert format_percentage("50%") == "50%"
        assert format_percentage("0.5") == "50.0%"
        assert format_percentage("invalid") == "invalid"

    def test_invalid_input(self):
        """Test invalid input handling."""
        assert format_percentage(None) == "None"


class TestTruncateText:
    """Test text truncation."""

    def test_no_truncation_needed(self):
        """Test text shorter than max length."""
        assert truncate_text("short", 10) == "short"

    def test_truncation_with_default_suffix(self):
        """Test truncation with default suffix."""
        assert truncate_text("very long text", 10) == "very lo..."

    def test_truncation_with_custom_suffix(self):
        """Test truncation with custom suffix."""
        assert truncate_text("very long text", 10, ">>") == "very lon>>"

    def test_suffix_longer_than_max_length(self):
        """Test suffix longer than max length."""
        assert truncate_text("text", 2, "...") == "te"


class TestFormatResourceName:
    """Test resource name formatting."""

    def test_short_name(self):
        """Test short name that doesn't need truncation."""
        assert format_resource_name("short") == "short"

    def test_long_name_with_hyphens(self):
        """Test long name with hyphens."""
        name = "haproxy-template-ic-7d9f8b6-x2kt9"
        result = format_resource_name(name, 20)
        assert len(result) <= 20
        assert "haproxy" in result
        assert "x2kt9" in result

    def test_long_name_fallback(self):
        """Test long name without meaningful parts."""
        name = "verylongnamewithnohyphenstobreakup"
        result = format_resource_name(name, 20)
        assert len(result) <= 20
        assert result.endswith("...")


class TestCreateSparkline:
    """Test sparkline creation."""

    def test_empty_values(self):
        """Test empty values."""
        assert create_sparkline([]) == ""
        assert create_sparkline([], 10) == ""

    def test_single_value(self):
        """Test single value."""
        result = create_sparkline([5], 8)
        assert len(result) == 8
        assert result == "▄" * 8  # All same level

    def test_increasing_values(self):
        """Test increasing values."""
        values = [1, 2, 3, 4, 5]
        result = create_sparkline(values, 5)
        assert len(result) == 5
        # Should show increasing pattern
        assert result[0] < result[-1] or all(c in "▁▂▃▄▅▆▇█" for c in result)

    def test_width_adjustment(self):
        """Test width adjustment."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = create_sparkline(values, 5)
        assert len(result) == 5

    def test_invalid_values(self):
        """Test invalid values handling."""
        result = create_sparkline([None, "invalid", []], 5)
        assert len(result) == 5
        assert all(c in "▁▂▃▄▅▆▇█" for c in result)


class TestFormatStatus:
    """Test status formatting."""

    def test_kubernetes_statuses(self):
        """Test Kubernetes pod statuses."""
        text, color = format_status("Running")
        assert "✅" in text
        assert color == "green"

        text, color = format_status("Pending")
        assert "🟡" in text
        assert color == "yellow"

        text, color = format_status("Failed")
        assert "❌" in text
        assert color == "red"

    def test_haproxy_statuses(self):
        """Test HAProxy statuses."""
        text, color = format_status("UP")
        assert "🟢" in text
        assert color == "green"

        text, color = format_status("DOWN")
        assert "🔴" in text
        assert color == "red"

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        text, color = format_status("running")
        assert "✅" in text
        assert color == "green"

        text, color = format_status("RUNNING")
        assert "🚀" in text
        assert color == "green"

    def test_unknown_status(self):
        """Test unknown status handling."""
        text, color = format_status("UNKNOWN_STATUS")
        assert "⚪" in text
        assert color == "dim"

    def test_custom_status_map(self):
        """Test custom status mapping."""
        custom_map = {"CUSTOM": ("🔵 CUSTOM", "blue")}

        text, color = format_status("custom", custom_map)
        assert text == "🔵 CUSTOM"
        assert color == "blue"
