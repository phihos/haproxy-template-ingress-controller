// Package executors provides pre-built executor functions for HAProxy configuration operations.
//
// This file contains generator functions that create type-safe executor functions
// from API descriptors. These generators eliminate repetitive boilerplate while
// maintaining full compile-time type safety through Go generics.
package executors

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"haproxy-template-ic/pkg/dataplane/client"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
)

// =============================================================================
// Type Conversion Helpers
// =============================================================================

// MarshalTo converts a source value to a destination type using JSON marshaling.
// This enables type-safe conversion between structurally compatible but nominally
// different types (e.g., converting *dataplaneapi.Backend to v32.Backend).
func MarshalTo[TDest any](src any) (TDest, error) {
	var dest TDest
	jsonData, err := json.Marshal(src)
	if err != nil {
		return dest, fmt.Errorf("failed to marshal source: %w", err)
	}
	if err := json.Unmarshal(jsonData, &dest); err != nil {
		return dest, fmt.Errorf("failed to unmarshal to destination type: %w", err)
	}
	return dest, nil
}

// =============================================================================
// Top-Level Resource Executor Generators
// =============================================================================

// GenerateTopLevelExecutors generates create, update, and delete executor functions
// for a top-level resource from its API descriptor.
//
// Example usage:
//
//	create, update, del := GenerateTopLevelExecutors(BackendAPI)
//
// The returned executors can be used directly with the operation types
// or stored in package-level variables for reuse.
func GenerateTopLevelExecutors[TUnified any](
	api TopLevelAPI[TUnified],
) (
	create ExecuteTopLevelFunc[TUnified],
	update ExecuteTopLevelFunc[TUnified],
	del ExecuteTopLevelFunc[TUnified],
) {
	create = func(ctx context.Context, c *client.DataplaneClient, txID string, model TUnified, _ string) error {
		methods := api.CreateMethods(c.Clientset(), txID)
		resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
			V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, model) },
			V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, model) },
			V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, model) },
		})
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, api.ResourceName+" creation")
	}

	update = func(ctx context.Context, c *client.DataplaneClient, txID string, model TUnified, name string) error {
		methods := api.UpdateMethods(c.Clientset(), txID)
		resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
			V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, name, model) },
			V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, name, model) },
			V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, name, model) },
		})
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, api.ResourceName+" update")
	}

	del = func(ctx context.Context, c *client.DataplaneClient, txID string, _ TUnified, name string) error {
		methods := api.DeleteMethods(c.Clientset(), txID)
		resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
			V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, name) },
			V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, name) },
			V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, name) },
		})
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, api.ResourceName+" deletion")
	}

	return create, update, del
}

// =============================================================================
// Indexed Child Resource Executor Generators
// =============================================================================

// GenerateIndexedChildExecutors generates create, update, and delete executor functions
// for an indexed child resource from its API descriptor.
//
// Indexed children are resources identified by their index within a parent,
// such as ACLs, filters, or rules within a frontend or backend.
//
// Example usage:
//
//	create, update, del := GenerateIndexedChildExecutors(ACLFrontendAPI)
func GenerateIndexedChildExecutors[TUnified any](
	api IndexedChildAPI[TUnified],
) (
	create ExecuteIndexedChildFunc[TUnified],
	update ExecuteIndexedChildFunc[TUnified],
	del ExecuteIndexedChildFunc[TUnified],
) {
	create = func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model TUnified) error {
		methods := api.CreateMethods(c.Clientset(), txID)
		resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
			V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, parent, index, model) },
			V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, parent, index, model) },
			V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, parent, index, model) },
		})
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, api.ResourceName+" creation in "+api.ParentType)
	}

	update = func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, model TUnified) error {
		methods := api.UpdateMethods(c.Clientset(), txID)
		resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
			V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, parent, index, model) },
			V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, parent, index, model) },
			V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, parent, index, model) },
		})
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, api.ResourceName+" update in "+api.ParentType)
	}

	del = func(ctx context.Context, c *client.DataplaneClient, txID string, parent string, index int, _ TUnified) error {
		methods := api.DeleteMethods(c.Clientset(), txID)
		resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
			V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, parent, index) },
			V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, parent, index) },
			V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, parent, index) },
		})
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		return client.CheckResponse(resp, api.ResourceName+" deletion from "+api.ParentType)
	}

	return create, update, del
}

// =============================================================================
// Named Child Resource Executor Generators
// =============================================================================

// GenerateNamedChildExecutors generates create, update, and delete executor functions
// for a named child resource from its API descriptor.
//
// Named children are resources identified by name within a parent,
// such as binds in frontends, or servers/server templates in backends.
//
// Note: These generators return factory functions that take the parent name
// and return the actual executor. This is because the parent name is typically
// known at operation creation time, not at executor definition time.
//
// Example usage:
//
//	createFactory, updateFactory, delFactory := GenerateNamedChildExecutors(BindFrontendAPI)
//	create := createFactory(frontendName)
func GenerateNamedChildExecutors[TUnified any](
	api NamedChildAPI[TUnified],
) (
	createFactory func(parentName string) ExecuteNamedChildFunc[TUnified],
	updateFactory func(parentName string) ExecuteNamedChildFunc[TUnified],
	deleteFactory func(parentName string) ExecuteNamedChildFunc[TUnified],
) {
	createFactory = makeNamedChildCreateFactory(api)
	updateFactory = makeNamedChildUpdateFactory(api)
	deleteFactory = makeNamedChildDeleteFactory(api)
	return createFactory, updateFactory, deleteFactory
}

func makeNamedChildCreateFactory[TUnified any](api NamedChildAPI[TUnified]) func(parentName string) ExecuteNamedChildFunc[TUnified] {
	return func(parentName string) ExecuteNamedChildFunc[TUnified] {
		return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model TUnified) error {
			methods := api.CreateMethods(c.Clientset(), txID, parentName)
			resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
				V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, model) },
				V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, model) },
				V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, model) },
			})
			if err != nil {
				return err
			}
			defer resp.Body.Close()
			return client.CheckResponse(resp, api.ResourceName+" creation in "+api.ParentType)
		}
	}
}

func makeNamedChildUpdateFactory[TUnified any](api NamedChildAPI[TUnified]) func(parentName string) ExecuteNamedChildFunc[TUnified] {
	return func(parentName string) ExecuteNamedChildFunc[TUnified] {
		return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model TUnified) error {
			methods := api.UpdateMethods(c.Clientset(), txID, parentName)
			resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
				V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, childName, model) },
				V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, childName, model) },
				V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, childName, model) },
			})
			if err != nil {
				return err
			}
			defer resp.Body.Close()
			return client.CheckResponse(resp, api.ResourceName+" update in "+api.ParentType)
		}
	}
}

func makeNamedChildDeleteFactory[TUnified any](api NamedChildAPI[TUnified]) func(parentName string) ExecuteNamedChildFunc[TUnified] {
	return func(parentName string) ExecuteNamedChildFunc[TUnified] {
		return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ TUnified) error {
			methods := api.DeleteMethods(c.Clientset(), txID, parentName)
			resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
				V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, childName) },
				V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, childName) },
				V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, childName) },
			})
			if err != nil {
				return err
			}
			defer resp.Body.Close()
			return client.CheckResponse(resp, api.ResourceName+" deletion from "+api.ParentType)
		}
	}
}

// =============================================================================
// Container Child Resource Executor Generators
// =============================================================================

// GenerateContainerChildExecutors generates create, update, and delete executor functions
// for a container child resource from its API descriptor.
//
// Container children are resources that belong to a named container section,
// such as users in userlists, mailer entries in mailers, or peer entries in peers.
//
// Note: These generators return factory functions that take the container name
// and return the actual executor.
//
// Example usage:
//
//	createFactory, updateFactory, delFactory := GenerateContainerChildExecutors(UserAPI)
//	create := createFactory(userlistName)
func GenerateContainerChildExecutors[TUnified any](
	api ContainerChildAPI[TUnified],
) (
	createFactory func(containerName string) ExecuteContainerChildFunc[TUnified],
	updateFactory func(containerName string) ExecuteContainerChildFunc[TUnified],
	deleteFactory func(containerName string) ExecuteContainerChildFunc[TUnified],
) {
	createFactory = makeContainerChildCreateFactory(api)
	updateFactory = makeContainerChildUpdateFactory(api)
	deleteFactory = makeContainerChildDeleteFactory(api)
	return createFactory, updateFactory, deleteFactory
}

func makeContainerChildCreateFactory[TUnified any](api ContainerChildAPI[TUnified]) func(containerName string) ExecuteContainerChildFunc[TUnified] {
	return func(containerName string) ExecuteContainerChildFunc[TUnified] {
		return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, _ string, model TUnified) error {
			methods := api.CreateMethods(c.Clientset(), txID, containerName)
			resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
				V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, model) },
				V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, model) },
				V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, model) },
			})
			if err != nil {
				return err
			}
			defer resp.Body.Close()
			return client.CheckResponse(resp, api.ResourceName+" creation in "+api.ContainerType)
		}
	}
}

func makeContainerChildUpdateFactory[TUnified any](api ContainerChildAPI[TUnified]) func(containerName string) ExecuteContainerChildFunc[TUnified] {
	return func(containerName string) ExecuteContainerChildFunc[TUnified] {
		return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, model TUnified) error {
			methods := api.UpdateMethods(c.Clientset(), txID, containerName)
			resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
				V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, childName, model) },
				V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, childName, model) },
				V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, childName, model) },
			})
			if err != nil {
				return err
			}
			defer resp.Body.Close()
			return client.CheckResponse(resp, api.ResourceName+" update in "+api.ContainerType)
		}
	}
}

func makeContainerChildDeleteFactory[TUnified any](api ContainerChildAPI[TUnified]) func(containerName string) ExecuteContainerChildFunc[TUnified] {
	return func(containerName string) ExecuteContainerChildFunc[TUnified] {
		return func(ctx context.Context, c *client.DataplaneClient, txID string, _ string, childName string, _ TUnified) error {
			methods := api.DeleteMethods(c.Clientset(), txID, containerName)
			resp, err := c.Dispatch(ctx, client.CallFunc[*http.Response]{
				V32: func(_ *v32.Client) (*http.Response, error) { return methods.V32(ctx, childName) },
				V31: func(_ *v31.Client) (*http.Response, error) { return methods.V31(ctx, childName) },
				V30: func(_ *v30.Client) (*http.Response, error) { return methods.V30(ctx, childName) },
			})
			if err != nil {
				return err
			}
			defer resp.Body.Close()
			return client.CheckResponse(resp, api.ResourceName+" deletion from "+api.ContainerType)
		}
	}
}
