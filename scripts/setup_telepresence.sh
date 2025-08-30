#!/bin/bash
set -e

echo "Setting up Telepresence for testing..."

# Set kubeconfig
export KUBECONFIG="$(pwd)/.pytest-kind/haproxy-template-ic-test/kubeconfig"

# Verify cluster is accessible
echo "Verifying cluster access..."
kubectl cluster-info

# Clean up any existing Telepresence state
echo "Cleaning up existing Telepresence state..."
telepresence quit 2>/dev/null || true
telepresence uninstall --everything 2>/dev/null || true
sleep 2

# Try to connect
echo "Attempting to connect Telepresence..."
telepresence connect

# Check status
echo "Telepresence status:"
telepresence status

echo "Setup complete!"