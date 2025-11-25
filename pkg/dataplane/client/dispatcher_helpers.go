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
//   - TUnified: The unified dataplaneapi model type (e.g., dataplaneapi.Backend)
//   - TV32, TV31, TV30: The version-specific model types (e.g., v32.Backend, v31.Backend, v30.Backend)
//   - TParams32, TParams31, TParams30: The version-specific parameter types
//
// Usage example:
//
//	resp, err := dispatchCreate(ctx, c, apiModel,
//	    func(m v32.Backend, p *v32.CreateBackendParams) (*http.Response, error) {
//	        return v32Client.CreateBackend(ctx, p, m)
//	    },
//	    func(m v31.Backend, p *v31.CreateBackendParams) (*http.Response, error) {
//	        return v31Client.CreateBackend(ctx, p, m)
//	    },
//	    func(m v30.Backend, p *v30.CreateBackendParams) (*http.Response, error) {
//	        return v30Client.CreateBackend(ctx, p, m)
//	    },
//	    params32, params31, params30,
//	)
func DispatchCreate[TUnified any, TV32 any, TV31 any, TV30 any, TParams32 any, TParams31 any, TParams30 any](
	ctx context.Context,
	c *DataplaneClient,
	unifiedModel TUnified,
	v32Call func(TV32, TParams32) (*http.Response, error),
	v31Call func(TV31, TParams31) (*http.Response, error),
	v30Call func(TV30, TParams30) (*http.Response, error),
	params32 TParams32,
	params31 TParams31,
	params30 TParams30,
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
			return v32Call(model, params32)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			var model TV31
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.1: %w", err)
			}
			return v31Call(model, params31)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			var model TV30
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.0: %w", err)
			}
			return v30Call(model, params30)
		},
	})
}

// DispatchUpdate is a generic helper for update/replace operations.
// Similar to dispatchCreate but includes the resource name parameter.
//
// Usage example:
//
//	resp, err := dispatchUpdate(ctx, c, name, apiModel,
//	    func(n string, m v32.Backend, p *v32.ReplaceBackendParams) (*http.Response, error) {
//	        return v32Client.ReplaceBackend(ctx, n, p, m)
//	    },
//	    func(n string, m v31.Backend, p *v31.ReplaceBackendParams) (*http.Response, error) {
//	        return v31Client.ReplaceBackend(ctx, n, p, m)
//	    },
//	    func(n string, m v30.Backend, p *v30.ReplaceBackendParams) (*http.Response, error) {
//	        return v30Client.ReplaceBackend(ctx, n, p, m)
//	    },
//	    params32, params31, params30,
//	)
func DispatchUpdate[TUnified any, TV32 any, TV31 any, TV30 any, TParams32 any, TParams31 any, TParams30 any](
	ctx context.Context,
	c *DataplaneClient,
	name string,
	unifiedModel TUnified,
	v32Call func(string, TV32, TParams32) (*http.Response, error),
	v31Call func(string, TV31, TParams31) (*http.Response, error),
	v30Call func(string, TV30, TParams30) (*http.Response, error),
	params32 TParams32,
	params31 TParams31,
	params30 TParams30,
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
			return v32Call(name, model, params32)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			var model TV31
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.1: %w", err)
			}
			return v31Call(name, model, params31)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			var model TV30
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.0: %w", err)
			}
			return v30Call(name, model, params30)
		},
	})
}

// DispatchDelete is a generic helper for delete operations.
// No model marshaling needed since delete only requires the resource name.
//
// Usage example:
//
//	resp, err := dispatchDelete(ctx, c, name,
//	    func(n string, p *v32.DeleteBackendParams) (*http.Response, error) {
//	        return v32Client.DeleteBackend(ctx, n, p)
//	    },
//	    func(n string, p *v31.DeleteBackendParams) (*http.Response, error) {
//	        return v31Client.DeleteBackend(ctx, n, p)
//	    },
//	    func(n string, p *v30.DeleteBackendParams) (*http.Response, error) {
//	        return v30Client.DeleteBackend(ctx, n, p)
//	    },
//	    params32, params31, params30,
//	)
func DispatchDelete[TParams32 any, TParams31 any, TParams30 any](
	ctx context.Context,
	c *DataplaneClient,
	name string,
	v32Call func(string, TParams32) (*http.Response, error),
	v31Call func(string, TParams31) (*http.Response, error),
	v30Call func(string, TParams30) (*http.Response, error),
	params32 TParams32,
	params31 TParams31,
	params30 TParams30,
) (*http.Response, error) {
	return c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(client *v32.Client) (*http.Response, error) {
			return v32Call(name, params32)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			return v31Call(name, params31)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			return v30Call(name, params30)
		},
	})
}

// DispatchCreateChild is a generic helper for creating child resources (e.g., binds, servers, ACLs).
// Child resources belong to a parent (e.g., frontend, backend) and require the parent name.
//
// Usage example:
//
//	resp, err := dispatchCreateChild(ctx, c, parentName, index, apiModel,
//	    func(parent string, idx int, m v32.Acl, p *v32.CreateAclFrontendParams) (*http.Response, error) {
//	        return v32Client.CreateAclFrontend(ctx, parent, idx, p, m)
//	    },
//	    func(parent string, idx int, m v31.Acl, p *v31.CreateAclFrontendParams) (*http.Response, error) {
//	        return v31Client.CreateAclFrontend(ctx, parent, idx, p, m)
//	    },
//	    func(parent string, idx int, m v30.Acl, p *v30.CreateAclFrontendParams) (*http.Response, error) {
//	        return v30Client.CreateAclFrontend(ctx, parent, idx, p, m)
//	    },
//	    params32, params31, params30,
//	)
func DispatchCreateChild[TUnified any, TV32 any, TV31 any, TV30 any, TParams32 any, TParams31 any, TParams30 any](
	ctx context.Context,
	c *DataplaneClient,
	parentName string,
	index int,
	unifiedModel TUnified,
	v32Call func(string, int, TV32, TParams32) (*http.Response, error),
	v31Call func(string, int, TV31, TParams31) (*http.Response, error),
	v30Call func(string, int, TV30, TParams30) (*http.Response, error),
	params32 TParams32,
	params31 TParams31,
	params30 TParams30,
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
			return v32Call(parentName, index, model, params32)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			var model TV31
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.1: %w", err)
			}
			return v31Call(parentName, index, model, params31)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			var model TV30
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.0: %w", err)
			}
			return v30Call(parentName, index, model, params30)
		},
	})
}

// DispatchReplaceChild is a generic helper for replacing/updating child resources.
// Similar to dispatchCreateChild but for replace operations.
//
// Usage example:
//
//	resp, err := dispatchReplaceChild(ctx, c, parentName, index, apiModel,
//	    func(parent string, idx int, m v32.Acl, p *v32.ReplaceAclFrontendParams) (*http.Response, error) {
//	        return v32Client.ReplaceAclFrontend(ctx, parent, idx, p, m)
//	    },
//	    func(parent string, idx int, m v31.Acl, p *v31.ReplaceAclFrontendParams) (*http.Response, error) {
//	        return v31Client.ReplaceAclFrontend(ctx, parent, idx, p, m)
//	    },
//	    func(parent string, idx int, m v30.Acl, p *v30.ReplaceAclFrontendParams) (*http.Response, error) {
//	        return v30Client.ReplaceAclFrontend(ctx, parent, idx, p, m)
//	    },
//	    params32, params31, params30,
//	)
func DispatchReplaceChild[TUnified any, TV32 any, TV31 any, TV30 any, TParams32 any, TParams31 any, TParams30 any](
	ctx context.Context,
	c *DataplaneClient,
	parentName string,
	index int,
	unifiedModel TUnified,
	v32Call func(string, int, TV32, TParams32) (*http.Response, error),
	v31Call func(string, int, TV31, TParams31) (*http.Response, error),
	v30Call func(string, int, TV30, TParams30) (*http.Response, error),
	params32 TParams32,
	params31 TParams31,
	params30 TParams30,
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
			return v32Call(parentName, index, model, params32)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			var model TV31
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.1: %w", err)
			}
			return v31Call(parentName, index, model, params31)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			var model TV30
			if err := json.Unmarshal(jsonData, &model); err != nil {
				return nil, fmt.Errorf("failed to unmarshal model for v3.0: %w", err)
			}
			return v30Call(parentName, index, model, params30)
		},
	})
}

// DispatchDeleteChild is a generic helper for deleting child resources.
// No model marshaling needed since delete only requires parent name and index.
//
// Usage example:
//
//	resp, err := dispatchDeleteChild(ctx, c, parentName, index,
//	    func(parent string, idx int, p *v32.DeleteAclFrontendParams) (*http.Response, error) {
//	        return v32Client.DeleteAclFrontend(ctx, parent, idx, p)
//	    },
//	    func(parent string, idx int, p *v31.DeleteAclFrontendParams) (*http.Response, error) {
//	        return v31Client.DeleteAclFrontend(ctx, parent, idx, p)
//	    },
//	    func(parent string, idx int, p *v30.DeleteAclFrontendParams) (*http.Response, error) {
//	        return v30Client.DeleteAclFrontend(ctx, parent, idx, p)
//	    },
//	    params32, params31, params30,
//	)
func DispatchDeleteChild[TParams32 any, TParams31 any, TParams30 any](
	ctx context.Context,
	c *DataplaneClient,
	parentName string,
	index int,
	v32Call func(string, int, TParams32) (*http.Response, error),
	v31Call func(string, int, TParams31) (*http.Response, error),
	v30Call func(string, int, TParams30) (*http.Response, error),
	params32 TParams32,
	params31 TParams31,
	params30 TParams30,
) (*http.Response, error) {
	return c.Dispatch(ctx, CallFunc[*http.Response]{
		V32: func(client *v32.Client) (*http.Response, error) {
			return v32Call(parentName, index, params32)
		},
		V31: func(client *v31.Client) (*http.Response, error) {
			return v31Call(parentName, index, params31)
		},
		V30: func(client *v30.Client) (*http.Response, error) {
			return v30Call(parentName, index, params30)
		},
	})
}
