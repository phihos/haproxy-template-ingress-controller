//go:build integration

package integration

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/rekby/fixenv"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"haproxy-template-ic/pkg/dataplane"
	"haproxy-template-ic/pkg/dataplane/auxiliaryfiles"
)

// TestMain sets up package-scoped fixtures and runs tests
func TestMain(m *testing.M) {
	fixenv.RunTests(m)
}

// syncTestCase defines a single sync test scenario
type syncTestCase struct {
	name              string
	initialConfigFile string // Config to push initially
	desiredConfigFile string // Target config to reach

	// Expected operation counts
	expectedCreates int
	expectedUpdates int
	expectedDeletes int

	// Expected operations (validated by operation descriptions)
	// Example: []string{"Create backend 'web'", "Create server 'srv1' in backend 'web'"}
	expectedOperations []string

	// Reload expectations
	// expectedReload indicates whether a HAProxy reload should be triggered.
	// true = expects status 202 with Reload-ID header
	// false = expects status 200 without reload
	expectedReload bool

	// Fallback to raw push expectation
	// expectedFallbackToRaw indicates whether the sync is expected to fall back to raw config push.
	// Fallback typically occurs when fine-grained sync encounters transactional conflicts
	// in the HAProxy Dataplane API (e.g., 409 conflicts when creating certain resources).
	// true = expects fallback to raw push (operation tracking may be less granular)
	// false = expects fine-grained sync to succeed without fallback
	expectedFallbackToRaw bool

	// Auxiliary files for INITIAL configuration
	// These files are uploaded before pushing the initial config to ensure it validates
	// Map: HAProxy file path → testdata file to load
	// Example: map[string]string{"/etc/haproxy/errors/400.http": "error-files/400.http"}
	initialGeneralFiles map[string]string
	initialSSLCertificates map[string]string
	initialMapFiles map[string]string

	// Auxiliary files for DESIRED configuration (used in sync operation)
	// These files are synced as part of the high-level Sync() call
	// Map: HAProxy file path → testdata file to load
	// Example: map[string]string{"/etc/haproxy/errors/400.http": "error-files/400.http"}
	generalFiles map[string]string

	// SSL certificates to sync before config operations
	// Map: SSL certificate name → testdata file to load
	// Example: map[string]string{"example.com.pem": "ssl-certs/example.com.pem"}
	sslCertificates map[string]string

	// Map files to sync before config operations
	// Map: map file path → testdata file to load
	// Example: map[string]string{"domains.map": "map-files/domains.map"}
	mapFiles map[string]string

	// Skip reason for unsupported features (test-first approach)
	// If set, test will be skipped with this message
	skipReason string
}

// TestSync runs table-driven synchronization tests
func TestSync(t *testing.T) {
	testCases := []syncTestCase{
		// ==================== BASIC BACKEND OPERATIONS ====================
		{
			name:              "add-backend-with-server",
			initialConfigFile: "basic/empty.cfg",
			desiredConfigFile: "basic/one-backend.cfg",
			expectedCreates:   2,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create backend 'test-backend'",
				"Create server 'srv1' in backend 'test-backend'",
			},
			expectedReload: true,
		},
		{
			name:              "remove-backend-with-server",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "basic/empty.cfg",
			expectedCreates:   0,
			expectedUpdates:   0,
			expectedDeletes:   1,
			expectedOperations: []string{
				"Delete backend 'test-backend'",
			},
			expectedReload: true,
		},

		// ==================== BASIC SERVER OPERATIONS ====================
		{
			name:              "add-server-to-backend",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "basic/two-servers.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create server 'srv2' in backend 'test-backend'",
			},
			expectedReload: true,
		},
		{
			name:              "remove-server-from-backend",
			initialConfigFile: "basic/two-servers.cfg",
			desiredConfigFile: "basic/one-backend.cfg",
			expectedCreates:   0,
			expectedUpdates:   0,
			expectedDeletes:   1,
			expectedOperations: []string{
				"Delete server 'srv2' from backend 'test-backend'",
			},
			expectedReload: true,
		},

		// ==================== SERVER ATTRIBUTE MODIFICATIONS ====================
		{
			name:              "server-change-weight",
			initialConfigFile: "servers/weight-100.cfg",
			desiredConfigFile: "servers/weight-200.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server 'srv1' in backend 'web'",
			},
			expectedReload: false,
		},
		{
			name:              "server-add-with-backup",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "servers/with-backup.cfg",
			expectedCreates:   3,
			expectedUpdates:   0,
			expectedDeletes:   1,
			expectedOperations: []string{
				"Delete backend 'test-backend'",
				"Create backend 'web'",
				"Create server 'srv1' in backend 'web'",
				"Create server 'srv2' in backend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "server-with-maxconn",
			initialConfigFile: "basic/empty.cfg",
			desiredConfigFile: "servers/with-maxconn.cfg",
			expectedCreates:   2,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create backend 'web'",
				"Create server 'srv1' in backend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "server-with-check-intervals",
			initialConfigFile: "basic/empty.cfg",
			desiredConfigFile: "servers/with-check-inter.cfg",
			expectedCreates:   2,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create backend 'web'",
				"Create server 'srv1' in backend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "server-change-address",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "servers/address-changed.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server 'srv1' in backend 'test-backend'",
			},
			expectedReload: false,
		},
		{
			name:              "server-change-port",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "servers/port-changed.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server 'srv1' in backend 'test-backend'",
			},
			expectedReload: false,
		},

		// ==================== RUNTIME API OPERATIONS (NO RELOAD) ====================
		{
			name:              "srv-weight-no-reload",
			initialConfigFile: "servers/weight-100.cfg",
			desiredConfigFile: "servers/weight-200.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server 'srv1' in backend 'web'",
			},
			expectedReload: false,
		},
		{
			name:              "srv-addr-no-reload",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "servers/address-changed.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server 'srv1' in backend 'test-backend'",
			},
			expectedReload: false,
		},
		{
			name:              "srv-port-no-reload",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "servers/port-changed.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server 'srv1' in backend 'test-backend'",
			},
			expectedReload: false,
		},
		{
			name:              "srv-enable-relocate",
			initialConfigFile: "servers/disabled-dummy.cfg",
			desiredConfigFile: "servers/enabled-real.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server 'srv1' in backend 'web'",
			},
			expectedReload: false,
		},
		{
			name:              "srv-disable-relocate",
			initialConfigFile: "servers/enabled-real.cfg",
			desiredConfigFile: "servers/disabled-dummy.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server 'srv1' in backend 'web'",
			},
			expectedReload: false,
		},
		{
			name:              "srv-maintenance",
			initialConfigFile: "servers/enabled-dummy.cfg",
			desiredConfigFile: "servers/disabled-dummy.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server 'srv1' in backend 'web'",
			},
			expectedReload: false,
		},

		// ==================== MULTIPLE BACKEND OPERATIONS ====================
		{
			name:              "add-two-backends",
			initialConfigFile: "basic/empty.cfg",
			desiredConfigFile: "backends/two-backends.cfg",
			expectedCreates:   4,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create backend 'web'",
				"Create server 'srv1' in backend 'web'",
				"Create backend 'api'",
				"Create server 'srv1' in backend 'api'",
			},
			expectedReload: true,
		},
		{
			name:              "add-three-backends",
			initialConfigFile: "basic/empty.cfg",
			desiredConfigFile: "backends/three-backends.cfg",
			expectedCreates:   6,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create backend 'web'",
				"Create server 'srv1' in backend 'web'",
				"Create backend 'api'",
				"Create server 'srv1' in backend 'api'",
				"Create backend 'admin'",
				"Create server 'srv1' in backend 'admin'",
			},
			expectedReload: true,
		},
		{
			name:              "remove-two-backends",
			initialConfigFile: "backends/two-backends.cfg",
			desiredConfigFile: "basic/empty.cfg",
			expectedCreates:   0,
			expectedUpdates:   0,
			expectedDeletes:   2,
			expectedOperations: []string{
				"Delete backend 'web'",
				"Delete backend 'api'",
			},
			expectedReload: true,
		},
		{
			name:              "add-backend-no-servers",
			initialConfigFile: "basic/empty.cfg",
			desiredConfigFile: "backends/empty-backend.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create backend 'web'",
			},
			expectedReload: true,
		},

		// ==================== COMPLEX MIXED OPERATIONS ====================
		{
			name:              "mixed-add-remove-servers",
			initialConfigFile: "complex/three-servers.cfg",
			desiredConfigFile: "complex/srv2-srv3.cfg",
			expectedCreates:   0,
			expectedUpdates:   0,
			expectedDeletes:   1,
			expectedOperations: []string{
				"Delete server 'srv1' from backend 'test-backend'",
			},
			expectedReload: true,
		},
		{
			name:              "replace-all-servers",
			initialConfigFile: "basic/two-servers.cfg",
			desiredConfigFile: "complex/all-new-servers.cfg",
			expectedCreates:   2,
			expectedUpdates:   0,
			expectedDeletes:   2,
			expectedOperations: []string{
				"Delete server 'srv1' from backend 'test-backend'",
				"Delete server 'srv2' from backend 'test-backend'",
				"Create server 'srv4' in backend 'test-backend'",
				"Create server 'srv5' in backend 'test-backend'",
			},
			expectedReload: true,
		},
		{
			name:              "multi-backend-mixed",
			initialConfigFile: "backends/two-backends.cfg",
			desiredConfigFile: "complex/multiple-backends-mixed.cfg",
			expectedCreates:   4,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create server 'srv3' in backend 'web'",
				"Create server 'srv2' in backend 'api'",
				"Create backend 'admin'",
				"Create server 'srv1' in backend 'admin'",
			},
			expectedReload: true,
		},
		{
			name:              "srv-weight-and-add",
			initialConfigFile: "servers/weight-100.cfg",
			desiredConfigFile: "servers/weight-100-plus-second.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create server 'srv2' in backend 'web'",
			},
			expectedReload: true,
		},

		// ==================== UNSUPPORTED FEATURES (WILL SKIP) ====================
		// These tests demonstrate features we want to support in the future
		// When implemented, remove the skipReason to enable the test

		{
			name:              "frontend-add",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "frontends/basic.cfg",
			expectedCreates:   2,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create frontend 'web'",
				"Create bind '*:80' in frontend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "frontend-with-acl",
			initialConfigFile: "frontends/basic.cfg",
			desiredConfigFile: "frontends/with-acl.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create ACL 'is_static' in frontend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-acl",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "acls/backend-with-acl.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create ACL 'is_local' in backend 'test-backend'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-http-request-rule",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "rules/http-request.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create HTTP request rule (set-header) in backend 'test-backend'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-http-response-rule",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "rules/http-response.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create HTTP response rule (set-header) in backend 'test-backend'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-change-balance-algorithm",
			initialConfigFile: "backend-attrs/balance-roundrobin.cfg",
			desiredConfigFile: "backends/balance-leastconn.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update backend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-change-mode",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "backend-attrs/mode-tcp.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update backend 'test-backend'",
			},
			expectedReload: true,
		},
		{
			name:              "global-change-maxconn",
			initialConfigFile: "global/maxconn-2000.cfg",
			desiredConfigFile: "global/maxconn-4000.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update global section",
			},
			expectedReload: true,
		},
		{
			name:              "defaults-change-mode",
			initialConfigFile: "basic/one-backend.cfg",
			desiredConfigFile: "defaults/mode-tcp.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update defaults section 'unnamed_defaults_1'",
			},
			expectedReload: true,
		},

		// ==================== TIMEOUT DIRECTIVE OPERATIONS ====================
		{
			name:              "defaults-change-timeouts",
			initialConfigFile: "timeouts/defaults-base.cfg",
			desiredConfigFile: "timeouts/defaults-modified.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update defaults section 'unnamed_defaults_1'",
			},
			expectedReload: true,
		},
		{
			name:              "frontend-add-timeouts",
			initialConfigFile: "timeouts/defaults-base.cfg",
			desiredConfigFile: "timeouts/frontend-with-timeouts.cfg",
			expectedCreates:   2,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create frontend 'http-in'",
				"Create bind '*:80' in frontend 'http-in'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-timeouts",
			initialConfigFile: "timeouts/defaults-base.cfg",
			desiredConfigFile: "timeouts/backend-with-timeouts.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update backend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-remove-timeouts",
			initialConfigFile: "timeouts/backend-with-timeouts.cfg",
			desiredConfigFile: "timeouts/defaults-base.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update backend 'web'",
			},
			expectedReload: true,
		},


	// ==================== COOKIE-BASED PERSISTENCE ====================
	{
		name:              "backend-add-server-cookies",
		initialConfigFile: "cookies/cookies-base.cfg",
		desiredConfigFile: "cookies/cookies-server-cookies.cfg",
		expectedCreates:   0,
		expectedUpdates:   3,
		expectedDeletes:   0,
		expectedOperations: []string{
			"Update backend 'web'",
			"Update server 'srv1' in backend 'web'",
			"Update server 'srv2' in backend 'web'",
		},
		expectedReload: true,
	},
	{
		name:              "backend-add-cookie-prefix",
		initialConfigFile: "cookies/cookies-server-cookies.cfg",
		desiredConfigFile: "cookies/cookies-with-prefix.cfg",
		expectedCreates:   0,
		expectedUpdates:   1,
		expectedDeletes:   0,
		expectedOperations: []string{
			"Update backend 'web'",
		},
		expectedReload: true,
	},
	{
		name:              "backend-remove-cookies",
		initialConfigFile: "cookies/cookies-server-cookies.cfg",
		desiredConfigFile: "cookies/cookies-base.cfg",
		expectedCreates:   0,
		expectedUpdates:   3,
		expectedDeletes:   0,
		expectedOperations: []string{
			"Update backend 'web'",
			"Update server 'srv1' in backend 'web'",
			"Update server 'srv2' in backend 'web'",
		},
		expectedReload: true,
	},

	// ==================== LISTEN SECTION OPERATIONS ====================
	{
		name:              "listen-add-section",
		initialConfigFile: "listen/listen-base.cfg",
		desiredConfigFile: "listen/listen-with-servers.cfg",
		expectedCreates:   0,
		expectedUpdates:   0,
		expectedDeletes:   1,
		expectedOperations: []string{
			"Delete backend 'web'",
		},
		expectedReload: true,
	},
	{
		name:              "listen-remove-section",
		initialConfigFile: "listen/listen-with-servers.cfg",
		desiredConfigFile: "listen/listen-base.cfg",
		expectedCreates:   1,
		expectedUpdates:   0,
		expectedDeletes:   1,
		expectedOperations: []string{
			"Delete listen section 'web'",
			"Create backend 'web'",
		},
		expectedReload: true,
	},
	{
		name:              "listen-tcp-mode",
		initialConfigFile: "listen/listen-base.cfg",
		desiredConfigFile: "listen/listen-tcp-mode.cfg",
		expectedCreates:   0,
		expectedUpdates:   1,
		expectedDeletes:   1,
		expectedOperations: []string{
			"Delete backend 'web'",
			"Update defaults section 'unnamed_defaults_1'",
		},
		expectedReload: true,
	},
		// ==================== BIND OPERATIONS ====================
		{
			name:              "frontend-add-binds",
			initialConfigFile: "binds/frontend-with-bind.cfg",
			desiredConfigFile: "binds/frontend-multiple-binds.cfg",
			expectedCreates:   2,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create bind '*:8080' in frontend 'http-in'",
				"Create bind '192.168.1.100:80' in frontend 'http-in'",
			},
			expectedReload: true,
		},
		{
			name:              "frontend-remove-binds",
			initialConfigFile: "binds/frontend-multiple-binds.cfg",
			desiredConfigFile: "binds/frontend-with-bind.cfg",
			expectedCreates:   0,
			expectedUpdates:   0,
			expectedDeletes:   2,
			expectedOperations: []string{
				"Delete bind '*:8080' from frontend 'http-in'",
				"Delete bind '192.168.1.100:80' from frontend 'http-in'",
			},
			expectedReload: true,
		},

		// ==================== TCP RULE OPERATIONS ====================
		{
			name:              "frontend-add-tcp-request-rule",
			initialConfigFile: "tcp-rules/frontend-base.cfg",
			desiredConfigFile: "tcp-rules/frontend-with-tcp-request.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create TCP request rule (connection) in frontend 'tcp-in'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-tcp-request-rule",
			initialConfigFile: "tcp-rules/backend-base.cfg",
			desiredConfigFile: "tcp-rules/backend-with-tcp-request.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create TCP request rule (content) in backend 'mysql'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-tcp-response-rule",
			initialConfigFile: "tcp-rules/backend-base.cfg",
			desiredConfigFile: "tcp-rules/backend-with-tcp-response.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create TCP response rule (content) in backend 'mysql'",
			},
			expectedReload: true,
		},

		// ==================== LOG TARGET OPERATIONS ====================
		{
			name:              "frontend-add-log-target",
			initialConfigFile: "log-targets/frontend-base.cfg",
			desiredConfigFile: "log-targets/frontend-with-log.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create log target (127.0.0.1:514) in frontend 'http-in'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-log-target",
			initialConfigFile: "log-targets/backend-base.cfg",
			desiredConfigFile: "log-targets/backend-with-log.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create log target (127.0.0.1:514) in backend 'web'",
			},
			expectedReload: true,
		},

		// ==================== STICK RULE OPERATIONS ====================
		{
			name:              "backend-add-stick-on-rule",
			initialConfigFile: "stick-rules/backend-base.cfg",
			desiredConfigFile: "stick-rules/backend-with-stick-on.cfg",
			expectedCreates:   1,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create stick rule (on) in backend 'web'",
				"Update backend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-stick-match-rule",
			initialConfigFile: "stick-rules/backend-base.cfg",
			desiredConfigFile: "stick-rules/backend-with-stick-match.cfg",
			expectedCreates:   1,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create stick rule (match) in backend 'web'",
				"Update backend 'web'",
			},
			expectedReload: true,
		},

		// ==================== HTTP AFTER RESPONSE RULE OPERATIONS ====================
		{
			name:              "backend-add-http-after-rule",
			initialConfigFile: "http-after-rules/backend-base.cfg",
			desiredConfigFile: "http-after-rules/backend-with-http-after.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create HTTP after response rule (set-header) in backend 'web'",
			},
			expectedReload: true,
		},

		// ==================== SWITCHING RULE OPERATIONS ====================
		{
			name:              "frontend-add-backend-switching-rule",
			initialConfigFile: "backend-switching-rules/frontend-base.cfg",
			desiredConfigFile: "backend-switching-rules/frontend-with-switching.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create backend switching rule (api) in frontend 'http-in'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-server-switching-rule",
			initialConfigFile: "server-switching-rules/backend-base.cfg",
			desiredConfigFile: "server-switching-rules/backend-with-switching.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create server switching rule (srv2) in backend 'web'",
			},
			expectedReload: true,
		},

		// ==================== FILTER OPERATIONS ====================
		{
			name:              "frontend-add-filter",
			initialConfigFile: "filters/frontend-base.cfg",
			desiredConfigFile: "filters/frontend-with-filter.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create filter (compression) in frontend 'http-in'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-filter",
			initialConfigFile: "filters/backend-base.cfg",
			desiredConfigFile: "filters/backend-with-filter.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create filter (compression) in backend 'web'",
			},
			expectedReload: true,
		},

		// ==================== CHECK RULE OPERATIONS ====================
		{
			name:              "backend-add-http-check",
			initialConfigFile: "http-checks/backend-base.cfg",
			desiredConfigFile: "http-checks/backend-with-http-check.cfg",
			expectedCreates:   2,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create HTTP check (send) in backend 'web'",
				"Create HTTP check (expect) in backend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-add-tcp-check",
			initialConfigFile: "tcp-checks/backend-base.cfg",
			desiredConfigFile: "tcp-checks/backend-with-tcp-check.cfg",
			expectedCreates:   2,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create TCP check (connect) in backend 'mysql'",
				"Create TCP check (expect) in backend 'mysql'",
			},
			expectedReload: true,
		},

		// ==================== CAPTURE OPERATIONS ====================
		{
			name:              "frontend-add-request-capture",
			initialConfigFile: "captures/frontend-base.cfg",
			desiredConfigFile: "captures/frontend-with-request-capture.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create capture (request) in frontend 'http-in'",
			},
			expectedReload: true,
		},
		{
			name:              "frontend-add-response-capture",
			initialConfigFile: "captures/frontend-base.cfg",
			desiredConfigFile: "captures/frontend-with-response-capture.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create capture (response) in frontend 'http-in'",
			},
			expectedReload: true,
		},

		// ==================== SERVER TEMPLATE OPERATIONS ====================
		{
			name:              "backend-add-server-template",
			initialConfigFile: "server-templates/backend-base.cfg",
			desiredConfigFile: "server-templates/backend-with-template.cfg",
			expectedCreates:   1,
			expectedUpdates:   0,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Create server template 'web-' in backend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-remove-server-template",
			initialConfigFile: "server-templates/backend-with-template.cfg",
			desiredConfigFile: "server-templates/backend-base.cfg",
			expectedCreates:   0,
			expectedUpdates:   0,
			expectedDeletes:   1,
			expectedOperations: []string{
				"Delete server template 'web-' from backend 'web'",
			},
			expectedReload: true,
		},
		{
			name:              "backend-update-server-template",
			initialConfigFile: "server-templates/backend-with-template.cfg",
			desiredConfigFile: "server-templates/template-num-changed.cfg",
			expectedCreates:   0,
			expectedUpdates:   1,
			expectedDeletes:   0,
			expectedOperations: []string{
				"Update server template 'web-' in backend 'web'",
			},
			expectedReload: true,
		},

		// ==================== HTTP ERRORS SECTION OPERATIONS ====================
		{
			name:              "add-http-errors-section",
			initialConfigFile: "http-errors/base.cfg",
			desiredConfigFile: "http-errors/with-errors.cfg",
			generalFiles: map[string]string{
				"/etc/haproxy/general/400.http": "error-files/400.http",
				"/etc/haproxy/general/403.http": "error-files/403.http",
				"/etc/haproxy/general/500.http": "error-files/500.http",
			},
			expectedCreates: 1,
			expectedUpdates: 0,
			expectedDeletes: 0,
			expectedOperations: []string{
				"Create http-errors section 'myerrors'",
			},
			expectedReload: true,
		},
		{
			name:              "remove-http-errors-section",
			initialConfigFile: "http-errors/with-errors.cfg",
			desiredConfigFile: "http-errors/base.cfg",
			// Initial config needs these files
			initialGeneralFiles: map[string]string{
				"/etc/haproxy/general/400.http": "error-files/400.http",
				"/etc/haproxy/general/403.http": "error-files/403.http",
				"/etc/haproxy/general/500.http": "error-files/500.http",
			},
			// Desired config has no error files (they should be deleted)
			generalFiles:    map[string]string{},
			expectedCreates: 0,
			expectedUpdates: 0,
			expectedDeletes: 1,
			expectedOperations: []string{
				"Delete http-errors section 'myerrors'",
			},
			expectedReload: true,
		},
		{
			name:              "update-http-errors-section",
			initialConfigFile: "http-errors/with-errors.cfg",
			desiredConfigFile: "http-errors/modified-errors.cfg",
			// Initial config needs these files
			initialGeneralFiles: map[string]string{
				"/etc/haproxy/general/400.http": "error-files/400.http",
				"/etc/haproxy/general/403.http": "error-files/403.http",
				"/etc/haproxy/general/500.http": "error-files/500.http",
			},
			// Desired config needs different files
			generalFiles: map[string]string{
				"/etc/haproxy/general/custom400.http": "error-files/custom400.http",
				"/etc/haproxy/general/404.http":       "error-files/404.http",
				"/etc/haproxy/general/503.http":       "error-files/503.http",
			},
			expectedCreates: 0,
			expectedUpdates: 1,
			expectedDeletes: 0,
			expectedOperations: []string{
				"Update http-errors section 'myerrors'",
			},
			expectedReload: true,
		},

		// ==================== SSL FRONTEND OPERATIONS ====================
		{
			name:              "add-ssl-frontend",
			initialConfigFile: "ssl-frontend/base.cfg",
			desiredConfigFile: "ssl-frontend/with-ssl.cfg",
			sslCertificates: map[string]string{
				"example.com.pem": "ssl-certs/example.com.pem",
			},
			expectedCreates: 2,
			expectedUpdates: 0,
			expectedDeletes: 1,
			expectedOperations: []string{
				"Delete frontend 'http'",
				"Create frontend 'https'",
				"Create bind '*:443 ssl crt /etc/haproxy/ssl/example_com.pem' in frontend 'https'",
			},
			expectedReload: true,
		},
		{
			name:              "remove-ssl-frontend",
			initialConfigFile: "ssl-frontend/with-ssl.cfg",
			desiredConfigFile: "ssl-frontend/base.cfg",
			// Initial config needs SSL cert
			initialSSLCertificates: map[string]string{
				"example.com.pem": "ssl-certs/example.com.pem",
			},
			// Desired config has no SSL (cert should be deleted)
			sslCertificates: map[string]string{},
			expectedCreates: 2,
			expectedUpdates: 0,
			expectedDeletes: 1,
			expectedOperations: []string{
				"Delete frontend 'https'",
				"Create frontend 'http'",
				"Create bind '*:80' in frontend 'http'",
			},
			expectedReload: true,
		},
		{
			name:              "update-ssl-frontend-cert",
			initialConfigFile: "ssl-frontend/with-ssl.cfg",
			desiredConfigFile: "ssl-frontend/modified-ssl.cfg",
			// Initial config needs this cert
			initialSSLCertificates: map[string]string{
				"example.com.pem": "ssl-certs/example.com.pem",
			},
			// Desired config needs different cert
			sslCertificates: map[string]string{
				"updated.com.pem": "ssl-certs/updated.com.pem",
			},
			expectedCreates: 0,
			expectedUpdates: 1,
			expectedDeletes: 0,
			expectedOperations: []string{
				"Update bind '*:443 ssl crt /etc/haproxy/ssl/updated_com.pem' in frontend 'https'",
			},
			expectedReload: true,
		},

		// ==================== MAP FILE OPERATIONS ====================
		{
			name:              "add-map-frontend",
			initialConfigFile: "map-frontend/base.cfg",
			desiredConfigFile: "map-frontend/with-map.cfg",
			mapFiles: map[string]string{
				"domains.map": "map-files/domains.map",
			},
			expectedCreates: 1,
			expectedUpdates: 1,
			expectedDeletes: 0,
			expectedOperations: []string{
				"Create backend switching rule (%[req.hdr(host),lower,map(/etc/haproxy/maps/domains.map,web)]) in frontend 'http'",
				"Update frontend 'http'",
			},
			expectedReload: true,
		},
		{
			name:              "remove-map-frontend",
			initialConfigFile: "map-frontend/with-map.cfg",
			desiredConfigFile: "map-frontend/base.cfg",
			// Initial config needs map file
			initialMapFiles: map[string]string{
				"domains.map": "map-files/domains.map",
			},
			// Desired config has no map file (should be deleted)
			mapFiles: map[string]string{},
			expectedCreates: 0,
			expectedUpdates: 1,
			expectedDeletes: 1,
			expectedOperations: []string{
				"Delete backend switching rule (%[req.hdr(host),lower,map(/etc/haproxy/maps/domains.map,web)]) from frontend 'http'",
				"Update frontend 'http'",
			},
			expectedReload: true,
		},
		{
			name:              "update-map-frontend",
			initialConfigFile: "map-frontend/with-map.cfg",
			desiredConfigFile: "map-frontend/modified-map.cfg",
			// Initial config needs this map
			initialMapFiles: map[string]string{
				"domains.map": "map-files/domains.map",
			},
			// Desired config needs different map
			mapFiles: map[string]string{
				"updated-domains.map": "map-files/updated-domains.map",
			},
			expectedCreates: 4,
			expectedUpdates: 0,
			expectedDeletes: 2,
			expectedOperations: []string{
				"Delete backend 'admin'",
				"Delete backend 'api'",
				"Create backend 'api-v2'",
				"Create backend 'mobile'",
				"Create server 'srv1' in backend 'api-v2'",
				"Create server 'srv1' in backend 'mobile'",
			},
			expectedReload: true,
		},

	// ==================== RESOLVERS SECTION OPERATIONS ====================
	{
		name:              "resolvers-add-section",
		initialConfigFile: "resolvers/resolvers-base.cfg",
		desiredConfigFile: "resolvers/resolvers-with-dns.cfg",
		expectedCreates:   1,
		expectedUpdates:   0,
		expectedDeletes:   0,
		expectedOperations: []string{
			"Create resolver 'dns'",
		},
		expectedReload:        true,
		expectedFallbackToRaw: true,
	},
	{
		name:              "resolvers-remove-section",
		initialConfigFile: "resolvers/resolvers-with-dns.cfg",
		desiredConfigFile: "resolvers/resolvers-base.cfg",
		expectedCreates:   0,
		expectedUpdates:   0,
		expectedDeletes:   1,
		expectedOperations: []string{
			"Delete resolver 'dns'",
		},
		expectedReload: true,
	},

	// ==================== MAILERS SECTION OPERATIONS ====================
	{
		name:              "mailers-add-section",
		initialConfigFile: "mailers/mailers-base.cfg",
		desiredConfigFile: "mailers/mailers-with-alerts.cfg",
		expectedCreates:   3,
		expectedUpdates:   0,
		expectedDeletes:   0,
		expectedOperations: []string{
			"Create mailers 'alerts'",
			"Create mailer entry 'smtp1' in mailers section 'alerts'",
			"Create mailer entry 'smtp2' in mailers section 'alerts'",
		},
		expectedReload: true,
	},
	{
		name:              "mailers-remove-section",
		initialConfigFile: "mailers/mailers-with-alerts.cfg",
		desiredConfigFile: "mailers/mailers-base.cfg",
		expectedCreates:   0,
		expectedUpdates:   0,
		expectedDeletes:   1,
		expectedOperations: []string{
			"Delete mailers 'alerts'",
		},
		expectedReload: true,
	},

	// ==================== PEERS SECTION OPERATIONS ====================
	{
		name:              "peers-add-section",
		initialConfigFile: "peers/peers-base.cfg",
		desiredConfigFile: "peers/peers-with-cluster.cfg",
		expectedCreates:   1,
		expectedUpdates:   1,
		expectedDeletes:   0,
		expectedOperations: []string{
			"Create peer section 'mycluster'",
			"Update backend 'web'",
		},
		expectedReload:        true,
		expectedFallbackToRaw: true,
	},
	{
		name:              "peers-remove-section",
		initialConfigFile: "peers/peers-with-cluster.cfg",
		desiredConfigFile: "peers/peers-base.cfg",
		expectedCreates:   0,
		expectedUpdates:   1,
		expectedDeletes:   1,
		expectedOperations: []string{
			"Delete peer section 'mycluster'",
			"Update backend 'web'",
		},
		expectedReload: true,
	},

	// ==================== CACHE SECTION OPERATIONS ====================
	{
		name:              "cache-add-section",
		initialConfigFile: "cache/cache-base.cfg",
		desiredConfigFile: "cache/cache-with-webcache.cfg",
		expectedCreates:   3,
		expectedUpdates:   0,
		expectedDeletes:   0,
		expectedOperations: []string{
			"Create cache 'webcache'",
			"Create HTTP request rule (cache-use) in backend 'web'",
			"Create HTTP response rule (cache-store) in backend 'web'",
		},
		expectedReload: true,
	},
	{
		name:              "cache-remove-section",
		initialConfigFile: "cache/cache-with-webcache.cfg",
		desiredConfigFile: "cache/cache-base.cfg",
		expectedCreates:   0,
		expectedUpdates:   0,
		expectedDeletes:   3,
		expectedOperations: []string{
			"Delete HTTP request rule (cache-use) from backend 'web'",
			"Delete HTTP response rule (cache-store) from backend 'web'",
			"Delete cache 'webcache'",
		},
		expectedReload: true,
	},

	// ==================== RING SECTION OPERATIONS ====================
	{
		name:              "ring-add-section",
		initialConfigFile: "ring/ring-base.cfg",
		desiredConfigFile: "ring/ring-with-myring.cfg",
		expectedCreates:   2,
		expectedUpdates:   0,
		expectedDeletes:   0,
		expectedOperations: []string{
			"Create ring 'myring'",
			"Create log target (ring@myring) in backend 'web'",
		},
		expectedReload: true,
	},
	{
		name:              "ring-remove-section",
		initialConfigFile: "ring/ring-with-myring.cfg",
		desiredConfigFile: "ring/ring-base.cfg",
		expectedCreates:   0,
		expectedUpdates:   0,
		expectedDeletes:   2,
		expectedOperations: []string{
			"Delete log target (ring@myring) from backend 'web'",
			"Delete ring 'myring'",
		},
		expectedReload: true,
	},
	}

	for _, tc := range testCases {
		tc := tc // capture range variable
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			runSyncTest(t, tc)
		})
	}
}

// runSyncTest executes a single sync test case with full validation
func runSyncTest(t *testing.T, tc syncTestCase) {
	// Skip if this tests an unsupported feature (test-first approach)
	if tc.skipReason != "" {
		t.Skip(tc.skipReason)
	}

	env := fixenv.New(t)
	ctx := context.Background()

	// Request fixtures
	client := TestDataplaneClient(env)      // Low-level client for setup/verification
	dpClient := TestDataplaneHighLevelClient(env) // High-level client for Sync API
	parser := TestParser(env)
	comp := TestComparator(env)

	// Step 0.5: Prepare auxiliary files (will be synced by Sync API)
	auxFiles := &dataplane.AuxiliaryFiles{
		GeneralFiles:    make([]auxiliaryfiles.GeneralFile, 0),
		SSLCertificates: make([]auxiliaryfiles.SSLCertificate, 0),
		MapFiles:        make([]auxiliaryfiles.MapFile, 0),
	}

	// Load general files from testdata
	if len(tc.generalFiles) > 0 {
		t.Logf("Preparing %d general files", len(tc.generalFiles))
		for haproxyPath, testdataFile := range tc.generalFiles {
			fullPath := filepath.Join("testdata", testdataFile)
			content, err := os.ReadFile(fullPath)
			require.NoError(t, err, "failed to read test file %s", testdataFile)

			auxFiles.GeneralFiles = append(auxFiles.GeneralFiles, auxiliaryfiles.GeneralFile{
				Filename: filepath.Base(haproxyPath),
				Content:  string(content),
			})
			t.Logf("  - %s ← %s", haproxyPath, testdataFile)
		}
	}

	// Load SSL certificates from testdata
	if len(tc.sslCertificates) > 0 {
		t.Logf("Preparing %d SSL certificates", len(tc.sslCertificates))
		for certName, testdataFile := range tc.sslCertificates {
			fullPath := filepath.Join("testdata", testdataFile)
			content, err := os.ReadFile(fullPath)
			require.NoError(t, err, "failed to read test cert %s", testdataFile)

			auxFiles.SSLCertificates = append(auxFiles.SSLCertificates, auxiliaryfiles.SSLCertificate{
				Path:    certName,
				Content: string(content),
			})
			t.Logf("  - %s ← %s", certName, testdataFile)
		}
	}

	// Load map files from testdata
	if len(tc.mapFiles) > 0 {
		t.Logf("Preparing %d map files", len(tc.mapFiles))
		for mapName, testdataFile := range tc.mapFiles {
			fullPath := filepath.Join("testdata", testdataFile)
			content, err := os.ReadFile(fullPath)
			require.NoError(t, err, "failed to read test map file %s", testdataFile)

			auxFiles.MapFiles = append(auxFiles.MapFiles, auxiliaryfiles.MapFile{
				Path:    mapName,
				Content: string(content),
			})
			t.Logf("  - %s ← %s", mapName, testdataFile)
		}
	}

	// Step 1: Upload INITIAL auxiliary files (if any) before pushing initial config
	// This ensures files exist when HAProxy validates the initial configuration
	if len(tc.initialGeneralFiles) > 0 {
		t.Logf("Uploading %d initial general files", len(tc.initialGeneralFiles))
		for haproxyPath, testdataFile := range tc.initialGeneralFiles {
			fullPath := filepath.Join("testdata", testdataFile)
			content, err := os.ReadFile(fullPath)
			require.NoError(t, err, "failed to read initial test file %s", testdataFile)

			filename := filepath.Base(haproxyPath)
			err = client.CreateGeneralFile(ctx, filename, string(content))
			if err != nil && !strings.Contains(err.Error(), "already exists") {
				require.NoError(t, err, "failed to upload initial general file %s", filename)
			}
			t.Logf("  - Uploaded initial file: %s", filename)
		}
	}

	if len(tc.initialSSLCertificates) > 0 {
		t.Logf("Uploading %d initial SSL certificates", len(tc.initialSSLCertificates))
		for certName, testdataFile := range tc.initialSSLCertificates {
			fullPath := filepath.Join("testdata", testdataFile)
			content, err := os.ReadFile(fullPath)
			require.NoError(t, err, "failed to read initial SSL cert %s", testdataFile)

			err = client.CreateSSLCertificate(ctx, certName, string(content))
			if err != nil && !strings.Contains(err.Error(), "already exists") {
				require.NoError(t, err, "failed to upload initial SSL certificate %s", certName)
			}
			t.Logf("  - Uploaded initial SSL cert: %s", certName)
		}
	}

	if len(tc.initialMapFiles) > 0 {
		t.Logf("Uploading %d initial map files", len(tc.initialMapFiles))
		for mapName, testdataFile := range tc.initialMapFiles {
			fullPath := filepath.Join("testdata", testdataFile)
			content, err := os.ReadFile(fullPath)
			require.NoError(t, err, "failed to read initial map file %s", testdataFile)

			err = client.CreateMapFile(ctx, mapName, string(content))
			if err != nil && !strings.Contains(err.Error(), "already exists") {
				require.NoError(t, err, "failed to upload initial map file %s", mapName)
			}
			t.Logf("  - Uploaded initial map file: %s", mapName)
		}
	}

	// Step 2: Push initial configuration (using low-level client)
	initialConfigContent := LoadTestConfig(t, tc.initialConfigFile)
	_, err := client.PushRawConfiguration(ctx, initialConfigContent)
	require.NoError(t, err, "pushing initial config should succeed")
	t.Logf("Pushed initial config: %s", tc.initialConfigFile)

	// Step 3: Sync to desired configuration using high-level API
	// This replaces the manual parse/compare/apply steps
	desiredConfigContent := LoadTestConfig(t, tc.desiredConfigFile)
	result, err := dpClient.Sync(ctx, desiredConfigContent, auxFiles, nil)
	require.NoError(t, err, "sync should succeed")
	t.Logf("Sync completed: %d operations, reload=%v, reloadID=%s",
		len(result.AppliedOperations), result.ReloadTriggered, result.ReloadID)

	// Step 3: Assert operation counts from sync result
	// Skip operation checks when fallback to raw push is expected, as operations aren't tracked during raw push
	if !tc.expectedFallbackToRaw {
		assert.Equal(t, tc.expectedCreates, result.Details.Creates, "create count mismatch")
		assert.Equal(t, tc.expectedUpdates, result.Details.Updates, "update count mismatch")
		assert.Equal(t, tc.expectedDeletes, result.Details.Deletes, "delete count mismatch")

		// Step 4: Validate operations by their descriptions
		if tc.expectedOperations != nil && len(tc.expectedOperations) > 0 {
			actualOps := make([]string, len(result.AppliedOperations))
			for i, op := range result.AppliedOperations {
				actualOps[i] = op.Description
			}
			assert.ElementsMatch(t, tc.expectedOperations, actualOps,
				"operation descriptions mismatch")
		}
	}

	// Step 5: Validate reload expectations
	if tc.expectedReload {
		assert.True(t, result.ReloadTriggered, "expected reload to be triggered")
		assert.NotEmpty(t, result.ReloadID, "expected reload ID to be set")
	} else {
		assert.False(t, result.ReloadTriggered, "expected no reload")
		assert.Empty(t, result.ReloadID, "expected no reload ID")
	}

	// Step 5.5: Validate fallback to raw push expectation
	if tc.expectedFallbackToRaw {
		assert.True(t, result.FallbackToRaw, "expected fallback to raw config push")
		t.Logf("⚠️  Fallback to raw config push occurred (expected)")
	} else {
		assert.False(t, result.FallbackToRaw, "expected fine-grained sync without fallback")
	}

	// Step 6: Parse desired config for idempotency verification
	desiredConfig, err := parser.ParseFromString(desiredConfigContent)
	require.NoError(t, err, "parsing desired config should succeed")
	t.Logf("Parsed desired config for verification")

	// Step 7: Read final config via API
	finalConfigStr, err := client.GetRawConfiguration(ctx)
	require.NoError(t, err, "reading final config should succeed")

	// Step 8: Parse final config
	finalConfig, err := parser.ParseFromString(finalConfigStr)
	require.NoError(t, err, "parsing final config should succeed")
	t.Logf("Parsed final config from API")

	// Step 9: Calculate verification diff (final → desired)
	verifyDiff, err := comp.Compare(finalConfig, desiredConfig)
	require.NoError(t, err, "verification comparison should succeed")
	t.Logf("Verification diff: %d creates, %d updates, %d deletes",
		verifyDiff.Summary.TotalCreates, verifyDiff.Summary.TotalUpdates, verifyDiff.Summary.TotalDeletes)

	// Step 10: Assert verification diff is EMPTY (idempotency check)
	// If there are differences, log them for debugging
	if verifyDiff.Summary.TotalCreates > 0 || verifyDiff.Summary.TotalUpdates > 0 || verifyDiff.Summary.TotalDeletes > 0 {
		t.Logf("⚠️  Idempotency check detected differences:")
		for _, op := range verifyDiff.Operations {
			opType := "unknown"
			switch op.Type() {
			case 0:
				opType = "CREATE"
			case 1:
				opType = "UPDATE"
			case 2:
				opType = "DELETE"
			}
			t.Logf("  - %s: %s", opType, op.Describe())
		}
	}

	assert.Equal(t, 0, verifyDiff.Summary.TotalCreates,
		"final config should match desired (no creates needed)")
	assert.Equal(t, 0, verifyDiff.Summary.TotalUpdates,
		"final config should match desired (no updates needed)")
	assert.Equal(t, 0, verifyDiff.Summary.TotalDeletes,
		"final config should match desired (no deletes needed)")

	if verifyDiff.Summary.TotalCreates == 0 &&
		verifyDiff.Summary.TotalUpdates == 0 &&
		verifyDiff.Summary.TotalDeletes == 0 {
		t.Logf("✓ Idempotency check passed: final config matches desired config")
	}
}
