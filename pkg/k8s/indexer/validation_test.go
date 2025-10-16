package indexer

import (
	"strings"
	"testing"
)

func TestValidateJSONPath_Success(t *testing.T) {
	tests := []struct {
		name string
		expr string
	}{
		{
			name: "simple field",
			expr: "metadata.namespace",
		},
		{
			name: "nested field",
			expr: "metadata.labels.app",
		},
		{
			name: "array subscript with string key",
			expr: "metadata.labels['app']",
		},
		{
			name: "array subscript with number",
			expr: "spec.ports[0]",
		},
		{
			name: "complex expression",
			expr: "spec.containers[0].ports[0].containerPort",
		},
		{
			name: "expression with leading dot",
			expr: ".metadata.namespace",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateJSONPath(tt.expr)
			if err != nil {
				t.Errorf("ValidateJSONPath() error = %v, want nil", err)
			}
		})
	}
}

func TestValidateJSONPath_InvalidSyntax(t *testing.T) {
	tests := []struct {
		name    string
		expr    string
		wantErr string
	}{
		{
			name:    "empty expression",
			expr:    "",
			wantErr: "empty",
		},
		{
			name:    "unclosed bracket",
			expr:    "metadata.labels['app",
			wantErr: "JSONPath",
		},
		{
			name:    "invalid bracket syntax",
			expr:    "metadata.labels[",
			wantErr: "JSONPath",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateJSONPath(tt.expr)
			if err == nil {
				t.Errorf("ValidateJSONPath() expected error, got nil")
				return
			}
			if !strings.Contains(err.Error(), tt.wantErr) {
				t.Errorf("ValidateJSONPath() error = %v, want error containing %q", err, tt.wantErr)
			}
		})
	}
}

func TestValidateJSONPath_Integration(t *testing.T) {
	// Test that validation matches actual evaluator behavior
	validExpressions := []string{
		"metadata.name",
		"metadata.namespace",
		"metadata.labels.app",
		"spec.selector.matchLabels.app",
	}

	for _, expr := range validExpressions {
		// Should pass validation
		err := ValidateJSONPath(expr)
		if err != nil {
			t.Errorf("ValidateJSONPath(%q) unexpected error: %v", expr, err)
		}

		// Should be able to create evaluator
		_, err = NewJSONPathEvaluator(expr)
		if err != nil {
			t.Errorf("NewJSONPathEvaluator(%q) unexpected error: %v", expr, err)
		}
	}
}
