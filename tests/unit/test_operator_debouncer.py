"""Unit tests for operator debouncer integration."""

from unittest.mock import AsyncMock, MagicMock, patch, ANY

import pytest

from haproxy_template_ic.operator import (
    cleanup_template_debouncer,
    init_template_debouncer,
    trigger_template_rendering,
)
from haproxy_template_ic.config_models import TemplateRenderingConfig

# Test constants
TEST_MIN_INTERVAL = 10
TEST_MAX_INTERVAL = 120


class TestOperatorDebouncerIntegration:
    """Test the integration of debouncer with the operator."""

    @pytest.mark.asyncio
    async def test_trigger_template_rendering_with_debouncer(self):
        """Test that trigger_template_rendering uses debouncer when available."""
        memo = MagicMock()
        memo.debouncer = MagicMock()
        memo.debouncer.trigger = AsyncMock()

        await trigger_template_rendering(memo)

        # Should call debouncer.trigger
        memo.debouncer.trigger.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_template_rendering_without_debouncer(self):
        """Test fallback to direct rendering when debouncer not available."""
        memo = MagicMock(spec=[])  # No debouncer attribute

        with patch(
            "haproxy_template_ic.operator.render_haproxy_templates"
        ) as mock_render:
            mock_render = AsyncMock()

            with patch(
                "haproxy_template_ic.operator.render_haproxy_templates", mock_render
            ):
                await trigger_template_rendering(memo)

            # Should fall back to direct rendering
            mock_render.assert_called_once_with(memo)

    @pytest.mark.asyncio
    async def test_init_template_debouncer(self):
        """Test debouncer initialization."""
        memo = MagicMock(spec=["config"])
        memo.config = MagicMock()
        memo.config.template_rendering = TemplateRenderingConfig(
            min_render_interval=TEST_MIN_INTERVAL, max_render_interval=TEST_MAX_INTERVAL
        )

        with patch(
            "haproxy_template_ic.operator.TemplateRenderDebouncer"
        ) as MockDebouncer:
            mock_instance = MagicMock()
            MockDebouncer.return_value = mock_instance

            await init_template_debouncer(memo)

            # Should create debouncer with correct params
            MockDebouncer.assert_called_once_with(
                min_interval=TEST_MIN_INTERVAL,
                max_interval=TEST_MAX_INTERVAL,
                render_func=ANY,  # render_haproxy_templates function
                memo=memo,
            )

            # Should start the debouncer
            mock_instance.start.assert_called_once()

            # Should store in memo
            assert memo.debouncer is mock_instance

    @pytest.mark.asyncio
    async def test_init_template_debouncer_stops_existing(self):
        """Test that init stops existing debouncer before creating new one."""
        memo = MagicMock()
        memo.config = MagicMock()
        memo.config.template_rendering = TemplateRenderingConfig()

        # Existing debouncer
        old_debouncer = MagicMock()
        old_debouncer.stop = AsyncMock()
        memo.debouncer = old_debouncer

        with patch("haproxy_template_ic.operator.TemplateRenderDebouncer"):
            await init_template_debouncer(memo)

            # Should stop old debouncer
            old_debouncer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_template_debouncer(self):
        """Test debouncer cleanup."""
        memo = MagicMock()
        mock_debouncer = MagicMock()
        mock_debouncer.stop = AsyncMock()
        memo.debouncer = mock_debouncer

        await cleanup_template_debouncer(memo)

        # Should stop debouncer
        mock_debouncer.stop.assert_called_once()

        # Should clear reference
        assert memo.debouncer is None

    @pytest.mark.asyncio
    async def test_cleanup_template_debouncer_no_debouncer(self):
        """Test cleanup when no debouncer exists."""
        memo = MagicMock(spec=[])  # No debouncer attribute

        # Should not raise error
        await cleanup_template_debouncer(memo)

    @pytest.mark.asyncio
    async def test_template_rendering_config_validation(self):
        """Test that template rendering config validates intervals."""
        # Valid config
        config = TemplateRenderingConfig(min_render_interval=5, max_render_interval=60)
        assert config.min_render_interval == 5
        assert config.max_render_interval == 60

        # Invalid: max < min
        with pytest.raises(ValueError, match="must be >= min_render_interval"):
            TemplateRenderingConfig(min_render_interval=10, max_render_interval=5)
