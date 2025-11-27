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
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestConvertClientMetadataToAPI(t *testing.T) {
	tests := []struct {
		name  string
		input map[string]interface{}
		want  map[string]map[string]interface{}
	}{
		{
			name:  "nil input returns nil",
			input: nil,
			want:  nil,
		},
		{
			name:  "empty map returns nil",
			input: map[string]interface{}{},
			want:  nil,
		},
		{
			name: "single comment",
			input: map[string]interface{}{
				"comment": "Pod: echo-server-v2",
			},
			want: map[string]map[string]interface{}{
				"comment": {"value": "Pod: echo-server-v2"},
			},
		},
		{
			name: "multiple metadata fields",
			input: map[string]interface{}{
				"comment":  "server comment",
				"disabled": true,
				"weight":   100,
			},
			want: map[string]map[string]interface{}{
				"comment":  {"value": "server comment"},
				"disabled": {"value": true},
				"weight":   {"value": 100},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ConvertClientMetadataToAPI(tt.input)
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
			name:  "nil input returns nil",
			input: nil,
			want:  nil,
		},
		{
			name:  "empty map returns nil",
			input: map[string]map[string]interface{}{},
			want:  nil,
		},
		{
			name: "single comment",
			input: map[string]map[string]interface{}{
				"comment": {"value": "Pod: echo-server-v2"},
			},
			want: map[string]interface{}{
				"comment": "Pod: echo-server-v2",
			},
		},
		{
			name: "multiple metadata fields",
			input: map[string]map[string]interface{}{
				"comment":  {"value": "server comment"},
				"disabled": {"value": true},
				"weight":   {"value": 100},
			},
			want: map[string]interface{}{
				"comment":  "server comment",
				"disabled": true,
				"weight":   100,
			},
		},
		{
			name: "nested map without value key is ignored",
			input: map[string]map[string]interface{}{
				"comment": {"value": "has value"},
				"invalid": {"other_key": "no value key"},
			},
			want: map[string]interface{}{
				"comment": "has value",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ConvertAPIMetadataToClient(tt.input)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestMetadataRoundTrip(t *testing.T) {
	// Test that converting to API and back yields original
	original := map[string]interface{}{
		"comment": "Pod: echo-server-v2",
		"weight":  100,
	}

	api := ConvertClientMetadataToAPI(original)
	roundTripped := ConvertAPIMetadataToClient(api)

	assert.Equal(t, original, roundTripped)
}
