//go:build integration

package integration

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/stretchr/testify/require"
	"haproxy-template-ic/pkg/dataplane/parser"
)

// LoadTestConfig loads a test HAProxy configuration file.
// The path is relative to the testdata directory.
func LoadTestConfig(t *testing.T, relativePath string) string {
	t.Helper()

	// Get the directory of this source file
	_, filename, _, ok := runtime.Caller(0)
	require.True(t, ok, "failed to get caller information")

	baseDir := filepath.Dir(filename)
	fullPath := filepath.Join(baseDir, "testdata", relativePath)

	content, err := os.ReadFile(fullPath)
	require.NoError(t, err, "failed to read test config file: %s", fullPath)

	return string(content)
}

// ParseTestConfig loads and parses a test configuration file.
func ParseTestConfig(t *testing.T, p *parser.Parser, relativePath string) *parser.StructuredConfig {
	t.Helper()

	configStr := LoadTestConfig(t, relativePath)
	cfg, err := p.ParseFromString(configStr)
	require.NoError(t, err, "failed to parse config from: %s", relativePath)

	return cfg
}
