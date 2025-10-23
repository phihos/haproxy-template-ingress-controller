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
