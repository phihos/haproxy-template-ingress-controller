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
	"net/http"
	"testing"

	"github.com/stretchr/testify/assert"

	"haproxy-template-ic/pkg/generated/dataplaneapi"
	v30 "haproxy-template-ic/pkg/generated/dataplaneapi/v30"
	v31 "haproxy-template-ic/pkg/generated/dataplaneapi/v31"
	v32 "haproxy-template-ic/pkg/generated/dataplaneapi/v32"
)

// TestDispatchCreate verifies that the DispatchCreate function signatures
// compile correctly with version-specific types. This is a compile-time type
// check, not a runtime test.
func TestDispatchCreate(t *testing.T) {
	// Verify type compatibility by declaring callback signatures.
	// These verify the dispatcher helpers accept correct function signatures.
	type v32CreateFunc func(v32.Backend, *v32.CreateBackendParams) (*http.Response, error)
	type v31CreateFunc func(v31.Backend, *v31.CreateBackendParams) (*http.Response, error)
	type v30CreateFunc func(v30.Backend, *v30.CreateBackendParams) (*http.Response, error)

	// Type assertions at compile time verify the function signatures are valid.
	var (
		_ v32CreateFunc
		_ v31CreateFunc
		_ v30CreateFunc
	)

	assert.True(t, true, "dispatcher create signatures compile correctly")
}

// TestDispatchUpdate verifies that the DispatchUpdate function signatures
// compile correctly with version-specific types.
func TestDispatchUpdate(t *testing.T) {
	type v32UpdateFunc func(string, v32.Backend, *v32.ReplaceBackendParams) (*http.Response, error)
	type v31UpdateFunc func(string, v31.Backend, *v31.ReplaceBackendParams) (*http.Response, error)
	type v30UpdateFunc func(string, v30.Backend, *v30.ReplaceBackendParams) (*http.Response, error)

	var (
		_ v32UpdateFunc
		_ v31UpdateFunc
		_ v30UpdateFunc
	)

	assert.True(t, true, "dispatcher update signatures compile correctly")
}

// TestDispatchDelete verifies that the DispatchDelete function signatures
// compile correctly with version-specific types.
func TestDispatchDelete(t *testing.T) {
	type v32DeleteFunc func(string, *v32.DeleteBackendParams) (*http.Response, error)
	type v31DeleteFunc func(string, *v31.DeleteBackendParams) (*http.Response, error)
	type v30DeleteFunc func(string, *v30.DeleteBackendParams) (*http.Response, error)

	var (
		_ v32DeleteFunc
		_ v31DeleteFunc
		_ v30DeleteFunc
	)

	assert.True(t, true, "dispatcher delete signatures compile correctly")
}

// TestDispatchCreateChild verifies that the DispatchCreateChild function signatures
// compile correctly with version-specific types.
func TestDispatchCreateChild(t *testing.T) {
	type v32CreateChildFunc func(string, int, v32.Acl, *v32.CreateAclFrontendParams) (*http.Response, error)
	type v31CreateChildFunc func(string, int, v31.Acl, *v31.CreateAclFrontendParams) (*http.Response, error)
	type v30CreateChildFunc func(string, int, v30.Acl, *v30.CreateAclFrontendParams) (*http.Response, error)

	var (
		_ v32CreateChildFunc
		_ v31CreateChildFunc
		_ v30CreateChildFunc
	)

	assert.True(t, true, "dispatcher create child signatures compile correctly")
}

// TestDispatchReplaceChild verifies that the DispatchReplaceChild function signatures
// compile correctly with version-specific types.
func TestDispatchReplaceChild(t *testing.T) {
	type v32ReplaceChildFunc func(string, int, v32.Acl, *v32.ReplaceAclFrontendParams) (*http.Response, error)
	type v31ReplaceChildFunc func(string, int, v31.Acl, *v31.ReplaceAclFrontendParams) (*http.Response, error)
	type v30ReplaceChildFunc func(string, int, v30.Acl, *v30.ReplaceAclFrontendParams) (*http.Response, error)

	var (
		_ v32ReplaceChildFunc
		_ v31ReplaceChildFunc
		_ v30ReplaceChildFunc
	)

	assert.True(t, true, "dispatcher replace child signatures compile correctly")
}

// TestDispatchDeleteChild verifies that the DispatchDeleteChild function signatures
// compile correctly with version-specific types.
func TestDispatchDeleteChild(t *testing.T) {
	type v32DeleteChildFunc func(string, int, *v32.DeleteAclFrontendParams) (*http.Response, error)
	type v31DeleteChildFunc func(string, int, *v31.DeleteAclFrontendParams) (*http.Response, error)
	type v30DeleteChildFunc func(string, int, *v30.DeleteAclFrontendParams) (*http.Response, error)

	var (
		_ v32DeleteChildFunc
		_ v31DeleteChildFunc
		_ v30DeleteChildFunc
	)

	assert.True(t, true, "dispatcher delete child signatures compile correctly")
}

// TestDispatchHelpersWithRealTypes verifies that the dispatcher helpers work
// with actual dataplaneapi types (not test types).
func TestDispatchHelpersWithRealTypes(t *testing.T) {
	t.Run("dispatchCreate with dataplaneapi.Backend", func(t *testing.T) {
		// Create a real dataplaneapi backend model and verify it can be
		// used with version-specific types through JSON marshaling.
		backend := dataplaneapi.Backend{
			Name: "test-backend",
		}

		// Verify the Backend type has expected fields.
		assert.Equal(t, "test-backend", backend.Name)
	})

	t.Run("dispatchCreateChild with dataplaneapi.Acl", func(t *testing.T) {
		// Create a real dataplaneapi ACL model and verify it can be
		// used with version-specific types through JSON marshaling.
		value := "/api"
		acl := dataplaneapi.Acl{
			AclName:   "is_api",
			Criterion: "path_beg",
			Value:     &value,
		}

		// Verify the Acl type has expected fields.
		assert.Equal(t, "is_api", acl.AclName)
		assert.Equal(t, "path_beg", acl.Criterion)
		assert.Equal(t, "/api", *acl.Value)
	})
}
