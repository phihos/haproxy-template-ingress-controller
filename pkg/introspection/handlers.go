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

package introspection

import (
	"fmt"
	"net/http"
	"strings"
)

// handleIndex serves a list of all registered variables.
//
// GET /debug/vars
//
// Returns JSON array of variable paths:
//
//	{
//	  "paths": ["config", "rendered", "resources/ingresses"],
//	  "count": 3
//	}
func (s *Server) handleIndex(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		WriteError(w, http.StatusMethodNotAllowed, "only GET is allowed")
		return
	}

	paths := s.registry.Paths()

	response := map[string]interface{}{
		"paths": paths,
		"count": len(paths),
	}

	WriteJSON(w, response)
}

// handleAllVars serves all variables as a single JSON object.
//
// GET /debug/vars/all
//
// Returns map of path → value:
//
//	{
//	  "config": {...},
//	  "rendered": {...},
//	  "resources/ingresses": {...}
//	}
//
// Warning: This can return large responses if many variables are registered.
func (s *Server) handleAllVars(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		WriteError(w, http.StatusMethodNotAllowed, "only GET is allowed")
		return
	}

	allVars, err := s.registry.All()
	if err != nil {
		WriteError(w, http.StatusInternalServerError, err.Error())
		return
	}

	WriteJSON(w, allVars)
}

// handleVar serves a specific variable by path, with optional field selection.
//
// GET /debug/vars/{path}
// GET /debug/vars/{path}?field={.jsonpath}
//
// Examples:
//   - GET /debug/vars/config - returns full config variable
//   - GET /debug/vars/config?field={.version} - returns just the version field
//   - GET /debug/vars/resources/ingresses - returns ingresses variable
//
// The path parameter is extracted from the URL path after /debug/vars/.
func (s *Server) handleVar(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		WriteError(w, http.StatusMethodNotAllowed, "only GET is allowed")
		return
	}

	// Extract variable path from URL
	// URL format: /debug/vars/{path}
	path := strings.TrimPrefix(r.URL.Path, "/debug/vars/")
	path = strings.TrimPrefix(path, "vars/") // Also support /debug/vars/vars/{path}

	// Handle special cases
	if path == "" || path == "/" {
		s.handleIndex(w, r)
		return
	}

	if path == "all" {
		s.handleAllVars(w, r)
		return
	}

	// Check for field query parameter
	field := ParseFieldQuery(r)

	// Get variable with optional field selection
	value, err := s.registry.GetWithField(path, field)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			WriteError(w, http.StatusNotFound, err.Error())
		} else {
			WriteError(w, http.StatusInternalServerError, err.Error())
		}
		return
	}

	WriteJSON(w, value)
}

// handleHealth serves a simple health check endpoint.
//
// GET /health
// GET /healthz
//
// Returns:
//
//	{
//	  "status": "ok"
//	}
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		WriteError(w, http.StatusMethodNotAllowed, "only GET is allowed")
		return
	}

	WriteJSON(w, map[string]string{
		"status": "ok",
	})
}

// handleNotFound serves a 404 response for unknown paths.
func (s *Server) handleNotFound(w http.ResponseWriter, r *http.Request) {
	WriteError(w, http.StatusNotFound, fmt.Sprintf("path %q not found", r.URL.Path))
}
