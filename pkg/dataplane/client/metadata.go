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

package client

// ConvertClientMetadataToAPI converts client-native flat metadata to Dataplane API nested format.
//
// The client-native library uses a flat map structure for metadata:
//
//	map[string]interface{}{"comment": "Pod: echo-server-v2"}
//
// The Dataplane API expects a nested map structure:
//
//	map[string]map[string]interface{}{"comment": {"value": "Pod: echo-server-v2"}}
//
// This conversion preserves server comments and other metadata throughout the
// fine-grained sync process, ensuring synced config remains close to the original.
func ConvertClientMetadataToAPI(clientMetadata map[string]interface{}) map[string]map[string]interface{} {
	if len(clientMetadata) == 0 {
		return nil
	}

	nested := make(map[string]map[string]interface{})
	for key, value := range clientMetadata {
		nested[key] = map[string]interface{}{
			"value": value,
		}
	}

	return nested
}

// ConvertAPIMetadataToClient converts Dataplane API nested metadata to client-native flat format.
//
// This is the reverse operation of ConvertClientMetadataToAPI, used when reading
// configurations from the Dataplane API and converting them back to client-native models.
//
// Dataplane API format:
//
//	map[string]map[string]interface{}{"comment": {"value": "Pod: echo-server-v2"}}
//
// Converts to client-native format:
//
//	map[string]interface{}{"comment": "Pod: echo-server-v2"}
func ConvertAPIMetadataToClient(apiMetadata map[string]map[string]interface{}) map[string]interface{} {
	if len(apiMetadata) == 0 {
		return nil
	}

	flat := make(map[string]interface{})
	for key, nested := range apiMetadata {
		if value, ok := nested["value"]; ok {
			flat[key] = value
		}
	}

	return flat
}
