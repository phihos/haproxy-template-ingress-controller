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
	"io"
	"strings"

	"github.com/nikolalohinski/gonja/v2/loaders"
)

// SimpleLoader is a basic in-memory template loader that doesn't require
// path prefixes or filesystem-like path resolution. It's simpler than
// Gonja's MemoryLoader which enforces '/' prefixes.
//
// This loader is designed for flat template namespaces where templates
// reference each other by simple names without directory hierarchies.
type SimpleLoader struct {
	templates map[string]string
}

// NewSimpleLoader creates a new SimpleLoader with the given templates.
// Template names can be any string - no '/' prefix required.
func NewSimpleLoader(templates map[string]string) loaders.Loader {
	return &SimpleLoader{
		templates: templates,
	}
}

// Read returns an io.Reader for the template content.
// The path is used as-is to look up the template in the map.
func (l *SimpleLoader) Read(path string) (io.Reader, error) {
	content, exists := l.templates[path]
	if !exists {
		return nil, fmt.Errorf("template not found: %s", path)
	}
	return strings.NewReader(content), nil
}

// Resolve returns the path unchanged. Since we use a flat namespace
// without directory hierarchies, no path resolution is needed.
func (l *SimpleLoader) Resolve(path string) (string, error) {
	// Check if template exists
	if _, exists := l.templates[path]; !exists {
		return "", fmt.Errorf("template not found: %s", path)
	}
	return path, nil
}

// Inherit returns the same loader instance. This loader doesn't support
// relative path resolution (e.g., "../other.html") since templates use
// a flat namespace.
func (l *SimpleLoader) Inherit(from string) (loaders.Loader, error) {
	// Return the same loader - no path context changes needed
	return l, nil
}
