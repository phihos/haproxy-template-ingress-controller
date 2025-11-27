// Copyright 2025 Philipp Hossner
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package client

import (
	"context"
	"encoding/json"
	"fmt"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
	"net/http"
)

// DispatchCreate is a generic helper for create operations that handles:
// - JSON marshaling of the unified API model
// - JSON unmarshaling into version-specific types
// - Dispatching to the appropriate version-specific client
// - Response validation
//
// This eliminates the repetitive dispatch pattern that was duplicated 125+ times across section files.
//
// Type parameters:
//   - TUnified: The unified client-native model type (e.g., models.Backend)
//   - TV32, TV31, TV30: The version-specific model types (e.g., v32.Backend, v31.Backend, v30.Backend)
//
// Each callback receives only the unmarshaled model - params should be created inside the callback.
// This ensures version-specific params are always created with the correct type.
//
// Usage example:
//
//	resp, err := DispatchCreate(ctx, c, model,
//	    func(m v32.Backend) (*http.Response, error) {
//	        params := &v32.CreateBackendParams{TransactionId: &txID}
//	        return clientset.V32().CreateBackend(ctx, params, m)
//	    },
//	    func(m v31.Backend) (*http.Response, error) {
//	        params := &v31.CreateBackendParams{TransactionId: &txID}
//	        return clientset.V31().CreateBackend(ctx, params, m)
//	    },
//	    func(m v30.Backend) (*http.Response, error) {
//	        params := &v30.CreateBackendParams{TransactionId: &txID}
//	        return clientset.V30().CreateBackend(ctx, params, m)
//	    },
//	)
func DispatchCreate[TUnified any, TV32 any, TV31 any, TV30 any](
	ctx context.Context,
	c *DataplaneClient,
	unifiedModel TUnified,
	v32Call func(TV32) (*http.Response, error),
	v31Call func(TV31) (*http.Response, error),
	v30Call func(TV30) (*http.Response, error),
) (*http.Response, error) {
	// Marshal unified model to JSON once
	jsonData, err := json.Marshal(unifiedModel)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal model: %w", err)
	}

	// Dispatch to version-specific client with automatic unmarshaling
	return c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(client *v32.Client) (*http.Response, error) {
			var model TV32
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.2: %w", err)
			}
			return v32Call(model)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			var model TV31
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.1: %w", err)
			}
			return v31Call(model)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			var model TV30
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.0: %w", err)
			}
			return v30Call(model)
		},
	})
}

// DispatchUpdate is a generic helper for update/replace operations.
// Similar to DispatchCreate but includes the resource name parameter.
//
// Each callback receives the name and unmarshaled model - params should be created inside the callback.
// This ensures version-specific params are always created with the correct type.
//
// Usage example:
//
//	resp, err := DispatchUpdate(ctx, c, name, model,
//	    func(n string, m v32.Backend) (*http.Response, error) {
//	        params := &v32.ReplaceBackendParams{TransactionId: &txID}
//	        return clientset.V32().ReplaceBackend(ctx, n, params, m)
//	    },
//	    func(n string, m v31.Backend) (*http.Response, error) {
//	        params := &v31.ReplaceBackendParams{TransactionId: &txID}
//	        return clientset.V31().ReplaceBackend(ctx, n, params, m)
//	    },
//	    func(n string, m v30.Backend) (*http.Response, error) {
//	        params := &v30.ReplaceBackendParams{TransactionId: &txID}
//	        return clientset.V30().ReplaceBackend(ctx, n, params, m)
//	    },
//	)
func DispatchUpdate[TUnified any, TV32 any, TV31 any, TV30 any](
	ctx context.Context,
	c *DataplaneClient,
	name string,
	unifiedModel TUnified,
	v32Call func(string, TV32) (*http.Response, error),
	v31Call func(string, TV31) (*http.Response, error),
	v30Call func(string, TV30) (*http.Response, error),
) (*http.Response, error) {
	// Marshal unified model to JSON once
	jsonData, err := json.Marshal(unifiedModel)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal model: %w", err)
	}

	// Dispatch to version-specific client with automatic unmarshaling
	return c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(client *v32.Client) (*http.Response, error) {
			var model TV32
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.2: %w", err)
			}
			return v32Call(name, model)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			var model TV31
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.1: %w", err)
			}
			return v31Call(name, model)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			var model TV30
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.0: %w", err)
			}
			return v30Call(name, model)
		},
	})
}

// DispatchDelete is a generic helper for delete operations.
// No model marshaling needed since delete only requires the resource name.
//
// Each callback receives only the name - params should be created inside the callback.
// This ensures version-specific params are always created with the correct type.
//
// Usage example:
//
//	resp, err := DispatchDelete(ctx, c, name,
//	    func(n string) (*http.Response, error) {
//	        params := &v32.DeleteBackendParams{TransactionId: &txID}
//	        return clientset.V32().DeleteBackend(ctx, n, params)
//	    },
//	    func(n string) (*http.Response, error) {
//	        params := &v31.DeleteBackendParams{TransactionId: &txID}
//	        return clientset.V31().DeleteBackend(ctx, n, params)
//	    },
//	    func(n string) (*http.Response, error) {
//	        params := &v30.DeleteBackendParams{TransactionId: &txID}
//	        return clientset.V30().DeleteBackend(ctx, n, params)
//	    },
//	)
func DispatchDelete(
	ctx context.Context,
	c *DataplaneClient,
	name string,
	v32Call func(string) (*http.Response, error),
	v31Call func(string) (*http.Response, error),
	v30Call func(string) (*http.Response, error),
) (*http.Response, error) {
	return c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(client *v32.Client) (*http.Response, error) {
			return v32Call(name)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			return v31Call(name)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			return v30Call(name)
		},
	})
}

// DispatchCreateChild is a generic helper for creating child resources (e.g., binds, servers, ACLs).
// Child resources belong to a parent (e.g., frontend, backend) and require the parent name.
//
// Each callback receives parent name, index, and unmarshaled model - params should be created inside the callback.
// This ensures version-specific params are always created with the correct type.
//
// Usage example:
//
//	resp, err := DispatchCreateChild(ctx, c, parentName, index, model,
//	    func(parent string, idx int, m v32.Acl) (*http.Response, error) {
//	        params := &v32.CreateAclFrontendParams{TransactionId: &txID}
//	        return clientset.V32().CreateAclFrontend(ctx, parent, idx, params, m)
//	    },
//	    func(parent string, idx int, m v31.Acl) (*http.Response, error) {
//	        params := &v31.CreateAclFrontendParams{TransactionId: &txID}
//	        return clientset.V31().CreateAclFrontend(ctx, parent, idx, params, m)
//	    },
//	    func(parent string, idx int, m v30.Acl) (*http.Response, error) {
//	        params := &v30.CreateAclFrontendParams{TransactionId: &txID}
//	        return clientset.V30().CreateAclFrontend(ctx, parent, idx, params, m)
//	    },
//	)
func DispatchCreateChild[TUnified any, TV32 any, TV31 any, TV30 any](
	ctx context.Context,
	c *DataplaneClient,
	parentName string,
	index int,
	unifiedModel TUnified,
	v32Call func(string, int, TV32) (*http.Response, error),
	v31Call func(string, int, TV31) (*http.Response, error),
	v30Call func(string, int, TV30) (*http.Response, error),
) (*http.Response, error) {
	// Marshal unified model to JSON once
	jsonData, err := json.Marshal(unifiedModel)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal model: %w", err)
	}

	// Dispatch to version-specific client with automatic unmarshaling
	return c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(client *v32.Client) (*http.Response, error) {
			var model TV32
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.2: %w", err)
			}
			return v32Call(parentName, index, model)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			var model TV31
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.1: %w", err)
			}
			return v31Call(parentName, index, model)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			var model TV30
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.0: %w", err)
			}
			return v30Call(parentName, index, model)
		},
	})
}

// DispatchReplaceChild is a generic helper for replacing/updating child resources.
// Similar to DispatchCreateChild but for replace operations.
//
// Each callback receives parent name, index, and unmarshaled model - params should be created inside the callback.
// This ensures version-specific params are always created with the correct type.
//
// Usage example:
//
//	resp, err := DispatchReplaceChild(ctx, c, parentName, index, model,
//	    func(parent string, idx int, m v32.Acl) (*http.Response, error) {
//	        params := &v32.ReplaceAclFrontendParams{TransactionId: &txID}
//	        return clientset.V32().ReplaceAclFrontend(ctx, parent, idx, params, m)
//	    },
//	    func(parent string, idx int, m v31.Acl) (*http.Response, error) {
//	        params := &v31.ReplaceAclFrontendParams{TransactionId: &txID}
//	        return clientset.V31().ReplaceAclFrontend(ctx, parent, idx, params, m)
//	    },
//	    func(parent string, idx int, m v30.Acl) (*http.Response, error) {
//	        params := &v30.ReplaceAclFrontendParams{TransactionId: &txID}
//	        return clientset.V30().ReplaceAclFrontend(ctx, parent, idx, params, m)
//	    },
//	)
func DispatchReplaceChild[TUnified any, TV32 any, TV31 any, TV30 any](
	ctx context.Context,
	c *DataplaneClient,
	parentName string,
	index int,
	unifiedModel TUnified,
	v32Call func(string, int, TV32) (*http.Response, error),
	v31Call func(string, int, TV31) (*http.Response, error),
	v30Call func(string, int, TV30) (*http.Response, error),
) (*http.Response, error) {
	// Marshal unified model to JSON once
	jsonData, err := json.Marshal(unifiedModel)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal model: %w", err)
	}

	// Dispatch to version-specific client with automatic unmarshaling
	return c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(client *v32.Client) (*http.Response, error) {
			var model TV32
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.2: %w", err)
			}
			return v32Call(parentName, index, model)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			var model TV31
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.1: %w", err)
			}
			return v31Call(parentName, index, model)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			var model TV30
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.0: %w", err)
			}
			return v30Call(parentName, index, model)
		},
	})
}

// DispatchDeleteChild is a generic helper for deleting child resources.
// No model marshaling needed since delete only requires parent name and index.
//
// Each callback receives parent name and index - params should be created inside the callback.
// This ensures version-specific params are always created with the correct type.
//
// Usage example:
//
//	resp, err := DispatchDeleteChild(ctx, c, parentName, index,
//	    func(parent string, idx int) (*http.Response, error) {
//	        params := &v32.DeleteAclFrontendParams{TransactionId: &txID}
//	        return clientset.V32().DeleteAclFrontend(ctx, parent, idx, params)
//	    },
//	    func(parent string, idx int) (*http.Response, error) {
//	        params := &v31.DeleteAclFrontendParams{TransactionId: &txID}
//	        return clientset.V31().DeleteAclFrontend(ctx, parent, idx, params)
//	    },
//	    func(parent string, idx int) (*http.Response, error) {
//	        params := &v30.DeleteAclFrontendParams{TransactionId: &txID}
//	        return clientset.V30().DeleteAclFrontend(ctx, parent, idx, params)
//	    },
//	)
func DispatchDeleteChild(
	ctx context.Context,
	c *DataplaneClient,
	parentName string,
	index int,
	v32Call func(string, int) (*http.Response, error),
	v31Call func(string, int) (*http.Response, error),
	v30Call func(string, int) (*http.Response, error),
) (*http.Response, error) {
	return c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(client *v32.Client) (*http.Response, error) {
			return v32Call(parentName, index)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			return v31Call(parentName, index)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			return v30Call(parentName, index)
		},
	})
}
