// Package executors provides pre-built executor functions for HAProxy configuration operations.
//
// This file defines generic API descriptor types that capture the versioned API method signatures.
// These descriptors enable executor generators to eliminate repetitive boilerplate while maintaining
// full compile-time type safety through Go generics.
package executors

import (
	"context"
	"net/http"

	"haproxy-template-ic/pkg/dataplane/client"
)

// =============================================================================
// Top-Level Resource API Descriptors
// =============================================================================

// TopLevelAPI describes versioned API methods for a top-level resource (backend, frontend, etc.).
// TUnified is the unified dataplaneapi model type (e.g., *dataplaneapi.Backend).
type TopLevelAPI[TUnified any] struct {
	// ResourceName is used for error messages (e.g., "backend", "frontend")
	ResourceName string

	// CreateMethods returns version-specific create functions bound to the given transaction
	CreateMethods func(cs *client.Clientset, txID string) TopLevelCreate[TUnified]

	// UpdateMethods returns version-specific update functions bound to the given transaction
	UpdateMethods func(cs *client.Clientset, txID string) TopLevelUpdate[TUnified]

	// DeleteMethods returns version-specific delete functions bound to the given transaction
	DeleteMethods func(cs *client.Clientset, txID string) TopLevelDelete
}

// TopLevelCreate holds version-specific create functions for top-level resources.
type TopLevelCreate[TUnified any] struct {
	V32 func(ctx context.Context, model TUnified) (*http.Response, error)
	V31 func(ctx context.Context, model TUnified) (*http.Response, error)
	V30 func(ctx context.Context, model TUnified) (*http.Response, error)
}

// TopLevelUpdate holds version-specific update functions for top-level resources.
type TopLevelUpdate[TUnified any] struct {
	V32 func(ctx context.Context, name string, model TUnified) (*http.Response, error)
	V31 func(ctx context.Context, name string, model TUnified) (*http.Response, error)
	V30 func(ctx context.Context, name string, model TUnified) (*http.Response, error)
}

// TopLevelDelete holds version-specific delete functions for top-level resources.
type TopLevelDelete struct {
	V32 func(ctx context.Context, name string) (*http.Response, error)
	V31 func(ctx context.Context, name string) (*http.Response, error)
	V30 func(ctx context.Context, name string) (*http.Response, error)
}

// =============================================================================
// Indexed Child Resource API Descriptors
// =============================================================================

// IndexedChildAPI describes versioned API methods for indexed child resources
// (ACLs, filters, rules, etc. within a frontend or backend).
// TUnified is the unified dataplaneapi model type (e.g., *dataplaneapi.Acl).
type IndexedChildAPI[TUnified any] struct {
	// ResourceName is used for error messages (e.g., "ACL", "filter")
	ResourceName string

	// ParentType describes the parent context (e.g., "frontend", "backend")
	ParentType string

	// CreateMethods returns version-specific create functions bound to the given transaction
	CreateMethods func(cs *client.Clientset, txID string) IndexedChildCreate[TUnified]

	// UpdateMethods returns version-specific update functions bound to the given transaction
	UpdateMethods func(cs *client.Clientset, txID string) IndexedChildUpdate[TUnified]

	// DeleteMethods returns version-specific delete functions bound to the given transaction
	DeleteMethods func(cs *client.Clientset, txID string) IndexedChildDelete
}

// IndexedChildCreate holds version-specific create functions for indexed child resources.
type IndexedChildCreate[TUnified any] struct {
	V32 func(ctx context.Context, parent string, index int, model TUnified) (*http.Response, error)
	V31 func(ctx context.Context, parent string, index int, model TUnified) (*http.Response, error)
	V30 func(ctx context.Context, parent string, index int, model TUnified) (*http.Response, error)
}

// IndexedChildUpdate holds version-specific update functions for indexed child resources.
type IndexedChildUpdate[TUnified any] struct {
	V32 func(ctx context.Context, parent string, index int, model TUnified) (*http.Response, error)
	V31 func(ctx context.Context, parent string, index int, model TUnified) (*http.Response, error)
	V30 func(ctx context.Context, parent string, index int, model TUnified) (*http.Response, error)
}

// IndexedChildDelete holds version-specific delete functions for indexed child resources.
type IndexedChildDelete struct {
	V32 func(ctx context.Context, parent string, index int) (*http.Response, error)
	V31 func(ctx context.Context, parent string, index int) (*http.Response, error)
	V30 func(ctx context.Context, parent string, index int) (*http.Response, error)
}

// =============================================================================
// Named Child Resource API Descriptors
// =============================================================================

// NamedChildAPI describes versioned API methods for named child resources
// (binds in frontends, servers in backends, server templates in backends).
// TUnified is the unified dataplaneapi model type (e.g., *dataplaneapi.Bind).
type NamedChildAPI[TUnified any] struct {
	// ResourceName is used for error messages (e.g., "bind", "server")
	ResourceName string

	// ParentType describes the parent context (e.g., "frontend", "backend")
	ParentType string

	// CreateMethods returns version-specific create functions bound to the given transaction and parent
	CreateMethods func(cs *client.Clientset, txID, parentName string) NamedChildCreate[TUnified]

	// UpdateMethods returns version-specific update functions bound to the given transaction and parent
	UpdateMethods func(cs *client.Clientset, txID, parentName string) NamedChildUpdate[TUnified]

	// DeleteMethods returns version-specific delete functions bound to the given transaction and parent
	DeleteMethods func(cs *client.Clientset, txID, parentName string) NamedChildDelete
}

// NamedChildCreate holds version-specific create functions for named child resources.
type NamedChildCreate[TUnified any] struct {
	V32 func(ctx context.Context, model TUnified) (*http.Response, error)
	V31 func(ctx context.Context, model TUnified) (*http.Response, error)
	V30 func(ctx context.Context, model TUnified) (*http.Response, error)
}

// NamedChildUpdate holds version-specific update functions for named child resources.
type NamedChildUpdate[TUnified any] struct {
	V32 func(ctx context.Context, childName string, model TUnified) (*http.Response, error)
	V31 func(ctx context.Context, childName string, model TUnified) (*http.Response, error)
	V30 func(ctx context.Context, childName string, model TUnified) (*http.Response, error)
}

// NamedChildDelete holds version-specific delete functions for named child resources.
type NamedChildDelete struct {
	V32 func(ctx context.Context, childName string) (*http.Response, error)
	V31 func(ctx context.Context, childName string) (*http.Response, error)
	V30 func(ctx context.Context, childName string) (*http.Response, error)
}

// =============================================================================
// Container Child Resource API Descriptors
// =============================================================================

// ContainerChildAPI describes versioned API methods for container child resources
// (users in userlists, mailer entries in mailers, peer entries in peers).
// TUnified is the unified dataplaneapi model type (e.g., *dataplaneapi.User).
type ContainerChildAPI[TUnified any] struct {
	// ResourceName is used for error messages (e.g., "user", "mailer entry")
	ResourceName string

	// ContainerType describes the container context (e.g., "userlist", "mailers")
	ContainerType string

	// CreateMethods returns version-specific create functions bound to the transaction and container
	CreateMethods func(cs *client.Clientset, txID, containerName string) ContainerChildCreate[TUnified]

	// UpdateMethods returns version-specific update functions bound to the transaction and container
	UpdateMethods func(cs *client.Clientset, txID, containerName string) ContainerChildUpdate[TUnified]

	// DeleteMethods returns version-specific delete functions bound to the transaction and container
	DeleteMethods func(cs *client.Clientset, txID, containerName string) ContainerChildDelete
}

// ContainerChildCreate holds version-specific create functions for container child resources.
type ContainerChildCreate[TUnified any] struct {
	V32 func(ctx context.Context, model TUnified) (*http.Response, error)
	V31 func(ctx context.Context, model TUnified) (*http.Response, error)
	V30 func(ctx context.Context, model TUnified) (*http.Response, error)
}

// ContainerChildUpdate holds version-specific update functions for container child resources.
type ContainerChildUpdate[TUnified any] struct {
	V32 func(ctx context.Context, childName string, model TUnified) (*http.Response, error)
	V31 func(ctx context.Context, childName string, model TUnified) (*http.Response, error)
	V30 func(ctx context.Context, childName string, model TUnified) (*http.Response, error)
}

// ContainerChildDelete holds version-specific delete functions for container child resources.
type ContainerChildDelete struct {
	V32 func(ctx context.Context, childName string) (*http.Response, error)
	V31 func(ctx context.Context, childName string) (*http.Response, error)
	V30 func(ctx context.Context, childName string) (*http.Response, error)
}

// =============================================================================
// Executor Function Type Aliases
// =============================================================================

// ExecuteTopLevelFunc is the function signature for top-level resource executors.
type ExecuteTopLevelFunc[TUnified any] func(
	ctx context.Context,
	c *client.DataplaneClient,
	txID string,
	model TUnified,
	name string,
) error

// ExecuteIndexedChildFunc is the function signature for indexed child resource executors.
type ExecuteIndexedChildFunc[TUnified any] func(
	ctx context.Context,
	c *client.DataplaneClient,
	txID string,
	parent string,
	index int,
	model TUnified,
) error

// ExecuteNamedChildFunc is the function signature for named child resource executors.
type ExecuteNamedChildFunc[TUnified any] func(
	ctx context.Context,
	c *client.DataplaneClient,
	txID string,
	parent string,
	childName string,
	model TUnified,
) error

// ExecuteContainerChildFunc is the function signature for container child resource executors.
type ExecuteContainerChildFunc[TUnified any] func(
	ctx context.Context,
	c *client.DataplaneClient,
	txID string,
	containerName string,
	childName string,
	model TUnified,
) error
