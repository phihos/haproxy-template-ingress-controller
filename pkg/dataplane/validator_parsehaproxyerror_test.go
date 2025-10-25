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

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestParseHAProxyError(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name: "single alert with full context",
			input: `Configuration file is valid
defaults
    mode http
    timeout client 30s

userlist auth_users
    user admin password ...
[ALERT] (001) : parsing [haproxy.cfg:15] : unknown user 'missing' in userlist 'auth_users' (declared at haproxy.cfg:12)

backend api
    server s1 127.0.0.1:8080

Fatal errors found in configuration.`,
			expected: `  userlist auth_users
      user admin password ...
→ [ALERT] (001) : parsing [haproxy.cfg:15] : unknown user 'missing' in userlist 'auth_users' (declared at haproxy.cfg:12)
  backend api
      server s1 127.0.0.1:8080`,
		},
		{
			name: "alert at start of output",
			input: `[ALERT] (001) : parsing [haproxy.cfg:1] : unknown keyword 'invalid' in 'global' section
global
    daemon

defaults
    mode http`,
			expected: `→ [ALERT] (001) : parsing [haproxy.cfg:1] : unknown keyword 'invalid' in 'global' section
  global
      daemon`,
		},
		{
			name: "alert at end of output",
			input: `global
    daemon

defaults
    mode http

backend api
[ALERT] (001) : parsing [haproxy.cfg:20] : backend 'api' has no server`,
			expected: `      mode http
  backend api
→ [ALERT] (001) : parsing [haproxy.cfg:20] : backend 'api' has no server`,
		},
		{
			name: "multiple alerts",
			input: `defaults
    mode http

frontend http
[ALERT] (001) : parsing [haproxy.cfg:10] : frontend 'http' has no 'bind' directive
    default_backend api

backend api
[ALERT] (002) : parsing [haproxy.cfg:15] : backend 'api' has no server
    balance roundrobin`,
			expected: `      mode http
  frontend http
→ [ALERT] (001) : parsing [haproxy.cfg:10] : frontend 'http' has no 'bind' directive
      default_backend api
  backend api

      default_backend api
  backend api
→ [ALERT] (002) : parsing [haproxy.cfg:15] : backend 'api' has no server
      balance roundrobin`,
		},
		{
			name: "no alerts - return full output",
			input: `global
    daemon

defaults
    mode http`,
			expected: `global
    daemon

defaults
    mode http`,
		},
		{
			name:     "empty output",
			input:    "",
			expected: "",
		},
		{
			name: "only summary lines - filtered out",
			input: `[ALERT] (001) : Fatal errors found in configuration.
[ALERT] (001) : Error(s) found in configuration file.`,
			expected: `[ALERT] (001) : Fatal errors found in configuration.
[ALERT] (001) : Error(s) found in configuration file.`,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := parseHAProxyError(tt.input, "")
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestParseHAProxyErrorWithConfigContext(t *testing.T) {
	configContent := `global
    daemon

defaults
    mode http
    timeout client 30s

backend api
    balance roundrobin
    server SRV_1 10.244.0.8:80.0
    server SRV_2 10.244.0.9:8080

frontend http
    bind :80`

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name: "error with config context",
			input: `[NOTICE]   (001) : haproxy version is 3.2.7
[NOTICE]   (001) : path to executable is /usr/local/sbin/haproxy
[ALERT]    (001) : config : [haproxy.cfg:10] : 'server api/SRV_1' : invalid character '.' in port number '80.0' in '10.244.0.8:80.0'`,
			expected: `  [NOTICE]   (001) : haproxy version is 3.2.7
  [NOTICE]   (001) : path to executable is /usr/local/sbin/haproxy
→ [ALERT]    (001) : config : [haproxy.cfg:10] : 'server api/SRV_1' : invalid character '.' in port number '80.0' in '10.244.0.8:80.0'

  Config context:
     7
     8   backend api
     9       balance roundrobin
    10 →     server SRV_1 10.244.0.8:80.0
    11       server SRV_2 10.244.0.9:8080
    12
    13   frontend http`,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := parseHAProxyError(tt.input, configContent)
			assert.Equal(t, tt.expected, result)
		})
	}
}
