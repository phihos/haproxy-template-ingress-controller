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

package sections

import (
	"testing"

	"github.com/haproxytech/client-native/v6/models"
	"github.com/stretchr/testify/assert"

	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

func TestPtrStr(t *testing.T) {
	tests := []struct {
		name string
		in   *string
		want string
	}{
		{
			name: "nil pointer",
			in:   nil,
			want: "",
		},
		{
			name: "empty string pointer",
			in:   ptr(""),
			want: "",
		},
		{
			name: "non-empty string pointer",
			in:   ptr("test"),
			want: "test",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ptrStr(tt.in)
			assert.Equal(t, tt.want, got)
		})
	}
}

// ptr returns a pointer to the given string.
func ptr(s string) *string {
	return &s
}

func TestBackendFactoryFunctions(t *testing.T) {
	backend := &models.Backend{}
	backend.Name = "api-backend"

	tests := []struct {
		name             string
		factory          func(*models.Backend) Operation
		wantType         OperationType
		wantSection      string
		wantPriority     int
		wantDescContains string
	}{
		{
			name:             "NewBackendCreate",
			factory:          NewBackendCreate,
			wantType:         OperationCreate,
			wantSection:      "backend",
			wantPriority:     PriorityBackend,
			wantDescContains: "Create backend 'api-backend'",
		},
		{
			name:             "NewBackendUpdate",
			factory:          NewBackendUpdate,
			wantType:         OperationUpdate,
			wantSection:      "backend",
			wantPriority:     PriorityBackend,
			wantDescContains: "Update backend 'api-backend'",
		},
		{
			name:             "NewBackendDelete",
			factory:          NewBackendDelete,
			wantType:         OperationDelete,
			wantSection:      "backend",
			wantPriority:     PriorityBackend,
			wantDescContains: "Delete backend 'api-backend'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory(backend)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, tt.wantSection, op.Section())
			assert.Equal(t, tt.wantPriority, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestFrontendFactoryFunctions(t *testing.T) {
	frontend := &models.Frontend{}
	frontend.Name = "http-frontend"

	tests := []struct {
		name             string
		factory          func(*models.Frontend) Operation
		wantType         OperationType
		wantSection      string
		wantPriority     int
		wantDescContains string
	}{
		{
			name:             "NewFrontendCreate",
			factory:          NewFrontendCreate,
			wantType:         OperationCreate,
			wantSection:      "frontend",
			wantPriority:     PriorityFrontend,
			wantDescContains: "Create frontend 'http-frontend'",
		},
		{
			name:             "NewFrontendUpdate",
			factory:          NewFrontendUpdate,
			wantType:         OperationUpdate,
			wantSection:      "frontend",
			wantPriority:     PriorityFrontend,
			wantDescContains: "Update frontend 'http-frontend'",
		},
		{
			name:             "NewFrontendDelete",
			factory:          NewFrontendDelete,
			wantType:         OperationDelete,
			wantSection:      "frontend",
			wantPriority:     PriorityFrontend,
			wantDescContains: "Delete frontend 'http-frontend'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory(frontend)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, tt.wantSection, op.Section())
			assert.Equal(t, tt.wantPriority, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestDefaultsFactoryFunctions(t *testing.T) {
	defaults := &models.Defaults{}
	defaults.Name = "http-defaults"

	tests := []struct {
		name             string
		factory          func(*models.Defaults) Operation
		wantType         OperationType
		wantSection      string
		wantPriority     int
		wantDescContains string
	}{
		{
			name:             "NewDefaultsCreate",
			factory:          NewDefaultsCreate,
			wantType:         OperationCreate,
			wantSection:      "defaults",
			wantPriority:     PriorityDefaults,
			wantDescContains: "Create defaults section 'http-defaults'",
		},
		{
			name:             "NewDefaultsUpdate",
			factory:          NewDefaultsUpdate,
			wantType:         OperationUpdate,
			wantSection:      "defaults",
			wantPriority:     PriorityDefaults,
			wantDescContains: "Update defaults section 'http-defaults'",
		},
		{
			name:             "NewDefaultsDelete",
			factory:          NewDefaultsDelete,
			wantType:         OperationDelete,
			wantSection:      "defaults",
			wantPriority:     PriorityDefaults,
			wantDescContains: "Delete defaults section 'http-defaults'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory(defaults)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, tt.wantSection, op.Section())
			assert.Equal(t, tt.wantPriority, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestGlobalFactoryFunction(t *testing.T) {
	global := &models.Global{}

	op := NewGlobalUpdate(global)

	assert.Equal(t, OperationUpdate, op.Type())
	assert.Equal(t, "global", op.Section())
	assert.Equal(t, PriorityGlobal, op.Priority())
	assert.Equal(t, "Update global section", op.Describe())
}

func TestACLFactoryFunctions(t *testing.T) {
	acl := &models.ACL{ACLName: "is_api"}

	t.Run("frontend ACL operations", func(t *testing.T) {
		tests := []struct {
			name             string
			factory          func(string, *models.ACL, int) Operation
			wantType         OperationType
			wantDescContains string
		}{
			{
				name:             "NewACLFrontendCreate",
				factory:          NewACLFrontendCreate,
				wantType:         OperationCreate,
				wantDescContains: "Create ACL 'is_api' in frontend 'http'",
			},
			{
				name:             "NewACLFrontendUpdate",
				factory:          NewACLFrontendUpdate,
				wantType:         OperationUpdate,
				wantDescContains: "Update ACL 'is_api' in frontend 'http'",
			},
			{
				name:             "NewACLFrontendDelete",
				factory:          NewACLFrontendDelete,
				wantType:         OperationDelete,
				wantDescContains: "Delete ACL 'is_api' from frontend 'http'",
			},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				op := tt.factory("http", acl, 0)

				assert.Equal(t, tt.wantType, op.Type())
				assert.Equal(t, "acl", op.Section())
				assert.Equal(t, PriorityACL, op.Priority())
				assert.Contains(t, op.Describe(), tt.wantDescContains)
			})
		}
	})

	t.Run("backend ACL operations", func(t *testing.T) {
		tests := []struct {
			name             string
			factory          func(string, *models.ACL, int) Operation
			wantType         OperationType
			wantDescContains string
		}{
			{
				name:             "NewACLBackendCreate",
				factory:          NewACLBackendCreate,
				wantType:         OperationCreate,
				wantDescContains: "Create ACL 'is_api' in backend 'api'",
			},
			{
				name:             "NewACLBackendUpdate",
				factory:          NewACLBackendUpdate,
				wantType:         OperationUpdate,
				wantDescContains: "Update ACL 'is_api' in backend 'api'",
			},
			{
				name:             "NewACLBackendDelete",
				factory:          NewACLBackendDelete,
				wantType:         OperationDelete,
				wantDescContains: "Delete ACL 'is_api' from backend 'api'",
			},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				op := tt.factory("api", acl, 0)

				assert.Equal(t, tt.wantType, op.Type())
				assert.Equal(t, "acl", op.Section())
				assert.Equal(t, PriorityACL, op.Priority())
				assert.Contains(t, op.Describe(), tt.wantDescContains)
			})
		}
	})
}

func TestServerFactoryFunctions(t *testing.T) {
	server := &models.Server{Name: "web1"}

	tests := []struct {
		name             string
		factory          func(string, *models.Server) Operation
		wantType         OperationType
		wantDescContains string
	}{
		{
			name:             "NewServerCreate",
			factory:          NewServerCreate,
			wantType:         OperationCreate,
			wantDescContains: "Create server 'web1' in backend 'api'",
		},
		{
			name:             "NewServerUpdate",
			factory:          NewServerUpdate,
			wantType:         OperationUpdate,
			wantDescContains: "Update server 'web1' in backend 'api'",
		},
		{
			name:             "NewServerDelete",
			factory:          NewServerDelete,
			wantType:         OperationDelete,
			wantDescContains: "Delete server 'web1' from backend 'api'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory("api", server)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, "server", op.Section())
			assert.Equal(t, PriorityServer, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestBindFactoryFunctions(t *testing.T) {
	bindName := "http-bind"
	bind := &dataplaneapi.Bind{Name: &bindName}

	tests := []struct {
		name             string
		factory          func(string, string, *dataplaneapi.Bind) Operation
		wantType         OperationType
		wantDescContains string
	}{
		{
			name:             "NewBindFrontendCreate",
			factory:          NewBindFrontendCreate,
			wantType:         OperationCreate,
			wantDescContains: "Create bind 'http-bind' in frontend 'http'",
		},
		{
			name:             "NewBindFrontendUpdate",
			factory:          NewBindFrontendUpdate,
			wantType:         OperationUpdate,
			wantDescContains: "Update bind 'http-bind' in frontend 'http'",
		},
		{
			name:             "NewBindFrontendDelete",
			factory:          NewBindFrontendDelete,
			wantType:         OperationDelete,
			wantDescContains: "Delete bind 'http-bind' from frontend 'http'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory("http", "http-bind", bind)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, "bind", op.Section())
			assert.Equal(t, PriorityBind, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestHTTPRequestRuleFactoryFunctions(t *testing.T) {
	rule := &models.HTTPRequestRule{}

	t.Run("frontend HTTP request rule operations", func(t *testing.T) {
		tests := []struct {
			name             string
			factory          func(string, *models.HTTPRequestRule, int) Operation
			wantType         OperationType
			wantDescContains string
		}{
			{
				name:             "NewHTTPRequestRuleFrontendCreate",
				factory:          NewHTTPRequestRuleFrontendCreate,
				wantType:         OperationCreate,
				wantDescContains: "Create HTTP request rule at index 5 in frontend 'http'",
			},
			{
				name:             "NewHTTPRequestRuleFrontendUpdate",
				factory:          NewHTTPRequestRuleFrontendUpdate,
				wantType:         OperationUpdate,
				wantDescContains: "Update HTTP request rule at index 5 in frontend 'http'",
			},
			{
				name:             "NewHTTPRequestRuleFrontendDelete",
				factory:          NewHTTPRequestRuleFrontendDelete,
				wantType:         OperationDelete,
				wantDescContains: "Delete HTTP request rule at index 5 from frontend 'http'",
			},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				op := tt.factory("http", rule, 5)

				assert.Equal(t, tt.wantType, op.Type())
				assert.Equal(t, "http_request_rule", op.Section())
				assert.Equal(t, PriorityRule, op.Priority())
				assert.Contains(t, op.Describe(), tt.wantDescContains)
			})
		}
	})

	t.Run("backend HTTP request rule operations", func(t *testing.T) {
		tests := []struct {
			name             string
			factory          func(string, *models.HTTPRequestRule, int) Operation
			wantType         OperationType
			wantDescContains string
		}{
			{
				name:             "NewHTTPRequestRuleBackendCreate",
				factory:          NewHTTPRequestRuleBackendCreate,
				wantType:         OperationCreate,
				wantDescContains: "Create HTTP request rule at index 3 in backend 'api'",
			},
			{
				name:             "NewHTTPRequestRuleBackendUpdate",
				factory:          NewHTTPRequestRuleBackendUpdate,
				wantType:         OperationUpdate,
				wantDescContains: "Update HTTP request rule at index 3 in backend 'api'",
			},
			{
				name:             "NewHTTPRequestRuleBackendDelete",
				factory:          NewHTTPRequestRuleBackendDelete,
				wantType:         OperationDelete,
				wantDescContains: "Delete HTTP request rule at index 3 from backend 'api'",
			},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				op := tt.factory("api", rule, 3)

				assert.Equal(t, tt.wantType, op.Type())
				assert.Equal(t, "http_request_rule", op.Section())
				assert.Equal(t, PriorityRule, op.Priority())
				assert.Contains(t, op.Describe(), tt.wantDescContains)
			})
		}
	})
}

func TestBackendSwitchingRuleFactoryFunctions(t *testing.T) {
	rule := &models.BackendSwitchingRule{Name: "api-backend"}

	tests := []struct {
		name             string
		factory          func(string, *models.BackendSwitchingRule, int) Operation
		wantType         OperationType
		wantDescContains string
	}{
		{
			name:             "NewBackendSwitchingRuleFrontendCreate",
			factory:          NewBackendSwitchingRuleFrontendCreate,
			wantType:         OperationCreate,
			wantDescContains: "Create backend switching rule at index 0 in frontend 'http'",
		},
		{
			name:             "NewBackendSwitchingRuleFrontendUpdate",
			factory:          NewBackendSwitchingRuleFrontendUpdate,
			wantType:         OperationUpdate,
			wantDescContains: "Update backend switching rule at index 0 in frontend 'http'",
		},
		{
			name:             "NewBackendSwitchingRuleFrontendDelete",
			factory:          NewBackendSwitchingRuleFrontendDelete,
			wantType:         OperationDelete,
			wantDescContains: "Delete backend switching rule at index 0 from frontend 'http'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory("http", rule, 0)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, "backend_switching_rule", op.Section())
			assert.Equal(t, PriorityBackendSwitchingRule, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestUserFactoryFunctions(t *testing.T) {
	user := &models.User{Username: "admin"}

	tests := []struct {
		name             string
		factory          func(string, *models.User) Operation
		wantType         OperationType
		wantDescContains string
	}{
		{
			name:             "NewUserCreate",
			factory:          NewUserCreate,
			wantType:         OperationCreate,
			wantDescContains: "Create user 'admin' in userlist 'admins'",
		},
		{
			name:             "NewUserUpdate",
			factory:          NewUserUpdate,
			wantType:         OperationUpdate,
			wantDescContains: "Update user 'admin' in userlist 'admins'",
		},
		{
			name:             "NewUserDelete",
			factory:          NewUserDelete,
			wantType:         OperationDelete,
			wantDescContains: "Delete user 'admin' from userlist 'admins'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory("admins", user)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, "user", op.Section())
			assert.Equal(t, PriorityUser, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestCacheFactoryFunctions(t *testing.T) {
	cacheName := "my-cache"
	cache := &models.Cache{Name: &cacheName}

	tests := []struct {
		name             string
		factory          func(*models.Cache) Operation
		wantType         OperationType
		wantDescContains string
	}{
		{
			name:             "NewCacheCreate",
			factory:          NewCacheCreate,
			wantType:         OperationCreate,
			wantDescContains: "Create cache 'my-cache'",
		},
		{
			name:             "NewCacheUpdate",
			factory:          NewCacheUpdate,
			wantType:         OperationUpdate,
			wantDescContains: "Update cache 'my-cache'",
		},
		{
			name:             "NewCacheDelete",
			factory:          NewCacheDelete,
			wantType:         OperationDelete,
			wantDescContains: "Delete cache 'my-cache'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory(cache)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, "cache", op.Section())
			assert.Equal(t, PriorityCache, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestResolverFactoryFunctions(t *testing.T) {
	resolver := &models.Resolver{}
	resolver.Name = "dns-resolver"

	tests := []struct {
		name             string
		factory          func(*models.Resolver) Operation
		wantType         OperationType
		wantDescContains string
	}{
		{
			name:             "NewResolverCreate",
			factory:          NewResolverCreate,
			wantType:         OperationCreate,
			wantDescContains: "Create resolver 'dns-resolver'",
		},
		{
			name:             "NewResolverUpdate",
			factory:          NewResolverUpdate,
			wantType:         OperationUpdate,
			wantDescContains: "Update resolver 'dns-resolver'",
		},
		{
			name:             "NewResolverDelete",
			factory:          NewResolverDelete,
			wantType:         OperationDelete,
			wantDescContains: "Delete resolver 'dns-resolver'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory(resolver)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, "resolver", op.Section())
			assert.Equal(t, PriorityResolver, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestNameserverFactoryFunctions(t *testing.T) {
	nameserver := &models.Nameserver{Name: "ns1"}

	tests := []struct {
		name             string
		factory          func(string, *models.Nameserver) Operation
		wantType         OperationType
		wantDescContains string
	}{
		{
			name:             "NewNameserverCreate",
			factory:          NewNameserverCreate,
			wantType:         OperationCreate,
			wantDescContains: "Create nameserver 'ns1' in resolver 'dns'",
		},
		{
			name:             "NewNameserverUpdate",
			factory:          NewNameserverUpdate,
			wantType:         OperationUpdate,
			wantDescContains: "Update nameserver 'ns1' in resolver 'dns'",
		},
		{
			name:             "NewNameserverDelete",
			factory:          NewNameserverDelete,
			wantType:         OperationDelete,
			wantDescContains: "Delete nameserver 'ns1' from resolver 'dns'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			op := tt.factory("dns", nameserver)

			assert.Equal(t, tt.wantType, op.Type())
			assert.Equal(t, "nameserver", op.Section())
			assert.Equal(t, PriorityResolver, op.Priority())
			assert.Contains(t, op.Describe(), tt.wantDescContains)
		})
	}
}

func TestPriorityConstants(t *testing.T) {
	// Test priority ordering
	// Lower priority = executed first for creates
	// Higher priority = executed last for creates, first for deletes

	// Global and defaults should be first (lowest priority)
	assert.Less(t, PriorityGlobal, PriorityFrontend)
	assert.Less(t, PriorityDefaults, PriorityFrontend)

	// Frontend/backend before their children
	assert.Less(t, PriorityFrontend, PriorityBind)
	assert.Less(t, PriorityBackend, PriorityServer)

	// Servers and binds before ACLs
	assert.Less(t, PriorityServer, PriorityACL)
	assert.Less(t, PriorityBind, PriorityACL)

	// ACLs before rules (rules depend on ACLs)
	assert.Less(t, PriorityACL, PriorityRule)
}
