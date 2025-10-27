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

// Package main provides the CLI entrypoint for the HAProxy template ingress controller.
//
// The controller accepts configuration via CLI flags, environment variables, or defaults:
//
//   - ConfigMap name: --configmap-name flag, CONFIGMAP_NAME env var, or "haproxy-config" default
//   - Secret name: --secret-name flag, SECRET_NAME env var, or "haproxy-credentials" default
//   - Webhook cert Secret: --webhook-cert-secret-name flag, WEBHOOK_CERT_SECRET_NAME env var, or "haproxy-webhook-certs" default
//   - Kubeconfig: --kubeconfig flag (for out-of-cluster development)
//
// The controller runs until receiving SIGTERM or SIGINT, at which point it performs
// graceful shutdown.
package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"math"
	"os"
	"os/signal"
	"runtime"
	"runtime/debug"
	"strconv"
	"syscall"

	_ "github.com/KimMachineGun/automemlimit"

	"haproxy-template-ic/pkg/controller"
	"haproxy-template-ic/pkg/k8s/client"
)

const (
	// DefaultCRDName is the default name for the HAProxyTemplateConfig CRD resource.
	DefaultCRDName = "haproxy-config"

	// DefaultSecretName is the default name for the credentials Secret.
	// #nosec G101 -- This is a Kubernetes resource name, not an actual credential
	DefaultSecretName = "haproxy-credentials"

	// DefaultWebhookCertSecretName is the default name for the webhook certificate Secret.
	// #nosec G101 -- This is a Kubernetes resource name, not an actual credential
	DefaultWebhookCertSecretName = "haproxy-webhook-certs"

	// DefaultDebugPort is the default port for the debug HTTP server (0 = disabled).
	DefaultDebugPort = 0
)

func main() {
	// Parse command-line flags
	var (
		crdName               string
		secretName            string
		webhookCertSecretName string
		kubeconfig            string
		debugPort             int
	)

	flag.StringVar(&crdName, "crd-name", "",
		"Name of the HAProxyTemplateConfig CRD containing controller configuration (env: CRD_NAME)")
	flag.StringVar(&secretName, "secret-name", "",
		"Name of the Secret containing HAProxy Dataplane API credentials (env: SECRET_NAME)")
	flag.StringVar(&webhookCertSecretName, "webhook-cert-secret-name", "",
		"Name of the Secret containing webhook TLS certificates (env: WEBHOOK_CERT_SECRET_NAME)")
	flag.StringVar(&kubeconfig, "kubeconfig", "",
		"Path to kubeconfig file (for out-of-cluster development)")
	flag.IntVar(&debugPort, "debug-port", 0,
		"Port for debug HTTP server (0 to disable, env: DEBUG_PORT)")
	flag.Parse()

	// Configuration priority: CLI flags > Environment variables > Defaults

	// CRD name
	if crdName == "" {
		crdName = os.Getenv("CRD_NAME")
	}
	if crdName == "" {
		crdName = DefaultCRDName
	}

	// Secret name
	if secretName == "" {
		secretName = os.Getenv("SECRET_NAME")
	}
	if secretName == "" {
		secretName = DefaultSecretName
	}

	// Webhook certificate Secret name
	if webhookCertSecretName == "" {
		webhookCertSecretName = os.Getenv("WEBHOOK_CERT_SECRET_NAME")
	}
	if webhookCertSecretName == "" {
		webhookCertSecretName = DefaultWebhookCertSecretName
	}

	// Debug port
	if debugPort == 0 {
		if envDebugPort := os.Getenv("DEBUG_PORT"); envDebugPort != "" {
			if port, err := strconv.Atoi(envDebugPort); err == nil {
				debugPort = port
			}
		}
	}
	if debugPort == 0 {
		debugPort = DefaultDebugPort
	}

	// Set up structured logging
	logLevel := slog.LevelInfo

	// Check VERBOSE environment variable for log level
	// 0 = WARNING, 1 = INFO (default), 2 = DEBUG
	switch os.Getenv("VERBOSE") {
	case "0":
		logLevel = slog.LevelWarn
	case "2":
		logLevel = slog.LevelDebug
	}

	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: logLevel,
	}))
	slog.SetDefault(logger)

	// Log detected resource limits for observability
	gomaxprocs := runtime.GOMAXPROCS(0)
	var gomemlimit string
	if limit := debug.SetMemoryLimit(-1); limit != math.MaxInt64 {
		gomemlimit = fmt.Sprintf("%d bytes (%.2f MiB)", limit, float64(limit)/(1024*1024))
	} else {
		gomemlimit = "unlimited"
	}

	logger.Info("HAProxy Template Ingress Controller starting",
		"version", "v0.1.0",
		"crd_name", crdName,
		"secret", secretName,
		"webhook_cert_secret", webhookCertSecretName,
		"debug_port", debugPort,
		"log_level", logLevel.String(),
		"gomaxprocs", gomaxprocs,
		"gomemlimit", gomemlimit)

	// Create Kubernetes client
	k8sClient, err := client.New(client.Config{
		Kubeconfig: kubeconfig,
	})
	if err != nil {
		logger.Error("Failed to create Kubernetes client", "error", err)
		os.Exit(1)
	}

	logger.Info("Kubernetes client created successfully",
		"namespace", k8sClient.Namespace(),
		"in_cluster", kubeconfig == "")

	// Set up signal handling for graceful shutdown
	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer cancel()

	// Run the controller
	if err := controller.Run(ctx, k8sClient, crdName, secretName, webhookCertSecretName, debugPort); err != nil {
		// Only log error if it's not a graceful shutdown
		if ctx.Err() == nil {
			logger.Error("Controller failed", "error", err)
			cancel()
			os.Exit(1) //nolint:gocritic // exitAfterDefer: cancel() called explicitly before exit
		}
	}

	logger.Info("Controller shutdown complete")
}
