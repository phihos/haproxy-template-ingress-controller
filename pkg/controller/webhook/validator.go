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
	"time"

	"haproxy-template-ic/pkg/controller/events"
	busevents "haproxy-template-ic/pkg/events"
	"haproxy-template-ic/pkg/webhook"
)

// createResourceValidator creates a ValidationFunc for a specific GVK.
//
// This validator uses the scatter-gather pattern to coordinate multiple
// validators (BasicValidator, DryRunValidator) via the EventBus.
//
// All validators must allow for the resource to be admitted (AND logic).
func (c *Component) createResourceValidator(gvk string) webhook.ValidationFunc {
	return func(valCtx *webhook.ValidationContext) (bool, string, error) {
		start := time.Now()

		c.logger.Debug("Validating resource",
			"gvk", gvk,
			"operation", valCtx.Operation,
			"namespace", valCtx.Namespace,
			"name", valCtx.Name)

		// Create validation request with actual operation from context
		req := events.NewWebhookValidationRequest(
			gvk,
			valCtx.Namespace,
			valCtx.Name,
			valCtx.Object,
			valCtx.Operation,
		)

		// Use scatter-gather to collect validation results from all validators
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		result, err := c.eventBus.Request(ctx, req, busevents.RequestOptions{
			Timeout:            5 * time.Second,
			ExpectedResponders: []string{"basic", "dryrun"},
		})

		// Handle timeout or error
		if err != nil {
			c.logger.Error("Validation request failed",
				"gvk", gvk,
				"operation", valCtx.Operation,
				"namespace", valCtx.Namespace,
				"name", valCtx.Name,
				"error", err)

			duration := time.Since(start).Seconds()
			if c.metrics != nil {
				c.metrics.RecordWebhookRequest(gvk, "error", duration)
				c.metrics.RecordWebhookValidation(gvk, "error")
			}

			return false, "validation timeout or internal error", nil
		}

		// Aggregate responses: ALL must allow for overall allow
		allowed, reason := c.aggregateResponses(result.Responses)

		// Record metrics
		duration := time.Since(start).Seconds()
		if c.metrics != nil {
			resultStr := "allowed"
			if !allowed {
				resultStr = "denied"
			}
			c.metrics.RecordWebhookRequest(gvk, resultStr, duration)
			c.metrics.RecordWebhookValidation(gvk, resultStr)
		}

		c.logger.Info("Validation completed",
			"gvk", gvk,
			"operation", valCtx.Operation,
			"namespace", valCtx.Namespace,
			"name", valCtx.Name,
			"allowed", allowed,
			"reason", reason,
			"duration_ms", time.Since(start).Milliseconds())

		return allowed, reason, nil
	}
}

// aggregateResponses combines validation responses using AND logic.
//
// ANY deny = overall deny, ALL allow = overall allow.
//
// Returns:
//   - allowed: true if all validators allowed
//   - reason: combined denial reasons from all denying validators
func (c *Component) aggregateResponses(responses []busevents.Response) (bool, string) {
	var denialReasons []string

	for _, resp := range responses {
		if valResp, ok := resp.(*events.WebhookValidationResponse); ok {
			if !valResp.Allowed {
				// Validator denied - collect reason
				denialReasons = append(denialReasons, fmt.Sprintf("%s: %s", valResp.ValidatorID, valResp.Reason))
			}
		}
	}

	// If any validator denied, return denied with combined reasons
	if len(denialReasons) > 0 {
		return false, fmt.Sprintf("validation failed: %v", denialReasons)
	}

	// All validators allowed
	return true, ""
}
