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

	"github.com/haproxytech/client-native/v6/models"

	"haproxy-template-ic/codegen/dataplaneapi"
)

// transform performs generic JSON-based transformation from client-native model to API model.
// Returns nil if input is nil or transformation fails.
func transform[T any](input interface{}) *T {
	if input == nil {
		return nil
	}

	data, err := json.Marshal(input)
	if err != nil {
		// This should rarely happen with valid models
		return nil
	}

	var result T
	if err := json.Unmarshal(data, &result); err != nil {
		// This should rarely happen with compatible JSON
		return nil
	}

	return &result
}

// ToAPIACL converts a client-native models.ACL to dataplaneapi.Acl.
func ToAPIACL(model *models.ACL) *dataplaneapi.Acl {
	return transform[dataplaneapi.Acl](model)
}

// ToAPIBackend converts a client-native models.Backend to dataplaneapi.Backend.
func ToAPIBackend(model *models.Backend) *dataplaneapi.Backend {
	return transform[dataplaneapi.Backend](model)
}

// ToAPIBackendSwitchingRule converts a client-native BackendSwitchingRule to dataplaneapi.BackendSwitchingRule.
func ToAPIBackendSwitchingRule(model *models.BackendSwitchingRule) *dataplaneapi.BackendSwitchingRule {
	return transform[dataplaneapi.BackendSwitchingRule](model)
}

// ToAPIBind converts a client-native models.Bind to dataplaneapi.Bind.
func ToAPIBind(model *models.Bind) *dataplaneapi.Bind {
	return transform[dataplaneapi.Bind](model)
}

// ToAPICache converts a client-native models.Cache to dataplaneapi.Cache.
func ToAPICache(model *models.Cache) *dataplaneapi.Cache {
	return transform[dataplaneapi.Cache](model)
}

// ToAPICapture converts a client-native models.Capture to dataplaneapi.Capture.
func ToAPICapture(model *models.Capture) *dataplaneapi.Capture {
	return transform[dataplaneapi.Capture](model)
}

// ToAPICrtStore converts a client-native models.CrtStore to dataplaneapi.CrtStore.
func ToAPICrtStore(model *models.CrtStore) *dataplaneapi.CrtStore {
	return transform[dataplaneapi.CrtStore](model)
}

// ToAPIDefaults converts a client-native models.Defaults to dataplaneapi.Defaults.
func ToAPIDefaults(model *models.Defaults) *dataplaneapi.Defaults {
	return transform[dataplaneapi.Defaults](model)
}

// ToAPIFCGIApp converts a client-native models.FCGIApp to dataplaneapi.FcgiApp.
func ToAPIFCGIApp(model *models.FCGIApp) *dataplaneapi.FcgiApp {
	return transform[dataplaneapi.FcgiApp](model)
}

// ToAPIFilter converts a client-native models.Filter to dataplaneapi.Filter.
func ToAPIFilter(model *models.Filter) *dataplaneapi.Filter {
	return transform[dataplaneapi.Filter](model)
}

// ToAPIFrontend converts a client-native models.Frontend to dataplaneapi.Frontend.
func ToAPIFrontend(model *models.Frontend) *dataplaneapi.Frontend {
	return transform[dataplaneapi.Frontend](model)
}

// ToAPIGlobal converts a client-native models.Global to dataplaneapi.Global.
func ToAPIGlobal(model *models.Global) *dataplaneapi.Global {
	return transform[dataplaneapi.Global](model)
}

// ToAPIHTTPAfterResponseRule converts a client-native HTTPAfterResponseRule to dataplaneapi.HttpAfterResponseRule.
func ToAPIHTTPAfterResponseRule(model *models.HTTPAfterResponseRule) *dataplaneapi.HttpAfterResponseRule {
	return transform[dataplaneapi.HttpAfterResponseRule](model)
}

// ToAPIHTTPCheck converts a client-native models.HTTPCheck to dataplaneapi.HttpCheck.
func ToAPIHTTPCheck(model *models.HTTPCheck) *dataplaneapi.HttpCheck {
	return transform[dataplaneapi.HttpCheck](model)
}

// ToAPIHTTPErrorRule converts a client-native HTTPErrorRule to dataplaneapi.HttpErrorRule.
func ToAPIHTTPErrorRule(model *models.HTTPErrorRule) *dataplaneapi.HttpErrorRule {
	return transform[dataplaneapi.HttpErrorRule](model)
}

// ToAPIHTTPErrorsSection converts a client-native HTTPErrorsSection to dataplaneapi.HttpErrorsSection.
func ToAPIHTTPErrorsSection(model *models.HTTPErrorsSection) *dataplaneapi.HttpErrorsSection {
	return transform[dataplaneapi.HttpErrorsSection](model)
}

// ToAPIHTTPRequestRule converts a client-native HTTPRequestRule to dataplaneapi.HttpRequestRule.
func ToAPIHTTPRequestRule(model *models.HTTPRequestRule) *dataplaneapi.HttpRequestRule {
	return transform[dataplaneapi.HttpRequestRule](model)
}

// ToAPIHTTPResponseRule converts a client-native HTTPResponseRule to dataplaneapi.HttpResponseRule.
func ToAPIHTTPResponseRule(model *models.HTTPResponseRule) *dataplaneapi.HttpResponseRule {
	return transform[dataplaneapi.HttpResponseRule](model)
}

// ToAPILogForward converts a client-native models.LogForward to dataplaneapi.LogForward.
func ToAPILogForward(model *models.LogForward) *dataplaneapi.LogForward {
	return transform[dataplaneapi.LogForward](model)
}

// ToAPILogTarget converts a client-native models.LogTarget to dataplaneapi.LogTarget.
func ToAPILogTarget(model *models.LogTarget) *dataplaneapi.LogTarget {
	return transform[dataplaneapi.LogTarget](model)
}

// ToAPIMailerEntry converts a client-native models.MailerEntry to dataplaneapi.MailerEntry.
func ToAPIMailerEntry(model *models.MailerEntry) *dataplaneapi.MailerEntry {
	return transform[dataplaneapi.MailerEntry](model)
}

// ToAPIMailersSection converts a client-native MailersSection to dataplaneapi.MailersSection.
func ToAPIMailersSection(model *models.MailersSection) *dataplaneapi.MailersSection {
	return transform[dataplaneapi.MailersSection](model)
}

// ToAPINameserver converts a client-native models.Nameserver to dataplaneapi.Nameserver.
func ToAPINameserver(model *models.Nameserver) *dataplaneapi.Nameserver {
	return transform[dataplaneapi.Nameserver](model)
}

// ToAPIPeerEntry converts a client-native models.PeerEntry to dataplaneapi.PeerEntry.
func ToAPIPeerEntry(model *models.PeerEntry) *dataplaneapi.PeerEntry {
	return transform[dataplaneapi.PeerEntry](model)
}

// ToAPIPeerSection converts a client-native models.PeerSection to dataplaneapi.PeerSection.
func ToAPIPeerSection(model *models.PeerSection) *dataplaneapi.PeerSection {
	return transform[dataplaneapi.PeerSection](model)
}

// ToAPIProgram converts a client-native models.Program to dataplaneapi.Program.
func ToAPIProgram(model *models.Program) *dataplaneapi.Program {
	return transform[dataplaneapi.Program](model)
}

// ToAPIResolver converts a client-native models.Resolver to dataplaneapi.Resolver.
func ToAPIResolver(model *models.Resolver) *dataplaneapi.Resolver {
	return transform[dataplaneapi.Resolver](model)
}

// ToAPIRing converts a client-native models.Ring to dataplaneapi.Ring.
func ToAPIRing(model *models.Ring) *dataplaneapi.Ring {
	return transform[dataplaneapi.Ring](model)
}

// ToAPIServer converts a client-native models.Server to dataplaneapi.Server.
func ToAPIServer(model *models.Server) *dataplaneapi.Server {
	return transform[dataplaneapi.Server](model)
}

// ToAPIServerSwitchingRule converts a client-native ServerSwitchingRule to dataplaneapi.ServerSwitchingRule.
func ToAPIServerSwitchingRule(model *models.ServerSwitchingRule) *dataplaneapi.ServerSwitchingRule {
	return transform[dataplaneapi.ServerSwitchingRule](model)
}

// ToAPIServerTemplate converts a client-native ServerTemplate to dataplaneapi.ServerTemplate.
func ToAPIServerTemplate(model *models.ServerTemplate) *dataplaneapi.ServerTemplate {
	return transform[dataplaneapi.ServerTemplate](model)
}

// ToAPIStickRule converts a client-native models.StickRule to dataplaneapi.StickRule.
func ToAPIStickRule(model *models.StickRule) *dataplaneapi.StickRule {
	return transform[dataplaneapi.StickRule](model)
}

// ToAPITCPCheck converts a client-native models.TCPCheck to dataplaneapi.TcpCheck.
func ToAPITCPCheck(model *models.TCPCheck) *dataplaneapi.TcpCheck {
	return transform[dataplaneapi.TcpCheck](model)
}

// ToAPITCPRequestRule converts a client-native TCPRequestRule to dataplaneapi.TcpRequestRule.
func ToAPITCPRequestRule(model *models.TCPRequestRule) *dataplaneapi.TcpRequestRule {
	return transform[dataplaneapi.TcpRequestRule](model)
}

// ToAPITCPResponseRule converts a client-native TCPResponseRule to dataplaneapi.TcpResponseRule.
func ToAPITCPResponseRule(model *models.TCPResponseRule) *dataplaneapi.TcpResponseRule {
	return transform[dataplaneapi.TcpResponseRule](model)
}

// ToAPIUser converts a client-native models.User to dataplaneapi.User.
func ToAPIUser(model *models.User) *dataplaneapi.User {
	return transform[dataplaneapi.User](model)
}

// ToAPIUserlist converts a client-native models.Userlist to dataplaneapi.Userlist.
func ToAPIUserlist(model *models.Userlist) *dataplaneapi.Userlist {
	return transform[dataplaneapi.Userlist](model)
}
