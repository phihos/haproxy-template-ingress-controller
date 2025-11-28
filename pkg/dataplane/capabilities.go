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

package dataplane

import "haproxy-template-ic/pkg/dataplane/client"

// Capabilities defines which features are available for a given HAProxy/DataPlane API version.
// This type is re-exported from pkg/dataplane/client for convenience.
type Capabilities = client.Capabilities

// CapabilitiesFromVersion computes capabilities based on a HAProxy version.
// This is used for local HAProxy binary detection (haproxy -v).
//
// Capability thresholds (verified against OpenAPI specs):
//   - SupportsCrtList: v3.2+ (CRT-list storage endpoint)
//   - SupportsMapStorage: v3.0+ (Map file storage endpoint)
//   - SupportsGeneralStorage: v3.0+ (General file storage)
//   - SupportsQUIC: v3.0+ (QUIC/HTTP3 configuration options)
//   - SupportsHTTP2: v3.0+ (HTTP/2 configuration)
//   - SupportsRuntimeMaps: v3.0+ (Runtime map operations)
//   - SupportsRuntimeServers: v3.0+ (Runtime server operations)
func CapabilitiesFromVersion(v *Version) Capabilities {
	if v == nil {
		return Capabilities{} // All false - safest default
	}

	return Capabilities{
		// Storage capabilities
		SupportsCrtList:        v.Major > 3 || (v.Major == 3 && v.Minor >= 2),
		SupportsMapStorage:     v.Major >= 3,
		SupportsGeneralStorage: v.Major >= 3,

		// Configuration capabilities
		SupportsHTTP2: v.Major >= 3,
		SupportsQUIC:  v.Major >= 3,

		// Runtime capabilities
		SupportsRuntimeMaps:    v.Major >= 3,
		SupportsRuntimeServers: v.Major >= 3,
	}
}
