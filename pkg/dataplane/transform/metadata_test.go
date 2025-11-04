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

package transform

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestConvertClientMetadataToAPI(t *testing.T) {
	tests := []struct {
		name  string
		input map[string]interface{}
		want  *map[string]map[string]interface{}
	}{
		{
			name:  "nil input",
			input: nil,
			want:  nil,
		},
		{
			name:  "empty map",
			input: map[string]interface{}{},
			want:  nil,
		},
		{
			name: "single string value",
			input: map[string]interface{}{
				"comment": "Pod: echo-server-v2",
			},
			want: &map[string]map[string]interface{}{
				"comment": {
					"value": "Pod: echo-server-v2",
				},
			},
		},
		{
			name: "multiple metadata keys",
			input: map[string]interface{}{
				"comment":   "Pod: echo-server-v2",
				"owner":     "team-platform",
				"region":    "us-west-2",
				"buildinfo": "v1.2.3-abc123",
			},
			want: &map[string]map[string]interface{}{
				"comment": {
					"value": "Pod: echo-server-v2",
				},
				"owner": {
					"value": "team-platform",
				},
				"region": {
					"value": "us-west-2",
				},
				"buildinfo": {
					"value": "v1.2.3-abc123",
				},
			},
		},
		{
			name: "numeric values",
			input: map[string]interface{}{
				"port":   8080,
				"weight": 100,
			},
			want: &map[string]map[string]interface{}{
				"port": {
					"value": 8080,
				},
				"weight": {
					"value": 100,
				},
			},
		},
		{
			name: "boolean values",
			input: map[string]interface{}{
				"enabled": true,
				"debug":   false,
			},
			want: &map[string]map[string]interface{}{
				"enabled": {
					"value": true,
				},
				"debug": {
					"value": false,
				},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := convertClientMetadataToAPI(tt.input)

			if tt.want == nil {
				assert.Nil(t, got)
				return
			}

			assert.NotNil(t, got)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestConvertAPIMetadataToClient(t *testing.T) {
	tests := []struct {
		name  string
		input map[string]map[string]interface{}
		want  map[string]interface{}
	}{
		{
			name:  "nil input",
			input: nil,
			want:  nil,
		},
		{
			name:  "empty map",
			input: map[string]map[string]interface{}{},
			want:  map[string]interface{}{},
		},
		{
			name: "single string value",
			input: map[string]map[string]interface{}{
				"comment": {
					"value": "Pod: echo-server-v2",
				},
			},
			want: map[string]interface{}{
				"comment": "Pod: echo-server-v2",
			},
		},
		{
			name: "multiple metadata keys",
			input: map[string]map[string]interface{}{
				"comment": {
					"value": "Pod: echo-server-v2",
				},
				"owner": {
					"value": "team-platform",
				},
				"region": {
					"value": "us-west-2",
				},
			},
			want: map[string]interface{}{
				"comment": "Pod: echo-server-v2",
				"owner":   "team-platform",
				"region":  "us-west-2",
			},
		},
		{
			name: "numeric values",
			input: map[string]map[string]interface{}{
				"port": {
					"value": 8080,
				},
			},
			want: map[string]interface{}{
				"port": 8080,
			},
		},
		{
			name: "nested map without value key",
			input: map[string]map[string]interface{}{
				"comment": {
					"value": "valid",
				},
				"invalid": {
					"other_key": "should be ignored",
				},
			},
			want: map[string]interface{}{
				"comment": "valid",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := convertAPIMetadataToClient(tt.input)

			if tt.want == nil {
				assert.Nil(t, got)
				return
			}

			assert.Equal(t, tt.want, got)
		})
	}
}

func TestMetadataConversionRoundTrip(t *testing.T) {
	tests := []struct {
		name     string
		original map[string]interface{}
	}{
		{
			name:     "nil",
			original: nil,
		},
		{
			name:     "empty",
			original: map[string]interface{}{},
		},
		{
			name: "single value",
			original: map[string]interface{}{
				"comment": "test",
			},
		},
		{
			name: "multiple values",
			original: map[string]interface{}{
				"comment": "test comment",
				"owner":   "team-a",
				"region":  "us-east-1",
			},
		},
		{
			name: "mixed types",
			original: map[string]interface{}{
				"comment": "test",
				"port":    8080,
				"enabled": true,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Convert client -> API -> client
			apiFormat := convertClientMetadataToAPI(tt.original)
			roundTrip := convertAPIMetadataToClient(apiFormat)

			if tt.original == nil {
				assert.Nil(t, roundTrip)
			} else if len(tt.original) == 0 {
				// Empty map should result in nil after API conversion
				assert.Nil(t, roundTrip)
			} else {
				assert.Equal(t, tt.original, roundTrip)
			}
		})
	}
}
