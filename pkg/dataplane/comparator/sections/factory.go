// Package sections provides factory functions for creating HAProxy configuration operations.
//
// These factory functions use generic operation types to eliminate repetitive boilerplate
// while maintaining type safety and compile-time verification.
package sections

import (
	"context"
	"fmt"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/dataplane/client"
	"haproxy-template-ic/pkg/dataplane/comparator/sections/executors"
	"haproxy-template-ic/pkg/dataplane/transform"
	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

// Operation defines the interface for all HAProxy configuration operations.
// This interface is implemented by all generic operation types (TopLevelOp, IndexChildOp, etc.)
type Operation interface {
	// Type returns the operation type (Create, Update, Delete)
	Type() OperationType

	// Section returns the configuration section this operation affects
	Section() string

	// Priority returns the execution priority (lower = first for creates, higher = first for deletes)
	Priority() int

	// Execute performs the operation via the Dataplane API
	Execute(ctx context.Context, c *client.DataplaneClient, txID string) error

	// Describe returns a human-readable description of the operation
	Describe() string
}

// ptrStr safely dereferences a string pointer, returning empty string if nil.
func ptrStr(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// =============================================================================
// Backend Factory Functions
// =============================================================================

// NewBackendCreate creates an operation to create a backend.
func NewBackendCreate(backend *models.Backend) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"backend",
		PriorityBackend,
		backend,
		transform.ToAPIBackend,
		BackendName,
		executors.BackendCreate(),
		DescribeTopLevel(OperationCreate, "backend", backend.Name),
	)
}

// NewBackendUpdate creates an operation to update a backend.
func NewBackendUpdate(backend *models.Backend) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"backend",
		PriorityBackend,
		backend,
		transform.ToAPIBackend,
		BackendName,
		executors.BackendUpdate(),
		DescribeTopLevel(OperationUpdate, "backend", backend.Name),
	)
}

// NewBackendDelete creates an operation to delete a backend.
func NewBackendDelete(backend *models.Backend) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"backend",
		PriorityBackend,
		backend,
		NilBackend,
		BackendName,
		executors.BackendDelete(),
		DescribeTopLevel(OperationDelete, "backend", backend.Name),
	)
}

// =============================================================================
// Frontend Factory Functions
// =============================================================================

// NewFrontendCreate creates an operation to create a frontend.
func NewFrontendCreate(frontend *models.Frontend) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"frontend",
		PriorityFrontend,
		frontend,
		transform.ToAPIFrontend,
		FrontendName,
		executors.FrontendCreate(),
		DescribeTopLevel(OperationCreate, "frontend", frontend.Name),
	)
}

// NewFrontendUpdate creates an operation to update a frontend.
func NewFrontendUpdate(frontend *models.Frontend) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"frontend",
		PriorityFrontend,
		frontend,
		transform.ToAPIFrontend,
		FrontendName,
		executors.FrontendUpdate(),
		DescribeTopLevel(OperationUpdate, "frontend", frontend.Name),
	)
}

// NewFrontendDelete creates an operation to delete a frontend.
func NewFrontendDelete(frontend *models.Frontend) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"frontend",
		PriorityFrontend,
		frontend,
		NilFrontend,
		FrontendName,
		executors.FrontendDelete(),
		DescribeTopLevel(OperationDelete, "frontend", frontend.Name),
	)
}

// =============================================================================
// Defaults Factory Functions
// =============================================================================

// NewDefaultsCreate creates an operation to create a defaults section.
func NewDefaultsCreate(defaults *models.Defaults) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"defaults",
		PriorityDefaults,
		defaults,
		transform.ToAPIDefaults,
		DefaultsName,
		executors.DefaultsCreate(),
		DescribeTopLevel(OperationCreate, "defaults section", defaults.Name),
	)
}

// NewDefaultsUpdate creates an operation to update a defaults section.
func NewDefaultsUpdate(defaults *models.Defaults) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"defaults",
		PriorityDefaults,
		defaults,
		transform.ToAPIDefaults,
		DefaultsName,
		executors.DefaultsUpdate(),
		DescribeTopLevel(OperationUpdate, "defaults section", defaults.Name),
	)
}

// NewDefaultsDelete creates an operation to delete a defaults section.
func NewDefaultsDelete(defaults *models.Defaults) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"defaults",
		PriorityDefaults,
		defaults,
		NilDefaults,
		DefaultsName,
		executors.DefaultsDelete(),
		DescribeTopLevel(OperationDelete, "defaults section", defaults.Name),
	)
}

// =============================================================================
// Global Factory Functions (Singleton - only update)
// =============================================================================

// NewGlobalUpdate creates an operation to update the global section.
func NewGlobalUpdate(global *models.Global) Operation {
	return NewSingletonOp(
		"global",
		PriorityGlobal,
		global,
		transform.ToAPIGlobal,
		executors.GlobalUpdate(),
		func() string { return "Update global section" },
	)
}

// =============================================================================
// ACL Factory Functions (Index-based child)
// =============================================================================

// NewACLFrontendCreate creates an operation to create an ACL in a frontend.
func NewACLFrontendCreate(frontendName string, acl *models.ACL, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"acl",
		PriorityACL,
		frontendName,
		index,
		acl,
		transform.ToAPIACL,
		executors.ACLFrontendCreate(),
		DescribeACL(OperationCreate, acl.ACLName, "frontend", frontendName),
	)
}

// NewACLFrontendUpdate creates an operation to update an ACL in a frontend.
func NewACLFrontendUpdate(frontendName string, acl *models.ACL, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"acl",
		PriorityACL,
		frontendName,
		index,
		acl,
		transform.ToAPIACL,
		executors.ACLFrontendUpdate(),
		DescribeACL(OperationUpdate, acl.ACLName, "frontend", frontendName),
	)
}

// NewACLFrontendDelete creates an operation to delete an ACL from a frontend.
func NewACLFrontendDelete(frontendName string, acl *models.ACL, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"acl",
		PriorityACL,
		frontendName,
		index,
		acl,
		NilACL,
		executors.ACLFrontendDelete(),
		DescribeACL(OperationDelete, acl.ACLName, "frontend", frontendName),
	)
}

// NewACLBackendCreate creates an operation to create an ACL in a backend.
func NewACLBackendCreate(backendName string, acl *models.ACL, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"acl",
		PriorityACL,
		backendName,
		index,
		acl,
		transform.ToAPIACL,
		executors.ACLBackendCreate(),
		DescribeACL(OperationCreate, acl.ACLName, "backend", backendName),
	)
}

// NewACLBackendUpdate creates an operation to update an ACL in a backend.
func NewACLBackendUpdate(backendName string, acl *models.ACL, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"acl",
		PriorityACL,
		backendName,
		index,
		acl,
		transform.ToAPIACL,
		executors.ACLBackendUpdate(),
		DescribeACL(OperationUpdate, acl.ACLName, "backend", backendName),
	)
}

// NewACLBackendDelete creates an operation to delete an ACL from a backend.
func NewACLBackendDelete(backendName string, acl *models.ACL, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"acl",
		PriorityACL,
		backendName,
		index,
		acl,
		NilACL,
		executors.ACLBackendDelete(),
		DescribeACL(OperationDelete, acl.ACLName, "backend", backendName),
	)
}

// =============================================================================
// HTTP Request Rule Factory Functions (Index-based child)
// =============================================================================

// NewHTTPRequestRuleFrontendCreate creates an operation to create an HTTP request rule in a frontend.
func NewHTTPRequestRuleFrontendCreate(frontendName string, rule *models.HTTPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"http_request_rule",
		PriorityRule, // HTTP request rules use PriorityRule
		frontendName,
		index,
		rule,
		transform.ToAPIHTTPRequestRule,
		executors.HTTPRequestRuleFrontendCreate(),
		func() string {
			return fmt.Sprintf("Create HTTP request rule at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewHTTPRequestRuleFrontendUpdate creates an operation to update an HTTP request rule in a frontend.
func NewHTTPRequestRuleFrontendUpdate(frontendName string, rule *models.HTTPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"http_request_rule",
		PriorityRule, // HTTP request rules use PriorityRule
		frontendName,
		index,
		rule,
		transform.ToAPIHTTPRequestRule,
		executors.HTTPRequestRuleFrontendUpdate(),
		func() string {
			return fmt.Sprintf("Update HTTP request rule at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewHTTPRequestRuleFrontendDelete creates an operation to delete an HTTP request rule from a frontend.
func NewHTTPRequestRuleFrontendDelete(frontendName string, rule *models.HTTPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"http_request_rule",
		PriorityRule, // HTTP request rules use PriorityRule
		frontendName,
		index,
		rule,
		func(r *models.HTTPRequestRule) *dataplaneapi.HttpRequestRule { return nil },
		executors.HTTPRequestRuleFrontendDelete(),
		func() string {
			return fmt.Sprintf("Delete HTTP request rule at index %d from frontend '%s'", index, frontendName)
		},
	)
}

// NewHTTPRequestRuleBackendCreate creates an operation to create an HTTP request rule in a backend.
func NewHTTPRequestRuleBackendCreate(backendName string, rule *models.HTTPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"http_request_rule",
		PriorityRule, // HTTP request rules use PriorityRule
		backendName,
		index,
		rule,
		transform.ToAPIHTTPRequestRule,
		executors.HTTPRequestRuleBackendCreate(),
		func() string {
			return fmt.Sprintf("Create HTTP request rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewHTTPRequestRuleBackendUpdate creates an operation to update an HTTP request rule in a backend.
func NewHTTPRequestRuleBackendUpdate(backendName string, rule *models.HTTPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"http_request_rule",
		PriorityRule, // HTTP request rules use PriorityRule
		backendName,
		index,
		rule,
		transform.ToAPIHTTPRequestRule,
		executors.HTTPRequestRuleBackendUpdate(),
		func() string {
			return fmt.Sprintf("Update HTTP request rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewHTTPRequestRuleBackendDelete creates an operation to delete an HTTP request rule from a backend.
func NewHTTPRequestRuleBackendDelete(backendName string, rule *models.HTTPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"http_request_rule",
		PriorityRule, // HTTP request rules use PriorityRule
		backendName,
		index,
		rule,
		func(r *models.HTTPRequestRule) *dataplaneapi.HttpRequestRule { return nil },
		executors.HTTPRequestRuleBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete HTTP request rule at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// HTTP Response Rule Factory Functions (Index-based child)
// =============================================================================

// NewHTTPResponseRuleFrontendCreate creates an operation to create an HTTP response rule in a frontend.
func NewHTTPResponseRuleFrontendCreate(frontendName string, rule *models.HTTPResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"http_response_rule",
		PriorityRule, // HTTP response rules use PriorityRule
		frontendName,
		index,
		rule,
		transform.ToAPIHTTPResponseRule,
		executors.HTTPResponseRuleFrontendCreate(),
		func() string {
			return fmt.Sprintf("Create HTTP response rule at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewHTTPResponseRuleFrontendUpdate creates an operation to update an HTTP response rule in a frontend.
func NewHTTPResponseRuleFrontendUpdate(frontendName string, rule *models.HTTPResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"http_response_rule",
		PriorityRule, // HTTP response rules use PriorityRule
		frontendName,
		index,
		rule,
		transform.ToAPIHTTPResponseRule,
		executors.HTTPResponseRuleFrontendUpdate(),
		func() string {
			return fmt.Sprintf("Update HTTP response rule at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewHTTPResponseRuleFrontendDelete creates an operation to delete an HTTP response rule from a frontend.
func NewHTTPResponseRuleFrontendDelete(frontendName string, rule *models.HTTPResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"http_response_rule",
		PriorityRule, // HTTP response rules use PriorityRule
		frontendName,
		index,
		rule,
		func(r *models.HTTPResponseRule) *dataplaneapi.HttpResponseRule { return nil },
		executors.HTTPResponseRuleFrontendDelete(),
		func() string {
			return fmt.Sprintf("Delete HTTP response rule at index %d from frontend '%s'", index, frontendName)
		},
	)
}

// NewHTTPResponseRuleBackendCreate creates an operation to create an HTTP response rule in a backend.
func NewHTTPResponseRuleBackendCreate(backendName string, rule *models.HTTPResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"http_response_rule",
		PriorityRule, // HTTP response rules use PriorityRule
		backendName,
		index,
		rule,
		transform.ToAPIHTTPResponseRule,
		executors.HTTPResponseRuleBackendCreate(),
		func() string {
			return fmt.Sprintf("Create HTTP response rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewHTTPResponseRuleBackendUpdate creates an operation to update an HTTP response rule in a backend.
func NewHTTPResponseRuleBackendUpdate(backendName string, rule *models.HTTPResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"http_response_rule",
		PriorityRule, // HTTP response rules use PriorityRule
		backendName,
		index,
		rule,
		transform.ToAPIHTTPResponseRule,
		executors.HTTPResponseRuleBackendUpdate(),
		func() string {
			return fmt.Sprintf("Update HTTP response rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewHTTPResponseRuleBackendDelete creates an operation to delete an HTTP response rule from a backend.
func NewHTTPResponseRuleBackendDelete(backendName string, rule *models.HTTPResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"http_response_rule",
		PriorityRule, // HTTP response rules use PriorityRule
		backendName,
		index,
		rule,
		func(r *models.HTTPResponseRule) *dataplaneapi.HttpResponseRule { return nil },
		executors.HTTPResponseRuleBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete HTTP response rule at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// Backend Switching Rule Factory Functions (Index-based child)
// =============================================================================

// NewBackendSwitchingRuleFrontendCreate creates an operation to create a backend switching rule.
func NewBackendSwitchingRuleFrontendCreate(frontendName string, rule *models.BackendSwitchingRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"backend_switching_rule",
		PriorityBackendSwitchingRule,
		frontendName,
		index,
		rule,
		transform.ToAPIBackendSwitchingRule,
		executors.BackendSwitchingRuleCreate(),
		func() string {
			return fmt.Sprintf("Create backend switching rule at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewBackendSwitchingRuleFrontendUpdate creates an operation to update a backend switching rule.
func NewBackendSwitchingRuleFrontendUpdate(frontendName string, rule *models.BackendSwitchingRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"backend_switching_rule",
		PriorityBackendSwitchingRule,
		frontendName,
		index,
		rule,
		transform.ToAPIBackendSwitchingRule,
		executors.BackendSwitchingRuleUpdate(),
		func() string {
			return fmt.Sprintf("Update backend switching rule at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewBackendSwitchingRuleFrontendDelete creates an operation to delete a backend switching rule.
func NewBackendSwitchingRuleFrontendDelete(frontendName string, rule *models.BackendSwitchingRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"backend_switching_rule",
		PriorityBackendSwitchingRule,
		frontendName,
		index,
		rule,
		func(r *models.BackendSwitchingRule) *dataplaneapi.BackendSwitchingRule { return nil },
		executors.BackendSwitchingRuleDelete(),
		func() string {
			return fmt.Sprintf("Delete backend switching rule at index %d from frontend '%s'", index, frontendName)
		},
	)
}

// =============================================================================
// Filter Factory Functions (Index-based child)
// =============================================================================

// NewFilterFrontendCreate creates an operation to create a filter in a frontend.
func NewFilterFrontendCreate(frontendName string, filter *models.Filter, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"filter",
		PriorityFilter,
		frontendName,
		index,
		filter,
		transform.ToAPIFilter,
		executors.FilterFrontendCreate(),
		func() string { return fmt.Sprintf("Create filter at index %d in frontend '%s'", index, frontendName) },
	)
}

// NewFilterFrontendUpdate creates an operation to update a filter in a frontend.
func NewFilterFrontendUpdate(frontendName string, filter *models.Filter, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"filter",
		PriorityFilter,
		frontendName,
		index,
		filter,
		transform.ToAPIFilter,
		executors.FilterFrontendUpdate(),
		func() string { return fmt.Sprintf("Update filter at index %d in frontend '%s'", index, frontendName) },
	)
}

// NewFilterFrontendDelete creates an operation to delete a filter from a frontend.
func NewFilterFrontendDelete(frontendName string, filter *models.Filter, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"filter",
		PriorityFilter,
		frontendName,
		index,
		filter,
		func(f *models.Filter) *dataplaneapi.Filter { return nil },
		executors.FilterFrontendDelete(),
		func() string { return fmt.Sprintf("Delete filter at index %d from frontend '%s'", index, frontendName) },
	)
}

// NewFilterBackendCreate creates an operation to create a filter in a backend.
func NewFilterBackendCreate(backendName string, filter *models.Filter, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"filter",
		PriorityFilter,
		backendName,
		index,
		filter,
		transform.ToAPIFilter,
		executors.FilterBackendCreate(),
		func() string { return fmt.Sprintf("Create filter at index %d in backend '%s'", index, backendName) },
	)
}

// NewFilterBackendUpdate creates an operation to update a filter in a backend.
func NewFilterBackendUpdate(backendName string, filter *models.Filter, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"filter",
		PriorityFilter,
		backendName,
		index,
		filter,
		transform.ToAPIFilter,
		executors.FilterBackendUpdate(),
		func() string { return fmt.Sprintf("Update filter at index %d in backend '%s'", index, backendName) },
	)
}

// NewFilterBackendDelete creates an operation to delete a filter from a backend.
func NewFilterBackendDelete(backendName string, filter *models.Filter, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"filter",
		PriorityFilter,
		backendName,
		index,
		filter,
		func(f *models.Filter) *dataplaneapi.Filter { return nil },
		executors.FilterBackendDelete(),
		func() string { return fmt.Sprintf("Delete filter at index %d from backend '%s'", index, backendName) },
	)
}

// =============================================================================
// Log Target Factory Functions (Index-based child)
// =============================================================================

// NewLogTargetFrontendCreate creates an operation to create a log target in a frontend.
func NewLogTargetFrontendCreate(frontendName string, logTarget *models.LogTarget, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"log_target",
		PriorityLogTarget,
		frontendName,
		index,
		logTarget,
		transform.ToAPILogTarget,
		executors.LogTargetFrontendCreate(),
		func() string {
			return fmt.Sprintf("Create log target at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewLogTargetFrontendUpdate creates an operation to update a log target in a frontend.
func NewLogTargetFrontendUpdate(frontendName string, logTarget *models.LogTarget, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"log_target",
		PriorityLogTarget,
		frontendName,
		index,
		logTarget,
		transform.ToAPILogTarget,
		executors.LogTargetFrontendUpdate(),
		func() string {
			return fmt.Sprintf("Update log target at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewLogTargetFrontendDelete creates an operation to delete a log target from a frontend.
func NewLogTargetFrontendDelete(frontendName string, logTarget *models.LogTarget, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"log_target",
		PriorityLogTarget,
		frontendName,
		index,
		logTarget,
		func(l *models.LogTarget) *dataplaneapi.LogTarget { return nil },
		executors.LogTargetFrontendDelete(),
		func() string {
			return fmt.Sprintf("Delete log target at index %d from frontend '%s'", index, frontendName)
		},
	)
}

// NewLogTargetBackendCreate creates an operation to create a log target in a backend.
func NewLogTargetBackendCreate(backendName string, logTarget *models.LogTarget, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"log_target",
		PriorityLogTarget,
		backendName,
		index,
		logTarget,
		transform.ToAPILogTarget,
		executors.LogTargetBackendCreate(),
		func() string { return fmt.Sprintf("Create log target at index %d in backend '%s'", index, backendName) },
	)
}

// NewLogTargetBackendUpdate creates an operation to update a log target in a backend.
func NewLogTargetBackendUpdate(backendName string, logTarget *models.LogTarget, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"log_target",
		PriorityLogTarget,
		backendName,
		index,
		logTarget,
		transform.ToAPILogTarget,
		executors.LogTargetBackendUpdate(),
		func() string { return fmt.Sprintf("Update log target at index %d in backend '%s'", index, backendName) },
	)
}

// NewLogTargetBackendDelete creates an operation to delete a log target from a backend.
func NewLogTargetBackendDelete(backendName string, logTarget *models.LogTarget, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"log_target",
		PriorityLogTarget,
		backendName,
		index,
		logTarget,
		func(l *models.LogTarget) *dataplaneapi.LogTarget { return nil },
		executors.LogTargetBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete log target at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// Bind Factory Functions (Name-based child)
// Note: Binds use dataplaneapi.Bind directly (already transformed before factory call)
// =============================================================================

// identityBindAPI returns the bind as-is (already API type).
func identityBindAPI(b *dataplaneapi.Bind) *dataplaneapi.Bind { return b }

// NewBindFrontendCreate creates an operation to create a bind in a frontend.
func NewBindFrontendCreate(frontendName, bindName string, bind *dataplaneapi.Bind) Operation {
	return NewNameChildOp(
		OperationCreate,
		"bind",
		PriorityBind,
		frontendName,
		bindName,
		bind,
		identityBindAPI,
		executors.BindFrontendCreate(frontendName),
		DescribeNamedChild(OperationCreate, "bind", bindName, "frontend", frontendName),
	)
}

// NewBindFrontendUpdate creates an operation to update a bind in a frontend.
func NewBindFrontendUpdate(frontendName, bindName string, bind *dataplaneapi.Bind) Operation {
	return NewNameChildOp(
		OperationUpdate,
		"bind",
		PriorityBind,
		frontendName,
		bindName,
		bind,
		identityBindAPI,
		executors.BindFrontendUpdate(frontendName),
		DescribeNamedChild(OperationUpdate, "bind", bindName, "frontend", frontendName),
	)
}

// NewBindFrontendDelete creates an operation to delete a bind from a frontend.
func NewBindFrontendDelete(frontendName, bindName string, bind *dataplaneapi.Bind) Operation {
	return NewNameChildOp(
		OperationDelete,
		"bind",
		PriorityBind,
		frontendName,
		bindName,
		bind,
		NilBindAPI,
		executors.BindFrontendDelete(frontendName),
		DescribeNamedChild(OperationDelete, "bind", bindName, "frontend", frontendName),
	)
}

// =============================================================================
// User Factory Functions (Container child)
// =============================================================================

// NewUserCreate creates an operation to create a user in a userlist.
func NewUserCreate(userlistName string, user *models.User) Operation {
	return NewContainerChildOp(
		OperationCreate,
		"user",
		PriorityUser,
		userlistName,
		user,
		transform.ToAPIUser,
		UserName,
		executors.UserCreate(userlistName),
		DescribeContainerChild(OperationCreate, "user", user.Username, "userlist", userlistName),
	)
}

// NewUserUpdate creates an operation to update a user in a userlist.
func NewUserUpdate(userlistName string, user *models.User) Operation {
	return NewContainerChildOp(
		OperationUpdate,
		"user",
		PriorityUser,
		userlistName,
		user,
		transform.ToAPIUser,
		UserName,
		executors.UserUpdate(userlistName),
		DescribeContainerChild(OperationUpdate, "user", user.Username, "userlist", userlistName),
	)
}

// NewUserDelete creates an operation to delete a user from a userlist.
func NewUserDelete(userlistName string, user *models.User) Operation {
	return NewContainerChildOp(
		OperationDelete,
		"user",
		PriorityUser,
		userlistName,
		user,
		NilUser,
		UserName,
		executors.UserDelete(userlistName),
		DescribeContainerChild(OperationDelete, "user", user.Username, "userlist", userlistName),
	)
}

// =============================================================================
// Mailer Entry Factory Functions (Container child)
// =============================================================================

// NewMailerEntryCreate creates an operation to create a mailer entry.
func NewMailerEntryCreate(mailersName string, entry *models.MailerEntry) Operation {
	return NewContainerChildOp(
		OperationCreate,
		"mailer_entry",
		PriorityMailers,
		mailersName,
		entry,
		transform.ToAPIMailerEntry,
		MailerEntryName,
		executors.MailerEntryCreate(mailersName),
		DescribeContainerChild(OperationCreate, "mailer entry", entry.Name, "mailers", mailersName),
	)
}

// NewMailerEntryUpdate creates an operation to update a mailer entry.
func NewMailerEntryUpdate(mailersName string, entry *models.MailerEntry) Operation {
	return NewContainerChildOp(
		OperationUpdate,
		"mailer_entry",
		PriorityMailers,
		mailersName,
		entry,
		transform.ToAPIMailerEntry,
		MailerEntryName,
		executors.MailerEntryUpdate(mailersName),
		DescribeContainerChild(OperationUpdate, "mailer entry", entry.Name, "mailers", mailersName),
	)
}

// NewMailerEntryDelete creates an operation to delete a mailer entry.
func NewMailerEntryDelete(mailersName string, entry *models.MailerEntry) Operation {
	return NewContainerChildOp(
		OperationDelete,
		"mailer_entry",
		PriorityMailers,
		mailersName,
		entry,
		NilMailerEntry,
		MailerEntryName,
		executors.MailerEntryDelete(mailersName),
		DescribeContainerChild(OperationDelete, "mailer entry", entry.Name, "mailers", mailersName),
	)
}

// =============================================================================
// Peer Entry Factory Functions (Container child)
// =============================================================================

// NewPeerEntryCreate creates an operation to create a peer entry.
func NewPeerEntryCreate(peerSectionName string, entry *models.PeerEntry) Operation {
	return NewContainerChildOp(
		OperationCreate,
		"peer_entry",
		PriorityPeerEntry,
		peerSectionName,
		entry,
		transform.ToAPIPeerEntry,
		PeerEntryName,
		executors.PeerEntryCreate(peerSectionName),
		DescribeContainerChild(OperationCreate, "peer entry", entry.Name, "peers", peerSectionName),
	)
}

// NewPeerEntryUpdate creates an operation to update a peer entry.
func NewPeerEntryUpdate(peerSectionName string, entry *models.PeerEntry) Operation {
	return NewContainerChildOp(
		OperationUpdate,
		"peer_entry",
		PriorityPeerEntry,
		peerSectionName,
		entry,
		transform.ToAPIPeerEntry,
		PeerEntryName,
		executors.PeerEntryUpdate(peerSectionName),
		DescribeContainerChild(OperationUpdate, "peer entry", entry.Name, "peers", peerSectionName),
	)
}

// NewPeerEntryDelete creates an operation to delete a peer entry.
func NewPeerEntryDelete(peerSectionName string, entry *models.PeerEntry) Operation {
	return NewContainerChildOp(
		OperationDelete,
		"peer_entry",
		PriorityPeerEntry,
		peerSectionName,
		entry,
		NilPeerEntry,
		PeerEntryName,
		executors.PeerEntryDelete(peerSectionName),
		DescribeContainerChild(OperationDelete, "peer entry", entry.Name, "peers", peerSectionName),
	)
}

// =============================================================================
// Nameserver Factory Functions (Container child)
// =============================================================================

// NewNameserverCreate creates an operation to create a nameserver in a resolver.
func NewNameserverCreate(resolverName string, nameserver *models.Nameserver) Operation {
	return NewContainerChildOp(
		OperationCreate,
		"nameserver",
		PriorityResolver,
		resolverName,
		nameserver,
		transform.ToAPINameserver,
		NameserverName,
		executors.NameserverCreate(resolverName),
		DescribeContainerChild(OperationCreate, "nameserver", nameserver.Name, "resolver", resolverName),
	)
}

// NewNameserverUpdate creates an operation to update a nameserver in a resolver.
func NewNameserverUpdate(resolverName string, nameserver *models.Nameserver) Operation {
	return NewContainerChildOp(
		OperationUpdate,
		"nameserver",
		PriorityResolver,
		resolverName,
		nameserver,
		transform.ToAPINameserver,
		NameserverName,
		executors.NameserverUpdate(resolverName),
		DescribeContainerChild(OperationUpdate, "nameserver", nameserver.Name, "resolver", resolverName),
	)
}

// NewNameserverDelete creates an operation to delete a nameserver from a resolver.
func NewNameserverDelete(resolverName string, nameserver *models.Nameserver) Operation {
	return NewContainerChildOp(
		OperationDelete,
		"nameserver",
		PriorityResolver,
		resolverName,
		nameserver,
		NilNameserver,
		NameserverName,
		executors.NameserverDelete(resolverName),
		DescribeContainerChild(OperationDelete, "nameserver", nameserver.Name, "resolver", resolverName),
	)
}

// =============================================================================
// Server Factory Functions (Name-based child)
// =============================================================================

// NewServerCreate creates an operation to create a server in a backend.
func NewServerCreate(backendName string, server *models.Server) Operation {
	return NewNameChildOp(
		OperationCreate,
		"server",
		PriorityServer,
		backendName,
		server.Name,
		server,
		transform.ToAPIServer,
		executors.ServerCreate(backendName),
		DescribeNamedChild(OperationCreate, "server", server.Name, "backend", backendName),
	)
}

// NewServerUpdate creates an operation to update a server in a backend.
func NewServerUpdate(backendName string, server *models.Server) Operation {
	return NewNameChildOp(
		OperationUpdate,
		"server",
		PriorityServer,
		backendName,
		server.Name,
		server,
		transform.ToAPIServer,
		executors.ServerUpdate(backendName),
		DescribeNamedChild(OperationUpdate, "server", server.Name, "backend", backendName),
	)
}

// NewServerDelete creates an operation to delete a server from a backend.
func NewServerDelete(backendName string, server *models.Server) Operation {
	return NewNameChildOp(
		OperationDelete,
		"server",
		PriorityServer,
		backendName,
		server.Name,
		server,
		NilServer,
		executors.ServerDelete(backendName),
		DescribeNamedChild(OperationDelete, "server", server.Name, "backend", backendName),
	)
}

// =============================================================================
// Server Template Factory Functions (Name-based child)
// =============================================================================

// NewServerTemplateCreate creates an operation to create a server template in a backend.
func NewServerTemplateCreate(backendName string, serverTemplate *models.ServerTemplate) Operation {
	return NewNameChildOp(
		OperationCreate,
		"server_template",
		PriorityServer, // Server templates use same priority as servers
		backendName,
		serverTemplate.Prefix,
		serverTemplate,
		transform.ToAPIServerTemplate,
		executors.ServerTemplateCreate(backendName),
		DescribeNamedChild(OperationCreate, "server template", serverTemplate.Prefix, "backend", backendName),
	)
}

// NewServerTemplateUpdate creates an operation to update a server template in a backend.
func NewServerTemplateUpdate(backendName string, serverTemplate *models.ServerTemplate) Operation {
	return NewNameChildOp(
		OperationUpdate,
		"server_template",
		PriorityServer, // Server templates use same priority as servers
		backendName,
		serverTemplate.Prefix,
		serverTemplate,
		transform.ToAPIServerTemplate,
		executors.ServerTemplateUpdate(backendName),
		DescribeNamedChild(OperationUpdate, "server template", serverTemplate.Prefix, "backend", backendName),
	)
}

// NewServerTemplateDelete creates an operation to delete a server template from a backend.
func NewServerTemplateDelete(backendName string, serverTemplate *models.ServerTemplate) Operation {
	return NewNameChildOp(
		OperationDelete,
		"server_template",
		PriorityServer, // Server templates use same priority as servers
		backendName,
		serverTemplate.Prefix,
		serverTemplate,
		NilServerTemplate,
		executors.ServerTemplateDelete(backendName),
		DescribeNamedChild(OperationDelete, "server template", serverTemplate.Prefix, "backend", backendName),
	)
}

// =============================================================================
// Cache Factory Functions
// =============================================================================

// NewCacheCreate creates an operation to create a cache section.
func NewCacheCreate(cache *models.Cache) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"cache",
		PriorityCache,
		cache,
		transform.ToAPICache,
		CacheName,
		executors.CacheCreate(),
		DescribeTopLevel(OperationCreate, "cache", CacheName(cache)),
	)
}

// NewCacheUpdate creates an operation to update a cache section.
func NewCacheUpdate(cache *models.Cache) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"cache",
		PriorityCache,
		cache,
		transform.ToAPICache,
		CacheName,
		executors.CacheUpdate(),
		DescribeTopLevel(OperationUpdate, "cache", CacheName(cache)),
	)
}

// NewCacheDelete creates an operation to delete a cache section.
func NewCacheDelete(cache *models.Cache) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"cache",
		PriorityCache,
		cache,
		NilCache,
		CacheName,
		executors.CacheDelete(),
		DescribeTopLevel(OperationDelete, "cache", CacheName(cache)),
	)
}

// =============================================================================
// HTTPErrorsSection Factory Functions
// =============================================================================

// NewHTTPErrorsSectionCreate creates an operation to create an http-errors section.
func NewHTTPErrorsSectionCreate(section *models.HTTPErrorsSection) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"http_errors",
		PriorityHTTPErrors,
		section,
		transform.ToAPIHTTPErrorsSection,
		HTTPErrorsSectionName,
		executors.HTTPErrorsSectionCreate(),
		DescribeTopLevel(OperationCreate, "http-errors", section.Name),
	)
}

// NewHTTPErrorsSectionUpdate creates an operation to update an http-errors section.
func NewHTTPErrorsSectionUpdate(section *models.HTTPErrorsSection) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"http_errors",
		PriorityHTTPErrors,
		section,
		transform.ToAPIHTTPErrorsSection,
		HTTPErrorsSectionName,
		executors.HTTPErrorsSectionUpdate(),
		DescribeTopLevel(OperationUpdate, "http-errors", section.Name),
	)
}

// NewHTTPErrorsSectionDelete creates an operation to delete an http-errors section.
func NewHTTPErrorsSectionDelete(section *models.HTTPErrorsSection) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"http_errors",
		PriorityHTTPErrors,
		section,
		NilHTTPErrorsSection,
		HTTPErrorsSectionName,
		executors.HTTPErrorsSectionDelete(),
		DescribeTopLevel(OperationDelete, "http-errors", section.Name),
	)
}

// =============================================================================
// LogForward Factory Functions
// =============================================================================

// NewLogForwardCreate creates an operation to create a log-forward section.
func NewLogForwardCreate(logForward *models.LogForward) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"log_forward",
		PriorityLogForward,
		logForward,
		transform.ToAPILogForward,
		LogForwardName,
		executors.LogForwardCreate(),
		DescribeTopLevel(OperationCreate, "log-forward", logForward.Name),
	)
}

// NewLogForwardUpdate creates an operation to update a log-forward section.
func NewLogForwardUpdate(logForward *models.LogForward) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"log_forward",
		PriorityLogForward,
		logForward,
		transform.ToAPILogForward,
		LogForwardName,
		executors.LogForwardUpdate(),
		DescribeTopLevel(OperationUpdate, "log-forward", logForward.Name),
	)
}

// NewLogForwardDelete creates an operation to delete a log-forward section.
func NewLogForwardDelete(logForward *models.LogForward) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"log_forward",
		PriorityLogForward,
		logForward,
		NilLogForward,
		LogForwardName,
		executors.LogForwardDelete(),
		DescribeTopLevel(OperationDelete, "log-forward", logForward.Name),
	)
}

// =============================================================================
// MailersSection Factory Functions
// =============================================================================

// NewMailersSectionCreate creates an operation to create a mailers section.
func NewMailersSectionCreate(section *models.MailersSection) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"mailers",
		PriorityMailers,
		section,
		transform.ToAPIMailersSection,
		MailersSectionName,
		executors.MailersSectionCreate(),
		DescribeTopLevel(OperationCreate, "mailers", section.Name),
	)
}

// NewMailersSectionUpdate creates an operation to update a mailers section.
func NewMailersSectionUpdate(section *models.MailersSection) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"mailers",
		PriorityMailers,
		section,
		transform.ToAPIMailersSection,
		MailersSectionName,
		executors.MailersSectionUpdate(),
		DescribeTopLevel(OperationUpdate, "mailers", section.Name),
	)
}

// NewMailersSectionDelete creates an operation to delete a mailers section.
func NewMailersSectionDelete(section *models.MailersSection) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"mailers",
		PriorityMailers,
		section,
		NilMailersSection,
		MailersSectionName,
		executors.MailersSectionDelete(),
		DescribeTopLevel(OperationDelete, "mailers", section.Name),
	)
}

// =============================================================================
// PeerSection Factory Functions
// Note: Update operations return an error as the API doesn't support direct updates.
// =============================================================================

// NewPeerSectionCreate creates an operation to create a peer section.
func NewPeerSectionCreate(section *models.PeerSection) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"peers",
		PriorityPeer,
		section,
		transform.ToAPIPeerSection,
		PeerSectionName,
		executors.PeerSectionCreate(),
		DescribeTopLevel(OperationCreate, "peers", section.Name),
	)
}

// NewPeerSectionUpdate creates an operation to update a peer section.
// Note: This operation will fail at execution time as the HAProxy Dataplane API
// does not support updating peer sections directly.
func NewPeerSectionUpdate(section *models.PeerSection) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"peers",
		PriorityPeer,
		section,
		transform.ToAPIPeerSection,
		PeerSectionName,
		executors.PeerSectionUpdate(),
		DescribeTopLevel(OperationUpdate, "peers", section.Name),
	)
}

// NewPeerSectionDelete creates an operation to delete a peer section.
func NewPeerSectionDelete(section *models.PeerSection) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"peers",
		PriorityPeer,
		section,
		NilPeerSection,
		PeerSectionName,
		executors.PeerSectionDelete(),
		DescribeTopLevel(OperationDelete, "peers", section.Name),
	)
}

// =============================================================================
// Program Factory Functions
// =============================================================================

// NewProgramCreate creates an operation to create a program section.
func NewProgramCreate(program *models.Program) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"program",
		PriorityProgram,
		program,
		transform.ToAPIProgram,
		ProgramName,
		executors.ProgramCreate(),
		DescribeTopLevel(OperationCreate, "program", program.Name),
	)
}

// NewProgramUpdate creates an operation to update a program section.
func NewProgramUpdate(program *models.Program) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"program",
		PriorityProgram,
		program,
		transform.ToAPIProgram,
		ProgramName,
		executors.ProgramUpdate(),
		DescribeTopLevel(OperationUpdate, "program", program.Name),
	)
}

// NewProgramDelete creates an operation to delete a program section.
func NewProgramDelete(program *models.Program) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"program",
		PriorityProgram,
		program,
		NilProgram,
		ProgramName,
		executors.ProgramDelete(),
		DescribeTopLevel(OperationDelete, "program", program.Name),
	)
}

// =============================================================================
// Resolver Factory Functions
// =============================================================================

// NewResolverCreate creates an operation to create a resolver section.
func NewResolverCreate(resolver *models.Resolver) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"resolver",
		PriorityResolver,
		resolver,
		transform.ToAPIResolver,
		ResolverName,
		executors.ResolverCreate(),
		DescribeTopLevel(OperationCreate, "resolver", resolver.Name),
	)
}

// NewResolverUpdate creates an operation to update a resolver section.
func NewResolverUpdate(resolver *models.Resolver) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"resolver",
		PriorityResolver,
		resolver,
		transform.ToAPIResolver,
		ResolverName,
		executors.ResolverUpdate(),
		DescribeTopLevel(OperationUpdate, "resolver", resolver.Name),
	)
}

// NewResolverDelete creates an operation to delete a resolver section.
func NewResolverDelete(resolver *models.Resolver) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"resolver",
		PriorityResolver,
		resolver,
		NilResolver,
		ResolverName,
		executors.ResolverDelete(),
		DescribeTopLevel(OperationDelete, "resolver", resolver.Name),
	)
}

// =============================================================================
// Ring Factory Functions
// =============================================================================

// NewRingCreate creates an operation to create a ring section.
func NewRingCreate(ring *models.Ring) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"ring",
		PriorityRing,
		ring,
		transform.ToAPIRing,
		RingName,
		executors.RingCreate(),
		DescribeTopLevel(OperationCreate, "ring", ring.Name),
	)
}

// NewRingUpdate creates an operation to update a ring section.
func NewRingUpdate(ring *models.Ring) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"ring",
		PriorityRing,
		ring,
		transform.ToAPIRing,
		RingName,
		executors.RingUpdate(),
		DescribeTopLevel(OperationUpdate, "ring", ring.Name),
	)
}

// NewRingDelete creates an operation to delete a ring section.
func NewRingDelete(ring *models.Ring) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"ring",
		PriorityRing,
		ring,
		NilRing,
		RingName,
		executors.RingDelete(),
		DescribeTopLevel(OperationDelete, "ring", ring.Name),
	)
}

// =============================================================================
// CrtStore Factory Functions
// =============================================================================

// NewCrtStoreCreate creates an operation to create a crt-store section.
func NewCrtStoreCreate(crtStore *models.CrtStore) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"crt_store",
		PriorityCrtStore,
		crtStore,
		transform.ToAPICrtStore,
		CrtStoreName,
		executors.CrtStoreCreate(),
		DescribeTopLevel(OperationCreate, "crt-store", crtStore.Name),
	)
}

// NewCrtStoreUpdate creates an operation to update a crt-store section.
func NewCrtStoreUpdate(crtStore *models.CrtStore) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"crt_store",
		PriorityCrtStore,
		crtStore,
		transform.ToAPICrtStore,
		CrtStoreName,
		executors.CrtStoreUpdate(),
		DescribeTopLevel(OperationUpdate, "crt-store", crtStore.Name),
	)
}

// NewCrtStoreDelete creates an operation to delete a crt-store section.
func NewCrtStoreDelete(crtStore *models.CrtStore) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"crt_store",
		PriorityCrtStore,
		crtStore,
		NilCrtStore,
		CrtStoreName,
		executors.CrtStoreDelete(),
		DescribeTopLevel(OperationDelete, "crt-store", crtStore.Name),
	)
}

// =============================================================================
// Userlist Factory Functions (Create/Delete only - no Update API)
// =============================================================================

// NewUserlistCreate creates an operation to create a userlist section.
func NewUserlistCreate(userlist *models.Userlist) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"userlist",
		PriorityUserlist,
		userlist,
		transform.ToAPIUserlist,
		UserlistName,
		executors.UserlistCreate(),
		DescribeTopLevel(OperationCreate, "userlist", userlist.Name),
	)
}

// NewUserlistDelete creates an operation to delete a userlist section.
func NewUserlistDelete(userlist *models.Userlist) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"userlist",
		PriorityUserlist,
		userlist,
		NilUserlist,
		UserlistName,
		executors.UserlistDelete(),
		DescribeTopLevel(OperationDelete, "userlist", userlist.Name),
	)
}

// =============================================================================
// FCGIApp Factory Functions
// =============================================================================

// NewFCGIAppCreate creates an operation to create a fcgi-app section.
func NewFCGIAppCreate(fcgiApp *models.FCGIApp) Operation {
	return NewTopLevelOp(
		OperationCreate,
		"fcgi_app",
		PriorityFCGIApp,
		fcgiApp,
		transform.ToAPIFCGIApp,
		FCGIAppName,
		executors.FCGIAppCreate(),
		DescribeTopLevel(OperationCreate, "fcgi-app", fcgiApp.Name),
	)
}

// NewFCGIAppUpdate creates an operation to update a fcgi-app section.
func NewFCGIAppUpdate(fcgiApp *models.FCGIApp) Operation {
	return NewTopLevelOp(
		OperationUpdate,
		"fcgi_app",
		PriorityFCGIApp,
		fcgiApp,
		transform.ToAPIFCGIApp,
		FCGIAppName,
		executors.FCGIAppUpdate(),
		DescribeTopLevel(OperationUpdate, "fcgi-app", fcgiApp.Name),
	)
}

// NewFCGIAppDelete creates an operation to delete a fcgi-app section.
func NewFCGIAppDelete(fcgiApp *models.FCGIApp) Operation {
	return NewTopLevelOp(
		OperationDelete,
		"fcgi_app",
		PriorityFCGIApp,
		fcgiApp,
		NilFCGIApp,
		FCGIAppName,
		executors.FCGIAppDelete(),
		DescribeTopLevel(OperationDelete, "fcgi-app", fcgiApp.Name),
	)
}

// =============================================================================
// TCP Request Rule Factory Functions (Index-based child)
// =============================================================================

// NewTCPRequestRuleFrontendCreate creates an operation to create a TCP request rule in a frontend.
func NewTCPRequestRuleFrontendCreate(frontendName string, rule *models.TCPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"tcp_request_rule",
		PriorityRule,
		frontendName,
		index,
		rule,
		transform.ToAPITCPRequestRule,
		executors.TCPRequestRuleFrontendCreate(),
		func() string {
			return fmt.Sprintf("Create TCP request rule at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewTCPRequestRuleFrontendUpdate creates an operation to update a TCP request rule in a frontend.
func NewTCPRequestRuleFrontendUpdate(frontendName string, rule *models.TCPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"tcp_request_rule",
		PriorityRule,
		frontendName,
		index,
		rule,
		transform.ToAPITCPRequestRule,
		executors.TCPRequestRuleFrontendUpdate(),
		func() string {
			return fmt.Sprintf("Update TCP request rule at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewTCPRequestRuleFrontendDelete creates an operation to delete a TCP request rule from a frontend.
func NewTCPRequestRuleFrontendDelete(frontendName string, rule *models.TCPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"tcp_request_rule",
		PriorityRule,
		frontendName,
		index,
		rule,
		func(r *models.TCPRequestRule) *dataplaneapi.TcpRequestRule { return nil },
		executors.TCPRequestRuleFrontendDelete(),
		func() string {
			return fmt.Sprintf("Delete TCP request rule at index %d from frontend '%s'", index, frontendName)
		},
	)
}

// NewTCPRequestRuleBackendCreate creates an operation to create a TCP request rule in a backend.
func NewTCPRequestRuleBackendCreate(backendName string, rule *models.TCPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"tcp_request_rule",
		PriorityRule,
		backendName,
		index,
		rule,
		transform.ToAPITCPRequestRule,
		executors.TCPRequestRuleBackendCreate(),
		func() string {
			return fmt.Sprintf("Create TCP request rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewTCPRequestRuleBackendUpdate creates an operation to update a TCP request rule in a backend.
func NewTCPRequestRuleBackendUpdate(backendName string, rule *models.TCPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"tcp_request_rule",
		PriorityRule,
		backendName,
		index,
		rule,
		transform.ToAPITCPRequestRule,
		executors.TCPRequestRuleBackendUpdate(),
		func() string {
			return fmt.Sprintf("Update TCP request rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewTCPRequestRuleBackendDelete creates an operation to delete a TCP request rule from a backend.
func NewTCPRequestRuleBackendDelete(backendName string, rule *models.TCPRequestRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"tcp_request_rule",
		PriorityRule,
		backendName,
		index,
		rule,
		func(r *models.TCPRequestRule) *dataplaneapi.TcpRequestRule { return nil },
		executors.TCPRequestRuleBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete TCP request rule at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// TCP Response Rule Factory Functions (Index-based child, Backend only)
// =============================================================================

// NewTCPResponseRuleBackendCreate creates an operation to create a TCP response rule in a backend.
func NewTCPResponseRuleBackendCreate(backendName string, rule *models.TCPResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"tcp_response_rule",
		PriorityRule,
		backendName,
		index,
		rule,
		transform.ToAPITCPResponseRule,
		executors.TCPResponseRuleBackendCreate(),
		func() string {
			return fmt.Sprintf("Create TCP response rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewTCPResponseRuleBackendUpdate creates an operation to update a TCP response rule in a backend.
func NewTCPResponseRuleBackendUpdate(backendName string, rule *models.TCPResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"tcp_response_rule",
		PriorityRule,
		backendName,
		index,
		rule,
		transform.ToAPITCPResponseRule,
		executors.TCPResponseRuleBackendUpdate(),
		func() string {
			return fmt.Sprintf("Update TCP response rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewTCPResponseRuleBackendDelete creates an operation to delete a TCP response rule from a backend.
func NewTCPResponseRuleBackendDelete(backendName string, rule *models.TCPResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"tcp_response_rule",
		PriorityRule,
		backendName,
		index,
		rule,
		func(r *models.TCPResponseRule) *dataplaneapi.TcpResponseRule { return nil },
		executors.TCPResponseRuleBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete TCP response rule at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// Stick Rule Factory Functions (Index-based child, Backend only)
// =============================================================================

// NewStickRuleBackendCreate creates an operation to create a stick rule in a backend.
func NewStickRuleBackendCreate(backendName string, rule *models.StickRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"stick_rule",
		PriorityStickRule,
		backendName,
		index,
		rule,
		transform.ToAPIStickRule,
		executors.StickRuleBackendCreate(),
		func() string {
			return fmt.Sprintf("Create stick rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewStickRuleBackendUpdate creates an operation to update a stick rule in a backend.
func NewStickRuleBackendUpdate(backendName string, rule *models.StickRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"stick_rule",
		PriorityStickRule,
		backendName,
		index,
		rule,
		transform.ToAPIStickRule,
		executors.StickRuleBackendUpdate(),
		func() string {
			return fmt.Sprintf("Update stick rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewStickRuleBackendDelete creates an operation to delete a stick rule from a backend.
func NewStickRuleBackendDelete(backendName string, rule *models.StickRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"stick_rule",
		PriorityStickRule,
		backendName,
		index,
		rule,
		func(r *models.StickRule) *dataplaneapi.StickRule { return nil },
		executors.StickRuleBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete stick rule at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// HTTP After Response Rule Factory Functions (Index-based child, Backend only)
// =============================================================================

// NewHTTPAfterResponseRuleBackendCreate creates an operation to create an HTTP after-response rule in a backend.
func NewHTTPAfterResponseRuleBackendCreate(backendName string, rule *models.HTTPAfterResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"http_after_response_rule",
		PriorityHTTPAfterRule,
		backendName,
		index,
		rule,
		transform.ToAPIHTTPAfterResponseRule,
		executors.HTTPAfterResponseRuleBackendCreate(),
		func() string {
			return fmt.Sprintf("Create HTTP after-response rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewHTTPAfterResponseRuleBackendUpdate creates an operation to update an HTTP after-response rule in a backend.
func NewHTTPAfterResponseRuleBackendUpdate(backendName string, rule *models.HTTPAfterResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"http_after_response_rule",
		PriorityHTTPAfterRule,
		backendName,
		index,
		rule,
		transform.ToAPIHTTPAfterResponseRule,
		executors.HTTPAfterResponseRuleBackendUpdate(),
		func() string {
			return fmt.Sprintf("Update HTTP after-response rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewHTTPAfterResponseRuleBackendDelete creates an operation to delete an HTTP after-response rule from a backend.
func NewHTTPAfterResponseRuleBackendDelete(backendName string, rule *models.HTTPAfterResponseRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"http_after_response_rule",
		PriorityHTTPAfterRule,
		backendName,
		index,
		rule,
		func(r *models.HTTPAfterResponseRule) *dataplaneapi.HttpAfterResponseRule { return nil },
		executors.HTTPAfterResponseRuleBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete HTTP after-response rule at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// Server Switching Rule Factory Functions (Index-based child, Backend only)
// =============================================================================

// NewServerSwitchingRuleBackendCreate creates an operation to create a server switching rule in a backend.
func NewServerSwitchingRuleBackendCreate(backendName string, rule *models.ServerSwitchingRule, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"server_switching_rule",
		PriorityServerSwitchingRule,
		backendName,
		index,
		rule,
		transform.ToAPIServerSwitchingRule,
		executors.ServerSwitchingRuleBackendCreate(),
		func() string {
			return fmt.Sprintf("Create server switching rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewServerSwitchingRuleBackendUpdate creates an operation to update a server switching rule in a backend.
func NewServerSwitchingRuleBackendUpdate(backendName string, rule *models.ServerSwitchingRule, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"server_switching_rule",
		PriorityServerSwitchingRule,
		backendName,
		index,
		rule,
		transform.ToAPIServerSwitchingRule,
		executors.ServerSwitchingRuleBackendUpdate(),
		func() string {
			return fmt.Sprintf("Update server switching rule at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewServerSwitchingRuleBackendDelete creates an operation to delete a server switching rule from a backend.
func NewServerSwitchingRuleBackendDelete(backendName string, rule *models.ServerSwitchingRule, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"server_switching_rule",
		PriorityServerSwitchingRule,
		backendName,
		index,
		rule,
		func(r *models.ServerSwitchingRule) *dataplaneapi.ServerSwitchingRule { return nil },
		executors.ServerSwitchingRuleBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete server switching rule at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// HTTP Check Factory Functions (Index-based child, Backend only)
// =============================================================================

// NewHTTPCheckBackendCreate creates an operation to create an HTTP check in a backend.
func NewHTTPCheckBackendCreate(backendName string, check *models.HTTPCheck, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"http_check",
		PriorityHTTPCheck,
		backendName,
		index,
		check,
		transform.ToAPIHTTPCheck,
		executors.HTTPCheckBackendCreate(),
		func() string {
			return fmt.Sprintf("Create HTTP check at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewHTTPCheckBackendUpdate creates an operation to update an HTTP check in a backend.
func NewHTTPCheckBackendUpdate(backendName string, check *models.HTTPCheck, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"http_check",
		PriorityHTTPCheck,
		backendName,
		index,
		check,
		transform.ToAPIHTTPCheck,
		executors.HTTPCheckBackendUpdate(),
		func() string {
			return fmt.Sprintf("Update HTTP check at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewHTTPCheckBackendDelete creates an operation to delete an HTTP check from a backend.
func NewHTTPCheckBackendDelete(backendName string, check *models.HTTPCheck, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"http_check",
		PriorityHTTPCheck,
		backendName,
		index,
		check,
		func(c *models.HTTPCheck) *dataplaneapi.HttpCheck { return nil },
		executors.HTTPCheckBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete HTTP check at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// TCP Check Factory Functions (Index-based child, Backend only)
// =============================================================================

// NewTCPCheckBackendCreate creates an operation to create a TCP check in a backend.
func NewTCPCheckBackendCreate(backendName string, check *models.TCPCheck, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"tcp_check",
		PriorityTCPCheck,
		backendName,
		index,
		check,
		transform.ToAPITCPCheck,
		executors.TCPCheckBackendCreate(),
		func() string {
			return fmt.Sprintf("Create TCP check at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewTCPCheckBackendUpdate creates an operation to update a TCP check in a backend.
func NewTCPCheckBackendUpdate(backendName string, check *models.TCPCheck, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"tcp_check",
		PriorityTCPCheck,
		backendName,
		index,
		check,
		transform.ToAPITCPCheck,
		executors.TCPCheckBackendUpdate(),
		func() string {
			return fmt.Sprintf("Update TCP check at index %d in backend '%s'", index, backendName)
		},
	)
}

// NewTCPCheckBackendDelete creates an operation to delete a TCP check from a backend.
func NewTCPCheckBackendDelete(backendName string, check *models.TCPCheck, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"tcp_check",
		PriorityTCPCheck,
		backendName,
		index,
		check,
		func(c *models.TCPCheck) *dataplaneapi.TcpCheck { return nil },
		executors.TCPCheckBackendDelete(),
		func() string {
			return fmt.Sprintf("Delete TCP check at index %d from backend '%s'", index, backendName)
		},
	)
}

// =============================================================================
// Capture (DeclareCapture) Factory Functions (Index-based child, Frontend only)
// =============================================================================

// NewCaptureFrontendCreate creates an operation to create a capture declaration in a frontend.
func NewCaptureFrontendCreate(frontendName string, capture *models.Capture, index int) Operation {
	return NewIndexChildOp(
		OperationCreate,
		"capture",
		PriorityCapture,
		frontendName,
		index,
		capture,
		transform.ToAPICapture,
		executors.DeclareCaptureFrontendCreate(),
		func() string {
			return fmt.Sprintf("Create capture at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewCaptureFrontendUpdate creates an operation to update a capture declaration in a frontend.
func NewCaptureFrontendUpdate(frontendName string, capture *models.Capture, index int) Operation {
	return NewIndexChildOp(
		OperationUpdate,
		"capture",
		PriorityCapture,
		frontendName,
		index,
		capture,
		transform.ToAPICapture,
		executors.DeclareCaptureFrontendUpdate(),
		func() string {
			return fmt.Sprintf("Update capture at index %d in frontend '%s'", index, frontendName)
		},
	)
}

// NewCaptureFrontendDelete creates an operation to delete a capture declaration from a frontend.
func NewCaptureFrontendDelete(frontendName string, capture *models.Capture, index int) Operation {
	return NewIndexChildOp(
		OperationDelete,
		"capture",
		PriorityCapture,
		frontendName,
		index,
		capture,
		func(c *models.Capture) *dataplaneapi.Capture { return nil },
		executors.DeclareCaptureFrontendDelete(),
		func() string {
			return fmt.Sprintf("Delete capture at index %d from frontend '%s'", index, frontendName)
		},
	)
}
