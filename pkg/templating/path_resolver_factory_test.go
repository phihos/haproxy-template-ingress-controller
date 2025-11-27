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
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNewPathResolverWithCapabilities(t *testing.T) {
	tests := []struct {
		name            string
		mapsDir         string
		sslDir          string
		generalDir      string
		supportsCrtList bool
		wantCRTListDir  string
	}{
		{
			name:            "CRT-list supported - uses SSL directory",
			mapsDir:         "/etc/haproxy/maps",
			sslDir:          "/etc/haproxy/ssl",
			generalDir:      "/etc/haproxy/files",
			supportsCrtList: true,
			wantCRTListDir:  "/etc/haproxy/ssl",
		},
		{
			name:            "CRT-list not supported - uses general directory",
			mapsDir:         "/etc/haproxy/maps",
			sslDir:          "/etc/haproxy/ssl",
			generalDir:      "/etc/haproxy/files",
			supportsCrtList: false,
			wantCRTListDir:  "/etc/haproxy/files",
		},
		{
			name:            "empty paths preserved",
			mapsDir:         "",
			sslDir:          "",
			generalDir:      "",
			supportsCrtList: true,
			wantCRTListDir:  "",
		},
		{
			name:            "relative paths work",
			mapsDir:         "maps",
			sslDir:          "ssl",
			generalDir:      "files",
			supportsCrtList: false,
			wantCRTListDir:  "files",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			pr := NewPathResolverWithCapabilities(tt.mapsDir, tt.sslDir, tt.generalDir, tt.supportsCrtList)

			assert.Equal(t, tt.mapsDir, pr.MapsDir, "MapsDir should be preserved")
			assert.Equal(t, tt.sslDir, pr.SSLDir, "SSLDir should be preserved")
			assert.Equal(t, tt.generalDir, pr.GeneralDir, "GeneralDir should be preserved")
			assert.Equal(t, tt.wantCRTListDir, pr.CRTListDir, "CRTListDir should match expected")
		})
	}
}

func TestNewPathResolverWithCapabilities_CRTListFallback(t *testing.T) {
	// Focused test on the CRT-list fallback behavior
	sslDir := "/etc/haproxy/ssl"
	generalDir := "/etc/haproxy/files"

	// When CRT-list is supported, CRTListDir should use SSL directory
	prSupported := NewPathResolverWithCapabilities("/maps", sslDir, generalDir, true)
	assert.Equal(t, sslDir, prSupported.CRTListDir,
		"With CRT-list support, CRTListDir should equal SSLDir")

	// When CRT-list is not supported, CRTListDir should fall back to general directory
	prUnsupported := NewPathResolverWithCapabilities("/maps", sslDir, generalDir, false)
	assert.Equal(t, generalDir, prUnsupported.CRTListDir,
		"Without CRT-list support, CRTListDir should fall back to GeneralDir")
}
