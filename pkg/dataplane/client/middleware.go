package client

import (
	"bytes"
	"io"
	"log/slog"
	"net/http"
)

// loggingRoundTripper is an HTTP RoundTripper that logs request details when
// the Dataplane API returns a 422 Unprocessable Entity status code.
//
// This helps debug why the API rejects certain requests by capturing:
// - HTTP method (GET, POST, PUT, etc.)
// - Full request URL including query parameters
// - Request body payload
//
// The middleware is transparent for successful requests and only adds logging
// overhead when a 422 error occurs.
type loggingRoundTripper struct {
	base   http.RoundTripper
	logger *slog.Logger
}

// newLoggingRoundTripper creates a new logging middleware that wraps the provided
// base RoundTripper. If base is nil, http.DefaultTransport is used.
func newLoggingRoundTripper(base http.RoundTripper, logger *slog.Logger) *loggingRoundTripper {
	if base == nil {
		base = http.DefaultTransport
	}
	if logger == nil {
		logger = slog.Default()
	}
	return &loggingRoundTripper{
		base:   base,
		logger: logger,
	}
}

// RoundTrip implements the http.RoundTripper interface.
//
// It captures the request body, executes the request, and logs details if
// the response status is 422 Unprocessable Entity.
func (t *loggingRoundTripper) RoundTrip(req *http.Request) (*http.Response, error) {
	// Capture request body for potential logging
	// We need to read the body before the request is sent, then restore it
	var requestBody []byte
	if req.Body != nil {
		var err error
		requestBody, err = io.ReadAll(req.Body)
		if err != nil {
			t.logger.Warn("failed to read request body for logging", "error", err)
		}
		// Restore the body for the actual request
		req.Body = io.NopCloser(bytes.NewBuffer(requestBody))
	}

	// Execute the actual HTTP request
	resp, err := t.base.RoundTrip(req)

	// Check for 422 status and log if found
	if err == nil && resp.StatusCode == 422 {
		// Capture response body for logging
		var responseBody []byte
		if resp.Body != nil {
			responseBody, err = io.ReadAll(resp.Body)
			if err != nil {
				t.logger.Warn("failed to read response body for logging", "error", err)
			}
			// Restore the response body for the caller
			resp.Body = io.NopCloser(bytes.NewBuffer(responseBody))
		}

		t.logger.Error("Dataplane API returned 422 Unprocessable Entity",
			"method", req.Method,
			"url", req.URL.String(),
			"request_body", string(requestBody),
			"response_body", string(responseBody),
			"status_code", resp.StatusCode,
		)
	}

	return resp, err
}
