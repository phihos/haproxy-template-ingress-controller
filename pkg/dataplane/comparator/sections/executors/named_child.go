// Package executors provides pre-built executor functions for HAProxy configuration operations.
package executors

import (
	"context"
	"fmt"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
)

// =============================================================================
// Bind Executors (Frontend)
// =============================================================================

// BindFrontendCreate returns an executor for creating binds in frontends.
// Note: Bind uses DispatchCreate (not DispatchCreateChild) because the API
// takes frontendName as a path parameter, not as part of an index-based child.
func BindFrontendCreate(frontendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *models.Bind) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *models.Bind) error {
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Bind) (*http.Response, error) {
				params := &v32.CreateBindFrontendParams{TransactionId: &txID}
				return clientset.V32().CreateBindFrontend(ctx, frontendName, params, m)
			},
			func(m v31.Bind) (*http.Response, error) {
				params := &v31.CreateBindFrontendParams{TransactionId: &txID}
				return clientset.V31().CreateBindFrontend(ctx, frontendName, params, m)
			},
			func(m v30.Bind) (*http.Response, error) {
				params := &v30.CreateBindFrontendParams{TransactionId: &txID}
				return clientset.V30().CreateBindFrontend(ctx, frontendName, params, m)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "bind creation in frontend")
	}
}

// BindFrontendUpdate returns an executor for updating binds in frontends.
func BindFrontendUpdate(frontendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *models.Bind) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *models.Bind) error {
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.Bind) (*http.Response, error) {
				params := &v32.ReplaceBindFrontendParams{TransactionId: &txID}
				return clientset.V32().ReplaceBindFrontend(ctx, frontendName, name, params, m)
			},
			func(name string, m v31.Bind) (*http.Response, error) {
				params := &v31.ReplaceBindFrontendParams{TransactionId: &txID}
				return clientset.V31().ReplaceBindFrontend(ctx, frontendName, name, params, m)
			},
			func(name string, m v30.Bind) (*http.Response, error) {
				params := &v30.ReplaceBindFrontendParams{TransactionId: &txID}
				return clientset.V30().ReplaceBindFrontend(ctx, frontendName, name, params, m)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "bind update in frontend")
	}
}

// BindFrontendDelete returns an executor for deleting binds from frontends.
func BindFrontendDelete(frontendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *models.Bind) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *models.Bind) error {
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string) (*http.Response, error) {
				params := &v32.DeleteBindFrontendParams{TransactionId: &txID}
				return clientset.V32().DeleteBindFrontend(ctx, frontendName, name, params)
			},
			func(name string) (*http.Response, error) {
				params := &v31.DeleteBindFrontendParams{TransactionId: &txID}
				return clientset.V31().DeleteBindFrontend(ctx, frontendName, name, params)
			},
			func(name string) (*http.Response, error) {
				params := &v30.DeleteBindFrontendParams{TransactionId: &txID}
				return clientset.V30().DeleteBindFrontend(ctx, frontendName, name, params)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "bind deletion from frontend")
	}
}

// =============================================================================
// Server Template Executors (Backend)
// =============================================================================

// ServerTemplateCreate returns an executor for creating server templates in backends.
func ServerTemplateCreate(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *models.ServerTemplate) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *models.ServerTemplate) error {
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.ServerTemplate) (*http.Response, error) {
				params := &v32.CreateServerTemplateParams{TransactionId: &txID}
				return clientset.V32().CreateServerTemplate(ctx, backendName, params, m)
			},
			func(m v31.ServerTemplate) (*http.Response, error) {
				params := &v31.CreateServerTemplateParams{TransactionId: &txID}
				return clientset.V31().CreateServerTemplate(ctx, backendName, params, m)
			},
			func(m v30.ServerTemplate) (*http.Response, error) {
				params := &v30.CreateServerTemplateParams{TransactionId: &txID}
				return clientset.V30().CreateServerTemplate(ctx, backendName, params, m)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server template creation")
	}
}

// ServerTemplateUpdate returns an executor for updating server templates in backends.
func ServerTemplateUpdate(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *models.ServerTemplate) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *models.ServerTemplate) error {
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.ServerTemplate) (*http.Response, error) {
				params := &v32.ReplaceServerTemplateParams{TransactionId: &txID}
				return clientset.V32().ReplaceServerTemplate(ctx, backendName, name, params, m)
			},
			func(name string, m v31.ServerTemplate) (*http.Response, error) {
				params := &v31.ReplaceServerTemplateParams{TransactionId: &txID}
				return clientset.V31().ReplaceServerTemplate(ctx, backendName, name, params, m)
			},
			func(name string, m v30.ServerTemplate) (*http.Response, error) {
				params := &v30.ReplaceServerTemplateParams{TransactionId: &txID}
				return clientset.V30().ReplaceServerTemplate(ctx, backendName, name, params, m)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server template update")
	}
}

// ServerTemplateDelete returns an executor for deleting server templates from backends.
func ServerTemplateDelete(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *models.ServerTemplate) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *models.ServerTemplate) error {
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string) (*http.Response, error) {
				params := &v32.DeleteServerTemplateParams{TransactionId: &txID}
				return clientset.V32().DeleteServerTemplate(ctx, backendName, name, params)
			},
			func(name string) (*http.Response, error) {
				params := &v31.DeleteServerTemplateParams{TransactionId: &txID}
				return clientset.V31().DeleteServerTemplate(ctx, backendName, name, params)
			},
			func(name string) (*http.Response, error) {
				params := &v30.DeleteServerTemplateParams{TransactionId: &txID}
				return clientset.V30().DeleteServerTemplate(ctx, backendName, name, params)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server template deletion")
	}
}

// =============================================================================
// Server Executors (Backend)
// =============================================================================

// ServerCreate returns an executor for creating servers in backends.
func ServerCreate(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *models.Server) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *models.Server) error {
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Server) (*http.Response, error) {
				params := &v32.CreateServerBackendParams{TransactionId: &txID}
				return clientset.V32().CreateServerBackend(ctx, backendName, params, m)
			},
			func(m v31.Server) (*http.Response, error) {
				params := &v31.CreateServerBackendParams{TransactionId: &txID}
				return clientset.V31().CreateServerBackend(ctx, backendName, params, m)
			},
			func(m v30.Server) (*http.Response, error) {
				params := &v30.CreateServerBackendParams{TransactionId: &txID}
				return clientset.V30().CreateServerBackend(ctx, backendName, params, m)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server creation in backend")
	}
}

// ServerUpdate returns an executor for updating servers in backends.
// When txID is empty, it uses version-based update (DataPlane API decides if reload is needed).
// When txID is non-empty, it uses the Configuration API with transaction.
func ServerUpdate(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *models.Server) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *models.Server) error {
		clientset := c.Clientset()

		// Get version if needed for version-based update
		var version64 int64
		if txID == "" {
			var err error
			version64, err = c.GetVersion(ctx)
			if err != nil {
				return fmt.Errorf("failed to get configuration version: %w", err)
			}
		}

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.Server) (*http.Response, error) {
				var params *v32.ReplaceServerBackendParams
				if txID != "" {
					params = &v32.ReplaceServerBackendParams{TransactionId: &txID}
				} else {
					version := v32.Version(version64)
					params = &v32.ReplaceServerBackendParams{Version: &version}
				}
				return clientset.V32().ReplaceServerBackend(ctx, backendName, name, params, m)
			},
			func(name string, m v31.Server) (*http.Response, error) {
				var params *v31.ReplaceServerBackendParams
				if txID != "" {
					params = &v31.ReplaceServerBackendParams{TransactionId: &txID}
				} else {
					version := v31.Version(version64)
					params = &v31.ReplaceServerBackendParams{Version: &version}
				}
				return clientset.V31().ReplaceServerBackend(ctx, backendName, name, params, m)
			},
			func(name string, m v30.Server) (*http.Response, error) {
				var params *v30.ReplaceServerBackendParams
				if txID != "" {
					params = &v30.ReplaceServerBackendParams{TransactionId: &txID}
				} else {
					version := v30.Version(version64)
					params = &v30.ReplaceServerBackendParams{Version: &version}
				}
				return clientset.V30().ReplaceServerBackend(ctx, backendName, name, params, m)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server update in backend")
	}
}

// ServerDelete returns an executor for deleting servers from backends.
func ServerDelete(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *models.Server) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *models.Server) error {
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string) (*http.Response, error) {
				params := &v32.DeleteServerBackendParams{TransactionId: &txID}
				return clientset.V32().DeleteServerBackend(ctx, backendName, name, params)
			},
			func(name string) (*http.Response, error) {
				params := &v31.DeleteServerBackendParams{TransactionId: &txID}
				return clientset.V31().DeleteServerBackend(ctx, backendName, name, params)
			},
			func(name string) (*http.Response, error) {
				params := &v30.DeleteServerBackendParams{TransactionId: &txID}
				return clientset.V30().DeleteServerBackend(ctx, backendName, name, params)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server deletion from backend")
	}
}
