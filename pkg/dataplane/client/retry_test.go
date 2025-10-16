package client

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestWithRetry_Success(t *testing.T) {
	config := RetryConfig{
		MaxAttempts: 3,
		RetryIf:     IsVersionConflict(),
	}

	attempts := 0
	result, err := WithRetry(context.Background(), config, func(attempt int) (string, error) {
		attempts++
		return "success", nil
	})

	require.NoError(t, err)
	assert.Equal(t, "success", result)
	assert.Equal(t, 1, attempts, "should succeed on first attempt")
}

func TestWithRetry_NoRetryOnNonMatchingError(t *testing.T) {
	config := RetryConfig{
		MaxAttempts: 3,
		RetryIf:     IsVersionConflict(),
	}

	attempts := 0
	result, err := WithRetry(context.Background(), config, func(attempt int) (string, error) {
		attempts++
		return "", errors.New("some other error")
	})

	require.Error(t, err)
	assert.Equal(t, "", result)
	assert.Equal(t, 1, attempts, "should not retry on non-matching error")
	assert.Equal(t, "some other error", err.Error())
}

func TestWithRetry_RetriesOnVersionConflict(t *testing.T) {
	config := RetryConfig{
		MaxAttempts: 3,
		RetryIf:     IsVersionConflict(),
		Backoff:     BackoffNone,
	}

	attempts := 0
	result, err := WithRetry(context.Background(), config, func(attempt int) (string, error) {
		attempts++
		if attempt < 3 {
			return "", &VersionConflictError{
				ExpectedVersion: 1,
				ActualVersion:   "2",
			}
		}
		return "success", nil
	})

	require.NoError(t, err)
	assert.Equal(t, "success", result)
	assert.Equal(t, 3, attempts, "should retry twice before succeeding")
}

func TestWithRetry_ExhaustsMaxAttempts(t *testing.T) {
	config := RetryConfig{
		MaxAttempts: 3,
		RetryIf:     IsVersionConflict(),
		Backoff:     BackoffNone,
	}

	attempts := 0
	result, err := WithRetry(context.Background(), config, func(attempt int) (string, error) {
		attempts++
		return "", &VersionConflictError{
			ExpectedVersion: 1,
			ActualVersion:   "2",
		}
	})

	require.Error(t, err)
	assert.Equal(t, "", result)
	assert.Equal(t, 3, attempts, "should exhaust all attempts")
	var vce *VersionConflictError
	assert.True(t, errors.As(err, &vce), "should return version conflict error")
}

func TestWithRetry_ContextCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	config := RetryConfig{
		MaxAttempts: 3,
		RetryIf:     IsVersionConflict(),
	}

	attempts := 0
	result, err := WithRetry(ctx, config, func(attempt int) (string, error) {
		attempts++
		return "", &VersionConflictError{
			ExpectedVersion: 1,
			ActualVersion:   "2",
		}
	})

	require.Error(t, err)
	assert.Equal(t, "", result)
	assert.Equal(t, 0, attempts, "should not execute when context is cancelled")
	assert.ErrorIs(t, err, context.Canceled)
}

func TestWithRetry_BackoffLinear(t *testing.T) {
	config := RetryConfig{
		MaxAttempts: 3,
		RetryIf:     IsVersionConflict(),
		Backoff:     BackoffLinear,
		BaseDelay:   50 * time.Millisecond,
	}

	start := time.Now()
	attempts := 0
	_, _ = WithRetry(context.Background(), config, func(attempt int) (string, error) {
		attempts++
		return "", &VersionConflictError{
			ExpectedVersion: 1,
			ActualVersion:   "2",
		}
	})
	elapsed := time.Since(start)

	assert.Equal(t, 3, attempts)
	// Should have 2 delays of 50ms each (between attempts 1-2 and 2-3)
	assert.GreaterOrEqual(t, elapsed, 100*time.Millisecond, "should apply linear backoff")
}

func TestWithRetry_BackoffExponential(t *testing.T) {
	config := RetryConfig{
		MaxAttempts: 4,
		RetryIf:     IsVersionConflict(),
		Backoff:     BackoffExponential,
		BaseDelay:   50 * time.Millisecond,
	}

	start := time.Now()
	attempts := 0
	_, _ = WithRetry(context.Background(), config, func(attempt int) (string, error) {
		attempts++
		return "", &VersionConflictError{
			ExpectedVersion: 1,
			ActualVersion:   "2",
		}
	})
	elapsed := time.Since(start)

	assert.Equal(t, 4, attempts)
	// Exponential backoff: 50ms + 100ms + 200ms = 350ms
	assert.GreaterOrEqual(t, elapsed, 350*time.Millisecond, "should apply exponential backoff")
}

func TestWithRetry_NoRetryIfNil(t *testing.T) {
	config := RetryConfig{
		MaxAttempts: 3,
		RetryIf:     nil, // No retry condition
	}

	attempts := 0
	result, err := WithRetry(context.Background(), config, func(attempt int) (string, error) {
		attempts++
		return "", &VersionConflictError{
			ExpectedVersion: 1,
			ActualVersion:   "2",
		}
	})

	require.Error(t, err)
	assert.Equal(t, "", result)
	assert.Equal(t, 1, attempts, "should not retry when RetryIf is nil")
}

func TestWithRetry_MaxAttemptsValidation(t *testing.T) {
	config := RetryConfig{
		MaxAttempts: 0, // Invalid
		RetryIf:     IsVersionConflict(),
	}

	attempts := 0
	result, err := WithRetry(context.Background(), config, func(attempt int) (string, error) {
		attempts++
		return "success", nil
	})

	require.NoError(t, err)
	assert.Equal(t, "success", result)
	assert.Equal(t, 1, attempts, "should default to 1 attempt when MaxAttempts is invalid")
}

func TestCalculateBackoff(t *testing.T) {
	baseDelay := 100 * time.Millisecond

	tests := []struct {
		strategy BackoffStrategy
		attempt  int
		expected time.Duration
	}{
		{BackoffNone, 1, 0},
		{BackoffNone, 2, 0},
		{BackoffLinear, 1, 100 * time.Millisecond},
		{BackoffLinear, 2, 100 * time.Millisecond},
		{BackoffLinear, 3, 100 * time.Millisecond},
		{BackoffExponential, 1, 100 * time.Millisecond},
		{BackoffExponential, 2, 200 * time.Millisecond},
		{BackoffExponential, 3, 400 * time.Millisecond},
		{BackoffExponential, 4, 800 * time.Millisecond},
	}

	for _, tc := range tests {
		t.Run(string(tc.strategy), func(t *testing.T) {
			actual := calculateBackoff(tc.strategy, baseDelay, tc.attempt)
			assert.Equal(t, tc.expected, actual)
		})
	}
}

func TestIsVersionConflict(t *testing.T) {
	condition := IsVersionConflict()

	tests := []struct {
		name     string
		err      error
		expected bool
	}{
		{
			name: "version conflict error",
			err: &VersionConflictError{
				ExpectedVersion: 1,
				ActualVersion:   "2",
			},
			expected: true,
		},
		{
			name:     "other error",
			err:      errors.New("some error"),
			expected: false,
		},
		{
			name:     "wrapped version conflict",
			err:      errors.New("wrapped: " + (&VersionConflictError{ExpectedVersion: 1, ActualVersion: "2"}).Error()),
			expected: false, // errors.As doesn't work with string wrapping
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			assert.Equal(t, tc.expected, condition(tc.err))
		})
	}
}
