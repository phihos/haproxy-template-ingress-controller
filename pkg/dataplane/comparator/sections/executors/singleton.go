// Package executors provides pre-built executor functions for HAProxy configuration operations.
package executors

import (
	"context"
	"net/http"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
)

// =============================================================================
// Global Section Executor
// =============================================================================

// GlobalUpdate returns an executor for updating the global section.
// The global section is a singleton - it always exists and can only be updated.
func GlobalUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, model *models.Global) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, model *models.Global) error {
		clientset := c.Clientset()

		// Global uses DispatchUpdate with empty name since it's a singleton
		resp, err := client.DispatchUpdate(ctx, c, "", model,
			func(_ string, m v32.Global) (*http.Response, error) {
				params := &v32.ReplaceGlobalParams{TransactionId: &txID}
				return clientset.V32().ReplaceGlobal(ctx, params, m)
			},
			func(_ string, m v31.Global) (*http.Response, error) {
				params := &v31.ReplaceGlobalParams{TransactionId: &txID}
				return clientset.V31().ReplaceGlobal(ctx, params, m)
			},
			func(_ string, m v30.Global) (*http.Response, error) {
				params := &v30.ReplaceGlobalParams{TransactionId: &txID}
				return clientset.V30().ReplaceGlobal(ctx, params, m)
			},
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "global section update")
	}
}
