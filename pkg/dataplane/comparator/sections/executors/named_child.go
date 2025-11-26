// Package executors provides pre-built executor functions for HAProxy configuration operations.
package executors

import (
	"context"
	"fmt"
	"net/http"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
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
func BindFrontendCreate(frontendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *dataplaneapi.Bind) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *dataplaneapi.Bind) error {
		params := &dataplaneapi.CreateBindFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Bind, _ *v32.CreateBindFrontendParams) (*http.Response, error) {
				return clientset.V32().CreateBindFrontend(ctx, frontendName, (*v32.CreateBindFrontendParams)(params), m)
			},
			func(m v31.Bind, _ *v31.CreateBindFrontendParams) (*http.Response, error) {
				return clientset.V31().CreateBindFrontend(ctx, frontendName, (*v31.CreateBindFrontendParams)(params), m)
			},
			func(m v30.Bind, _ *v30.CreateBindFrontendParams) (*http.Response, error) {
				return clientset.V30().CreateBindFrontend(ctx, frontendName, (*v30.CreateBindFrontendParams)(params), m)
			},
			(*v32.CreateBindFrontendParams)(params),
			(*v31.CreateBindFrontendParams)(params),
			(*v30.CreateBindFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "bind creation in frontend")
	}
}

// BindFrontendUpdate returns an executor for updating binds in frontends.
func BindFrontendUpdate(frontendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *dataplaneapi.Bind) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *dataplaneapi.Bind) error {
		params := &dataplaneapi.ReplaceBindFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.Bind, _ *v32.ReplaceBindFrontendParams) (*http.Response, error) {
				return clientset.V32().ReplaceBindFrontend(ctx, frontendName, name, (*v32.ReplaceBindFrontendParams)(params), m)
			},
			func(name string, m v31.Bind, _ *v31.ReplaceBindFrontendParams) (*http.Response, error) {
				return clientset.V31().ReplaceBindFrontend(ctx, frontendName, name, (*v31.ReplaceBindFrontendParams)(params), m)
			},
			func(name string, m v30.Bind, _ *v30.ReplaceBindFrontendParams) (*http.Response, error) {
				return clientset.V30().ReplaceBindFrontend(ctx, frontendName, name, (*v30.ReplaceBindFrontendParams)(params), m)
			},
			(*v32.ReplaceBindFrontendParams)(params),
			(*v31.ReplaceBindFrontendParams)(params),
			(*v30.ReplaceBindFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "bind update in frontend")
	}
}

// BindFrontendDelete returns an executor for deleting binds from frontends.
func BindFrontendDelete(frontendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *dataplaneapi.Bind) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *dataplaneapi.Bind) error {
		params := &dataplaneapi.DeleteBindFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string, _ *v32.DeleteBindFrontendParams) (*http.Response, error) {
				return clientset.V32().DeleteBindFrontend(ctx, frontendName, name, (*v32.DeleteBindFrontendParams)(params))
			},
			func(name string, _ *v31.DeleteBindFrontendParams) (*http.Response, error) {
				return clientset.V31().DeleteBindFrontend(ctx, frontendName, name, (*v31.DeleteBindFrontendParams)(params))
			},
			func(name string, _ *v30.DeleteBindFrontendParams) (*http.Response, error) {
				return clientset.V30().DeleteBindFrontend(ctx, frontendName, name, (*v30.DeleteBindFrontendParams)(params))
			},
			(*v32.DeleteBindFrontendParams)(params),
			(*v31.DeleteBindFrontendParams)(params),
			(*v30.DeleteBindFrontendParams)(params),
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
func ServerTemplateCreate(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *dataplaneapi.ServerTemplate) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *dataplaneapi.ServerTemplate) error {
		params := &dataplaneapi.CreateServerTemplateParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.ServerTemplate, _ *v32.CreateServerTemplateParams) (*http.Response, error) {
				return clientset.V32().CreateServerTemplate(ctx, backendName, (*v32.CreateServerTemplateParams)(params), m)
			},
			func(m v31.ServerTemplate, _ *v31.CreateServerTemplateParams) (*http.Response, error) {
				return clientset.V31().CreateServerTemplate(ctx, backendName, (*v31.CreateServerTemplateParams)(params), m)
			},
			func(m v30.ServerTemplate, _ *v30.CreateServerTemplateParams) (*http.Response, error) {
				return clientset.V30().CreateServerTemplate(ctx, backendName, (*v30.CreateServerTemplateParams)(params), m)
			},
			(*v32.CreateServerTemplateParams)(params),
			(*v31.CreateServerTemplateParams)(params),
			(*v30.CreateServerTemplateParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server template creation")
	}
}

// ServerTemplateUpdate returns an executor for updating server templates in backends.
func ServerTemplateUpdate(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *dataplaneapi.ServerTemplate) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *dataplaneapi.ServerTemplate) error {
		params := &dataplaneapi.ReplaceServerTemplateParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.ServerTemplate, _ *v32.ReplaceServerTemplateParams) (*http.Response, error) {
				return clientset.V32().ReplaceServerTemplate(ctx, backendName, name, (*v32.ReplaceServerTemplateParams)(params), m)
			},
			func(name string, m v31.ServerTemplate, _ *v31.ReplaceServerTemplateParams) (*http.Response, error) {
				return clientset.V31().ReplaceServerTemplate(ctx, backendName, name, (*v31.ReplaceServerTemplateParams)(params), m)
			},
			func(name string, m v30.ServerTemplate, _ *v30.ReplaceServerTemplateParams) (*http.Response, error) {
				return clientset.V30().ReplaceServerTemplate(ctx, backendName, name, (*v30.ReplaceServerTemplateParams)(params), m)
			},
			(*v32.ReplaceServerTemplateParams)(params),
			(*v31.ReplaceServerTemplateParams)(params),
			(*v30.ReplaceServerTemplateParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server template update")
	}
}

// ServerTemplateDelete returns an executor for deleting server templates from backends.
func ServerTemplateDelete(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *dataplaneapi.ServerTemplate) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *dataplaneapi.ServerTemplate) error {
		params := &dataplaneapi.DeleteServerTemplateParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string, _ *v32.DeleteServerTemplateParams) (*http.Response, error) {
				return clientset.V32().DeleteServerTemplate(ctx, backendName, name, (*v32.DeleteServerTemplateParams)(params))
			},
			func(name string, _ *v31.DeleteServerTemplateParams) (*http.Response, error) {
				return clientset.V31().DeleteServerTemplate(ctx, backendName, name, (*v31.DeleteServerTemplateParams)(params))
			},
			func(name string, _ *v30.DeleteServerTemplateParams) (*http.Response, error) {
				return clientset.V30().DeleteServerTemplate(ctx, backendName, name, (*v30.DeleteServerTemplateParams)(params))
			},
			(*v32.DeleteServerTemplateParams)(params),
			(*v31.DeleteServerTemplateParams)(params),
			(*v30.DeleteServerTemplateParams)(params),
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
func ServerCreate(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *dataplaneapi.Server) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model *dataplaneapi.Server) error {
		params := &dataplaneapi.CreateServerBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Server, _ *v32.CreateServerBackendParams) (*http.Response, error) {
				return clientset.V32().CreateServerBackend(ctx, backendName, (*v32.CreateServerBackendParams)(params), m)
			},
			func(m v31.Server, _ *v31.CreateServerBackendParams) (*http.Response, error) {
				return clientset.V31().CreateServerBackend(ctx, backendName, (*v31.CreateServerBackendParams)(params), m)
			},
			func(m v30.Server, _ *v30.CreateServerBackendParams) (*http.Response, error) {
				return clientset.V30().CreateServerBackend(ctx, backendName, (*v30.CreateServerBackendParams)(params), m)
			},
			(*v32.CreateServerBackendParams)(params),
			(*v31.CreateServerBackendParams)(params),
			(*v30.CreateServerBackendParams)(params),
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
func ServerUpdate(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *dataplaneapi.Server) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model *dataplaneapi.Server) error {
		clientset := c.Clientset()

		// Build params based on whether we have a transaction ID or not
		var params32 *v32.ReplaceServerBackendParams
		var params31 *v31.ReplaceServerBackendParams
		var params30 *v30.ReplaceServerBackendParams

		if txID != "" {
			// Use transaction ID
			params32 = &v32.ReplaceServerBackendParams{TransactionId: &txID}
			params31 = &v31.ReplaceServerBackendParams{TransactionId: &txID}
			params30 = &v30.ReplaceServerBackendParams{TransactionId: &txID}
		} else {
			// Use version-based update (DataPlane API decides if runtime update is possible)
			version64, err := c.GetVersion(ctx)
			if err != nil {
				return fmt.Errorf("failed to get configuration version: %w", err)
			}
			version32 := v32.Version(version64)
			version31 := v31.Version(version64)
			version30 := v30.Version(version64)
			params32 = &v32.ReplaceServerBackendParams{Version: &version32}
			params31 = &v31.ReplaceServerBackendParams{Version: &version31}
			params30 = &v30.ReplaceServerBackendParams{Version: &version30}
		}

		resp, err := client.DispatchUpdate(ctx, c, childName, model,
			func(name string, m v32.Server, _ *v32.ReplaceServerBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceServerBackend(ctx, backendName, name, params32, m)
			},
			func(name string, m v31.Server, _ *v31.ReplaceServerBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceServerBackend(ctx, backendName, name, params31, m)
			},
			func(name string, m v30.Server, _ *v30.ReplaceServerBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceServerBackend(ctx, backendName, name, params30, m)
			},
			params32,
			params31,
			params30,
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server update in backend")
	}
}

// ServerDelete returns an executor for deleting servers from backends.
func ServerDelete(backendName string) func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, childName string, model *dataplaneapi.Server) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ *dataplaneapi.Server) error {
		params := &dataplaneapi.DeleteServerBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, childName,
			func(name string, _ *v32.DeleteServerBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteServerBackend(ctx, backendName, name, (*v32.DeleteServerBackendParams)(params))
			},
			func(name string, _ *v31.DeleteServerBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteServerBackend(ctx, backendName, name, (*v31.DeleteServerBackendParams)(params))
			},
			func(name string, _ *v30.DeleteServerBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteServerBackend(ctx, backendName, name, (*v30.DeleteServerBackendParams)(params))
			},
			(*v32.DeleteServerBackendParams)(params),
			(*v31.DeleteServerBackendParams)(params),
			(*v30.DeleteServerBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server deletion from backend")
	}
}
