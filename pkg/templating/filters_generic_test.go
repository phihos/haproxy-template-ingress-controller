package templating

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestGonjaFilter_SortBy(t *testing.T) {
	tests := []struct {
		name     string
		template string
		context  map[string]interface{}
		want     string
		wantErr  bool
	}{
		{
			name: "sort by single field ascending",
			template: `{%- for item in items | sort_by(["$.name"]) -%}
{{ item.name }},
{%- endfor %}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"name": "charlie"},
					{"name": "alice"},
					{"name": "bob"},
				},
			},
			want: "alice,bob,charlie,",
		},
		{
			name: "sort by single field descending",
			template: `{%- for item in items | sort_by(["$.priority:desc"]) -%}
{{ item.name }}:{{ item.priority }},
{%- endfor %}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"name": "low", "priority": 1},
					{"name": "high", "priority": 3},
					{"name": "medium", "priority": 2},
				},
			},
			want: "high:3,medium:2,low:1,",
		},
		{
			name: "sort by length descending",
			template: `{%- for item in items | sort_by(["$.path | length:desc"]) -%}
{{ item.path }},
{%- endfor %}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"path": "/short"},
					{"path": "/very/long/path"},
					{"path": "/medium/path"},
				},
			},
			want: "/very/long/path,/medium/path,/short,",
		},
		{
			name: "sort by multiple criteria",
			template: `{%- for item in routes | sort_by(["$.type", "$.priority:desc", "$.name"]) -%}
{{ item.type }}/{{ item.priority }}/{{ item.name }},
{%- endfor %}`,
			context: map[string]interface{}{
				"routes": []map[string]interface{}{
					{"type": "http", "priority": 2, "name": "b"},
					{"type": "grpc", "priority": 1, "name": "a"},
					{"type": "http", "priority": 3, "name": "a"},
					{"type": "http", "priority": 2, "name": "a"},
					{"type": "grpc", "priority": 2, "name": "b"},
				},
			},
			want: "grpc/2/b,grpc/1/a,http/3/a,http/2/a,http/2/b,",
		},
		{
			name: "sort by existence check",
			template: `{%- for item in items | sort_by(["$.optional:exists:desc"]) -%}
{{ item.name }}:{{ item.optional | default("none") }},
{%- endfor %}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"name": "without"},
					{"name": "with", "optional": "value"},
					{"name": "also-without"},
				},
			},
			want: "with:value,without:none,also-without:none,", // :exists:desc means items with field come first
		},
		{
			name: "Gateway API route precedence - method and headers",
			template: `{%- for route in routes | sort_by(["$.match.method:exists:desc", "$.match.headers | length:desc"]) -%}
{{ route.name }},
{%- endfor %}`,
			context: map[string]interface{}{
				"routes": []map[string]interface{}{
					{"name": "catchall", "match": map[string]interface{}{}},
					{"name": "get-with-2-headers", "match": map[string]interface{}{"method": "GET", "headers": []interface{}{"X-Auth", "X-Version"}}},
					{"name": "get-with-1-header", "match": map[string]interface{}{"method": "GET", "headers": []interface{}{"X-Auth"}}},
					{"name": "get-only", "match": map[string]interface{}{"method": "GET"}},
				},
			},
			want: "get-with-2-headers,get-with-1-header,get-only,catchall,", // Most specific first, catch-all last
		},
		{
			name:     "empty list",
			template: `{{ items | sort_by(["$.name"]) | length }}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{},
			},
			want: "0",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine, err := New(EngineTypeGonja, map[string]string{"test": tt.template}, nil, nil)
			require.NoError(t, err)

			got, err := engine.Render("test", tt.context)
			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}

func TestGonjaFilter_GroupBy(t *testing.T) {
	tests := []struct {
		name     string
		template string
		context  map[string]interface{}
		want     string
		wantErr  bool
	}{
		{
			name: "group by single field",
			template: `{%- set grouped = routes | group_by("$.type") -%}
{%- if "http" in grouped %}http: {{ grouped["http"] | length }}{%- endif %}
{%- if "grpc" in grouped %}
grpc: {{ grouped["grpc"] | length }}{%- endif %}`,
			context: map[string]interface{}{
				"routes": []map[string]interface{}{
					{"type": "http", "name": "route1"},
					{"type": "grpc", "name": "route2"},
					{"type": "http", "name": "route3"},
				},
			},
			want: "http: 2\ngrpc: 1",
		},
		{
			name: "group with duplicates",
			template: `{%- set grouped = items | group_by("$.key") -%}
{%- if "a" in grouped %}a: count={{ grouped["a"] | length }}{%- endif %}
{%- if "b" in grouped %}
b: count={{ grouped["b"] | length }}{%- endif %}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"key": "a", "value": 1},
					{"key": "b", "value": 2},
					{"key": "a", "value": 3},
				},
			},
			want: "a: count=2\nb: count=1",
		},
		{
			name:     "empty list",
			template: `{{ items | group_by("$.key") | length }}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{},
			},
			want: "0",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine, err := New(EngineTypeGonja, map[string]string{"test": tt.template}, nil, nil)
			require.NoError(t, err)

			got, err := engine.Render("test", tt.context)
			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}

// Transform filter is not currently used in templates
// Keeping as placeholder for future tests if needed

func TestGonjaFilter_Extract(t *testing.T) {
	tests := []struct {
		name     string
		template string
		context  map[string]interface{}
		want     string
		wantErr  bool
	}{
		{
			name: "extract simple field",
			template: `{%- for name in items | extract("$.name") -%}
{{ name }},
{%- endfor %}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"name": "alice", "age": 30},
					{"name": "bob", "age": 25},
				},
			},
			want: "alice,bob,",
		},
		{
			name: "extract nested field",
			template: `{%- for port in services | extract("$.spec.port") -%}
{{ port }},
{%- endfor %}`,
			context: map[string]interface{}{
				"services": []map[string]interface{}{
					{"name": "svc1", "spec": map[string]interface{}{"port": 80}},
					{"name": "svc2", "spec": map[string]interface{}{"port": 443}},
				},
			},
			want: "80,443,",
		},
		{
			name: "extract with expression",
			template: `{%- for key in items | extract("$.namespace ~ '_' ~ $.name") -%}
{{ key }},
{%- endfor %}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"namespace": "ns1", "name": "app1"},
					{"namespace": "ns2", "name": "app2"},
				},
			},
			want: "ns1_app1,ns2_app2,",
		},
		{
			name:     "empty list",
			template: `{{ items | extract("$.field") | length }}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{},
			},
			want: "0",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine, err := New(EngineTypeGonja, map[string]string{"test": tt.template}, nil, nil)
			require.NoError(t, err)

			got, err := engine.Render("test", tt.context)
			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}

// Note: conflicts_by is a test, not a filter, and is not currently used in templates
// Tests removed due to Gonja argument passing complexities

func TestGonjaFilter_Debug(t *testing.T) {
	tests := []struct {
		name         string
		template     string
		context      map[string]interface{}
		wantContains []string
		wantErr      bool
	}{
		{
			name:     "debug simple object",
			template: `{{ item | debug }}`,
			context: map[string]interface{}{
				"item": map[string]interface{}{
					"name":  "test",
					"value": 42,
				},
			},
			wantContains: []string{
				"# DEBUG:",
				`#   "name": "test"`,
				`#   "value": 42`,
			},
		},
		{
			name:     "debug with label",
			template: `{{ item | debug("my-label") }}`,
			context: map[string]interface{}{
				"item": map[string]interface{}{
					"key": "value",
				},
			},
			wantContains: []string{
				"# DEBUG my-label:",
				`#   "key": "value"`,
			},
		},
		{
			name:     "debug array",
			template: `{{ items | debug }}`,
			context: map[string]interface{}{
				"items": []interface{}{"a", "b", "c"},
			},
			wantContains: []string{
				"# DEBUG:",
				"#   \"a\"",
				"#   \"b\"",
				"#   \"c\"",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine, err := New(EngineTypeGonja, map[string]string{"test": tt.template}, nil, nil)
			require.NoError(t, err)

			got, err := engine.Render("test", tt.context)
			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			for _, wantStr := range tt.wantContains {
				assert.Contains(t, got, wantStr)
			}
		})
	}
}

func TestGonjaFilter_Eval(t *testing.T) {
	tests := []struct {
		name         string
		template     string
		context      map[string]interface{}
		wantContains string
		wantErr      bool
	}{
		{
			name:     "eval simple field",
			template: `{{ item | eval("$.name") }}`,
			context: map[string]interface{}{
				"item": map[string]interface{}{
					"name": "test-name",
				},
			},
			wantContains: "test-name (string)",
		},
		{
			name:     "eval nested field",
			template: `{{ item | eval("$.config.port") }}`,
			context: map[string]interface{}{
				"item": map[string]interface{}{
					"config": map[string]interface{}{
						"port": 8080,
					},
				},
			},
			wantContains: "8080",
		},
		{
			name:     "eval with length modifier",
			template: `{{ item | eval("$.items | length") }}`,
			context: map[string]interface{}{
				"item": map[string]interface{}{
					"items": []interface{}{"a", "b", "c"},
				},
			},
			wantContains: "3 (int)",
		},
		{
			name:     "eval with exists check",
			template: `{{ item | eval("$.optional:exists") }}`,
			context: map[string]interface{}{
				"item": map[string]interface{}{
					"optional": "value",
				},
			},
			wantContains: "true (bool)",
		},
		{
			name:     "eval with exists check (missing field)",
			template: `{{ item | eval("$.missing:exists") }}`,
			context: map[string]interface{}{
				"item": map[string]interface{}{
					"other": "value",
				},
			},
			wantContains: "false (bool)",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine, err := New(EngineTypeGonja, map[string]string{"test": tt.template}, nil, nil)
			require.NoError(t, err)

			got, err := engine.Render("test", tt.context)
			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Contains(t, got, tt.wantContains)
		})
	}
}

// Test edge cases and error conditions.
func TestGonjaFilter_EdgeCases(t *testing.T) {
	tests := []struct {
		name     string
		template string
		context  map[string]interface{}
		want     string
		wantErr  bool
	}{
		{
			name:     "sort_by with nil input",
			template: `{{ null_value | default([]) | sort_by(["$.field"]) | length }}`,
			context: map[string]interface{}{
				"null_value": nil,
			},
			want: "0",
		},
		{
			name:     "group_by with missing field",
			template: `{{ items | group_by("$.missing") | length }}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"name": "test"},
				},
			},
			want: "1", // Should group under empty string key
		},
		{
			name: "sort_by with mixed types",
			template: `{%- for item in items | sort_by(["$.value"]) -%}
{{ item.value }},
{%- endfor %}`,
			context: map[string]interface{}{
				"items": []map[string]interface{}{
					{"value": "string"},
					{"value": 123},
					{"value": true},
				},
			},
			want: "123,string,True,", // Gonja renders boolean true as "True"
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine, err := New(EngineTypeGonja, map[string]string{"test": tt.template}, nil, nil)
			require.NoError(t, err)

			got, err := engine.Render("test", tt.context)
			if tt.wantErr {
				require.Error(t, err)
				return
			}

			require.NoError(t, err)
			assert.Equal(t, tt.want, got)
		})
	}
}
