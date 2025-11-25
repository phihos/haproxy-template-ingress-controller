// Package executors provides pre-built executor functions for HAProxy configuration operations.
package executors

import (
	"context"
	"net/http"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
)

// =============================================================================
// Global Section Executor
// =============================================================================

// GlobalUpdate returns an executor for updating the global section.
// The global section is a singleton - it always exists and can only be updated.
func GlobalUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Global) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *dataplaneapi.Global) error {
		params := &dataplaneapi.ReplaceGlobalParams{TransactionId: &txID}
		clientset := c.Clientset()

		// Global uses DispatchUpdate with empty name since it's a singleton
		resp, err := client.DispatchUpdate(ctx, c, "", model,
			func(_ string, m v32.Global, _ *v32.ReplaceGlobalParams) (*http.Response, error) {
				return clientset.V32().ReplaceGlobal(ctx, (*v32.ReplaceGlobalParams)(params), m)
			},
			func(_ string, m v31.Global, _ *v31.ReplaceGlobalParams) (*http.Response, error) {
				return clientset.V31().ReplaceGlobal(ctx, (*v31.ReplaceGlobalParams)(params), m)
			},
			func(_ string, m v30.Global, _ *v30.ReplaceGlobalParams) (*http.Response, error) {
				return clientset.V30().ReplaceGlobal(ctx, (*v30.ReplaceGlobalParams)(params), m)
			},
			(*v32.ReplaceGlobalParams)(params),
			(*v31.ReplaceGlobalParams)(params),
			(*v30.ReplaceGlobalParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "global section update")
	}
}
