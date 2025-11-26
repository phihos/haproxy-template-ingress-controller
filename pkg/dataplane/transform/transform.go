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

// Package transform provides transformation functions to convert client-native
// parser models to Dataplane API models.
//
// The client-native library (haproxytech/client-native) provides configuration
// parsing but uses internal model types that don't always match the Dataplane
// API's OpenAPI schema. This package provides conversion functions using JSON
// marshaling/unmarshaling to transform between these representations.
//
// This centralization eliminates ~77 duplicate inline conversions across the
// comparator/sections package.
package transform

import (
	"encoding/json"
	"fmt"
	"log/slog"

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/pkg/generated/dataplaneapi"
)

// transform performs generic JSON-based transformation from client-native model to API model.
// Returns nil if input is nil or transformation fails.
//
// IMPORTANT: Transformation failures are logged at ERROR level with full details to aid debugging.
// Check logs if fine-grained sync falls back to raw config push unexpectedly.
func transform[T any](input interface{}) *T {
	if input == nil {
		return nil
	}

	data, err := json.Marshal(input)
	if err != nil {
		// Log transformation failure with type information
		slog.Error("transform: JSON marshal failed",
			"source_type", fmt.Sprintf("%T", input),
			"error", err,
			"details", "This indicates a bug in the client-native library or incompatible model structure",
		)
		return nil
	}

	var result T
	if err := json.Unmarshal(data, &result); err != nil {
		// Log transformation failure with JSON payload for debugging
		slog.Error("transform: JSON unmarshal failed",
			"source_type", fmt.Sprintf("%T", input),
			"target_type", fmt.Sprintf("%T", result),
			"json_payload", string(data),
			"error", err,
			"details", "This indicates incompatible JSON schemas between client-native and Dataplane API models",
		)
		return nil
	}

	return &result
}

// ToAPIACL converts a client-native models.ACL to dataplaneapi.Acl.
func ToAPIACL(model *models.ACL) *dataplaneapi.Acl {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Acl](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIBackend converts a client-native models.Backend to dataplaneapi.Backend.
//
// Special handling for servers field: Backend contains a map of servers, and each
// server has metadata that needs format conversion. This function transforms the
// backend structure while also converting server metadata from flat to nested format.
func ToAPIBackend(model *models.Backend) *dataplaneapi.Backend {
	if model == nil {
		return nil
	}

	// Preserve original servers
	origServers := model.Servers

	// Temporarily clear servers for base transformation
	model.Servers = nil

	// Transform backend without servers using generic function
	result := transform[dataplaneapi.Backend](model)

	// Restore original servers on input (avoid side effects)
	model.Servers = origServers

	if result == nil {
		return nil
	}

	// Convert servers with metadata transformation
	if len(origServers) > 0 {
		serversMap := make(map[string]dataplaneapi.Server)
		for name := range origServers {
			server := origServers[name]
			// Convert each server's metadata
			apiServer := ToAPIServer(&server)
			if apiServer != nil {
				serversMap[name] = *apiServer
			}
		}
		result.Servers = &serversMap
	}

	return result
}

// ToAPIBackendSwitchingRule converts a client-native BackendSwitchingRule to dataplaneapi.BackendSwitchingRule.
func ToAPIBackendSwitchingRule(model *models.BackendSwitchingRule) *dataplaneapi.BackendSwitchingRule {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.BackendSwitchingRule](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIBind converts a client-native models.Bind to dataplaneapi.Bind.
func ToAPIBind(model *models.Bind) *dataplaneapi.Bind {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Bind](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPICache converts a client-native models.Cache to dataplaneapi.Cache.
func ToAPICache(model *models.Cache) *dataplaneapi.Cache {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Cache](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPICapture converts a client-native models.Capture to dataplaneapi.Capture.
func ToAPICapture(model *models.Capture) *dataplaneapi.Capture {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Capture](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPICrtStore converts a client-native models.CrtStore to dataplaneapi.CrtStore.
func ToAPICrtStore(model *models.CrtStore) *dataplaneapi.CrtStore {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.CrtStore](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIDefaults converts a client-native models.Defaults to dataplaneapi.Defaults.
func ToAPIDefaults(model *models.Defaults) *dataplaneapi.Defaults {
	if model == nil {
		return nil
	}
	return transform[dataplaneapi.Defaults](model)
}

// ToAPIFCGIApp converts a client-native models.FCGIApp to dataplaneapi.FcgiApp.
func ToAPIFCGIApp(model *models.FCGIApp) *dataplaneapi.FcgiApp {
	if model == nil {
		return nil
	}
	return transform[dataplaneapi.FcgiApp](model)
}

// ToAPIFilter converts a client-native models.Filter to dataplaneapi.Filter.
func ToAPIFilter(model *models.Filter) *dataplaneapi.Filter {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Filter](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIFrontend converts a client-native models.Frontend to dataplaneapi.Frontend.
func ToAPIFrontend(model *models.Frontend) *dataplaneapi.Frontend {
	if model == nil {
		return nil
	}
	return transform[dataplaneapi.Frontend](model)
}

// ToAPIGlobal converts a client-native models.Global to dataplaneapi.Global.
func ToAPIGlobal(model *models.Global) *dataplaneapi.Global {
	if model == nil {
		return nil
	}
	return transform[dataplaneapi.Global](model)
}

// ToAPIHTTPAfterResponseRule converts a client-native HTTPAfterResponseRule to dataplaneapi.HttpAfterResponseRule.
func ToAPIHTTPAfterResponseRule(model *models.HTTPAfterResponseRule) *dataplaneapi.HttpAfterResponseRule {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.HttpAfterResponseRule](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIHTTPCheck converts a client-native models.HTTPCheck to dataplaneapi.HttpCheck.
func ToAPIHTTPCheck(model *models.HTTPCheck) *dataplaneapi.HttpCheck {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.HttpCheck](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIHTTPErrorRule converts a client-native HTTPErrorRule to dataplaneapi.HttpErrorRule.
func ToAPIHTTPErrorRule(model *models.HTTPErrorRule) *dataplaneapi.HttpErrorRule {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.HttpErrorRule](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIHTTPErrorsSection converts a client-native HTTPErrorsSection to dataplaneapi.HttpErrorsSection.
func ToAPIHTTPErrorsSection(model *models.HTTPErrorsSection) *dataplaneapi.HttpErrorsSection {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.HttpErrorsSection](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIHTTPRequestRule converts a client-native HTTPRequestRule to dataplaneapi.HttpRequestRule.
func ToAPIHTTPRequestRule(model *models.HTTPRequestRule) *dataplaneapi.HttpRequestRule {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.HttpRequestRule](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIHTTPResponseRule converts a client-native HTTPResponseRule to dataplaneapi.HttpResponseRule.
func ToAPIHTTPResponseRule(model *models.HTTPResponseRule) *dataplaneapi.HttpResponseRule {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.HttpResponseRule](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPILogForward converts a client-native models.LogForward to dataplaneapi.LogForward.
func ToAPILogForward(model *models.LogForward) *dataplaneapi.LogForward {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.LogForward](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPILogTarget converts a client-native models.LogTarget to dataplaneapi.LogTarget.
func ToAPILogTarget(model *models.LogTarget) *dataplaneapi.LogTarget {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.LogTarget](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIMailerEntry converts a client-native models.MailerEntry to dataplaneapi.MailerEntry.
func ToAPIMailerEntry(model *models.MailerEntry) *dataplaneapi.MailerEntry {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.MailerEntry](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIMailersSection converts a client-native MailersSection to dataplaneapi.MailersSection.
func ToAPIMailersSection(model *models.MailersSection) *dataplaneapi.MailersSection {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.MailersSection](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPINameserver converts a client-native models.Nameserver to dataplaneapi.Nameserver.
func ToAPINameserver(model *models.Nameserver) *dataplaneapi.Nameserver {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Nameserver](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIPeerEntry converts a client-native models.PeerEntry to dataplaneapi.PeerEntry.
func ToAPIPeerEntry(model *models.PeerEntry) *dataplaneapi.PeerEntry {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.PeerEntry](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIPeerSection converts a client-native models.PeerSection to dataplaneapi.PeerSection.
func ToAPIPeerSection(model *models.PeerSection) *dataplaneapi.PeerSection {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.PeerSection](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIProgram converts a client-native models.Program to dataplaneapi.Program.
func ToAPIProgram(model *models.Program) *dataplaneapi.Program {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Program](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIResolver converts a client-native models.Resolver to dataplaneapi.Resolver.
func ToAPIResolver(model *models.Resolver) *dataplaneapi.Resolver {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Resolver](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIRing converts a client-native models.Ring to dataplaneapi.Ring.
func ToAPIRing(model *models.Ring) *dataplaneapi.Ring {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Ring](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIServer converts a client-native models.Server to dataplaneapi.Server.
//
// Special handling for metadata field: client-native uses flat map structure
// (map[string]interface{}) while Dataplane API expects nested map structure
// (*map[string]map[string]interface{}). This function converts between formats
// to preserve server comments and metadata throughout the sync process.
func ToAPIServer(model *models.Server) *dataplaneapi.Server {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Server](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIServerSwitchingRule converts a client-native ServerSwitchingRule to dataplaneapi.ServerSwitchingRule.
func ToAPIServerSwitchingRule(model *models.ServerSwitchingRule) *dataplaneapi.ServerSwitchingRule {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.ServerSwitchingRule](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIServerTemplate converts a client-native ServerTemplate to dataplaneapi.ServerTemplate.
func ToAPIServerTemplate(model *models.ServerTemplate) *dataplaneapi.ServerTemplate {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.ServerTemplate](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIStickRule converts a client-native models.StickRule to dataplaneapi.StickRule.
func ToAPIStickRule(model *models.StickRule) *dataplaneapi.StickRule {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.StickRule](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPITCPCheck converts a client-native models.TCPCheck to dataplaneapi.TcpCheck.
func ToAPITCPCheck(model *models.TCPCheck) *dataplaneapi.TcpCheck {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.TcpCheck](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPITCPRequestRule converts a client-native TCPRequestRule to dataplaneapi.TcpRequestRule.
func ToAPITCPRequestRule(model *models.TCPRequestRule) *dataplaneapi.TcpRequestRule {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.TcpRequestRule](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPITCPResponseRule converts a client-native TCPResponseRule to dataplaneapi.TcpResponseRule.
func ToAPITCPResponseRule(model *models.TCPResponseRule) *dataplaneapi.TcpResponseRule {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.TcpResponseRule](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIUser converts a client-native models.User to dataplaneapi.User.
func ToAPIUser(model *models.User) *dataplaneapi.User {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.User](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}

// ToAPIUserlist converts a client-native models.Userlist to dataplaneapi.Userlist.
func ToAPIUserlist(model *models.Userlist) *dataplaneapi.Userlist {
	if model == nil {
		return nil
	}

	// Preserve original metadata
	origMetadata := model.Metadata

	// Temporarily clear metadata for base transformation
	model.Metadata = nil

	// Transform without metadata using generic function
	result := transform[dataplaneapi.Userlist](model)

	// Restore original metadata on input (avoid side effects)
	model.Metadata = origMetadata

	if result == nil {
		return nil
	}

	// Convert metadata from client-native flat format to Dataplane API nested format
	metadata := convertClientMetadataToAPI(origMetadata)
	if len(metadata) > 0 {
		result.Metadata = &metadata
	}

	return result
}
