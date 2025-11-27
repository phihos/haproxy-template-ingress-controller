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

// NewPathResolverWithCapabilities creates a PathResolver with CRT-list directory
// determined by HAProxy capabilities. When CRT-list storage is not supported
// (HAProxy < 3.2), CRT-list files are stored in the general files directory
// instead of the SSL directory.
//
// This factory function centralizes the path resolution logic that was previously
// duplicated across renderer, dryrunvalidator, and testrunner components.
//
// Parameters:
//   - mapsDir: Absolute path to the HAProxy maps directory (e.g., /etc/haproxy/maps)
//   - sslDir: Absolute path to the HAProxy SSL certificates directory (e.g., /etc/haproxy/ssl)
//   - generalDir: Absolute path to the HAProxy general files directory (e.g., /etc/haproxy/general)
//   - supportsCrtList: Whether HAProxy supports CRT-list storage (v3.2+)
//
// Returns:
//   - A configured PathResolver with CRTListDir set based on capability
func NewPathResolverWithCapabilities(mapsDir, sslDir, generalDir string, supportsCrtList bool) *PathResolver {
	crtListDir := sslDir
	if !supportsCrtList {
		crtListDir = generalDir
	}

	return &PathResolver{
		MapsDir:    mapsDir,
		SSLDir:     sslDir,
		CRTListDir: crtListDir,
		GeneralDir: generalDir,
	}
}
