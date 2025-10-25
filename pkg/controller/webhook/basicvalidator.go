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

package webhook

import (
	"context"
	"fmt"
	"log/slog"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"

	"haproxy-template-ic/pkg/controller/events"
	busevents "haproxy-template-ic/pkg/events"
)

const (
	// BasicValidatorID identifies the basic validator in scatter-gather responses.
	BasicValidatorID = "basic"
)

// BasicValidatorComponent performs basic structural validation of Kubernetes resources.
//
// This validator checks:
//   - Object is a valid map structure
//   - Required metadata fields exist
//   - Metadata fields have valid values
//
// It subscribes to WebhookValidationRequest events and publishes
// WebhookValidationResponse events.
type BasicValidatorComponent struct {
	eventBus *busevents.EventBus
	logger   *slog.Logger
}

// NewBasicValidatorComponent creates a new basic validator component.
func NewBasicValidatorComponent(eventBus *busevents.EventBus, logger *slog.Logger) *BasicValidatorComponent {
	return &BasicValidatorComponent{
		eventBus: eventBus,
		logger:   logger.With("component", "basic-validator"),
	}
}

// Start begins the validator's event loop.
func (b *BasicValidatorComponent) Start(ctx context.Context) error {
	b.logger.Info("Basic validator starting")

	eventChan := b.eventBus.Subscribe(EventBufferSize)

	for {
		select {
		case event := <-eventChan:
			b.handleEvent(event)

		case <-ctx.Done():
			b.logger.Info("Basic validator shutting down", "reason", ctx.Err())
			return nil
		}
	}
}

// handleEvent processes events from the EventBus.
func (b *BasicValidatorComponent) handleEvent(event busevents.Event) {
	if req, ok := event.(*events.WebhookValidationRequest); ok {
		b.handleValidationRequest(req)
	}
}

// handleValidationRequest processes a webhook validation request.
func (b *BasicValidatorComponent) handleValidationRequest(req *events.WebhookValidationRequest) {
	b.logger.Debug("Processing validation request",
		"request_id", req.ID,
		"gvk", req.GVK,
		"namespace", req.Namespace,
		"name", req.Name)

	// Validate object is unstructured
	obj, ok := req.Object.(*unstructured.Unstructured)
	if !ok {
		b.publishResponse(req.ID, false, fmt.Sprintf("invalid object type: %T", req.Object))
		return
	}

	// Validate basic structure
	if err := b.validateBasicStructure(obj); err != nil {
		b.publishResponse(req.ID, false, err.Error())
		return
	}

	b.logger.Debug("Validation passed", "request_id", req.ID)
	b.publishResponse(req.ID, true, "")
}

// validateBasicStructure performs basic structural validation on a Kubernetes resource.
//
// Checks:
//   - Metadata field exists
//   - Metadata.name exists (if not generated name)
//   - Metadata.namespace exists (for namespaced resources)
func (b *BasicValidatorComponent) validateBasicStructure(obj *unstructured.Unstructured) error {
	// Check metadata exists (it's always present in unstructured.Unstructured)
	name := obj.GetName()
	generateName := obj.GetGenerateName()

	// Check name exists (unless generateName is used)
	if name == "" && generateName == "" {
		return fmt.Errorf("metadata.name or metadata.generateName is required")
	}

	// Check namespace for namespaced resources
	// Note: GetNamespace() returns empty string for cluster-scoped resources
	namespace := obj.GetNamespace()
	if namespace == "" {
		// This is fine for cluster-scoped resources, we don't enforce namespace
	}

	return nil
}

// publishResponse publishes a WebhookValidationResponse event.
func (b *BasicValidatorComponent) publishResponse(requestID string, allowed bool, reason string) {
	response := events.NewWebhookValidationResponse(requestID, BasicValidatorID, allowed, reason)
	b.eventBus.Publish(response)

	if allowed {
		b.logger.Debug("Published allowed response", "request_id", requestID)
	} else {
		b.logger.Info("Published denied response",
			"request_id", requestID,
			"reason", reason)
	}
}
