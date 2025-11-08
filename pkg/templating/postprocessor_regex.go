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
	"regexp"
	"strings"
)

// RegexReplaceProcessor applies regex-based find/replace to template output.
//
// The processor operates line-by-line, applying the regex pattern to each line
// independently. This enables efficient processing of large outputs and supports
// line-anchored patterns like ^[ ]+ for indentation normalization.
//
// Example usage for indentation normalization:
//
//	processor, err := NewRegexReplaceProcessor("^[ ]+", "  ")
//	normalized, err := processor.Process(haproxyConfig)
//
// This replaces any leading spaces with exactly 2 spaces per line.
type RegexReplaceProcessor struct {
	pattern *regexp.Regexp
	replace string
}

// NewRegexReplaceProcessor creates a new regex replace processor.
//
// Parameters:
//   - pattern: Regular expression pattern to match (e.g., "^[ ]+" for leading spaces)
//   - replace: Replacement string (e.g., "  " for 2-space indentation)
//
// Returns an error if the regex pattern is invalid.
func NewRegexReplaceProcessor(pattern, replace string) (*RegexReplaceProcessor, error) {
	re, err := regexp.Compile(pattern)
	if err != nil {
		return nil, fmt.Errorf("invalid regex pattern %q: %w", pattern, err)
	}

	return &RegexReplaceProcessor{
		pattern: re,
		replace: replace,
	}, nil
}

// Process applies the regex replacement to each line of the input.
//
// The processor:
//  1. Splits input into lines
//  2. Applies regex replacement to each line independently
//  3. Joins lines back together with original line endings
//
// This line-by-line approach enables:
//   - Efficient processing of large files
//   - Line-anchored patterns (^ and $)
//   - Predictable behavior for indentation normalization
func (p *RegexReplaceProcessor) Process(input string) (string, error) {
	if input == "" {
		return input, nil
	}

	lines := strings.Split(input, "\n")
	for i, line := range lines {
		lines[i] = p.pattern.ReplaceAllString(line, p.replace)
	}

	return strings.Join(lines, "\n"), nil
}
