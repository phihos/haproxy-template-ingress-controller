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
	"fmt"
	"path/filepath"
)

// PathResolver resolves auxiliary file names to absolute paths based on file type.
// This is used by the get_path filter to automatically construct absolute paths
// for HAProxy auxiliary files (maps, SSL certificates, general files).
type PathResolver struct {
	// MapsDir is the absolute path to the HAProxy maps directory.
	// Default: /etc/haproxy/maps
	MapsDir string

	// SSLDir is the absolute path to the HAProxy SSL certificates directory.
	// Default: /etc/haproxy/ssl
	SSLDir string

	// GeneralDir is the absolute path to the HAProxy general files directory.
	// Default: /etc/haproxy/general
	GeneralDir string
}

// GetPath is a template filter that resolves a filename to its absolute path
// based on the file type.
//
// Usage in templates:
//
//	{{ "host.map" | get_path("map") }}        → /etc/haproxy/maps/host.map
//	{{ "504.http" | get_path("file") }}       → /etc/haproxy/general/504.http
//	{{ "cert.pem" | get_path("cert") }}       → /etc/haproxy/ssl/cert.pem
//
// Parameters:
//   - filename: The base filename (without directory path)
//   - args: Single argument specifying file type: "map", "file", or "cert"
//
// Returns:
//   - Absolute path to the file
//   - Error if filename is not a string, file type is missing/invalid, or path construction fails
func (pr *PathResolver) GetPath(filename interface{}, args ...interface{}) (interface{}, error) {
	// Validate filename is a string
	filenameStr, ok := filename.(string)
	if !ok {
		return nil, fmt.Errorf("get_path: filename must be a string, got %T", filename)
	}

	if filenameStr == "" {
		return nil, fmt.Errorf("get_path: filename cannot be empty")
	}

	// Validate file type argument is provided
	if len(args) == 0 {
		return nil, fmt.Errorf("get_path: file type argument required (\"map\", \"file\", or \"cert\")")
	}

	// Extract and validate file type
	fileTypeInterface := args[0]
	fileType, ok := fileTypeInterface.(string)
	if !ok {
		return nil, fmt.Errorf("get_path: file type must be a string, got %T", fileTypeInterface)
	}

	// Resolve path based on file type
	var basePath string
	switch fileType {
	case "map":
		basePath = pr.MapsDir
	case "file":
		basePath = pr.GeneralDir
	case "cert":
		basePath = pr.SSLDir
	default:
		return nil, fmt.Errorf("get_path: invalid file type %q, must be \"map\", \"file\", or \"cert\"", fileType)
	}

	// Construct absolute path
	absolutePath := filepath.Join(basePath, filenameStr)

	return absolutePath, nil
}

// GlobMatch filters a list of strings by glob pattern.
//
// Usage in templates:
//
//	{%- set matching = template_snippets | glob_match("backend-annotation-*") %}
//	{%- for snippet_name in matching %}
//	  {% include snippet_name %}
//	{%- endfor %}
//
// Parameters:
//   - in: List of strings to filter ([]interface{} or []string)
//   - args: Single argument specifying glob pattern (supports * and ? wildcards)
//
// Returns:
//   - Filtered list containing only matching strings
//   - Error if input is not a list, pattern is missing, or pattern is invalid
func GlobMatch(in interface{}, args ...interface{}) (interface{}, error) {
	// Convert input to []interface{}
	var list []interface{}

	switch v := in.(type) {
	case []interface{}:
		list = v
	case []string:
		// Convert []string to []interface{}
		list = make([]interface{}, len(v))
		for i, s := range v {
			list[i] = s
		}
	default:
		return nil, fmt.Errorf("glob_match: input must be a list, got %T", in)
	}

	// Validate pattern argument
	if len(args) == 0 {
		return nil, fmt.Errorf("glob_match: pattern argument required")
	}

	pattern, ok := args[0].(string)
	if !ok {
		return nil, fmt.Errorf("glob_match: pattern must be a string, got %T", args[0])
	}

	// Filter by glob pattern
	var result []interface{}
	for _, item := range list {
		str, ok := item.(string)
		if !ok {
			continue // Skip non-string items
		}

		matched, err := filepath.Match(pattern, str)
		if err != nil {
			return nil, fmt.Errorf("glob_match: invalid pattern %q: %w", pattern, err)
		}

		if matched {
			result = append(result, str)
		}
	}

	return result, nil
}

// B64Decode decodes a base64-encoded string.
//
// Usage in templates:
//
//	{{ secret.data.username | b64decode }}
//	{{ secret.data.password | b64decode }}
//
// Parameters:
//   - in: Base64-encoded string to decode
//
// Returns:
//   - Decoded string
//   - Error if input is not a string or decoding fails
//
// Note: Kubernetes secrets automatically base64-encode all data values,
// so this filter is needed to access the plain-text content.
func B64Decode(in interface{}, args ...interface{}) (interface{}, error) {
	str, ok := in.(string)
	if !ok {
		return nil, fmt.Errorf("b64decode: input must be a string, got %T", in)
	}

	decoded, err := base64.StdEncoding.DecodeString(str)
	if err != nil {
		return nil, fmt.Errorf("b64decode: %w", err)
	}

	return string(decoded), nil
}
