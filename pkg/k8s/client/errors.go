package client

import "fmt"

// ClientError represents errors that occur during Kubernetes client operations.
type ClientError struct {
	Operation string
	Err       error
}

func (e *ClientError) Error() string {
	return fmt.Sprintf("k8s client error during %s: %v", e.Operation, e.Err)
}

func (e *ClientError) Unwrap() error {
	return e.Err
}

// NamespaceDiscoveryError represents errors that occur during namespace discovery.
type NamespaceDiscoveryError struct {
	Path string
	Err  error
}

func (e *NamespaceDiscoveryError) Error() string {
	return fmt.Sprintf("failed to discover namespace from %s: %v", e.Path, e.Err)
}

func (e *NamespaceDiscoveryError) Unwrap() error {
	return e.Err
}
