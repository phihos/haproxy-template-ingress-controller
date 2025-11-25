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
// ACL Executors (Frontend)
// =============================================================================

// ACLFrontendCreate returns an executor for creating ACLs in frontends.
func ACLFrontendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Acl) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Acl) error {
		params := &dataplaneapi.CreateAclFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Acl, _ *v32.CreateAclFrontendParams) (*http.Response, error) {
				return clientset.V32().CreateAclFrontend(ctx, p, idx, (*v32.CreateAclFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.Acl, _ *v31.CreateAclFrontendParams) (*http.Response, error) {
				return clientset.V31().CreateAclFrontend(ctx, p, idx, (*v31.CreateAclFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.Acl, _ *v30.CreateAclFrontendParams) (*http.Response, error) {
				return clientset.V30().CreateAclFrontend(ctx, p, idx, (*v30.CreateAclFrontendParams)(params), m)
			},
			(*v32.CreateAclFrontendParams)(params),
			(*v31.CreateAclFrontendParams)(params),
			(*v30.CreateAclFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "ACL creation in frontend")
	}
}

// ACLFrontendUpdate returns an executor for updating ACLs in frontends.
func ACLFrontendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Acl) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Acl) error {
		params := &dataplaneapi.ReplaceAclFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Acl, _ *v32.ReplaceAclFrontendParams) (*http.Response, error) {
				return clientset.V32().ReplaceAclFrontend(ctx, p, idx, (*v32.ReplaceAclFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.Acl, _ *v31.ReplaceAclFrontendParams) (*http.Response, error) {
				return clientset.V31().ReplaceAclFrontend(ctx, p, idx, (*v31.ReplaceAclFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.Acl, _ *v30.ReplaceAclFrontendParams) (*http.Response, error) {
				return clientset.V30().ReplaceAclFrontend(ctx, p, idx, (*v30.ReplaceAclFrontendParams)(params), m)
			},
			(*v32.ReplaceAclFrontendParams)(params),
			(*v31.ReplaceAclFrontendParams)(params),
			(*v30.ReplaceAclFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "ACL update in frontend")
	}
}

// ACLFrontendDelete returns an executor for deleting ACLs from frontends.
func ACLFrontendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Acl) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Acl) error {
		params := &dataplaneapi.DeleteAclFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteAclFrontendParams) (*http.Response, error) {
				return clientset.V32().DeleteAclFrontend(ctx, p, idx, (*v32.DeleteAclFrontendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteAclFrontendParams) (*http.Response, error) {
				return clientset.V31().DeleteAclFrontend(ctx, p, idx, (*v31.DeleteAclFrontendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteAclFrontendParams) (*http.Response, error) {
				return clientset.V30().DeleteAclFrontend(ctx, p, idx, (*v30.DeleteAclFrontendParams)(params))
			},
			(*v32.DeleteAclFrontendParams)(params),
			(*v31.DeleteAclFrontendParams)(params),
			(*v30.DeleteAclFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "ACL deletion from frontend")
	}
}

// =============================================================================
// ACL Executors (Backend)
// =============================================================================

// ACLBackendCreate returns an executor for creating ACLs in backends.
func ACLBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Acl) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Acl) error {
		params := &dataplaneapi.CreateAclBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Acl, _ *v32.CreateAclBackendParams) (*http.Response, error) {
				return clientset.V32().CreateAclBackend(ctx, p, idx, (*v32.CreateAclBackendParams)(params), m)
			},
			func(p string, idx int, m v31.Acl, _ *v31.CreateAclBackendParams) (*http.Response, error) {
				return clientset.V31().CreateAclBackend(ctx, p, idx, (*v31.CreateAclBackendParams)(params), m)
			},
			func(p string, idx int, m v30.Acl, _ *v30.CreateAclBackendParams) (*http.Response, error) {
				return clientset.V30().CreateAclBackend(ctx, p, idx, (*v30.CreateAclBackendParams)(params), m)
			},
			(*v32.CreateAclBackendParams)(params),
			(*v31.CreateAclBackendParams)(params),
			(*v30.CreateAclBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "ACL creation in backend")
	}
}

// ACLBackendUpdate returns an executor for updating ACLs in backends.
func ACLBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Acl) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Acl) error {
		params := &dataplaneapi.ReplaceAclBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Acl, _ *v32.ReplaceAclBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceAclBackend(ctx, p, idx, (*v32.ReplaceAclBackendParams)(params), m)
			},
			func(p string, idx int, m v31.Acl, _ *v31.ReplaceAclBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceAclBackend(ctx, p, idx, (*v31.ReplaceAclBackendParams)(params), m)
			},
			func(p string, idx int, m v30.Acl, _ *v30.ReplaceAclBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceAclBackend(ctx, p, idx, (*v30.ReplaceAclBackendParams)(params), m)
			},
			(*v32.ReplaceAclBackendParams)(params),
			(*v31.ReplaceAclBackendParams)(params),
			(*v30.ReplaceAclBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "ACL update in backend")
	}
}

// ACLBackendDelete returns an executor for deleting ACLs from backends.
func ACLBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Acl) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Acl) error {
		params := &dataplaneapi.DeleteAclBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteAclBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteAclBackend(ctx, p, idx, (*v32.DeleteAclBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteAclBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteAclBackend(ctx, p, idx, (*v31.DeleteAclBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteAclBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteAclBackend(ctx, p, idx, (*v30.DeleteAclBackendParams)(params))
			},
			(*v32.DeleteAclBackendParams)(params),
			(*v31.DeleteAclBackendParams)(params),
			(*v30.DeleteAclBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "ACL deletion from backend")
	}
}

// =============================================================================
// HTTP Request Rule Executors (Frontend)
// =============================================================================

// HTTPRequestRuleFrontendCreate returns an executor for creating HTTP request rules in frontends.
func HTTPRequestRuleFrontendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpRequestRule) error {
		params := &dataplaneapi.CreateHTTPRequestRuleFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpRequestRule, _ *v32.CreateHTTPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V32().CreateHTTPRequestRuleFrontend(ctx, p, idx, (*v32.CreateHTTPRequestRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpRequestRule, _ *v31.CreateHTTPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V31().CreateHTTPRequestRuleFrontend(ctx, p, idx, (*v31.CreateHTTPRequestRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpRequestRule, _ *v30.CreateHTTPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V30().CreateHTTPRequestRuleFrontend(ctx, p, idx, (*v30.CreateHTTPRequestRuleFrontendParams)(params), m)
			},
			(*v32.CreateHTTPRequestRuleFrontendParams)(params),
			(*v31.CreateHTTPRequestRuleFrontendParams)(params),
			(*v30.CreateHTTPRequestRuleFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP request rule creation in frontend")
	}
}

// HTTPRequestRuleFrontendUpdate returns an executor for updating HTTP request rules in frontends.
func HTTPRequestRuleFrontendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpRequestRule) error {
		params := &dataplaneapi.ReplaceHTTPRequestRuleFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpRequestRule, _ *v32.ReplaceHTTPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V32().ReplaceHTTPRequestRuleFrontend(ctx, p, idx, (*v32.ReplaceHTTPRequestRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpRequestRule, _ *v31.ReplaceHTTPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V31().ReplaceHTTPRequestRuleFrontend(ctx, p, idx, (*v31.ReplaceHTTPRequestRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpRequestRule, _ *v30.ReplaceHTTPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V30().ReplaceHTTPRequestRuleFrontend(ctx, p, idx, (*v30.ReplaceHTTPRequestRuleFrontendParams)(params), m)
			},
			(*v32.ReplaceHTTPRequestRuleFrontendParams)(params),
			(*v31.ReplaceHTTPRequestRuleFrontendParams)(params),
			(*v30.ReplaceHTTPRequestRuleFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP request rule update in frontend")
	}
}

// HTTPRequestRuleFrontendDelete returns an executor for deleting HTTP request rules from frontends.
func HTTPRequestRuleFrontendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpRequestRule) error {
		params := &dataplaneapi.DeleteHTTPRequestRuleFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteHTTPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V32().DeleteHTTPRequestRuleFrontend(ctx, p, idx, (*v32.DeleteHTTPRequestRuleFrontendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteHTTPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V31().DeleteHTTPRequestRuleFrontend(ctx, p, idx, (*v31.DeleteHTTPRequestRuleFrontendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteHTTPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V30().DeleteHTTPRequestRuleFrontend(ctx, p, idx, (*v30.DeleteHTTPRequestRuleFrontendParams)(params))
			},
			(*v32.DeleteHTTPRequestRuleFrontendParams)(params),
			(*v31.DeleteHTTPRequestRuleFrontendParams)(params),
			(*v30.DeleteHTTPRequestRuleFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP request rule deletion from frontend")
	}
}

// =============================================================================
// HTTP Request Rule Executors (Backend)
// =============================================================================

// HTTPRequestRuleBackendCreate returns an executor for creating HTTP request rules in backends.
func HTTPRequestRuleBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpRequestRule) error {
		params := &dataplaneapi.CreateHTTPRequestRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpRequestRule, _ *v32.CreateHTTPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V32().CreateHTTPRequestRuleBackend(ctx, p, idx, (*v32.CreateHTTPRequestRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpRequestRule, _ *v31.CreateHTTPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V31().CreateHTTPRequestRuleBackend(ctx, p, idx, (*v31.CreateHTTPRequestRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpRequestRule, _ *v30.CreateHTTPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V30().CreateHTTPRequestRuleBackend(ctx, p, idx, (*v30.CreateHTTPRequestRuleBackendParams)(params), m)
			},
			(*v32.CreateHTTPRequestRuleBackendParams)(params),
			(*v31.CreateHTTPRequestRuleBackendParams)(params),
			(*v30.CreateHTTPRequestRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP request rule creation in backend")
	}
}

// HTTPRequestRuleBackendUpdate returns an executor for updating HTTP request rules in backends.
func HTTPRequestRuleBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpRequestRule) error {
		params := &dataplaneapi.ReplaceHTTPRequestRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpRequestRule, _ *v32.ReplaceHTTPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceHTTPRequestRuleBackend(ctx, p, idx, (*v32.ReplaceHTTPRequestRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpRequestRule, _ *v31.ReplaceHTTPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceHTTPRequestRuleBackend(ctx, p, idx, (*v31.ReplaceHTTPRequestRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpRequestRule, _ *v30.ReplaceHTTPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceHTTPRequestRuleBackend(ctx, p, idx, (*v30.ReplaceHTTPRequestRuleBackendParams)(params), m)
			},
			(*v32.ReplaceHTTPRequestRuleBackendParams)(params),
			(*v31.ReplaceHTTPRequestRuleBackendParams)(params),
			(*v30.ReplaceHTTPRequestRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP request rule update in backend")
	}
}

// HTTPRequestRuleBackendDelete returns an executor for deleting HTTP request rules from backends.
func HTTPRequestRuleBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpRequestRule) error {
		params := &dataplaneapi.DeleteHTTPRequestRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteHTTPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteHTTPRequestRuleBackend(ctx, p, idx, (*v32.DeleteHTTPRequestRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteHTTPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteHTTPRequestRuleBackend(ctx, p, idx, (*v31.DeleteHTTPRequestRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteHTTPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteHTTPRequestRuleBackend(ctx, p, idx, (*v30.DeleteHTTPRequestRuleBackendParams)(params))
			},
			(*v32.DeleteHTTPRequestRuleBackendParams)(params),
			(*v31.DeleteHTTPRequestRuleBackendParams)(params),
			(*v30.DeleteHTTPRequestRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP request rule deletion from backend")
	}
}

// =============================================================================
// HTTP Response Rule Executors (Frontend)
// =============================================================================

// HTTPResponseRuleFrontendCreate returns an executor for creating HTTP response rules in frontends.
func HTTPResponseRuleFrontendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpResponseRule) error {
		params := &dataplaneapi.CreateHTTPResponseRuleFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpResponseRule, _ *v32.CreateHTTPResponseRuleFrontendParams) (*http.Response, error) {
				return clientset.V32().CreateHTTPResponseRuleFrontend(ctx, p, idx, (*v32.CreateHTTPResponseRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpResponseRule, _ *v31.CreateHTTPResponseRuleFrontendParams) (*http.Response, error) {
				return clientset.V31().CreateHTTPResponseRuleFrontend(ctx, p, idx, (*v31.CreateHTTPResponseRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpResponseRule, _ *v30.CreateHTTPResponseRuleFrontendParams) (*http.Response, error) {
				return clientset.V30().CreateHTTPResponseRuleFrontend(ctx, p, idx, (*v30.CreateHTTPResponseRuleFrontendParams)(params), m)
			},
			(*v32.CreateHTTPResponseRuleFrontendParams)(params),
			(*v31.CreateHTTPResponseRuleFrontendParams)(params),
			(*v30.CreateHTTPResponseRuleFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP response rule creation in frontend")
	}
}

// HTTPResponseRuleFrontendUpdate returns an executor for updating HTTP response rules in frontends.
func HTTPResponseRuleFrontendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpResponseRule) error {
		params := &dataplaneapi.ReplaceHTTPResponseRuleFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpResponseRule, _ *v32.ReplaceHTTPResponseRuleFrontendParams) (*http.Response, error) {
				return clientset.V32().ReplaceHTTPResponseRuleFrontend(ctx, p, idx, (*v32.ReplaceHTTPResponseRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpResponseRule, _ *v31.ReplaceHTTPResponseRuleFrontendParams) (*http.Response, error) {
				return clientset.V31().ReplaceHTTPResponseRuleFrontend(ctx, p, idx, (*v31.ReplaceHTTPResponseRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpResponseRule, _ *v30.ReplaceHTTPResponseRuleFrontendParams) (*http.Response, error) {
				return clientset.V30().ReplaceHTTPResponseRuleFrontend(ctx, p, idx, (*v30.ReplaceHTTPResponseRuleFrontendParams)(params), m)
			},
			(*v32.ReplaceHTTPResponseRuleFrontendParams)(params),
			(*v31.ReplaceHTTPResponseRuleFrontendParams)(params),
			(*v30.ReplaceHTTPResponseRuleFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP response rule update in frontend")
	}
}

// HTTPResponseRuleFrontendDelete returns an executor for deleting HTTP response rules from frontends.
func HTTPResponseRuleFrontendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpResponseRule) error {
		params := &dataplaneapi.DeleteHTTPResponseRuleFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteHTTPResponseRuleFrontendParams) (*http.Response, error) {
				return clientset.V32().DeleteHTTPResponseRuleFrontend(ctx, p, idx, (*v32.DeleteHTTPResponseRuleFrontendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteHTTPResponseRuleFrontendParams) (*http.Response, error) {
				return clientset.V31().DeleteHTTPResponseRuleFrontend(ctx, p, idx, (*v31.DeleteHTTPResponseRuleFrontendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteHTTPResponseRuleFrontendParams) (*http.Response, error) {
				return clientset.V30().DeleteHTTPResponseRuleFrontend(ctx, p, idx, (*v30.DeleteHTTPResponseRuleFrontendParams)(params))
			},
			(*v32.DeleteHTTPResponseRuleFrontendParams)(params),
			(*v31.DeleteHTTPResponseRuleFrontendParams)(params),
			(*v30.DeleteHTTPResponseRuleFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP response rule deletion from frontend")
	}
}

// =============================================================================
// HTTP Response Rule Executors (Backend)
// =============================================================================

// HTTPResponseRuleBackendCreate returns an executor for creating HTTP response rules in backends.
func HTTPResponseRuleBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpResponseRule) error {
		params := &dataplaneapi.CreateHTTPResponseRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpResponseRule, _ *v32.CreateHTTPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V32().CreateHTTPResponseRuleBackend(ctx, p, idx, (*v32.CreateHTTPResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpResponseRule, _ *v31.CreateHTTPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V31().CreateHTTPResponseRuleBackend(ctx, p, idx, (*v31.CreateHTTPResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpResponseRule, _ *v30.CreateHTTPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V30().CreateHTTPResponseRuleBackend(ctx, p, idx, (*v30.CreateHTTPResponseRuleBackendParams)(params), m)
			},
			(*v32.CreateHTTPResponseRuleBackendParams)(params),
			(*v31.CreateHTTPResponseRuleBackendParams)(params),
			(*v30.CreateHTTPResponseRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP response rule creation in backend")
	}
}

// HTTPResponseRuleBackendUpdate returns an executor for updating HTTP response rules in backends.
func HTTPResponseRuleBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpResponseRule) error {
		params := &dataplaneapi.ReplaceHTTPResponseRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpResponseRule, _ *v32.ReplaceHTTPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceHTTPResponseRuleBackend(ctx, p, idx, (*v32.ReplaceHTTPResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpResponseRule, _ *v31.ReplaceHTTPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceHTTPResponseRuleBackend(ctx, p, idx, (*v31.ReplaceHTTPResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpResponseRule, _ *v30.ReplaceHTTPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceHTTPResponseRuleBackend(ctx, p, idx, (*v30.ReplaceHTTPResponseRuleBackendParams)(params), m)
			},
			(*v32.ReplaceHTTPResponseRuleBackendParams)(params),
			(*v31.ReplaceHTTPResponseRuleBackendParams)(params),
			(*v30.ReplaceHTTPResponseRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP response rule update in backend")
	}
}

// HTTPResponseRuleBackendDelete returns an executor for deleting HTTP response rules from backends.
func HTTPResponseRuleBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpResponseRule) error {
		params := &dataplaneapi.DeleteHTTPResponseRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteHTTPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteHTTPResponseRuleBackend(ctx, p, idx, (*v32.DeleteHTTPResponseRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteHTTPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteHTTPResponseRuleBackend(ctx, p, idx, (*v31.DeleteHTTPResponseRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteHTTPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteHTTPResponseRuleBackend(ctx, p, idx, (*v30.DeleteHTTPResponseRuleBackendParams)(params))
			},
			(*v32.DeleteHTTPResponseRuleBackendParams)(params),
			(*v31.DeleteHTTPResponseRuleBackendParams)(params),
			(*v30.DeleteHTTPResponseRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP response rule deletion from backend")
	}
}

// =============================================================================
// Backend Switching Rule Executors
// =============================================================================

// BackendSwitchingRuleCreate returns an executor for creating backend switching rules.
func BackendSwitchingRuleCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.BackendSwitchingRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.BackendSwitchingRule) error {
		params := &dataplaneapi.CreateBackendSwitchingRuleParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.BackendSwitchingRule, _ *v32.CreateBackendSwitchingRuleParams) (*http.Response, error) {
				return clientset.V32().CreateBackendSwitchingRule(ctx, p, idx, (*v32.CreateBackendSwitchingRuleParams)(params), m)
			},
			func(p string, idx int, m v31.BackendSwitchingRule, _ *v31.CreateBackendSwitchingRuleParams) (*http.Response, error) {
				return clientset.V31().CreateBackendSwitchingRule(ctx, p, idx, (*v31.CreateBackendSwitchingRuleParams)(params), m)
			},
			func(p string, idx int, m v30.BackendSwitchingRule, _ *v30.CreateBackendSwitchingRuleParams) (*http.Response, error) {
				return clientset.V30().CreateBackendSwitchingRule(ctx, p, idx, (*v30.CreateBackendSwitchingRuleParams)(params), m)
			},
			(*v32.CreateBackendSwitchingRuleParams)(params),
			(*v31.CreateBackendSwitchingRuleParams)(params),
			(*v30.CreateBackendSwitchingRuleParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "backend switching rule creation")
	}
}

// BackendSwitchingRuleUpdate returns an executor for updating backend switching rules.
func BackendSwitchingRuleUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.BackendSwitchingRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.BackendSwitchingRule) error {
		params := &dataplaneapi.ReplaceBackendSwitchingRuleParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.BackendSwitchingRule, _ *v32.ReplaceBackendSwitchingRuleParams) (*http.Response, error) {
				return clientset.V32().ReplaceBackendSwitchingRule(ctx, p, idx, (*v32.ReplaceBackendSwitchingRuleParams)(params), m)
			},
			func(p string, idx int, m v31.BackendSwitchingRule, _ *v31.ReplaceBackendSwitchingRuleParams) (*http.Response, error) {
				return clientset.V31().ReplaceBackendSwitchingRule(ctx, p, idx, (*v31.ReplaceBackendSwitchingRuleParams)(params), m)
			},
			func(p string, idx int, m v30.BackendSwitchingRule, _ *v30.ReplaceBackendSwitchingRuleParams) (*http.Response, error) {
				return clientset.V30().ReplaceBackendSwitchingRule(ctx, p, idx, (*v30.ReplaceBackendSwitchingRuleParams)(params), m)
			},
			(*v32.ReplaceBackendSwitchingRuleParams)(params),
			(*v31.ReplaceBackendSwitchingRuleParams)(params),
			(*v30.ReplaceBackendSwitchingRuleParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "backend switching rule update")
	}
}

// BackendSwitchingRuleDelete returns an executor for deleting backend switching rules.
func BackendSwitchingRuleDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.BackendSwitchingRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.BackendSwitchingRule) error {
		params := &dataplaneapi.DeleteBackendSwitchingRuleParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteBackendSwitchingRuleParams) (*http.Response, error) {
				return clientset.V32().DeleteBackendSwitchingRule(ctx, p, idx, (*v32.DeleteBackendSwitchingRuleParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteBackendSwitchingRuleParams) (*http.Response, error) {
				return clientset.V31().DeleteBackendSwitchingRule(ctx, p, idx, (*v31.DeleteBackendSwitchingRuleParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteBackendSwitchingRuleParams) (*http.Response, error) {
				return clientset.V30().DeleteBackendSwitchingRule(ctx, p, idx, (*v30.DeleteBackendSwitchingRuleParams)(params))
			},
			(*v32.DeleteBackendSwitchingRuleParams)(params),
			(*v31.DeleteBackendSwitchingRuleParams)(params),
			(*v30.DeleteBackendSwitchingRuleParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "backend switching rule deletion")
	}
}

// =============================================================================
// Filter Executors (Frontend)
// =============================================================================

// FilterFrontendCreate returns an executor for creating filters in frontends.
func FilterFrontendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Filter) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Filter) error {
		params := &dataplaneapi.CreateFilterFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Filter, _ *v32.CreateFilterFrontendParams) (*http.Response, error) {
				return clientset.V32().CreateFilterFrontend(ctx, p, idx, (*v32.CreateFilterFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.Filter, _ *v31.CreateFilterFrontendParams) (*http.Response, error) {
				return clientset.V31().CreateFilterFrontend(ctx, p, idx, (*v31.CreateFilterFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.Filter, _ *v30.CreateFilterFrontendParams) (*http.Response, error) {
				return clientset.V30().CreateFilterFrontend(ctx, p, idx, (*v30.CreateFilterFrontendParams)(params), m)
			},
			(*v32.CreateFilterFrontendParams)(params),
			(*v31.CreateFilterFrontendParams)(params),
			(*v30.CreateFilterFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "filter creation in frontend")
	}
}

// FilterFrontendUpdate returns an executor for updating filters in frontends.
func FilterFrontendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Filter) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Filter) error {
		params := &dataplaneapi.ReplaceFilterFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Filter, _ *v32.ReplaceFilterFrontendParams) (*http.Response, error) {
				return clientset.V32().ReplaceFilterFrontend(ctx, p, idx, (*v32.ReplaceFilterFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.Filter, _ *v31.ReplaceFilterFrontendParams) (*http.Response, error) {
				return clientset.V31().ReplaceFilterFrontend(ctx, p, idx, (*v31.ReplaceFilterFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.Filter, _ *v30.ReplaceFilterFrontendParams) (*http.Response, error) {
				return clientset.V30().ReplaceFilterFrontend(ctx, p, idx, (*v30.ReplaceFilterFrontendParams)(params), m)
			},
			(*v32.ReplaceFilterFrontendParams)(params),
			(*v31.ReplaceFilterFrontendParams)(params),
			(*v30.ReplaceFilterFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "filter update in frontend")
	}
}

// FilterFrontendDelete returns an executor for deleting filters from frontends.
func FilterFrontendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Filter) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Filter) error {
		params := &dataplaneapi.DeleteFilterFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteFilterFrontendParams) (*http.Response, error) {
				return clientset.V32().DeleteFilterFrontend(ctx, p, idx, (*v32.DeleteFilterFrontendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteFilterFrontendParams) (*http.Response, error) {
				return clientset.V31().DeleteFilterFrontend(ctx, p, idx, (*v31.DeleteFilterFrontendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteFilterFrontendParams) (*http.Response, error) {
				return clientset.V30().DeleteFilterFrontend(ctx, p, idx, (*v30.DeleteFilterFrontendParams)(params))
			},
			(*v32.DeleteFilterFrontendParams)(params),
			(*v31.DeleteFilterFrontendParams)(params),
			(*v30.DeleteFilterFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "filter deletion from frontend")
	}
}

// =============================================================================
// Filter Executors (Backend)
// =============================================================================

// FilterBackendCreate returns an executor for creating filters in backends.
func FilterBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Filter) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Filter) error {
		params := &dataplaneapi.CreateFilterBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Filter, _ *v32.CreateFilterBackendParams) (*http.Response, error) {
				return clientset.V32().CreateFilterBackend(ctx, p, idx, (*v32.CreateFilterBackendParams)(params), m)
			},
			func(p string, idx int, m v31.Filter, _ *v31.CreateFilterBackendParams) (*http.Response, error) {
				return clientset.V31().CreateFilterBackend(ctx, p, idx, (*v31.CreateFilterBackendParams)(params), m)
			},
			func(p string, idx int, m v30.Filter, _ *v30.CreateFilterBackendParams) (*http.Response, error) {
				return clientset.V30().CreateFilterBackend(ctx, p, idx, (*v30.CreateFilterBackendParams)(params), m)
			},
			(*v32.CreateFilterBackendParams)(params),
			(*v31.CreateFilterBackendParams)(params),
			(*v30.CreateFilterBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "filter creation in backend")
	}
}

// FilterBackendUpdate returns an executor for updating filters in backends.
func FilterBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Filter) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Filter) error {
		params := &dataplaneapi.ReplaceFilterBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Filter, _ *v32.ReplaceFilterBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceFilterBackend(ctx, p, idx, (*v32.ReplaceFilterBackendParams)(params), m)
			},
			func(p string, idx int, m v31.Filter, _ *v31.ReplaceFilterBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceFilterBackend(ctx, p, idx, (*v31.ReplaceFilterBackendParams)(params), m)
			},
			func(p string, idx int, m v30.Filter, _ *v30.ReplaceFilterBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceFilterBackend(ctx, p, idx, (*v30.ReplaceFilterBackendParams)(params), m)
			},
			(*v32.ReplaceFilterBackendParams)(params),
			(*v31.ReplaceFilterBackendParams)(params),
			(*v30.ReplaceFilterBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "filter update in backend")
	}
}

// FilterBackendDelete returns an executor for deleting filters from backends.
func FilterBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Filter) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Filter) error {
		params := &dataplaneapi.DeleteFilterBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteFilterBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteFilterBackend(ctx, p, idx, (*v32.DeleteFilterBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteFilterBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteFilterBackend(ctx, p, idx, (*v31.DeleteFilterBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteFilterBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteFilterBackend(ctx, p, idx, (*v30.DeleteFilterBackendParams)(params))
			},
			(*v32.DeleteFilterBackendParams)(params),
			(*v31.DeleteFilterBackendParams)(params),
			(*v30.DeleteFilterBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "filter deletion from backend")
	}
}

// =============================================================================
// Log Target Executors (Frontend)
// =============================================================================

// LogTargetFrontendCreate returns an executor for creating log targets in frontends.
func LogTargetFrontendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.LogTarget) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.LogTarget) error {
		params := &dataplaneapi.CreateLogTargetFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.LogTarget, _ *v32.CreateLogTargetFrontendParams) (*http.Response, error) {
				return clientset.V32().CreateLogTargetFrontend(ctx, p, idx, (*v32.CreateLogTargetFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.LogTarget, _ *v31.CreateLogTargetFrontendParams) (*http.Response, error) {
				return clientset.V31().CreateLogTargetFrontend(ctx, p, idx, (*v31.CreateLogTargetFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.LogTarget, _ *v30.CreateLogTargetFrontendParams) (*http.Response, error) {
				return clientset.V30().CreateLogTargetFrontend(ctx, p, idx, (*v30.CreateLogTargetFrontendParams)(params), m)
			},
			(*v32.CreateLogTargetFrontendParams)(params),
			(*v31.CreateLogTargetFrontendParams)(params),
			(*v30.CreateLogTargetFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "log target creation in frontend")
	}
}

// LogTargetFrontendUpdate returns an executor for updating log targets in frontends.
func LogTargetFrontendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.LogTarget) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.LogTarget) error {
		params := &dataplaneapi.ReplaceLogTargetFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.LogTarget, _ *v32.ReplaceLogTargetFrontendParams) (*http.Response, error) {
				return clientset.V32().ReplaceLogTargetFrontend(ctx, p, idx, (*v32.ReplaceLogTargetFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.LogTarget, _ *v31.ReplaceLogTargetFrontendParams) (*http.Response, error) {
				return clientset.V31().ReplaceLogTargetFrontend(ctx, p, idx, (*v31.ReplaceLogTargetFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.LogTarget, _ *v30.ReplaceLogTargetFrontendParams) (*http.Response, error) {
				return clientset.V30().ReplaceLogTargetFrontend(ctx, p, idx, (*v30.ReplaceLogTargetFrontendParams)(params), m)
			},
			(*v32.ReplaceLogTargetFrontendParams)(params),
			(*v31.ReplaceLogTargetFrontendParams)(params),
			(*v30.ReplaceLogTargetFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "log target update in frontend")
	}
}

// LogTargetFrontendDelete returns an executor for deleting log targets from frontends.
func LogTargetFrontendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.LogTarget) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.LogTarget) error {
		params := &dataplaneapi.DeleteLogTargetFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteLogTargetFrontendParams) (*http.Response, error) {
				return clientset.V32().DeleteLogTargetFrontend(ctx, p, idx, (*v32.DeleteLogTargetFrontendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteLogTargetFrontendParams) (*http.Response, error) {
				return clientset.V31().DeleteLogTargetFrontend(ctx, p, idx, (*v31.DeleteLogTargetFrontendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteLogTargetFrontendParams) (*http.Response, error) {
				return clientset.V30().DeleteLogTargetFrontend(ctx, p, idx, (*v30.DeleteLogTargetFrontendParams)(params))
			},
			(*v32.DeleteLogTargetFrontendParams)(params),
			(*v31.DeleteLogTargetFrontendParams)(params),
			(*v30.DeleteLogTargetFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "log target deletion from frontend")
	}
}

// =============================================================================
// Log Target Executors (Backend)
// =============================================================================

// LogTargetBackendCreate returns an executor for creating log targets in backends.
func LogTargetBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.LogTarget) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.LogTarget) error {
		params := &dataplaneapi.CreateLogTargetBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.LogTarget, _ *v32.CreateLogTargetBackendParams) (*http.Response, error) {
				return clientset.V32().CreateLogTargetBackend(ctx, p, idx, (*v32.CreateLogTargetBackendParams)(params), m)
			},
			func(p string, idx int, m v31.LogTarget, _ *v31.CreateLogTargetBackendParams) (*http.Response, error) {
				return clientset.V31().CreateLogTargetBackend(ctx, p, idx, (*v31.CreateLogTargetBackendParams)(params), m)
			},
			func(p string, idx int, m v30.LogTarget, _ *v30.CreateLogTargetBackendParams) (*http.Response, error) {
				return clientset.V30().CreateLogTargetBackend(ctx, p, idx, (*v30.CreateLogTargetBackendParams)(params), m)
			},
			(*v32.CreateLogTargetBackendParams)(params),
			(*v31.CreateLogTargetBackendParams)(params),
			(*v30.CreateLogTargetBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "log target creation in backend")
	}
}

// LogTargetBackendUpdate returns an executor for updating log targets in backends.
func LogTargetBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.LogTarget) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.LogTarget) error {
		params := &dataplaneapi.ReplaceLogTargetBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.LogTarget, _ *v32.ReplaceLogTargetBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceLogTargetBackend(ctx, p, idx, (*v32.ReplaceLogTargetBackendParams)(params), m)
			},
			func(p string, idx int, m v31.LogTarget, _ *v31.ReplaceLogTargetBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceLogTargetBackend(ctx, p, idx, (*v31.ReplaceLogTargetBackendParams)(params), m)
			},
			func(p string, idx int, m v30.LogTarget, _ *v30.ReplaceLogTargetBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceLogTargetBackend(ctx, p, idx, (*v30.ReplaceLogTargetBackendParams)(params), m)
			},
			(*v32.ReplaceLogTargetBackendParams)(params),
			(*v31.ReplaceLogTargetBackendParams)(params),
			(*v30.ReplaceLogTargetBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "log target update in backend")
	}
}

// LogTargetBackendDelete returns an executor for deleting log targets from backends.
func LogTargetBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.LogTarget) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.LogTarget) error {
		params := &dataplaneapi.DeleteLogTargetBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteLogTargetBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteLogTargetBackend(ctx, p, idx, (*v32.DeleteLogTargetBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteLogTargetBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteLogTargetBackend(ctx, p, idx, (*v31.DeleteLogTargetBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteLogTargetBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteLogTargetBackend(ctx, p, idx, (*v30.DeleteLogTargetBackendParams)(params))
			},
			(*v32.DeleteLogTargetBackendParams)(params),
			(*v31.DeleteLogTargetBackendParams)(params),
			(*v30.DeleteLogTargetBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "log target deletion from backend")
	}
}

// =============================================================================
// TCP Request Rule Executors (Frontend)
// =============================================================================

// TCPRequestRuleFrontendCreate returns an executor for creating TCP request rules in frontends.
func TCPRequestRuleFrontendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpRequestRule) error {
		params := &dataplaneapi.CreateTCPRequestRuleFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.TcpRequestRule, _ *v32.CreateTCPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V32().CreateTCPRequestRuleFrontend(ctx, p, idx, (*v32.CreateTCPRequestRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.TcpRequestRule, _ *v31.CreateTCPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V31().CreateTCPRequestRuleFrontend(ctx, p, idx, (*v31.CreateTCPRequestRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.TcpRequestRule, _ *v30.CreateTCPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V30().CreateTCPRequestRuleFrontend(ctx, p, idx, (*v30.CreateTCPRequestRuleFrontendParams)(params), m)
			},
			(*v32.CreateTCPRequestRuleFrontendParams)(params),
			(*v31.CreateTCPRequestRuleFrontendParams)(params),
			(*v30.CreateTCPRequestRuleFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP request rule creation in frontend")
	}
}

// TCPRequestRuleFrontendUpdate returns an executor for updating TCP request rules in frontends.
func TCPRequestRuleFrontendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpRequestRule) error {
		params := &dataplaneapi.ReplaceTCPRequestRuleFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.TcpRequestRule, _ *v32.ReplaceTCPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V32().ReplaceTCPRequestRuleFrontend(ctx, p, idx, (*v32.ReplaceTCPRequestRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v31.TcpRequestRule, _ *v31.ReplaceTCPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V31().ReplaceTCPRequestRuleFrontend(ctx, p, idx, (*v31.ReplaceTCPRequestRuleFrontendParams)(params), m)
			},
			func(p string, idx int, m v30.TcpRequestRule, _ *v30.ReplaceTCPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V30().ReplaceTCPRequestRuleFrontend(ctx, p, idx, (*v30.ReplaceTCPRequestRuleFrontendParams)(params), m)
			},
			(*v32.ReplaceTCPRequestRuleFrontendParams)(params),
			(*v31.ReplaceTCPRequestRuleFrontendParams)(params),
			(*v30.ReplaceTCPRequestRuleFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP request rule update in frontend")
	}
}

// TCPRequestRuleFrontendDelete returns an executor for deleting TCP request rules from frontends.
func TCPRequestRuleFrontendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.TcpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.TcpRequestRule) error {
		params := &dataplaneapi.DeleteTCPRequestRuleFrontendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteTCPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V32().DeleteTCPRequestRuleFrontend(ctx, p, idx, (*v32.DeleteTCPRequestRuleFrontendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteTCPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V31().DeleteTCPRequestRuleFrontend(ctx, p, idx, (*v31.DeleteTCPRequestRuleFrontendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteTCPRequestRuleFrontendParams) (*http.Response, error) {
				return clientset.V30().DeleteTCPRequestRuleFrontend(ctx, p, idx, (*v30.DeleteTCPRequestRuleFrontendParams)(params))
			},
			(*v32.DeleteTCPRequestRuleFrontendParams)(params),
			(*v31.DeleteTCPRequestRuleFrontendParams)(params),
			(*v30.DeleteTCPRequestRuleFrontendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP request rule deletion from frontend")
	}
}

// =============================================================================
// TCP Request Rule Executors (Backend)
// =============================================================================

// TCPRequestRuleBackendCreate returns an executor for creating TCP request rules in backends.
func TCPRequestRuleBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpRequestRule) error {
		params := &dataplaneapi.CreateTCPRequestRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.TcpRequestRule, _ *v32.CreateTCPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V32().CreateTCPRequestRuleBackend(ctx, p, idx, (*v32.CreateTCPRequestRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.TcpRequestRule, _ *v31.CreateTCPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V31().CreateTCPRequestRuleBackend(ctx, p, idx, (*v31.CreateTCPRequestRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.TcpRequestRule, _ *v30.CreateTCPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V30().CreateTCPRequestRuleBackend(ctx, p, idx, (*v30.CreateTCPRequestRuleBackendParams)(params), m)
			},
			(*v32.CreateTCPRequestRuleBackendParams)(params),
			(*v31.CreateTCPRequestRuleBackendParams)(params),
			(*v30.CreateTCPRequestRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP request rule creation in backend")
	}
}

// TCPRequestRuleBackendUpdate returns an executor for updating TCP request rules in backends.
func TCPRequestRuleBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpRequestRule) error {
		params := &dataplaneapi.ReplaceTCPRequestRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.TcpRequestRule, _ *v32.ReplaceTCPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceTCPRequestRuleBackend(ctx, p, idx, (*v32.ReplaceTCPRequestRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.TcpRequestRule, _ *v31.ReplaceTCPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceTCPRequestRuleBackend(ctx, p, idx, (*v31.ReplaceTCPRequestRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.TcpRequestRule, _ *v30.ReplaceTCPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceTCPRequestRuleBackend(ctx, p, idx, (*v30.ReplaceTCPRequestRuleBackendParams)(params), m)
			},
			(*v32.ReplaceTCPRequestRuleBackendParams)(params),
			(*v31.ReplaceTCPRequestRuleBackendParams)(params),
			(*v30.ReplaceTCPRequestRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP request rule update in backend")
	}
}

// TCPRequestRuleBackendDelete returns an executor for deleting TCP request rules from backends.
func TCPRequestRuleBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.TcpRequestRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.TcpRequestRule) error {
		params := &dataplaneapi.DeleteTCPRequestRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteTCPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteTCPRequestRuleBackend(ctx, p, idx, (*v32.DeleteTCPRequestRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteTCPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteTCPRequestRuleBackend(ctx, p, idx, (*v31.DeleteTCPRequestRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteTCPRequestRuleBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteTCPRequestRuleBackend(ctx, p, idx, (*v30.DeleteTCPRequestRuleBackendParams)(params))
			},
			(*v32.DeleteTCPRequestRuleBackendParams)(params),
			(*v31.DeleteTCPRequestRuleBackendParams)(params),
			(*v30.DeleteTCPRequestRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP request rule deletion from backend")
	}
}

// =============================================================================
// TCP Response Rule Executors (Backend only)
// =============================================================================

// TCPResponseRuleBackendCreate returns an executor for creating TCP response rules in backends.
func TCPResponseRuleBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpResponseRule) error {
		params := &dataplaneapi.CreateTCPResponseRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.TcpResponseRule, _ *v32.CreateTCPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V32().CreateTCPResponseRuleBackend(ctx, p, idx, (*v32.CreateTCPResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.TcpResponseRule, _ *v31.CreateTCPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V31().CreateTCPResponseRuleBackend(ctx, p, idx, (*v31.CreateTCPResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.TcpResponseRule, _ *v30.CreateTCPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V30().CreateTCPResponseRuleBackend(ctx, p, idx, (*v30.CreateTCPResponseRuleBackendParams)(params), m)
			},
			(*v32.CreateTCPResponseRuleBackendParams)(params),
			(*v31.CreateTCPResponseRuleBackendParams)(params),
			(*v30.CreateTCPResponseRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP response rule creation in backend")
	}
}

// TCPResponseRuleBackendUpdate returns an executor for updating TCP response rules in backends.
func TCPResponseRuleBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpResponseRule) error {
		params := &dataplaneapi.ReplaceTCPResponseRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.TcpResponseRule, _ *v32.ReplaceTCPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceTCPResponseRuleBackend(ctx, p, idx, (*v32.ReplaceTCPResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.TcpResponseRule, _ *v31.ReplaceTCPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceTCPResponseRuleBackend(ctx, p, idx, (*v31.ReplaceTCPResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.TcpResponseRule, _ *v30.ReplaceTCPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceTCPResponseRuleBackend(ctx, p, idx, (*v30.ReplaceTCPResponseRuleBackendParams)(params), m)
			},
			(*v32.ReplaceTCPResponseRuleBackendParams)(params),
			(*v31.ReplaceTCPResponseRuleBackendParams)(params),
			(*v30.ReplaceTCPResponseRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP response rule update in backend")
	}
}

// TCPResponseRuleBackendDelete returns an executor for deleting TCP response rules from backends.
func TCPResponseRuleBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.TcpResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.TcpResponseRule) error {
		params := &dataplaneapi.DeleteTCPResponseRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteTCPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteTCPResponseRuleBackend(ctx, p, idx, (*v32.DeleteTCPResponseRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteTCPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteTCPResponseRuleBackend(ctx, p, idx, (*v31.DeleteTCPResponseRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteTCPResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteTCPResponseRuleBackend(ctx, p, idx, (*v30.DeleteTCPResponseRuleBackendParams)(params))
			},
			(*v32.DeleteTCPResponseRuleBackendParams)(params),
			(*v31.DeleteTCPResponseRuleBackendParams)(params),
			(*v30.DeleteTCPResponseRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP response rule deletion from backend")
	}
}

// =============================================================================
// Stick Rule Executors (Backend only)
// =============================================================================

// StickRuleBackendCreate returns an executor for creating stick rules in backends.
func StickRuleBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.StickRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.StickRule) error {
		params := &dataplaneapi.CreateStickRuleParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.StickRule, _ *v32.CreateStickRuleParams) (*http.Response, error) {
				return clientset.V32().CreateStickRule(ctx, p, idx, (*v32.CreateStickRuleParams)(params), m)
			},
			func(p string, idx int, m v31.StickRule, _ *v31.CreateStickRuleParams) (*http.Response, error) {
				return clientset.V31().CreateStickRule(ctx, p, idx, (*v31.CreateStickRuleParams)(params), m)
			},
			func(p string, idx int, m v30.StickRule, _ *v30.CreateStickRuleParams) (*http.Response, error) {
				return clientset.V30().CreateStickRule(ctx, p, idx, (*v30.CreateStickRuleParams)(params), m)
			},
			(*v32.CreateStickRuleParams)(params),
			(*v31.CreateStickRuleParams)(params),
			(*v30.CreateStickRuleParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "stick rule creation in backend")
	}
}

// StickRuleBackendUpdate returns an executor for updating stick rules in backends.
func StickRuleBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.StickRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.StickRule) error {
		params := &dataplaneapi.ReplaceStickRuleParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.StickRule, _ *v32.ReplaceStickRuleParams) (*http.Response, error) {
				return clientset.V32().ReplaceStickRule(ctx, p, idx, (*v32.ReplaceStickRuleParams)(params), m)
			},
			func(p string, idx int, m v31.StickRule, _ *v31.ReplaceStickRuleParams) (*http.Response, error) {
				return clientset.V31().ReplaceStickRule(ctx, p, idx, (*v31.ReplaceStickRuleParams)(params), m)
			},
			func(p string, idx int, m v30.StickRule, _ *v30.ReplaceStickRuleParams) (*http.Response, error) {
				return clientset.V30().ReplaceStickRule(ctx, p, idx, (*v30.ReplaceStickRuleParams)(params), m)
			},
			(*v32.ReplaceStickRuleParams)(params),
			(*v31.ReplaceStickRuleParams)(params),
			(*v30.ReplaceStickRuleParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "stick rule update in backend")
	}
}

// StickRuleBackendDelete returns an executor for deleting stick rules from backends.
func StickRuleBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.StickRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.StickRule) error {
		params := &dataplaneapi.DeleteStickRuleParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteStickRuleParams) (*http.Response, error) {
				return clientset.V32().DeleteStickRule(ctx, p, idx, (*v32.DeleteStickRuleParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteStickRuleParams) (*http.Response, error) {
				return clientset.V31().DeleteStickRule(ctx, p, idx, (*v31.DeleteStickRuleParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteStickRuleParams) (*http.Response, error) {
				return clientset.V30().DeleteStickRule(ctx, p, idx, (*v30.DeleteStickRuleParams)(params))
			},
			(*v32.DeleteStickRuleParams)(params),
			(*v31.DeleteStickRuleParams)(params),
			(*v30.DeleteStickRuleParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "stick rule deletion from backend")
	}
}

// =============================================================================
// HTTP After Response Rule Executors (Backend only)
// =============================================================================

// HTTPAfterResponseRuleBackendCreate returns an executor for creating HTTP after response rules in backends.
func HTTPAfterResponseRuleBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpAfterResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpAfterResponseRule) error {
		params := &dataplaneapi.CreateHTTPAfterResponseRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpAfterResponseRule, _ *v32.CreateHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V32().CreateHTTPAfterResponseRuleBackend(ctx, p, idx, (*v32.CreateHTTPAfterResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpAfterResponseRule, _ *v31.CreateHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V31().CreateHTTPAfterResponseRuleBackend(ctx, p, idx, (*v31.CreateHTTPAfterResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpAfterResponseRule, _ *v30.CreateHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V30().CreateHTTPAfterResponseRuleBackend(ctx, p, idx, (*v30.CreateHTTPAfterResponseRuleBackendParams)(params), m)
			},
			(*v32.CreateHTTPAfterResponseRuleBackendParams)(params),
			(*v31.CreateHTTPAfterResponseRuleBackendParams)(params),
			(*v30.CreateHTTPAfterResponseRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP after response rule creation in backend")
	}
}

// HTTPAfterResponseRuleBackendUpdate returns an executor for updating HTTP after response rules in backends.
func HTTPAfterResponseRuleBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpAfterResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpAfterResponseRule) error {
		params := &dataplaneapi.ReplaceHTTPAfterResponseRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpAfterResponseRule, _ *v32.ReplaceHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceHTTPAfterResponseRuleBackend(ctx, p, idx, (*v32.ReplaceHTTPAfterResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpAfterResponseRule, _ *v31.ReplaceHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceHTTPAfterResponseRuleBackend(ctx, p, idx, (*v31.ReplaceHTTPAfterResponseRuleBackendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpAfterResponseRule, _ *v30.ReplaceHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceHTTPAfterResponseRuleBackend(ctx, p, idx, (*v30.ReplaceHTTPAfterResponseRuleBackendParams)(params), m)
			},
			(*v32.ReplaceHTTPAfterResponseRuleBackendParams)(params),
			(*v31.ReplaceHTTPAfterResponseRuleBackendParams)(params),
			(*v30.ReplaceHTTPAfterResponseRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP after response rule update in backend")
	}
}

// HTTPAfterResponseRuleBackendDelete returns an executor for deleting HTTP after response rules from backends.
func HTTPAfterResponseRuleBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpAfterResponseRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpAfterResponseRule) error {
		params := &dataplaneapi.DeleteHTTPAfterResponseRuleBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteHTTPAfterResponseRuleBackend(ctx, p, idx, (*v32.DeleteHTTPAfterResponseRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteHTTPAfterResponseRuleBackend(ctx, p, idx, (*v31.DeleteHTTPAfterResponseRuleBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteHTTPAfterResponseRuleBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteHTTPAfterResponseRuleBackend(ctx, p, idx, (*v30.DeleteHTTPAfterResponseRuleBackendParams)(params))
			},
			(*v32.DeleteHTTPAfterResponseRuleBackendParams)(params),
			(*v31.DeleteHTTPAfterResponseRuleBackendParams)(params),
			(*v30.DeleteHTTPAfterResponseRuleBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP after response rule deletion from backend")
	}
}

// =============================================================================
// Server Switching Rule Executors (Backend only)
// =============================================================================

// ServerSwitchingRuleBackendCreate returns an executor for creating server switching rules in backends.
func ServerSwitchingRuleBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.ServerSwitchingRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.ServerSwitchingRule) error {
		params := &dataplaneapi.CreateServerSwitchingRuleParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.ServerSwitchingRule, _ *v32.CreateServerSwitchingRuleParams) (*http.Response, error) {
				return clientset.V32().CreateServerSwitchingRule(ctx, p, idx, (*v32.CreateServerSwitchingRuleParams)(params), m)
			},
			func(p string, idx int, m v31.ServerSwitchingRule, _ *v31.CreateServerSwitchingRuleParams) (*http.Response, error) {
				return clientset.V31().CreateServerSwitchingRule(ctx, p, idx, (*v31.CreateServerSwitchingRuleParams)(params), m)
			},
			func(p string, idx int, m v30.ServerSwitchingRule, _ *v30.CreateServerSwitchingRuleParams) (*http.Response, error) {
				return clientset.V30().CreateServerSwitchingRule(ctx, p, idx, (*v30.CreateServerSwitchingRuleParams)(params), m)
			},
			(*v32.CreateServerSwitchingRuleParams)(params),
			(*v31.CreateServerSwitchingRuleParams)(params),
			(*v30.CreateServerSwitchingRuleParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server switching rule creation in backend")
	}
}

// ServerSwitchingRuleBackendUpdate returns an executor for updating server switching rules in backends.
func ServerSwitchingRuleBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.ServerSwitchingRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.ServerSwitchingRule) error {
		params := &dataplaneapi.ReplaceServerSwitchingRuleParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.ServerSwitchingRule, _ *v32.ReplaceServerSwitchingRuleParams) (*http.Response, error) {
				return clientset.V32().ReplaceServerSwitchingRule(ctx, p, idx, (*v32.ReplaceServerSwitchingRuleParams)(params), m)
			},
			func(p string, idx int, m v31.ServerSwitchingRule, _ *v31.ReplaceServerSwitchingRuleParams) (*http.Response, error) {
				return clientset.V31().ReplaceServerSwitchingRule(ctx, p, idx, (*v31.ReplaceServerSwitchingRuleParams)(params), m)
			},
			func(p string, idx int, m v30.ServerSwitchingRule, _ *v30.ReplaceServerSwitchingRuleParams) (*http.Response, error) {
				return clientset.V30().ReplaceServerSwitchingRule(ctx, p, idx, (*v30.ReplaceServerSwitchingRuleParams)(params), m)
			},
			(*v32.ReplaceServerSwitchingRuleParams)(params),
			(*v31.ReplaceServerSwitchingRuleParams)(params),
			(*v30.ReplaceServerSwitchingRuleParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server switching rule update in backend")
	}
}

// ServerSwitchingRuleBackendDelete returns an executor for deleting server switching rules from backends.
func ServerSwitchingRuleBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.ServerSwitchingRule) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.ServerSwitchingRule) error {
		params := &dataplaneapi.DeleteServerSwitchingRuleParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteServerSwitchingRuleParams) (*http.Response, error) {
				return clientset.V32().DeleteServerSwitchingRule(ctx, p, idx, (*v32.DeleteServerSwitchingRuleParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteServerSwitchingRuleParams) (*http.Response, error) {
				return clientset.V31().DeleteServerSwitchingRule(ctx, p, idx, (*v31.DeleteServerSwitchingRuleParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteServerSwitchingRuleParams) (*http.Response, error) {
				return clientset.V30().DeleteServerSwitchingRule(ctx, p, idx, (*v30.DeleteServerSwitchingRuleParams)(params))
			},
			(*v32.DeleteServerSwitchingRuleParams)(params),
			(*v31.DeleteServerSwitchingRuleParams)(params),
			(*v30.DeleteServerSwitchingRuleParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "server switching rule deletion from backend")
	}
}

// =============================================================================
// HTTP Check Executors (Backend only)
// =============================================================================

// HTTPCheckBackendCreate returns an executor for creating HTTP checks in backends.
func HTTPCheckBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpCheck) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpCheck) error {
		params := &dataplaneapi.CreateHTTPCheckBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpCheck, _ *v32.CreateHTTPCheckBackendParams) (*http.Response, error) {
				return clientset.V32().CreateHTTPCheckBackend(ctx, p, idx, (*v32.CreateHTTPCheckBackendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpCheck, _ *v31.CreateHTTPCheckBackendParams) (*http.Response, error) {
				return clientset.V31().CreateHTTPCheckBackend(ctx, p, idx, (*v31.CreateHTTPCheckBackendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpCheck, _ *v30.CreateHTTPCheckBackendParams) (*http.Response, error) {
				return clientset.V30().CreateHTTPCheckBackend(ctx, p, idx, (*v30.CreateHTTPCheckBackendParams)(params), m)
			},
			(*v32.CreateHTTPCheckBackendParams)(params),
			(*v31.CreateHTTPCheckBackendParams)(params),
			(*v30.CreateHTTPCheckBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP check creation in backend")
	}
}

// HTTPCheckBackendUpdate returns an executor for updating HTTP checks in backends.
func HTTPCheckBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpCheck) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.HttpCheck) error {
		params := &dataplaneapi.ReplaceHTTPCheckBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.HttpCheck, _ *v32.ReplaceHTTPCheckBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceHTTPCheckBackend(ctx, p, idx, (*v32.ReplaceHTTPCheckBackendParams)(params), m)
			},
			func(p string, idx int, m v31.HttpCheck, _ *v31.ReplaceHTTPCheckBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceHTTPCheckBackend(ctx, p, idx, (*v31.ReplaceHTTPCheckBackendParams)(params), m)
			},
			func(p string, idx int, m v30.HttpCheck, _ *v30.ReplaceHTTPCheckBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceHTTPCheckBackend(ctx, p, idx, (*v30.ReplaceHTTPCheckBackendParams)(params), m)
			},
			(*v32.ReplaceHTTPCheckBackendParams)(params),
			(*v31.ReplaceHTTPCheckBackendParams)(params),
			(*v30.ReplaceHTTPCheckBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP check update in backend")
	}
}

// HTTPCheckBackendDelete returns an executor for deleting HTTP checks from backends.
func HTTPCheckBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpCheck) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.HttpCheck) error {
		params := &dataplaneapi.DeleteHTTPCheckBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteHTTPCheckBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteHTTPCheckBackend(ctx, p, idx, (*v32.DeleteHTTPCheckBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteHTTPCheckBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteHTTPCheckBackend(ctx, p, idx, (*v31.DeleteHTTPCheckBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteHTTPCheckBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteHTTPCheckBackend(ctx, p, idx, (*v30.DeleteHTTPCheckBackendParams)(params))
			},
			(*v32.DeleteHTTPCheckBackendParams)(params),
			(*v31.DeleteHTTPCheckBackendParams)(params),
			(*v30.DeleteHTTPCheckBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "HTTP check deletion from backend")
	}
}

// =============================================================================
// TCP Check Executors (Backend only)
// =============================================================================

// TCPCheckBackendCreate returns an executor for creating TCP checks in backends.
func TCPCheckBackendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpCheck) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpCheck) error {
		params := &dataplaneapi.CreateTCPCheckBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.TcpCheck, _ *v32.CreateTCPCheckBackendParams) (*http.Response, error) {
				return clientset.V32().CreateTCPCheckBackend(ctx, p, idx, (*v32.CreateTCPCheckBackendParams)(params), m)
			},
			func(p string, idx int, m v31.TcpCheck, _ *v31.CreateTCPCheckBackendParams) (*http.Response, error) {
				return clientset.V31().CreateTCPCheckBackend(ctx, p, idx, (*v31.CreateTCPCheckBackendParams)(params), m)
			},
			func(p string, idx int, m v30.TcpCheck, _ *v30.CreateTCPCheckBackendParams) (*http.Response, error) {
				return clientset.V30().CreateTCPCheckBackend(ctx, p, idx, (*v30.CreateTCPCheckBackendParams)(params), m)
			},
			(*v32.CreateTCPCheckBackendParams)(params),
			(*v31.CreateTCPCheckBackendParams)(params),
			(*v30.CreateTCPCheckBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP check creation in backend")
	}
}

// TCPCheckBackendUpdate returns an executor for updating TCP checks in backends.
func TCPCheckBackendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpCheck) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.TcpCheck) error {
		params := &dataplaneapi.ReplaceTCPCheckBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.TcpCheck, _ *v32.ReplaceTCPCheckBackendParams) (*http.Response, error) {
				return clientset.V32().ReplaceTCPCheckBackend(ctx, p, idx, (*v32.ReplaceTCPCheckBackendParams)(params), m)
			},
			func(p string, idx int, m v31.TcpCheck, _ *v31.ReplaceTCPCheckBackendParams) (*http.Response, error) {
				return clientset.V31().ReplaceTCPCheckBackend(ctx, p, idx, (*v31.ReplaceTCPCheckBackendParams)(params), m)
			},
			func(p string, idx int, m v30.TcpCheck, _ *v30.ReplaceTCPCheckBackendParams) (*http.Response, error) {
				return clientset.V30().ReplaceTCPCheckBackend(ctx, p, idx, (*v30.ReplaceTCPCheckBackendParams)(params), m)
			},
			(*v32.ReplaceTCPCheckBackendParams)(params),
			(*v31.ReplaceTCPCheckBackendParams)(params),
			(*v30.ReplaceTCPCheckBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP check update in backend")
	}
}

// TCPCheckBackendDelete returns an executor for deleting TCP checks from backends.
func TCPCheckBackendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.TcpCheck) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.TcpCheck) error {
		params := &dataplaneapi.DeleteTCPCheckBackendParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteTCPCheckBackendParams) (*http.Response, error) {
				return clientset.V32().DeleteTCPCheckBackend(ctx, p, idx, (*v32.DeleteTCPCheckBackendParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteTCPCheckBackendParams) (*http.Response, error) {
				return clientset.V31().DeleteTCPCheckBackend(ctx, p, idx, (*v31.DeleteTCPCheckBackendParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteTCPCheckBackendParams) (*http.Response, error) {
				return clientset.V30().DeleteTCPCheckBackend(ctx, p, idx, (*v30.DeleteTCPCheckBackendParams)(params))
			},
			(*v32.DeleteTCPCheckBackendParams)(params),
			(*v31.DeleteTCPCheckBackendParams)(params),
			(*v30.DeleteTCPCheckBackendParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "TCP check deletion from backend")
	}
}

// =============================================================================
// Declare Capture Executors (Frontend only)
// =============================================================================

// DeclareCaptureFrontendCreate returns an executor for creating declare captures in frontends.
func DeclareCaptureFrontendCreate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Capture) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Capture) error {
		params := &dataplaneapi.CreateDeclareCaptureParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchCreateChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Capture, _ *v32.CreateDeclareCaptureParams) (*http.Response, error) {
				return clientset.V32().CreateDeclareCapture(ctx, p, idx, (*v32.CreateDeclareCaptureParams)(params), m)
			},
			func(p string, idx int, m v31.Capture, _ *v31.CreateDeclareCaptureParams) (*http.Response, error) {
				return clientset.V31().CreateDeclareCapture(ctx, p, idx, (*v31.CreateDeclareCaptureParams)(params), m)
			},
			func(p string, idx int, m v30.Capture, _ *v30.CreateDeclareCaptureParams) (*http.Response, error) {
				return clientset.V30().CreateDeclareCapture(ctx, p, idx, (*v30.CreateDeclareCaptureParams)(params), m)
			},
			(*v32.CreateDeclareCaptureParams)(params),
			(*v31.CreateDeclareCaptureParams)(params),
			(*v30.CreateDeclareCaptureParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "declare capture creation in frontend")
	}
}

// DeclareCaptureFrontendUpdate returns an executor for updating declare captures in frontends.
func DeclareCaptureFrontendUpdate() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Capture) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model *dataplaneapi.Capture) error {
		params := &dataplaneapi.ReplaceDeclareCaptureParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchReplaceChild(ctx, c, parent, index, model,
			func(p string, idx int, m v32.Capture, _ *v32.ReplaceDeclareCaptureParams) (*http.Response, error) {
				return clientset.V32().ReplaceDeclareCapture(ctx, p, idx, (*v32.ReplaceDeclareCaptureParams)(params), m)
			},
			func(p string, idx int, m v31.Capture, _ *v31.ReplaceDeclareCaptureParams) (*http.Response, error) {
				return clientset.V31().ReplaceDeclareCapture(ctx, p, idx, (*v31.ReplaceDeclareCaptureParams)(params), m)
			},
			func(p string, idx int, m v30.Capture, _ *v30.ReplaceDeclareCaptureParams) (*http.Response, error) {
				return clientset.V30().ReplaceDeclareCapture(ctx, p, idx, (*v30.ReplaceDeclareCaptureParams)(params), m)
			},
			(*v32.ReplaceDeclareCaptureParams)(params),
			(*v31.ReplaceDeclareCaptureParams)(params),
			(*v30.ReplaceDeclareCaptureParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "declare capture update in frontend")
	}
}

// DeclareCaptureFrontendDelete returns an executor for deleting declare captures from frontends.
func DeclareCaptureFrontendDelete() func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Capture) error {
	return func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ *dataplaneapi.Capture) error {
		params := &dataplaneapi.DeleteDeclareCaptureParams{TransactionId: &txID}
		clientset := c.Clientset()

		resp, err := client.DispatchDeleteChild(ctx, c, parent, index,
			func(p string, idx int, _ *v32.DeleteDeclareCaptureParams) (*http.Response, error) {
				return clientset.V32().DeleteDeclareCapture(ctx, p, idx, (*v32.DeleteDeclareCaptureParams)(params))
			},
			func(p string, idx int, _ *v31.DeleteDeclareCaptureParams) (*http.Response, error) {
				return clientset.V31().DeleteDeclareCapture(ctx, p, idx, (*v31.DeleteDeclareCaptureParams)(params))
			},
			func(p string, idx int, _ *v30.DeleteDeclareCaptureParams) (*http.Response, error) {
				return clientset.V30().DeleteDeclareCapture(ctx, p, idx, (*v30.DeleteDeclareCaptureParams)(params))
			},
			(*v32.DeleteDeclareCaptureParams)(params),
			(*v31.DeleteDeclareCaptureParams)(params),
			(*v30.DeleteDeclareCaptureParams)(params),
		)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, "declare capture deletion from frontend")
	}
}
