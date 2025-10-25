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

package sections

import (
	"context"
	"fmt"
	"net/http"

	"haproxy-template-ic/pkg/dataplane/client"
)

// NamedModel is an interface for models that have a Name field.
type NamedModel interface {
	GetName() string
}

// executeCreateHelper provides a common execution pattern for create operations.
// It handles: validation, transformation, API call with transaction/version, response checking.
func executeCreateHelper[TModel any, TAPIModel any](
	ctx context.Context,
	transactionID string,
	model *TModel,
	getName func(*TModel) string,
	transformFunc func(*TModel) *TAPIModel,
	createAPICall func(context.Context, *TAPIModel, string) (*http.Response, error),
	resourceType string,
) error {
	// Validation
	if model == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}
	name := getName(model)
	if name == "" {
		return fmt.Errorf("%s name is empty", resourceType)
	}

	// Transform
	apiModel := transformFunc(model)
	if apiModel == nil {
		return fmt.Errorf("failed to transform %s", resourceType)
	}

	// Execute API call
	resp, err := createAPICall(ctx, apiModel, transactionID)
	if err != nil {
		return fmt.Errorf("failed to create %s '%s': %w", resourceType, name, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s creation failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}

// executeCreateTransactionOnlyHelper provides execution pattern for transaction-only creates.
// Used for resources that don't support runtime API (e.g., backend, defaults, frontend).
func executeCreateTransactionOnlyHelper[TModel any, TAPIModel any, TParams any](
	ctx context.Context,
	transactionID string,
	model *TModel,
	getName func(*TModel) string,
	transformFunc func(*TModel) *TAPIModel,
	paramsConstructor func(string) TParams,
	apiCall func(context.Context, TParams, TAPIModel) (*http.Response, error),
	resourceType string,
) error {
	// Validation
	if model == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}
	name := getName(model)
	if name == "" {
		return fmt.Errorf("%s name is empty", resourceType)
	}

	// Transform
	apiModel := transformFunc(model)
	if apiModel == nil {
		return fmt.Errorf("failed to transform %s", resourceType)
	}

	// Prepare parameters with transaction ID
	params := paramsConstructor(transactionID)

	// Execute API call
	resp, err := apiCall(ctx, params, *apiModel)
	if err != nil {
		return fmt.Errorf("failed to create %s '%s': %w", resourceType, name, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s creation failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}

// executeUpdateHelper provides a common execution pattern for update operations.
func executeUpdateHelper[TModel any, TAPIModel any](
	ctx context.Context,
	transactionID string,
	model *TModel,
	getName func(*TModel) string,
	transformFunc func(*TModel) *TAPIModel,
	updateAPICall func(context.Context, string, *TAPIModel, string) (*http.Response, error),
	resourceType string,
) error {
	// Validation
	if model == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}
	name := getName(model)
	if name == "" {
		return fmt.Errorf("%s name is empty", resourceType)
	}

	// Transform
	apiModel := transformFunc(model)
	if apiModel == nil {
		return fmt.Errorf("failed to transform %s", resourceType)
	}

	// Execute API call
	resp, err := updateAPICall(ctx, name, apiModel, transactionID)
	if err != nil {
		return fmt.Errorf("failed to update %s '%s': %w", resourceType, name, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s update failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}

// executeUpdateTransactionOnlyHelper provides execution pattern for transaction-only updates.
// Used for resources that don't support runtime API (e.g., backend, defaults, frontend).
func executeUpdateTransactionOnlyHelper[TModel any, TAPIModel any, TParams any](
	ctx context.Context,
	transactionID string,
	model *TModel,
	getName func(*TModel) string,
	transformFunc func(*TModel) *TAPIModel,
	paramsConstructor func(string) TParams,
	apiCall func(context.Context, string, TParams, TAPIModel) (*http.Response, error),
	resourceType string,
) error {
	// Validation
	if model == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}
	name := getName(model)
	if name == "" {
		return fmt.Errorf("%s name is empty", resourceType)
	}

	// Transform
	apiModel := transformFunc(model)
	if apiModel == nil {
		return fmt.Errorf("failed to transform %s", resourceType)
	}

	// Prepare parameters with transaction ID
	params := paramsConstructor(transactionID)

	// Execute API call
	resp, err := apiCall(ctx, name, params, *apiModel)
	if err != nil {
		return fmt.Errorf("failed to update %s '%s': %w", resourceType, name, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s update failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}

// executeDeleteHelper provides a common execution pattern for delete operations.
func executeDeleteHelper[TModel any](
	ctx context.Context,
	transactionID string,
	model *TModel,
	getName func(*TModel) string,
	deleteAPICall func(context.Context, string, string) (*http.Response, error),
	resourceType string,
) error {
	// Validation
	if model == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}
	name := getName(model)
	if name == "" {
		return fmt.Errorf("%s name is empty", resourceType)
	}

	// Execute API call
	resp, err := deleteAPICall(ctx, name, transactionID)
	if err != nil {
		return fmt.Errorf("failed to delete %s '%s': %w", resourceType, name, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s deletion failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}

// executeDeleteTransactionOnlyHelper provides execution pattern for transaction-only deletes.
// Used for resources that don't support runtime API (e.g., backend, defaults, frontend).
func executeDeleteTransactionOnlyHelper[TModel any, TParams any](
	ctx context.Context,
	transactionID string,
	model *TModel,
	getName func(*TModel) string,
	paramsConstructor func(string) TParams,
	apiCall func(context.Context, string, TParams) (*http.Response, error),
	resourceType string,
) error {
	// Validation
	if model == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}
	name := getName(model)
	if name == "" {
		return fmt.Errorf("%s name is empty", resourceType)
	}

	// Prepare parameters with transaction ID
	params := paramsConstructor(transactionID)

	// Execute API call
	resp, err := apiCall(ctx, name, params)
	if err != nil {
		return fmt.Errorf("failed to delete %s '%s': %w", resourceType, name, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s deletion failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}

// wrapAPICallWithVersionOrTransaction wraps an API call to use either transaction ID or version.
func wrapAPICallWithVersionOrTransaction[TParams any](
	ctx context.Context,
	c *client.DataplaneClient,
	transactionID string,
	paramsConstructor func() TParams,
	setTransactionID func(TParams, *string),
	setVersion func(TParams, *int),
	apiCall func(context.Context, TParams) (*http.Response, error),
) (*http.Response, error) {
	params := paramsConstructor()

	if transactionID != "" {
		setTransactionID(params, &transactionID)
		return apiCall(ctx, params)
	}

	v, err := c.GetVersion(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get version: %w", err)
	}
	version := int(v)
	setVersion(params, &version)
	return apiCall(ctx, params)
}

// executeCreateChildHelper provides execution pattern for creating child resources.
// Child resources belong to a parent section and support both transaction and runtime API.
func executeCreateChildHelper[TModel any, TAPIModel any, TParams any](
	ctx context.Context,
	c *client.DataplaneClient,
	transactionID string,
	model *TModel,
	parentName string,
	getName func(*TModel) string,
	transformFunc func(*TModel) *TAPIModel,
	paramsConstructor func(string) TParams,
	setTransactionID func(TParams, *string),
	setVersion func(TParams, *int),
	apiCall func(context.Context, TParams, TAPIModel) (*http.Response, error),
	resourceType string,
	parentType string,
) error {
	// Validation
	if model == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}
	name := getName(model)
	if name == "" {
		return fmt.Errorf("%s name is empty", resourceType)
	}
	if parentName == "" {
		return fmt.Errorf("%s name is empty", parentType)
	}

	// Transform
	apiModel := transformFunc(model)
	if apiModel == nil {
		return fmt.Errorf("failed to transform %s", resourceType)
	}

	// Prepare parameters
	params := paramsConstructor(parentName)

	// Execute API call
	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path
		setTransactionID(params, &transactionID)
		resp, err = apiCall(ctx, params, *apiModel)
	} else {
		// Runtime API path with version retry
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			setVersion(params, &version)
			return apiCall(ctx, params, *apiModel)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to create %s '%s' in %s '%s': %w", resourceType, name, parentType, parentName, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s creation failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}

// executeDeleteChildHelper provides execution pattern for deleting child resources.
func executeDeleteChildHelper[TModel any, TParams any](
	ctx context.Context,
	c *client.DataplaneClient,
	transactionID string,
	model *TModel,
	parentName string,
	getName func(*TModel) string,
	paramsConstructor func(string) TParams,
	setTransactionID func(TParams, *string),
	setVersion func(TParams, *int),
	apiCall func(context.Context, string, TParams) (*http.Response, error),
	resourceType string,
	parentType string,
) error {
	// Validation
	if model == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}
	name := getName(model)
	if name == "" {
		return fmt.Errorf("%s name is empty", resourceType)
	}
	if parentName == "" {
		return fmt.Errorf("%s name is empty", parentType)
	}

	// Prepare parameters
	params := paramsConstructor(parentName)

	// Execute API call
	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path
		setTransactionID(params, &transactionID)
		resp, err = apiCall(ctx, name, params)
	} else {
		// Runtime API path with version retry
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			setVersion(params, &version)
			return apiCall(ctx, name, params)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to delete %s '%s' from %s '%s': %w", resourceType, name, parentType, parentName, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s deletion failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}

// executeReplaceChildHelper provides execution pattern for replacing/updating child resources.
func executeReplaceChildHelper[TModel any, TAPIModel any, TParams any](
	ctx context.Context,
	c *client.DataplaneClient,
	transactionID string,
	model *TModel,
	parentName string,
	getName func(*TModel) string,
	transformFunc func(*TModel) *TAPIModel,
	paramsConstructor func(string) TParams,
	setTransactionID func(TParams, *string),
	setVersion func(TParams, *int),
	apiCall func(context.Context, string, TParams, TAPIModel) (*http.Response, error),
	resourceType string,
	parentType string,
) error {
	// Validation
	if model == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}
	name := getName(model)
	if name == "" {
		return fmt.Errorf("%s name is empty", resourceType)
	}
	if parentName == "" {
		return fmt.Errorf("%s name is empty", parentType)
	}

	// Transform
	apiModel := transformFunc(model)
	if apiModel == nil {
		return fmt.Errorf("failed to transform %s", resourceType)
	}

	// Prepare parameters
	params := paramsConstructor(parentName)

	// Execute API call
	var resp *http.Response
	var err error

	if transactionID != "" {
		// Transaction path
		setTransactionID(params, &transactionID)
		resp, err = apiCall(ctx, name, params, *apiModel)
	} else {
		// Runtime API path with version retry
		resp, err = client.ExecuteWithVersion(ctx, c, func(ctx context.Context, version int) (*http.Response, error) {
			setVersion(params, &version)
			return apiCall(ctx, name, params, *apiModel)
		})
	}

	if err != nil {
		return fmt.Errorf("failed to replace %s '%s' in %s '%s': %w", resourceType, name, parentType, parentName, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s replacement failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}

// executeModifyIndexedRuleHelper provides execution pattern for creating/updating indexed rules (transaction-only).
// Used for rules that are indexed (e.g., stick rules, TCP checks, HTTP rules).
func executeModifyIndexedRuleHelper[TModel any, TAPIModel any, TParams any](
	ctx context.Context,
	transactionID string,
	rule *TModel,
	parentName string,
	index int,
	transformFunc func(*TModel) *TAPIModel,
	paramsConstructor func(string) TParams,
	apiCall func(context.Context, string, int, TParams, TAPIModel) (*http.Response, error),
	resourceType string,
	parentType string,
	operationVerb string,
) error {
	// Validation
	if rule == nil {
		return fmt.Errorf("%s is nil", resourceType)
	}

	// Transform
	apiModel := transformFunc(rule)
	if apiModel == nil {
		return fmt.Errorf("failed to transform %s", resourceType)
	}

	// Prepare parameters with transaction ID
	params := paramsConstructor(transactionID)

	// Execute API call
	resp, err := apiCall(ctx, parentName, index, params, *apiModel)
	if err != nil {
		return fmt.Errorf("failed to %s %s in %s '%s': %w", operationVerb, resourceType, parentType, parentName, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s %s failed with status %d", resourceType, operationVerb, resp.StatusCode)
	}

	return nil
}

// executeCreateIndexedRuleHelper provides execution pattern for creating indexed rules (transaction-only).
func executeCreateIndexedRuleHelper[TModel any, TAPIModel any, TParams any](
	ctx context.Context,
	transactionID string,
	rule *TModel,
	parentName string,
	index int,
	transformFunc func(*TModel) *TAPIModel,
	paramsConstructor func(string) TParams,
	apiCall func(context.Context, string, int, TParams, TAPIModel) (*http.Response, error),
	resourceType string,
	parentType string,
) error {
	return executeModifyIndexedRuleHelper(ctx, transactionID, rule, parentName, index, transformFunc, paramsConstructor, apiCall, resourceType, parentType, "create")
}

// executeReplaceIndexedRuleHelper provides execution pattern for replacing/updating indexed rules (transaction-only).
func executeReplaceIndexedRuleHelper[TModel any, TAPIModel any, TParams any](
	ctx context.Context,
	transactionID string,
	rule *TModel,
	parentName string,
	index int,
	transformFunc func(*TModel) *TAPIModel,
	paramsConstructor func(string) TParams,
	apiCall func(context.Context, string, int, TParams, TAPIModel) (*http.Response, error),
	resourceType string,
	parentType string,
) error {
	return executeModifyIndexedRuleHelper(ctx, transactionID, rule, parentName, index, transformFunc, paramsConstructor, apiCall, resourceType, parentType, "update")
}

// executeDeleteIndexedRuleHelper provides execution pattern for deleting indexed rules (transaction-only).
func executeDeleteIndexedRuleHelper[TParams any](
	ctx context.Context,
	transactionID string,
	parentName string,
	index int,
	paramsConstructor func(string) TParams,
	apiCall func(context.Context, string, int, TParams) (*http.Response, error),
	resourceType string,
	parentType string,
) error {
	// Prepare parameters with transaction ID
	params := paramsConstructor(transactionID)

	// Execute API call
	resp, err := apiCall(ctx, parentName, index, params)
	if err != nil {
		return fmt.Errorf("failed to delete %s from %s '%s': %w", resourceType, parentType, parentName, err)
	}
	defer resp.Body.Close()

	// Check response
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s deletion failed with status %d", resourceType, resp.StatusCode)
	}

	return nil
}
