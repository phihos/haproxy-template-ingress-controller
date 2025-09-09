"""
Unit tests for TUI utility functions.

Tests formatting functions, edge cases, and error handling.
"""

from datetime import datetime, timezone

from haproxy_template_ic.tui.utils import format_size, format_timestamp, format_age


class TestFormatSize:
    """Test format_size function."""

    def test_format_size_bytes(self):
        """Test formatting bytes."""
        assert format_size(0) == "0B"
        assert format_size(1) == "1B"
        assert format_size(512) == "512B"
        assert format_size(1023) == "1023B"

    def test_format_size_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_size(1024) == "1.0KB"
        assert format_size(1536) == "1.5KB"
        assert format_size(2048) == "2.0KB"
        assert format_size(1024 * 1024 - 1) == "1024.0KB"

    def test_format_size_megabytes(self):
        """Test formatting megabytes."""
        assert format_size(1024 * 1024) == "1.0MB"
        assert format_size(1024 * 1024 * 1.5) == "1.5MB"
        assert format_size(1024 * 1024 * 512) == "512.0MB"

    def test_format_size_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_size(1024 * 1024 * 1024) == "1.0GB"
        assert format_size(1024 * 1024 * 1024 * 2.5) == "2.5GB"

    def test_format_size_string_input(self):
        """Test formatting with string input."""
        assert format_size("1024") == "1.0KB"
        assert format_size("2048") == "2.0KB"
        assert format_size("0") == "0B"

    def test_format_size_float_input(self):
        """Test formatting with float input."""
        assert format_size(1024.5) == "1.0KB"
        assert format_size(1536.7) == "1.5KB"

    def test_format_size_negative_values(self):
        """Test formatting negative values."""
        assert format_size(-1) == "0B"
        assert format_size(-1024) == "0B"

    def test_format_size_invalid_input(self):
        """Test formatting invalid input."""
        assert format_size(None) == "0B"
        assert format_size("invalid") == "0B"
        assert format_size([1, 2, 3]) == "0B"
        assert format_size({"size": 1024}) == "0B"

    def test_format_size_edge_cases(self):
        """Test edge cases."""
        # Very large number
        very_large = 1024 * 1024 * 1024 * 1024
        result = format_size(very_large)
        assert "GB" in result

        # Exact boundary values
        assert format_size(1024) == "1.0KB"
        assert format_size(1024 * 1024) == "1.0MB"
        assert format_size(1024 * 1024 * 1024) == "1.0GB"


class TestFormatTimestamp:
    """Test format_timestamp function."""

    def test_format_timestamp_none(self):
        """Test formatting None timestamp."""
        assert format_timestamp(None) == "-"
        assert format_timestamp("") == "-"

    def test_format_timestamp_iso_string_with_z(self):
        """Test formatting ISO string with Z suffix."""
        iso_string = "2024-01-15T10:30:45Z"
        result = format_timestamp(iso_string)
        # Should return formatted time (exact format depends on local timezone)
        assert ":" in result
        assert len(result.split(":")) == 3  # HH:MM:SS

    def test_format_timestamp_iso_string_with_timezone(self):
        """Test formatting ISO string with timezone offset."""
        iso_string = "2024-01-15T10:30:45+02:00"
        result = format_timestamp(iso_string)
        assert ":" in result
        assert len(result.split(":")) == 3

    def test_format_timestamp_already_formatted(self):
        """Test with already formatted timestamp."""
        formatted = "10:30:45"
        result = format_timestamp(formatted)
        assert result == formatted

    def test_format_timestamp_datetime_object_with_timezone(self):
        """Test formatting datetime object with timezone."""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = format_timestamp(dt)
        assert ":" in result
        assert len(result.split(":")) == 3

    def test_format_timestamp_datetime_object_naive(self):
        """Test formatting naive datetime object."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = format_timestamp(dt)
        assert result == "10:30:45"

    def test_format_timestamp_custom_format(self):
        """Test formatting with custom format string."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = format_timestamp(dt, format_str="%Y-%m-%d %H:%M")
        assert result == "2024-01-15 10:30"

    def test_format_timestamp_invalid_input(self):
        """Test formatting invalid input."""
        assert format_timestamp(123) == "123"  # Numbers returned as-is
        assert (
            format_timestamp(["invalid"]) == "['invalid']"
        )  # Lists converted to string

    def test_format_timestamp_malformed_iso(self):
        """Test with malformed ISO string."""
        malformed = "2024-01-15X10:30:45"
        result = format_timestamp(malformed)
        assert result == malformed  # Should return as-is if no 'T'


class TestFormatAge:
    """Test format_age function."""

    def test_format_age_recent(self):
        """Test formatting recent timestamps."""
        # 30 seconds ago
        recent = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        result = format_age(recent)
        assert result == "<1m"

    def test_format_age_minutes(self):
        """Test formatting minutes ago."""
        # Approximate timestamp for 5 minutes ago
        import datetime as dt

        five_min_ago = datetime.now(timezone.utc) - dt.timedelta(minutes=5)
        timestamp = five_min_ago.isoformat().replace("+00:00", "Z")
        result = format_age(timestamp)
        assert result == "5m"

    def test_format_age_hours(self):
        """Test formatting hours ago."""
        import datetime as dt

        two_hours_ago = datetime.now(timezone.utc) - dt.timedelta(hours=2)
        timestamp = two_hours_ago.isoformat().replace("+00:00", "Z")
        result = format_age(timestamp)
        assert result == "2h"

    def test_format_age_days(self):
        """Test formatting days ago."""
        import datetime as dt

        two_days_ago = datetime.now(timezone.utc) - dt.timedelta(days=2)
        timestamp = two_days_ago.isoformat().replace("+00:00", "Z")
        result = format_age(timestamp)
        assert result == "2d"

    def test_format_age_none(self):
        """Test formatting None timestamp."""
        assert format_age(None) == "Unknown"

    def test_format_age_empty_string(self):
        """Test formatting empty string."""
        assert format_age("") == "Unknown"

    def test_format_age_invalid_format(self):
        """Test formatting invalid timestamp."""
        result = format_age("invalid-timestamp")
        assert result == "Unknown"

    def test_format_age_future_timestamp(self):
        """Test formatting future timestamp."""
        import datetime as dt

        future = datetime.now(timezone.utc) + dt.timedelta(hours=1)
        timestamp = future.isoformat().replace("+00:00", "Z")
        result = format_age(timestamp)
        # Should handle gracefully (might show "just now" or negative time)
        assert isinstance(result, str)

    def test_format_age_different_formats(self):
        """Test different timestamp formats."""
        # ISO with timezone
        iso_tz = "2024-01-15T10:30:45+02:00"
        result1 = format_age(iso_tz)
        assert isinstance(result1, str)

        # ISO with Z
        iso_z = "2024-01-15T10:30:45Z"
        result2 = format_age(iso_z)
        assert isinstance(result2, str)

    def test_format_age_very_old(self):
        """Test formatting very old timestamps."""
        import datetime as dt

        very_old = datetime.now(timezone.utc) - dt.timedelta(days=365)
        timestamp = very_old.isoformat().replace("+00:00", "Z")
        result = format_age(timestamp)
        # Should handle large time differences gracefully
        assert isinstance(result, str)
        assert len(result) > 0


class TestUtilsIntegration:
    """Integration tests for utility functions."""

    def test_size_formatting_pipeline(self):
        """Test size formatting with various realistic values."""
        test_cases = [
            (0, "0B"),
            (1, "1B"),
            (1024, "1.0KB"),
            (1048576, "1.0MB"),  # 1024*1024
            (1073741824, "1.0GB"),  # 1024*1024*1024
            (1536, "1.5KB"),  # 1.5 KB
            (2621440, "2.5MB"),  # 2.5 MB
        ]

        for size, expected in test_cases:
            assert format_size(size) == expected

    def test_timestamp_formatting_pipeline(self):
        """Test timestamp formatting with common patterns."""
        # Test with a known datetime
        dt = datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)

        # Default format (HH:MM:SS in local time)
        default_result = format_timestamp(dt)
        assert ":" in default_result

        # Custom format
        date_result = format_timestamp(dt, "%Y-%m-%d")
        assert date_result.startswith("2024-01-")

        # ISO string input
        iso_result = format_timestamp("2024-01-15T14:30:45Z")
        assert ":" in iso_result

    def test_age_formatting_scenarios(self):
        """Test age formatting for common dashboard scenarios."""
        import datetime as dt

        base_time = datetime.now(timezone.utc)

        # Test scenarios that would appear in a dashboard
        scenarios = [
            (base_time - dt.timedelta(seconds=30), lambda x: x == "<1m"),
            (base_time - dt.timedelta(minutes=5), lambda x: x == "5m"),
            (base_time - dt.timedelta(hours=2), lambda x: x == "2h"),
            (base_time - dt.timedelta(days=1), lambda x: x == "1d"),
        ]

        for timestamp, validator in scenarios:
            iso_timestamp = timestamp.isoformat().replace("+00:00", "Z")
            result = format_age(iso_timestamp)
            assert validator(result), (
                f"Failed for timestamp {iso_timestamp}, got {result}"
            )

    def test_error_handling_consistency(self):
        """Test that all utility functions handle errors gracefully."""
        invalid_inputs = [None, "", "invalid", [], {}, 123.456]

        for invalid_input in invalid_inputs:
            # format_size should return "0B" for invalid input
            size_result = format_size(invalid_input)
            assert isinstance(size_result, str)

            # format_timestamp should return string representation or "-"
            timestamp_result = format_timestamp(invalid_input)
            assert isinstance(timestamp_result, str)

            # format_age should return a meaningful string
            age_result = format_age(invalid_input)
            assert isinstance(age_result, str)
            assert len(age_result) > 0

    def test_utility_functions_with_real_data(self):
        """Test utility functions with realistic dashboard data."""
        # Simulate data that would come from the dashboard
        template_sizes = [0, 1024, 2048, 1048576]  # 0B, 1KB, 2KB, 1MB
        timestamps = ["2024-01-15T10:30:45Z", "2024-01-15T09:30:45Z", None, ""]

        # Test all size formatting
        for size in template_sizes:
            result = format_size(size)
            assert "B" in result  # All should have byte unit

        # Test all timestamp formatting
        for timestamp in timestamps:
            result = format_timestamp(timestamp)
            assert isinstance(result, str)

        # Test age formatting
        for timestamp in timestamps:
            result = format_age(timestamp)
            assert isinstance(result, str)
