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
	"fmt"

	"github.com/nikolalohinski/gonja/v2"
	"github.com/nikolalohinski/gonja/v2/exec"
)

// TemplateEngine provides template compilation and rendering capabilities.
// It pre-compiles all templates at initialization for optimal runtime performance
// and early detection of syntax errors.
type TemplateEngine struct {
	// engineType is the template engine used for rendering
	engineType EngineType

	// rawTemplates stores the original template strings by name
	rawTemplates map[string]string

	// compiledTemplates stores pre-compiled templates by name
	compiledTemplates map[string]*exec.Template
}

// New creates a new TemplateEngine with the specified engine type and templates.
// All templates are compiled during initialization. Returns an error if any
// template fails to compile or if the engine type is not supported.
//
// Example:
//
//	templates := map[string]string{
//	    "greeting": "Hello {{ name }}!",
//	    "config":   "server {{ host }}:{{ port }}",
//	}
//	engine, err := templating.New(templating.EngineTypeGonja, templates)
//	if err != nil {
//	    log.Fatal(err)
//	}
func New(engineType EngineType, templates map[string]string) (*TemplateEngine, error) {
	// Validate engine type
	if engineType != EngineTypeGonja {
		return nil, NewUnsupportedEngineError(engineType)
	}

	engine := &TemplateEngine{
		engineType:        engineType,
		rawTemplates:      make(map[string]string, len(templates)),
		compiledTemplates: make(map[string]*exec.Template, len(templates)),
	}

	// Store raw templates and compile each one
	for name, content := range templates {
		engine.rawTemplates[name] = content

		// Compile the template
		compiled, err := gonja.FromString(content)
		if err != nil {
			return nil, NewCompilationError(name, content, err)
		}

		engine.compiledTemplates[name] = compiled
	}

	return engine, nil
}

// Render executes the named template with the provided context and returns the
// rendered output. Returns an error if the template does not exist or if
// rendering fails.
//
// Example:
//
//	context := map[string]interface{}{
//	    "name": "World",
//	}
//	output, err := engine.Render("greeting", context)
//	if err != nil {
//	    log.Fatal(err)
//	}
//	fmt.Println(output) // Output: Hello World!
func (e *TemplateEngine) Render(templateName string, context map[string]interface{}) (string, error) {
	// Look up the compiled template
	template, exists := e.compiledTemplates[templateName]
	if !exists {
		// Collect available template names for the error message
		availableNames := make([]string, 0, len(e.compiledTemplates))
		for name := range e.compiledTemplates {
			availableNames = append(availableNames, name)
		}
		return "", NewTemplateNotFoundError(templateName, availableNames)
	}

	// Execute the template with the provided context
	ctx := exec.NewContext(context)
	output, err := template.ExecuteToString(ctx)
	if err != nil {
		return "", NewRenderError(templateName, err)
	}

	return output, nil
}

// EngineType returns the template engine type used by this instance.
func (e *TemplateEngine) EngineType() EngineType {
	return e.engineType
}

// TemplateNames returns a list of all available template names.
func (e *TemplateEngine) TemplateNames() []string {
	names := make([]string, 0, len(e.rawTemplates))
	for name := range e.rawTemplates {
		names = append(names, name)
	}
	return names
}

// HasTemplate returns true if a template with the given name exists.
func (e *TemplateEngine) HasTemplate(templateName string) bool {
	_, exists := e.compiledTemplates[templateName]
	return exists
}

// GetRawTemplate returns the original (uncompiled) template string for the given name.
// Returns an error if the template does not exist.
func (e *TemplateEngine) GetRawTemplate(templateName string) (string, error) {
	template, exists := e.rawTemplates[templateName]
	if !exists {
		availableNames := make([]string, 0, len(e.rawTemplates))
		for name := range e.rawTemplates {
			availableNames = append(availableNames, name)
		}
		return "", NewTemplateNotFoundError(templateName, availableNames)
	}
	return template, nil
}

// TemplateCount returns the number of templates in this engine.
func (e *TemplateEngine) TemplateCount() int {
	return len(e.compiledTemplates)
}

// String returns a string representation of the engine for debugging.
func (e *TemplateEngine) String() string {
	return fmt.Sprintf("TemplateEngine{type=%s, templates=%d}", e.engineType, e.TemplateCount())
}
