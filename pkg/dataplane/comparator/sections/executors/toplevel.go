// Package executors provides pre-built executor functions for HAProxy configuration operations.
//
// These functions encapsulate the dispatcher callback boilerplate, providing a clean
// interface between the generic operation types and the versioned DataPlane API clients.
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

// BackendCreate returns an executor for creating backends.
func BackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Backend, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Backend, _ string) error {
		params := &dataplaneapi.CreateBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Backend, _ *v32.CreateBackendParams) (*http.Response, error) {
				return clientset.V32().CreateBackend(ctx, (*v32.CreateBackendParams)(params), m)
			},
			func(m v31.Backend, _ *v31.CreateBackendParams) (*http.Response, error) {
				return clientset.V31().CreateBackend(ctx, (*v31.CreateBackendParams)(params), m)
			},
			func(m v30.Backend, _ *v30.CreateBackendParams) (*http.Response, error) {
				return clientset.V30().CreateBackend(ctx, (*v30.CreateBackendParams)(params), m)
			},
			(*v32.CreateBackendParams)(params),
			(*v31.CreateBackendParams)(params),
			(*v30.CreateBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "backend creation")
	}
}

// BackendUpdate returns an executor for updating backends.
func BackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Backend, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Backend, name string) error {
		params := &dataplaneapi.ReplaceBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.Backend, _ *v32.ReplaceBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceBackend(ctx, n, (*v32.ReplaceBackendParams)(params), m)
			},
			func(n string, m v31.Backend, _ *v31.ReplaceBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceBackend(ctx, n, (*v31.ReplaceBackendParams)(params), m)
			},
			func(n string, m v30.Backend, _ *v30.ReplaceBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceBackend(ctx, n, (*v30.ReplaceBackendParams)(params), m)
			},
			(*v32.ReplaceBackendParams)(params),
			(*v31.ReplaceBackendParams)(params),
			(*v30.ReplaceBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "backend update")
	}
}

// BackendDelete returns an executor for deleting backends.
func BackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Backend, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Backend, name string) error {
		params := &dataplaneapi.DeleteBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteBackend(ctx, n, (*v32.DeleteBackendParams)(params))
			},
			func(n string, _ *v31.DeleteBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteBackend(ctx, n, (*v31.DeleteBackendParams)(params))
			},
			func(n string, _ *v30.DeleteBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteBackend(ctx, n, (*v30.DeleteBackendParams)(params))
			},
			(*v32.DeleteBackendParams)(params),
			(*v31.DeleteBackendParams)(params),
			(*v30.DeleteBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "backend deletion")
	}
}

// FrontendCreate returns an executor for creating frontends.
func FrontendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Frontend, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Frontend, _ string) error {
		params := &dataplaneapi.CreateFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Frontend, _ *v32.CreateFrontendParams) (*http.Response, error) {
				return clientset.V32().CreateFrontend(ctx, (*v32.CreateFrontendParams)(params), m)
			},
			func(m v31.Frontend, _ *v31.CreateFrontendParams) (*http.Response, error) {
				return clientset.V31().CreateFrontend(ctx, (*v31.CreateFrontendParams)(params), m)
			},
			func(m v30.Frontend, _ *v30.CreateFrontendParams) (*http.Response, error) {
				return clientset.V30().CreateFrontend(ctx, (*v30.CreateFrontendParams)(params), m)
			},
			(*v32.CreateFrontendParams)(params),
			(*v31.CreateFrontendParams)(params),
			(*v30.CreateFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "frontend creation")
	}
}

// FrontendUpdate returns an executor for updating frontends.
func FrontendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Frontend, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Frontend, name string) error {
		params := &dataplaneapi.ReplaceFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.Frontend, _ *v32.ReplaceFrontendParams) (*http.Response, error) {
				return clientset.V32().ReplaceFrontend(ctx, n, (*v32.ReplaceFrontendParams)(params), m)
			},
			func(n string, m v31.Frontend, _ *v31.ReplaceFrontendParams) (*http.Response, error) {
				return clientset.V31().ReplaceFrontend(ctx, n, (*v31.ReplaceFrontendParams)(params), m)
			},
			func(n string, m v30.Frontend, _ *v30.ReplaceFrontendParams) (*http.Response, error) {
				return clientset.V30().ReplaceFrontend(ctx, n, (*v30.ReplaceFrontendParams)(params), m)
			},
			(*v32.ReplaceFrontendParams)(params),
			(*v31.ReplaceFrontendParams)(params),
			(*v30.ReplaceFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "frontend update")
	}
}

// FrontendDelete returns an executor for deleting frontends.
func FrontendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Frontend, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Frontend, name string) error {
		params := &dataplaneapi.DeleteFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteFrontendParams) (*http.Response, error) {
				return clientset.V32().DeleteFrontend(ctx, n, (*v32.DeleteFrontendParams)(params))
			},
			func(n string, _ *v31.DeleteFrontendParams) (*http.Response, error) {
				return clientset.V31().DeleteFrontend(ctx, n, (*v31.DeleteFrontendParams)(params))
			},
			func(n string, _ *v30.DeleteFrontendParams) (*http.Response, error) {
				return clientset.V30().DeleteFrontend(ctx, n, (*v30.DeleteFrontendParams)(params))
			},
			(*v32.DeleteFrontendParams)(params),
			(*v31.DeleteFrontendParams)(params),
			(*v30.DeleteFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "frontend deletion")
	}
}

// DefaultsCreate returns an executor for creating defaults sections.
func DefaultsCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Defaults, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Defaults, _ string) error {
		params := &dataplaneapi.CreateDefaultsSectionParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Defaults, _ *v32.CreateDefaultsSectionParams) (*http.Response, error) {
				return clientset.V32().CreateDefaultsSection(ctx, (*v32.CreateDefaultsSectionParams)(params), m)
			},
			func(m v31.Defaults, _ *v31.CreateDefaultsSectionParams) (*http.Response, error) {
				return clientset.V31().CreateDefaultsSection(ctx, (*v31.CreateDefaultsSectionParams)(params), m)
			},
			func(m v30.Defaults, _ *v30.CreateDefaultsSectionParams) (*http.Response, error) {
				return clientset.V30().CreateDefaultsSection(ctx, (*v30.CreateDefaultsSectionParams)(params), m)
			},
			(*v32.CreateDefaultsSectionParams)(params),
			(*v31.CreateDefaultsSectionParams)(params),
			(*v30.CreateDefaultsSectionParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "defaults creation")
	}
}

// DefaultsUpdate returns an executor for updating defaults sections.
func DefaultsUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Defaults, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Defaults, name string) error {
		params := &dataplaneapi.ReplaceDefaultsSectionParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.Defaults, _ *v32.ReplaceDefaultsSectionParams) (*http.Response, error) {
				return clientset.V32().ReplaceDefaultsSection(ctx, n, (*v32.ReplaceDefaultsSectionParams)(params), m)
			},
			func(n string, m v31.Defaults, _ *v31.ReplaceDefaultsSectionParams) (*http.Response, error) {
				return clientset.V31().ReplaceDefaultsSection(ctx, n, (*v31.ReplaceDefaultsSectionParams)(params), m)
			},
			func(n string, m v30.Defaults, _ *v30.ReplaceDefaultsSectionParams) (*http.Response, error) {
				return clientset.V30().ReplaceDefaultsSection(ctx, n, (*v30.ReplaceDefaultsSectionParams)(params), m)
			},
			(*v32.ReplaceDefaultsSectionParams)(params),
			(*v31.ReplaceDefaultsSectionParams)(params),
			(*v30.ReplaceDefaultsSectionParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "defaults update")
	}
}

// DefaultsDelete returns an executor for deleting defaults sections.
func DefaultsDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Defaults, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Defaults, name string) error {
		params := &dataplaneapi.DeleteDefaultsSectionParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteDefaultsSectionParams) (*http.Response, error) {
				return clientset.V32().DeleteDefaultsSection(ctx, n, (*v32.DeleteDefaultsSectionParams)(params))
			},
			func(n string, _ *v31.DeleteDefaultsSectionParams) (*http.Response, error) {
				return clientset.V31().DeleteDefaultsSection(ctx, n, (*v31.DeleteDefaultsSectionParams)(params))
			},
			func(n string, _ *v30.DeleteDefaultsSectionParams) (*http.Response, error) {
				return clientset.V30().DeleteDefaultsSection(ctx, n, (*v30.DeleteDefaultsSectionParams)(params))
			},
			(*v32.DeleteDefaultsSectionParams)(params),
			(*v31.DeleteDefaultsSectionParams)(params),
			(*v30.DeleteDefaultsSectionParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "defaults deletion")
	}
}

// =============================================================================
// Cache Executors
// =============================================================================

// CacheCreate returns an executor for creating cache sections.
func CacheCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Cache, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Cache, _ string) error {
		params := &dataplaneapi.CreateCacheParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Cache, _ *v32.CreateCacheParams) (*http.Response, error) {
				return clientset.V32().CreateCache(ctx, (*v32.CreateCacheParams)(params), m)
			},
			func(m v31.Cache, _ *v31.CreateCacheParams) (*http.Response, error) {
				return clientset.V31().CreateCache(ctx, (*v31.CreateCacheParams)(params), m)
			},
			func(m v30.Cache, _ *v30.CreateCacheParams) (*http.Response, error) {
				return clientset.V30().CreateCache(ctx, (*v30.CreateCacheParams)(params), m)
			},
			(*v32.CreateCacheParams)(params),
			(*v31.CreateCacheParams)(params),
			(*v30.CreateCacheParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "cache creation")
	}
}

// CacheUpdate returns an executor for updating cache sections.
func CacheUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Cache, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Cache, name string) error {
		params := &dataplaneapi.ReplaceCacheParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.Cache, _ *v32.ReplaceCacheParams) (*http.Response, error) {
				return clientset.V32().ReplaceCache(ctx, n, (*v32.ReplaceCacheParams)(params), m)
			},
			func(n string, m v31.Cache, _ *v31.ReplaceCacheParams) (*http.Response, error) {
				return clientset.V31().ReplaceCache(ctx, n, (*v31.ReplaceCacheParams)(params), m)
			},
			func(n string, m v30.Cache, _ *v30.ReplaceCacheParams) (*http.Response, error) {
				return clientset.V30().ReplaceCache(ctx, n, (*v30.ReplaceCacheParams)(params), m)
			},
			(*v32.ReplaceCacheParams)(params),
			(*v31.ReplaceCacheParams)(params),
			(*v30.ReplaceCacheParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "cache update")
	}
}

// CacheDelete returns an executor for deleting cache sections.
func CacheDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Cache, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Cache, name string) error {
		params := &dataplaneapi.DeleteCacheParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteCacheParams) (*http.Response, error) {
				return clientset.V32().DeleteCache(ctx, n, (*v32.DeleteCacheParams)(params))
			},
			func(n string, _ *v31.DeleteCacheParams) (*http.Response, error) {
				return clientset.V31().DeleteCache(ctx, n, (*v31.DeleteCacheParams)(params))
			},
			func(n string, _ *v30.DeleteCacheParams) (*http.Response, error) {
				return clientset.V30().DeleteCache(ctx, n, (*v30.DeleteCacheParams)(params))
			},
			(*v32.DeleteCacheParams)(params),
			(*v31.DeleteCacheParams)(params),
			(*v30.DeleteCacheParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "cache deletion")
	}
}

// =============================================================================
// HTTPErrorsSection Executors
// =============================================================================

// HTTPErrorsSectionCreate returns an executor for creating http-errors sections.
func HTTPErrorsSectionCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.HttpErrorsSection, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.HttpErrorsSection, _ string) error {
		params := &dataplaneapi.CreateHTTPErrorsSectionParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.HttpErrorsSection, _ *v32.CreateHTTPErrorsSectionParams) (*http.Response, error) {
				return clientset.V32().CreateHTTPErrorsSection(ctx, (*v32.CreateHTTPErrorsSectionParams)(params), m)
			},
			func(m v31.HttpErrorsSection, _ *v31.CreateHTTPErrorsSectionParams) (*http.Response, error) {
				return clientset.V31().CreateHTTPErrorsSection(ctx, (*v31.CreateHTTPErrorsSectionParams)(params), m)
			},
			func(m v30.HttpErrorsSection, _ *v30.CreateHTTPErrorsSectionParams) (*http.Response, error) {
				return clientset.V30().CreateHTTPErrorsSection(ctx, (*v30.CreateHTTPErrorsSectionParams)(params), m)
			},
			(*v32.CreateHTTPErrorsSectionParams)(params),
			(*v31.CreateHTTPErrorsSectionParams)(params),
			(*v30.CreateHTTPErrorsSectionParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "http-errors section creation")
	}
}

// HTTPErrorsSectionUpdate returns an executor for updating http-errors sections.
func HTTPErrorsSectionUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.HttpErrorsSection, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.HttpErrorsSection, name string) error {
		params := &dataplaneapi.ReplaceHTTPErrorsSectionParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.HttpErrorsSection, _ *v32.ReplaceHTTPErrorsSectionParams) (*http.Response, error) {
				return clientset.V32().ReplaceHTTPErrorsSection(ctx, n, (*v32.ReplaceHTTPErrorsSectionParams)(params), m)
			},
			func(n string, m v31.HttpErrorsSection, _ *v31.ReplaceHTTPErrorsSectionParams) (*http.Response, error) {
				return clientset.V31().ReplaceHTTPErrorsSection(ctx, n, (*v31.ReplaceHTTPErrorsSectionParams)(params), m)
			},
			func(n string, m v30.HttpErrorsSection, _ *v30.ReplaceHTTPErrorsSectionParams) (*http.Response, error) {
				return clientset.V30().ReplaceHTTPErrorsSection(ctx, n, (*v30.ReplaceHTTPErrorsSectionParams)(params), m)
			},
			(*v32.ReplaceHTTPErrorsSectionParams)(params),
			(*v31.ReplaceHTTPErrorsSectionParams)(params),
			(*v30.ReplaceHTTPErrorsSectionParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "http-errors section update")
	}
}

// HTTPErrorsSectionDelete returns an executor for deleting http-errors sections.
func HTTPErrorsSectionDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.HttpErrorsSection, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.HttpErrorsSection, name string) error {
		params := &dataplaneapi.DeleteHTTPErrorsSectionParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteHTTPErrorsSectionParams) (*http.Response, error) {
				return clientset.V32().DeleteHTTPErrorsSection(ctx, n, (*v32.DeleteHTTPErrorsSectionParams)(params))
			},
			func(n string, _ *v31.DeleteHTTPErrorsSectionParams) (*http.Response, error) {
				return clientset.V31().DeleteHTTPErrorsSection(ctx, n, (*v31.DeleteHTTPErrorsSectionParams)(params))
			},
			func(n string, _ *v30.DeleteHTTPErrorsSectionParams) (*http.Response, error) {
				return clientset.V30().DeleteHTTPErrorsSection(ctx, n, (*v30.DeleteHTTPErrorsSectionParams)(params))
			},
			(*v32.DeleteHTTPErrorsSectionParams)(params),
			(*v31.DeleteHTTPErrorsSectionParams)(params),
			(*v30.DeleteHTTPErrorsSectionParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "http-errors section deletion")
	}
}

// =============================================================================
// LogForward Executors
// =============================================================================

// LogForwardCreate returns an executor for creating log-forward sections.
func LogForwardCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.LogForward, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.LogForward, _ string) error {
		params := &dataplaneapi.CreateLogForwardParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.LogForward, _ *v32.CreateLogForwardParams) (*http.Response, error) {
				return clientset.V32().CreateLogForward(ctx, (*v32.CreateLogForwardParams)(params), m)
			},
			func(m v31.LogForward, _ *v31.CreateLogForwardParams) (*http.Response, error) {
				return clientset.V31().CreateLogForward(ctx, (*v31.CreateLogForwardParams)(params), m)
			},
			func(m v30.LogForward, _ *v30.CreateLogForwardParams) (*http.Response, error) {
				return clientset.V30().CreateLogForward(ctx, (*v30.CreateLogForwardParams)(params), m)
			},
			(*v32.CreateLogForwardParams)(params),
			(*v31.CreateLogForwardParams)(params),
			(*v30.CreateLogForwardParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "log-forward creation")
	}
}

// LogForwardUpdate returns an executor for updating log-forward sections.
func LogForwardUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.LogForward, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.LogForward, name string) error {
		params := &dataplaneapi.ReplaceLogForwardParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.LogForward, _ *v32.ReplaceLogForwardParams) (*http.Response, error) {
				return clientset.V32().ReplaceLogForward(ctx, n, (*v32.ReplaceLogForwardParams)(params), m)
			},
			func(n string, m v31.LogForward, _ *v31.ReplaceLogForwardParams) (*http.Response, error) {
				return clientset.V31().ReplaceLogForward(ctx, n, (*v31.ReplaceLogForwardParams)(params), m)
			},
			func(n string, m v30.LogForward, _ *v30.ReplaceLogForwardParams) (*http.Response, error) {
				return clientset.V30().ReplaceLogForward(ctx, n, (*v30.ReplaceLogForwardParams)(params), m)
			},
			(*v32.ReplaceLogForwardParams)(params),
			(*v31.ReplaceLogForwardParams)(params),
			(*v30.ReplaceLogForwardParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "log-forward update")
	}
}

// LogForwardDelete returns an executor for deleting log-forward sections.
func LogForwardDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.LogForward, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.LogForward, name string) error {
		params := &dataplaneapi.DeleteLogForwardParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteLogForwardParams) (*http.Response, error) {
				return clientset.V32().DeleteLogForward(ctx, n, (*v32.DeleteLogForwardParams)(params))
			},
			func(n string, _ *v31.DeleteLogForwardParams) (*http.Response, error) {
				return clientset.V31().DeleteLogForward(ctx, n, (*v31.DeleteLogForwardParams)(params))
			},
			func(n string, _ *v30.DeleteLogForwardParams) (*http.Response, error) {
				return clientset.V30().DeleteLogForward(ctx, n, (*v30.DeleteLogForwardParams)(params))
			},
			(*v32.DeleteLogForwardParams)(params),
			(*v31.DeleteLogForwardParams)(params),
			(*v30.DeleteLogForwardParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "log-forward deletion")
	}
}

// =============================================================================
// MailersSection Executors (no Update - API doesn't support it)
// =============================================================================

// MailersSectionCreate returns an executor for creating mailers sections.
func MailersSectionCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.MailersSection, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.MailersSection, _ string) error {
		params := &dataplaneapi.CreateMailersSectionParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.MailersSection, _ *v32.CreateMailersSectionParams) (*http.Response, error) {
				return clientset.V32().CreateMailersSection(ctx, (*v32.CreateMailersSectionParams)(params), m)
			},
			func(m v31.MailersSection, _ *v31.CreateMailersSectionParams) (*http.Response, error) {
				return clientset.V31().CreateMailersSection(ctx, (*v31.CreateMailersSectionParams)(params), m)
			},
			func(m v30.MailersSection, _ *v30.CreateMailersSectionParams) (*http.Response, error) {
				return clientset.V30().CreateMailersSection(ctx, (*v30.CreateMailersSectionParams)(params), m)
			},
			(*v32.CreateMailersSectionParams)(params),
			(*v31.CreateMailersSectionParams)(params),
			(*v30.CreateMailersSectionParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "mailers section creation")
	}
}

// MailersSectionUpdate returns an executor for updating mailers sections.
func MailersSectionUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.MailersSection, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.MailersSection, name string) error {
		params := &dataplaneapi.EditMailersSectionParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.MailersSection, _ *v32.EditMailersSectionParams) (*http.Response, error) {
				return clientset.V32().EditMailersSection(ctx, n, (*v32.EditMailersSectionParams)(params), m)
			},
			func(n string, m v31.MailersSection, _ *v31.EditMailersSectionParams) (*http.Response, error) {
				return clientset.V31().EditMailersSection(ctx, n, (*v31.EditMailersSectionParams)(params), m)
			},
			func(n string, m v30.MailersSection, _ *v30.EditMailersSectionParams) (*http.Response, error) {
				return clientset.V30().EditMailersSection(ctx, n, (*v30.EditMailersSectionParams)(params), m)
			},
			(*v32.EditMailersSectionParams)(params),
			(*v31.EditMailersSectionParams)(params),
			(*v30.EditMailersSectionParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "mailers section update")
	}
}

// MailersSectionDelete returns an executor for deleting mailers sections.
func MailersSectionDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.MailersSection, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.MailersSection, name string) error {
		params := &dataplaneapi.DeleteMailersSectionParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteMailersSectionParams) (*http.Response, error) {
				return clientset.V32().DeleteMailersSection(ctx, n, (*v32.DeleteMailersSectionParams)(params))
			},
			func(n string, _ *v31.DeleteMailersSectionParams) (*http.Response, error) {
				return clientset.V31().DeleteMailersSection(ctx, n, (*v31.DeleteMailersSectionParams)(params))
			},
			func(n string, _ *v30.DeleteMailersSectionParams) (*http.Response, error) {
				return clientset.V30().DeleteMailersSection(ctx, n, (*v30.DeleteMailersSectionParams)(params))
			},
			(*v32.DeleteMailersSectionParams)(params),
			(*v31.DeleteMailersSectionParams)(params),
			(*v30.DeleteMailersSectionParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "mailers section deletion")
	}
}

// =============================================================================
// PeerSection Executors (no Update - API doesn't support it)
// =============================================================================

// PeerSectionCreate returns an executor for creating peer sections.
func PeerSectionCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.PeerSection, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.PeerSection, _ string) error {
		params := &dataplaneapi.CreatePeerParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.PeerSection, _ *v32.CreatePeerParams) (*http.Response, error) {
				return clientset.V32().CreatePeer(ctx, (*v32.CreatePeerParams)(params), m)
			},
			func(m v31.PeerSection, _ *v31.CreatePeerParams) (*http.Response, error) {
				return clientset.V31().CreatePeer(ctx, (*v31.CreatePeerParams)(params), m)
			},
			func(m v30.PeerSection, _ *v30.CreatePeerParams) (*http.Response, error) {
				return clientset.V30().CreatePeer(ctx, (*v30.CreatePeerParams)(params), m)
			},
			(*v32.CreatePeerParams)(params),
			(*v31.CreatePeerParams)(params),
			(*v30.CreatePeerParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "peer section creation")
	}
}

// PeerSectionUpdate returns an executor for updating peer sections.
// Note: The HAProxy Dataplane API does not support updating peer sections directly.
func PeerSectionUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.PeerSection, name string) error {
	return func(_ context.Context, _ *client.DataplaneClient, _ string, _ *dataplaneapi.PeerSection, name string) error {
		return fmt.Errorf("peer section updates are not supported by HAProxy Dataplane API (section: %s)", name)
	}
}

// PeerSectionDelete returns an executor for deleting peer sections.
func PeerSectionDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.PeerSection, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.PeerSection, name string) error {
		params := &dataplaneapi.DeletePeerParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeletePeerParams) (*http.Response, error) {
				return clientset.V32().DeletePeer(ctx, n, (*v32.DeletePeerParams)(params))
			},
			func(n string, _ *v31.DeletePeerParams) (*http.Response, error) {
				return clientset.V31().DeletePeer(ctx, n, (*v31.DeletePeerParams)(params))
			},
			func(n string, _ *v30.DeletePeerParams) (*http.Response, error) {
				return clientset.V30().DeletePeer(ctx, n, (*v30.DeletePeerParams)(params))
			},
			(*v32.DeletePeerParams)(params),
			(*v31.DeletePeerParams)(params),
			(*v30.DeletePeerParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "peer section deletion")
	}
}

// =============================================================================
// Program Executors
// =============================================================================

// ProgramCreate returns an executor for creating program sections.
func ProgramCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Program, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Program, _ string) error {
		params := &dataplaneapi.CreateProgramParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Program, _ *v32.CreateProgramParams) (*http.Response, error) {
				return clientset.V32().CreateProgram(ctx, (*v32.CreateProgramParams)(params), m)
			},
			func(m v31.Program, _ *v31.CreateProgramParams) (*http.Response, error) {
				return clientset.V31().CreateProgram(ctx, (*v31.CreateProgramParams)(params), m)
			},
			func(m v30.Program, _ *v30.CreateProgramParams) (*http.Response, error) {
				return clientset.V30().CreateProgram(ctx, (*v30.CreateProgramParams)(params), m)
			},
			(*v32.CreateProgramParams)(params),
			(*v31.CreateProgramParams)(params),
			(*v30.CreateProgramParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "program creation")
	}
}

// ProgramUpdate returns an executor for updating program sections.
func ProgramUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Program, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Program, name string) error {
		params := &dataplaneapi.ReplaceProgramParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.Program, _ *v32.ReplaceProgramParams) (*http.Response, error) {
				return clientset.V32().ReplaceProgram(ctx, n, (*v32.ReplaceProgramParams)(params), m)
			},
			func(n string, m v31.Program, _ *v31.ReplaceProgramParams) (*http.Response, error) {
				return clientset.V31().ReplaceProgram(ctx, n, (*v31.ReplaceProgramParams)(params), m)
			},
			func(n string, m v30.Program, _ *v30.ReplaceProgramParams) (*http.Response, error) {
				return clientset.V30().ReplaceProgram(ctx, n, (*v30.ReplaceProgramParams)(params), m)
			},
			(*v32.ReplaceProgramParams)(params),
			(*v31.ReplaceProgramParams)(params),
			(*v30.ReplaceProgramParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "program update")
	}
}

// ProgramDelete returns an executor for deleting program sections.
func ProgramDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Program, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Program, name string) error {
		params := &dataplaneapi.DeleteProgramParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteProgramParams) (*http.Response, error) {
				return clientset.V32().DeleteProgram(ctx, n, (*v32.DeleteProgramParams)(params))
			},
			func(n string, _ *v31.DeleteProgramParams) (*http.Response, error) {
				return clientset.V31().DeleteProgram(ctx, n, (*v31.DeleteProgramParams)(params))
			},
			func(n string, _ *v30.DeleteProgramParams) (*http.Response, error) {
				return clientset.V30().DeleteProgram(ctx, n, (*v30.DeleteProgramParams)(params))
			},
			(*v32.DeleteProgramParams)(params),
			(*v31.DeleteProgramParams)(params),
			(*v30.DeleteProgramParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "program deletion")
	}
}

// =============================================================================
// Resolver Executors
// =============================================================================

// ResolverCreate returns an executor for creating resolver sections.
func ResolverCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Resolver, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Resolver, _ string) error {
		params := &dataplaneapi.CreateResolverParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Resolver, _ *v32.CreateResolverParams) (*http.Response, error) {
				return clientset.V32().CreateResolver(ctx, (*v32.CreateResolverParams)(params), m)
			},
			func(m v31.Resolver, _ *v31.CreateResolverParams) (*http.Response, error) {
				return clientset.V31().CreateResolver(ctx, (*v31.CreateResolverParams)(params), m)
			},
			func(m v30.Resolver, _ *v30.CreateResolverParams) (*http.Response, error) {
				return clientset.V30().CreateResolver(ctx, (*v30.CreateResolverParams)(params), m)
			},
			(*v32.CreateResolverParams)(params),
			(*v31.CreateResolverParams)(params),
			(*v30.CreateResolverParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "resolver creation")
	}
}

// ResolverUpdate returns an executor for updating resolver sections.
func ResolverUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Resolver, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Resolver, name string) error {
		params := &dataplaneapi.ReplaceResolverParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.Resolver, _ *v32.ReplaceResolverParams) (*http.Response, error) {
				return clientset.V32().ReplaceResolver(ctx, n, (*v32.ReplaceResolverParams)(params), m)
			},
			func(n string, m v31.Resolver, _ *v31.ReplaceResolverParams) (*http.Response, error) {
				return clientset.V31().ReplaceResolver(ctx, n, (*v31.ReplaceResolverParams)(params), m)
			},
			func(n string, m v30.Resolver, _ *v30.ReplaceResolverParams) (*http.Response, error) {
				return clientset.V30().ReplaceResolver(ctx, n, (*v30.ReplaceResolverParams)(params), m)
			},
			(*v32.ReplaceResolverParams)(params),
			(*v31.ReplaceResolverParams)(params),
			(*v30.ReplaceResolverParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "resolver update")
	}
}

// ResolverDelete returns an executor for deleting resolver sections.
func ResolverDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Resolver, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Resolver, name string) error {
		params := &dataplaneapi.DeleteResolverParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteResolverParams) (*http.Response, error) {
				return clientset.V32().DeleteResolver(ctx, n, (*v32.DeleteResolverParams)(params))
			},
			func(n string, _ *v31.DeleteResolverParams) (*http.Response, error) {
				return clientset.V31().DeleteResolver(ctx, n, (*v31.DeleteResolverParams)(params))
			},
			func(n string, _ *v30.DeleteResolverParams) (*http.Response, error) {
				return clientset.V30().DeleteResolver(ctx, n, (*v30.DeleteResolverParams)(params))
			},
			(*v32.DeleteResolverParams)(params),
			(*v31.DeleteResolverParams)(params),
			(*v30.DeleteResolverParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "resolver deletion")
	}
}

// =============================================================================
// Ring Executors
// =============================================================================

// RingCreate returns an executor for creating ring sections.
func RingCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Ring, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Ring, _ string) error {
		params := &dataplaneapi.CreateRingParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Ring, _ *v32.CreateRingParams) (*http.Response, error) {
				return clientset.V32().CreateRing(ctx, (*v32.CreateRingParams)(params), m)
			},
			func(m v31.Ring, _ *v31.CreateRingParams) (*http.Response, error) {
				return clientset.V31().CreateRing(ctx, (*v31.CreateRingParams)(params), m)
			},
			func(m v30.Ring, _ *v30.CreateRingParams) (*http.Response, error) {
				return clientset.V30().CreateRing(ctx, (*v30.CreateRingParams)(params), m)
			},
			(*v32.CreateRingParams)(params),
			(*v31.CreateRingParams)(params),
			(*v30.CreateRingParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "ring creation")
	}
}

// RingUpdate returns an executor for updating ring sections.
func RingUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Ring, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Ring, name string) error {
		params := &dataplaneapi.ReplaceRingParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.Ring, _ *v32.ReplaceRingParams) (*http.Response, error) {
				return clientset.V32().ReplaceRing(ctx, n, (*v32.ReplaceRingParams)(params), m)
			},
			func(n string, m v31.Ring, _ *v31.ReplaceRingParams) (*http.Response, error) {
				return clientset.V31().ReplaceRing(ctx, n, (*v31.ReplaceRingParams)(params), m)
			},
			func(n string, m v30.Ring, _ *v30.ReplaceRingParams) (*http.Response, error) {
				return clientset.V30().ReplaceRing(ctx, n, (*v30.ReplaceRingParams)(params), m)
			},
			(*v32.ReplaceRingParams)(params),
			(*v31.ReplaceRingParams)(params),
			(*v30.ReplaceRingParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "ring update")
	}
}

// RingDelete returns an executor for deleting ring sections.
func RingDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Ring, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Ring, name string) error {
		params := &dataplaneapi.DeleteRingParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteRingParams) (*http.Response, error) {
				return clientset.V32().DeleteRing(ctx, n, (*v32.DeleteRingParams)(params))
			},
			func(n string, _ *v31.DeleteRingParams) (*http.Response, error) {
				return clientset.V31().DeleteRing(ctx, n, (*v31.DeleteRingParams)(params))
			},
			func(n string, _ *v30.DeleteRingParams) (*http.Response, error) {
				return clientset.V30().DeleteRing(ctx, n, (*v30.DeleteRingParams)(params))
			},
			(*v32.DeleteRingParams)(params),
			(*v31.DeleteRingParams)(params),
			(*v30.DeleteRingParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "ring deletion")
	}
}

// =============================================================================
// CrtStore Executors
// =============================================================================

// CrtStoreCreate returns an executor for creating crt-store sections.
func CrtStoreCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.CrtStore, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.CrtStore, _ string) error {
		params := &dataplaneapi.CreateCrtStoreParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.CrtStore, _ *v32.CreateCrtStoreParams) (*http.Response, error) {
				return clientset.V32().CreateCrtStore(ctx, (*v32.CreateCrtStoreParams)(params), m)
			},
			func(m v31.CrtStore, _ *v31.CreateCrtStoreParams) (*http.Response, error) {
				return clientset.V31().CreateCrtStore(ctx, (*v31.CreateCrtStoreParams)(params), m)
			},
			func(m v30.CrtStore, _ *v30.CreateCrtStoreParams) (*http.Response, error) {
				return clientset.V30().CreateCrtStore(ctx, (*v30.CreateCrtStoreParams)(params), m)
			},
			(*v32.CreateCrtStoreParams)(params),
			(*v31.CreateCrtStoreParams)(params),
			(*v30.CreateCrtStoreParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "crt-store creation")
	}
}

// CrtStoreUpdate returns an executor for updating crt-store sections.
func CrtStoreUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.CrtStore, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.CrtStore, name string) error {
		params := &dataplaneapi.EditCrtStoreParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.CrtStore, _ *v32.EditCrtStoreParams) (*http.Response, error) {
				return clientset.V32().EditCrtStore(ctx, n, (*v32.EditCrtStoreParams)(params), m)
			},
			func(n string, m v31.CrtStore, _ *v31.EditCrtStoreParams) (*http.Response, error) {
				return clientset.V31().EditCrtStore(ctx, n, (*v31.EditCrtStoreParams)(params), m)
			},
			func(n string, m v30.CrtStore, _ *v30.EditCrtStoreParams) (*http.Response, error) {
				return clientset.V30().EditCrtStore(ctx, n, (*v30.EditCrtStoreParams)(params), m)
			},
			(*v32.EditCrtStoreParams)(params),
			(*v31.EditCrtStoreParams)(params),
			(*v30.EditCrtStoreParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "crt-store update")
	}
}

// CrtStoreDelete returns an executor for deleting crt-store sections.
func CrtStoreDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.CrtStore, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.CrtStore, name string) error {
		params := &dataplaneapi.DeleteCrtStoreParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteCrtStoreParams) (*http.Response, error) {
				return clientset.V32().DeleteCrtStore(ctx, n, (*v32.DeleteCrtStoreParams)(params))
			},
			func(n string, _ *v31.DeleteCrtStoreParams) (*http.Response, error) {
				return clientset.V31().DeleteCrtStore(ctx, n, (*v31.DeleteCrtStoreParams)(params))
			},
			func(n string, _ *v30.DeleteCrtStoreParams) (*http.Response, error) {
				return clientset.V30().DeleteCrtStore(ctx, n, (*v30.DeleteCrtStoreParams)(params))
			},
			(*v32.DeleteCrtStoreParams)(params),
			(*v31.DeleteCrtStoreParams)(params),
			(*v30.DeleteCrtStoreParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "crt-store deletion")
	}
}

// =============================================================================
// Userlist Executors (no Update - API doesn't support it)
// =============================================================================

// UserlistCreate returns an executor for creating userlist sections.
func UserlistCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Userlist, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Userlist, _ string) error {
		params := &dataplaneapi.CreateUserlistParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.Userlist, _ *v32.CreateUserlistParams) (*http.Response, error) {
				return clientset.V32().CreateUserlist(ctx, (*v32.CreateUserlistParams)(params), m)
			},
			func(m v31.Userlist, _ *v31.CreateUserlistParams) (*http.Response, error) {
				return clientset.V31().CreateUserlist(ctx, (*v31.CreateUserlistParams)(params), m)
			},
			func(m v30.Userlist, _ *v30.CreateUserlistParams) (*http.Response, error) {
				return clientset.V30().CreateUserlist(ctx, (*v30.CreateUserlistParams)(params), m)
			},
			(*v32.CreateUserlistParams)(params),
			(*v31.CreateUserlistParams)(params),
			(*v30.CreateUserlistParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "userlist creation")
	}
}

// UserlistDelete returns an executor for deleting userlist sections.
func UserlistDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Userlist, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.Userlist, name string) error {
		params := &dataplaneapi.DeleteUserlistParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteUserlistParams) (*http.Response, error) {
				return clientset.V32().DeleteUserlist(ctx, n, (*v32.DeleteUserlistParams)(params))
			},
			func(n string, _ *v31.DeleteUserlistParams) (*http.Response, error) {
				return clientset.V31().DeleteUserlist(ctx, n, (*v31.DeleteUserlistParams)(params))
			},
			func(n string, _ *v30.DeleteUserlistParams) (*http.Response, error) {
				return clientset.V30().DeleteUserlist(ctx, n, (*v30.DeleteUserlistParams)(params))
			},
			(*v32.DeleteUserlistParams)(params),
			(*v31.DeleteUserlistParams)(params),
			(*v30.DeleteUserlistParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "userlist deletion")
	}
}

// =============================================================================
// FCGI App Executors (Top-level section, full CRUD)
// =============================================================================

// FCGIAppCreate returns an executor for creating fcgi-app sections.
func FCGIAppCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.FCGIApp, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.FCGIApp, _ string) error {
		params := &dataplaneapi.CreateFCGIAppParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreate(ctx, c, model,
			func(m v32.FCGIApp, _ *v32.CreateFCGIAppParams) (*http.Response, error) {
				return clientset.V32().CreateFCGIApp(ctx, (*v32.CreateFCGIAppParams)(params), m)
			},
			func(m v31.FCGIApp, _ *v31.CreateFCGIAppParams) (*http.Response, error) {
				return clientset.V31().CreateFCGIApp(ctx, (*v31.CreateFCGIAppParams)(params), m)
			},
			func(m v30.FCGIApp, _ *v30.CreateFCGIAppParams) (*http.Response, error) {
				return clientset.V30().CreateFCGIApp(ctx, (*v30.CreateFCGIAppParams)(params), m)
			},
			(*v32.CreateFCGIAppParams)(params),
			(*v31.CreateFCGIAppParams)(params),
			(*v30.CreateFCGIAppParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "fcgi-app creation")
	}
}

// FCGIAppUpdate returns an executor for updating fcgi-app sections.
func FCGIAppUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.FCGIApp, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.FCGIApp, name string) error {
		params := &dataplaneapi.ReplaceFCGIAppParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchUpdate(ctx, c, name, model,
			func(n string, m v32.FCGIApp, _ *v32.ReplaceFCGIAppParams) (*http.Response, error) {
				return clientset.V32().ReplaceFCGIApp(ctx, n, (*v32.ReplaceFCGIAppParams)(params), m)
			},
			func(n string, m v31.FCGIApp, _ *v31.ReplaceFCGIAppParams) (*http.Response, error) {
				return clientset.V31().ReplaceFCGIApp(ctx, n, (*v31.ReplaceFCGIAppParams)(params), m)
			},
			func(n string, m v30.FCGIApp, _ *v30.ReplaceFCGIAppParams) (*http.Response, error) {
				return clientset.V30().ReplaceFCGIApp(ctx, n, (*v30.ReplaceFCGIAppParams)(params), m)
			},
			(*v32.ReplaceFCGIAppParams)(params),
			(*v31.ReplaceFCGIAppParams)(params),
			(*v30.ReplaceFCGIAppParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "fcgi-app update")
	}
}

// FCGIAppDelete returns an executor for deleting fcgi-app sections.
func FCGIAppDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.FCGIApp, name string) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, _ *dataplaneapi.FCGIApp, name string) error {
		params := &dataplaneapi.DeleteFCGIAppParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDelete(ctx, c, name,
			func(n string, _ *v32.DeleteFCGIAppParams) (*http.Response, error) {
				return clientset.V32().DeleteFCGIApp(ctx, n, (*v32.DeleteFCGIAppParams)(params))
			},
			func(n string, _ *v31.DeleteFCGIAppParams) (*http.Response, error) {
				return clientset.V31().DeleteFCGIApp(ctx, n, (*v31.DeleteFCGIAppParams)(params))
			},
			func(n string, _ *v30.DeleteFCGIAppParams) (*http.Response, error) {
				return clientset.V30().DeleteFCGIApp(ctx, n, (*v30.DeleteFCGIAppParams)(params))
			},
			(*v32.DeleteFCGIAppParams)(params),
			(*v31.DeleteFCGIAppParams)(params),
			(*v30.DeleteFCGIAppParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "fcgi-app deletion")
	}
}
