package client

import (
	"context"
	"fmt"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
	"net/http"
)

// CallFunc represents a versioned API call function.
// Each field is a function that takes a version-specific client and returns a result of type T.
// This allows type-safe dispatch to the appropriate client version based on runtime detection.
//
// Example usage:
//
//	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
//	    V32: func(c *v32.Client) (*http.Response, error) { return c.SomeMethod(ctx, params) },
//	    V31: func(c *v31.Client) (*http.Response, error) { return c.SomeMethod(ctx, params) },
//	    V30: func(c *v30.Client) (*http.Response, error) { return c.SomeMethod(ctx, params) },
//	})
type CallFunc[T any] struct {
	// V32 is the function to call for DataPlane API v3.2+
	V32 func(*v32.Client) (T, error)

	// V31 is the function to call for DataPlane API v3.1
	V31 func(*v31.Client) (T, error)

	// V30 is the function to call for DataPlane API v3.0
	V30 func(*v30.Client) (T, error)
}

// Dispatch executes the appropriate versioned function based on the detected API version.
// This is the primary method for executing API calls that work across all versions.
//
// Returns error if:
//   - The client type is unexpected
//   - The version-specific function is nil
//   - The versioned function itself returns an error
//
// Example:
//
//	resp, err := c.Dispatch(ctx, CallFunc[*http.Response]{
//	    V32: func(c *v32.Client) (*http.Response, error) {
//	        return c.GetAllStorageMapFiles(ctx)
//	    },
//	    V31: func(c *v31.Client) (*http.Response, error) {
//	        return c.GetAllStorageMapFiles(ctx)
//	    },
//	    V30: func(c *v30.Client) (*http.Response, error) {
//	        return c.GetAllStorageMapFiles(ctx)
//	    },
//	})
func (c *DataplaneClient) Dispatch(ctx context.Context, call CallFunc[*http.Response]) (*http.Response, error) {
	return c.DispatchWithCapability(ctx, call, nil)
}

// DispatchWithCapability executes the appropriate versioned function with an optional capability check.
// Use this for version-specific features (e.g., crt-list only available in v3.2+).
//
// The capability check is performed before executing the versioned function. If the check fails,
// the function is not executed and the capability error is returned.
//
// Parameters:
//   - ctx: Context for the API call
//   - call: Version-specific functions to execute
//   - capabilityCheck: Optional function to verify feature availability. If nil, no check is performed.
//
// Returns error if:
//   - Capability check fails
//   - The client type is unexpected
//   - The version-specific function is nil
//   - The versioned function itself returns an error
//
// Example (CRT-list only in v3.2+):
//
//	resp, err := c.DispatchWithCapability(ctx, CallFunc[*http.Response]{
//	    V32: func(c *v32.Client) (*http.Response, error) {
//	        return c.GetAllStorageSSLCrtListFiles(ctx)
//	    },
//	    // V31 and V30 omitted - not supported
//	}, func(caps Capabilities) error {
//	    if !caps.SupportsCrtList {
//	        return fmt.Errorf("crt-list storage requires DataPlane API v3.2+")
//	    }
//	    return nil
//	})
func (c *DataplaneClient) DispatchWithCapability(
	ctx context.Context,
	call CallFunc[*http.Response],
	capabilityCheck func(Capabilities) error,
) (*http.Response, error) {
	// Check capabilities first (for version-specific features)
	if capabilityCheck != nil {
		if err := capabilityCheck(c.clientset.Capabilities()); err != nil {
			return nil, err
		}
	}

	// Dispatch to appropriate version
	switch client := c.clientset.PreferredClient().(type) {
	case *v32.Client:
		if call.V32 == nil {
			return nil, fmt.Errorf("operation not supported by DataPlane API v3.2 (v3.2 function is nil)")
		}
		return call.V32(client)

	case *v31.Client:
		if call.V31 == nil {
			return nil, fmt.Errorf("operation not supported by DataPlane API v3.1 (v3.1 function is nil)")
		}
		return call.V31(client)

	case *v30.Client:
		if call.V30 == nil {
			return nil, fmt.Errorf("operation not supported by DataPlane API v3.0 (v3.0 function is nil)")
		}
		return call.V30(client)

	default:
		return nil, fmt.Errorf("unexpected client type: %T", client)
	}
}

// DispatchGeneric is a generic version of Dispatch for non-HTTP response types.
// Use this when the return type is not *http.Response (e.g., for string, int64, etc.).
//
// This is a package-level function because it needs to work with any clientset,
// not just DataplaneClient instances.
//
// Example (returning parsed data instead of raw response):
//
//	version, err := DispatchGeneric[int64](ctx, c.clientset, CallFunc[int64]{
//	    V32: func(c *v32.Client) (int64, error) {
//	        resp, err := c.GetConfigurationVersion(ctx, &v32.GetConfigurationVersionParams{})
//	        if err != nil {
//	            return 0, err
//	        }
//	        defer resp.Body.Close()
//	        // ... parse version from response ...
//	        return parsedVersion, nil
//	    },
//	    // ... similar for V31 and V30 ...
//	})
func DispatchGeneric[T any](
	ctx context.Context,
	clientset *Clientset,
	call CallFunc[T],
) (T, error) {
	switch client := clientset.PreferredClient().(type) {
	case *v32.Client:
		if call.V32 == nil {
			var zero T
			return zero, fmt.Errorf("operation not supported by DataPlane API v3.2 (v3.2 function is nil)")
		}
		return call.V32(client)

	case *v31.Client:
		if call.V31 == nil {
			var zero T
			return zero, fmt.Errorf("operation not supported by DataPlane API v3.1 (v3.1 function is nil)")
		}
		return call.V31(client)

	case *v30.Client:
		if call.V30 == nil {
			var zero T
			return zero, fmt.Errorf("operation not supported by DataPlane API v3.0 (v3.0 function is nil)")
		}
		return call.V30(client)

	default:
		var zero T
		return zero, fmt.Errorf("unexpected client type: %T", client)
	}
}
