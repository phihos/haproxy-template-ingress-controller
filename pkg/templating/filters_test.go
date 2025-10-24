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
	"encoding/base64"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestPathResolver_GetPath(t *testing.T) {
	resolver := &PathResolver{
		MapsDir:    "/etc/haproxy/maps",
		SSLDir:     "/etc/haproxy/ssl",
		GeneralDir: "/etc/haproxy/general",
	}

	tests := []struct {
		name     string
		filename interface{}
		args     []interface{}
		want     string
		wantErr  bool
	}{
		{
			name:     "map file",
			filename: "host.map",
			args:     []interface{}{"map"},
			want:     "/etc/haproxy/maps/host.map",
		},
		{
			name:     "general file",
			filename: "503.http",
			args:     []interface{}{"file"},
			want:     "/etc/haproxy/general/503.http",
		},
		{
			name:     "ssl certificate",
			filename: "cert.pem",
			args:     []interface{}{"cert"},
			want:     "/etc/haproxy/ssl/cert.pem",
		},
		{
			name:     "empty filename",
			filename: "",
			args:     []interface{}{"map"},
			wantErr:  true,
		},
		{
			name:     "non-string filename",
			filename: 123,
			args:     []interface{}{"map"},
			wantErr:  true,
		},
		{
			name:     "missing file type arg",
			filename: "test.map",
			args:     []interface{}{},
			wantErr:  true,
		},
		{
			name:     "invalid file type",
			filename: "test.txt",
			args:     []interface{}{"invalid"},
			wantErr:  true,
		},
		{
			name:     "non-string file type",
			filename: "test.map",
			args:     []interface{}{123},
			wantErr:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := resolver.GetPath(tt.filename, tt.args...)

			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestGlobMatch(t *testing.T) {
	tests := []struct {
		name    string
		input   interface{}
		pattern string
		want    []interface{}
		wantErr bool
	}{
		{
			name:    "simple wildcard match",
			input:   []interface{}{"backend-annotation-auth", "backend-annotation-rate-limit", "frontend-config"},
			pattern: "backend-annotation-*",
			want:    []interface{}{"backend-annotation-auth", "backend-annotation-rate-limit"},
		},
		{
			name:    "no matches",
			input:   []interface{}{"frontend-config", "global-config"},
			pattern: "backend-*",
			want:    nil,
		},
		{
			name:    "question mark wildcard",
			input:   []interface{}{"test1", "test2", "test10", "prod1"},
			pattern: "test?",
			want:    []interface{}{"test1", "test2"},
		},
		{
			name:    "exact match",
			input:   []interface{}{"exact", "exact-match", "not-exact"},
			pattern: "exact",
			want:    []interface{}{"exact"},
		},
		{
			name:    "all match",
			input:   []interface{}{"one", "two", "three"},
			pattern: "*",
			want:    []interface{}{"one", "two", "three"},
		},
		{
			name:    "empty list",
			input:   []interface{}{},
			pattern: "*",
			want:    nil,
		},
		{
			name:    "string slice input",
			input:   []string{"backend-annotation-auth", "backend-annotation-rate-limit"},
			pattern: "backend-*",
			want:    []interface{}{"backend-annotation-auth", "backend-annotation-rate-limit"},
		},
		{
			name:    "mixed types in list - skips non-strings",
			input:   []interface{}{"valid", 123, "another-valid", true},
			pattern: "*valid",
			want:    []interface{}{"valid", "another-valid"},
		},
		{
			name:    "non-list input",
			input:   "not-a-list",
			pattern: "*",
			wantErr: true,
		},
		{
			name:    "missing pattern argument",
			input:   []interface{}{"test"},
			pattern: "",
			wantErr: true,
		},
		{
			name:    "invalid glob pattern",
			input:   []interface{}{"test"},
			pattern: "[invalid",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var args []interface{}
			if tt.pattern != "" {
				args = []interface{}{tt.pattern}
			}

			got, err := GlobMatch(tt.input, args...)

			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestB64Decode(t *testing.T) {
	tests := []struct {
		name    string
		input   interface{}
		want    string
		wantErr bool
	}{
		{
			name:  "simple string",
			input: base64.StdEncoding.EncodeToString([]byte("Hello, World!")),
			want:  "Hello, World!",
		},
		{
			name:  "empty string",
			input: base64.StdEncoding.EncodeToString([]byte("")),
			want:  "",
		},
		{
			name:  "special characters",
			input: base64.StdEncoding.EncodeToString([]byte("user:password!@#$%")),
			want:  "user:password!@#$%",
		},
		{
			name:  "multiline",
			input: base64.StdEncoding.EncodeToString([]byte("line1\nline2\nline3")),
			want:  "line1\nline2\nline3",
		},
		{
			name:  "encrypted password (HAProxy userlist format)",
			input: base64.StdEncoding.EncodeToString([]byte("$5$rounds=5000$salt$hashedpassword")),
			want:  "$5$rounds=5000$salt$hashedpassword",
		},
		{
			name:    "non-string input",
			input:   123,
			wantErr: true,
		},
		{
			name:    "invalid base64",
			input:   "not-valid-base64!!!",
			wantErr: true,
		},
		{
			name:    "nil input",
			input:   nil,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := B64Decode(tt.input)

			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}
