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

// Note: Basic structure validation is now tested in basicvalidator_test.go
//
// The webhook validator coordinator (createResourceValidator) is tested via integration_test.go
// because it requires a full EventBus with subscribers (BasicValidator, DryRunValidator)
// to function properly. Unit testing it in isolation is not meaningful.
