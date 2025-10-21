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

package templating

import (
	"io"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestSimpleLoader_Read(t *testing.T) {
	templates := map[string]string{
		"template1": "Content 1",
		"template2": "Content 2",
		"greeting":  "Hello {{ name }}",
	}

	loader := NewSimpleLoader(templates)

	tests := []struct {
		name    string
		path    string
		want    string
		wantErr bool
	}{
		{
			name: "read existing template",
			path: "template1",
			want: "Content 1",
		},
		{
			name: "read another template",
			path: "template2",
			want: "Content 2",
		},
		{
			name: "read template with variables",
			path: "greeting",
			want: "Hello {{ name }}",
		},
		{
			name:    "read non-existent template",
			path:    "missing",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			reader, err := loader.Read(tt.path)

			if tt.wantErr {
				require.Error(t, err)
				assert.Nil(t, reader)
				assert.Contains(t, err.Error(), "template not found")
				return
			}

			require.NoError(t, err)
			require.NotNil(t, reader)

			// Read the content
			content, err := io.ReadAll(reader)
			require.NoError(t, err)
			assert.Equal(t, tt.want, string(content))
		})
	}
}

func TestSimpleLoader_Resolve(t *testing.T) {
	templates := map[string]string{
		"template1":     "Content 1",
		"template2":     "Content 2",
		"with-dashes":   "Content",
		"with_under":    "Content",
		"path/with/dir": "Should work despite '/' in name",
	}

	loader := NewSimpleLoader(templates)

	tests := []struct {
		name    string
		path    string
		want    string
		wantErr bool
	}{
		{
			name: "resolve simple name",
			path: "template1",
			want: "template1",
		},
		{
			name: "resolve name with dashes",
			path: "with-dashes",
			want: "with-dashes",
		},
		{
			name: "resolve name with underscores",
			path: "with_under",
			want: "with_under",
		},
		{
			name: "resolve name with slashes",
			path: "path/with/dir",
			want: "path/with/dir",
		},
		{
			name:    "resolve non-existent template",
			path:    "missing",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			resolved, err := loader.Resolve(tt.path)

			if tt.wantErr {
				require.Error(t, err)
				assert.Contains(t, err.Error(), "template not found")
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, resolved)
		})
	}
}

func TestSimpleLoader_Inherit(t *testing.T) {
	templates := map[string]string{
		"parent": "Parent content",
		"child":  "Child content",
	}

	loader := NewSimpleLoader(templates)

	tests := []struct {
		name string
		from string
	}{
		{
			name: "inherit with empty from",
			from: "",
		},
		{
			name: "inherit from parent",
			from: "parent",
		},
		{
			name: "inherit from child",
			from: "child",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			inherited, err := loader.Inherit(tt.from)
			require.NoError(t, err)
			require.NotNil(t, inherited)

			// The inherited loader should be the same instance (no path context)
			assert.Equal(t, loader, inherited)

			// Verify we can still read all templates from inherited loader
			reader, err := inherited.Read("parent")
			require.NoError(t, err)
			content, err := io.ReadAll(reader)
			require.NoError(t, err)
			assert.Equal(t, "Parent content", string(content))
		})
	}
}

func TestSimpleLoader_EmptyTemplates(t *testing.T) {
	templates := map[string]string{}
	loader := NewSimpleLoader(templates)

	// Read should fail for any path
	_, err := loader.Read("any")
	require.Error(t, err)
	assert.Contains(t, err.Error(), "template not found")

	// Resolve should fail for any path
	_, err = loader.Resolve("any")
	require.Error(t, err)
	assert.Contains(t, err.Error(), "template not found")

	// Inherit should still work
	inherited, err := loader.Inherit("")
	require.NoError(t, err)
	assert.Equal(t, loader, inherited)
}

func TestSimpleLoader_SpecialCharacters(t *testing.T) {
	templates := map[string]string{
		"name with spaces": "Content",
		"name.with.dots":   "Content",
		"name@special#":    "Content",
	}

	loader := NewSimpleLoader(templates)

	// All special character names should work
	tests := []string{
		"name with spaces",
		"name.with.dots",
		"name@special#",
	}

	for _, name := range tests {
		t.Run(name, func(t *testing.T) {
			// Read should work
			reader, err := loader.Read(name)
			require.NoError(t, err)
			content, err := io.ReadAll(reader)
			require.NoError(t, err)
			assert.Equal(t, "Content", string(content))

			// Resolve should work
			resolved, err := loader.Resolve(name)
			require.NoError(t, err)
			assert.Equal(t, name, resolved)
		})
	}
}
