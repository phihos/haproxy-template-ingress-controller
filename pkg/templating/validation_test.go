package templating

import (
	"errors"
	"strings"
	"testing"
)

func TestValidateTemplate_Success(t *testing.T) {
	tests := []struct {
		name     string
		template string
	}{
		{
			name:     "simple template",
			template: "Hello {{ name }}!",
		},
		{
			name:     "template with loop",
			template: "{% for item in items %}{{ item }}{% endfor %}",
		},
		{
			name:     "template with conditional",
			template: "{% if enabled %}Active{% else %}Inactive{% endif %}",
		},
		{
			name:     "template with filter",
			template: "{{ value|upper }}",
		},
		{
			name:     "empty template",
			template: "",
		},
		{
			name:     "plain text",
			template: "This is plain text with no template syntax",
		},
		{
			name:     "HAProxy config template",
			template: "frontend {{ frontend_name }}\n  bind {{ bind_address }}:{{ port }}\n",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateTemplate(tt.template, EngineTypeGonja)
			if err != nil {
				t.Errorf("ValidateTemplate() error = %v, want nil", err)
			}
		})
	}
}

func TestValidateTemplate_InvalidSyntax(t *testing.T) {
	tests := []struct {
		name     string
		template string
		wantErr  string
	}{
		{
			name:     "unclosed variable tag",
			template: "Hello {{ name",
			wantErr:  "template",
		},
		{
			name:     "unclosed block tag",
			template: "{% for item in items",
			wantErr:  "template",
		},
		{
			name:     "invalid tag syntax",
			template: "{% invalid_tag %}",
			wantErr:  "template",
		},
		{
			name:     "mismatched block tags",
			template: "{% if condition %}content{% endfor %}",
			wantErr:  "template",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateTemplate(tt.template, EngineTypeGonja)
			if err == nil {
				t.Errorf("ValidateTemplate() expected error, got nil")
				return
			}
			if !strings.Contains(err.Error(), tt.wantErr) {
				t.Errorf("ValidateTemplate() error = %v, want error containing %q", err, tt.wantErr)
			}
		})
	}
}

func TestValidateTemplate_UnsupportedEngine(t *testing.T) {
	// Create an invalid engine type (anything other than EngineTypeGonja)
	invalidEngine := EngineType(999)

	err := ValidateTemplate("{{ test }}", invalidEngine)
	if err == nil {
		t.Fatal("ValidateTemplate() expected error for unsupported engine, got nil")
	}

	// Check that we get an UnsupportedEngineError
	var unsupportedErr *UnsupportedEngineError
	if !errors.As(err, &unsupportedErr) {
		t.Errorf("ValidateTemplate() error type = %T, want *UnsupportedEngineError", err)
	}
}

func TestValidateTemplate_GonjaEngine(t *testing.T) {
	// Test that EngineTypeGonja works correctly
	err := ValidateTemplate("{{ variable }}", EngineTypeGonja)
	if err != nil {
		t.Errorf("ValidateTemplate() with EngineTypeGonja error = %v, want nil", err)
	}
}
