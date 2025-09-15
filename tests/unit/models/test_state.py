"""Unit tests for ApplicationState model and property accessors."""

from unittest.mock import MagicMock
from kopf._core.engines.indexing import OperatorIndices

from haproxy_template_ic.models.state import ApplicationState
from haproxy_template_ic.credentials import Credentials
from haproxy_template_ic.models.context import HAProxyConfigContext
from haproxy_template_ic.templating import TemplateRenderer


class TestApplicationState:
    """Test ApplicationState property accessors and backward compatibility."""

    def test_haproxy_config_context_property(self):
        """Test haproxy_config_context property accessor."""
        # Create a mock ApplicationState with the necessary structure
        state = MagicMock()
        mock_context = MagicMock(spec=HAProxyConfigContext)

        # Mock the configuration.haproxy_config_context path
        state.configuration.haproxy_config_context = mock_context

        # Set up the property to return the correct value
        type(state).haproxy_config_context = ApplicationState.haproxy_config_context

        # Test that the property returns the context from configuration
        assert state.haproxy_config_context is mock_context

    def test_indices_property(self):
        """Test indices property accessor."""
        # Create a mock ApplicationState with the necessary structure
        state = MagicMock()
        mock_indices = MagicMock(spec=OperatorIndices)

        # Mock the resources.indices path
        state.resources.indices = mock_indices

        # Set up the property to return the correct value
        type(state).indices = ApplicationState.indices

        # Test that the property returns the indices from resources
        assert state.indices is mock_indices

    def test_credentials_property(self):
        """Test credentials property accessor."""
        # Create a mock ApplicationState with the necessary structure
        state = MagicMock()
        mock_credentials = MagicMock(spec=Credentials)

        # Mock the configuration.credentials path
        state.configuration.credentials = mock_credentials

        # Set up the property to return the correct value
        type(state).credentials = ApplicationState.credentials

        # Test that the property returns the credentials from configuration
        assert state.credentials is mock_credentials

    def test_template_renderer_property(self):
        """Test template_renderer property accessor."""
        # Create a mock ApplicationState with the necessary structure
        state = MagicMock()
        mock_renderer = MagicMock(spec=TemplateRenderer)

        # Mock the configuration.template_renderer path
        state.configuration.template_renderer = mock_renderer

        # Set up the property to return the correct value
        type(state).template_renderer = ApplicationState.template_renderer

        # Test that the property returns the template renderer from configuration
        assert state.template_renderer is mock_renderer

    def test_config_property(self):
        """Test config property accessor."""
        # Create a mock ApplicationState with the necessary structure
        state = MagicMock()
        from haproxy_template_ic.models.config import Config

        mock_config = MagicMock(spec=Config)

        # Mock the configuration.config path
        state.configuration.config = mock_config

        # Set up the property to return the correct value
        type(state).config = ApplicationState.config

        # Test that the property returns the config from configuration
        assert state.config is mock_config
