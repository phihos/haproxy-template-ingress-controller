# haproxy_dataplane_v3.BackendSwitchingRuleApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_backend_switching_rule**](BackendSwitchingRuleApi.md#create_backend_switching_rule) | **POST** /services/haproxy/configuration/frontends/{parent_name}/backend_switching_rules/{index} | Add a new Backend Switching Rule
[**delete_backend_switching_rule**](BackendSwitchingRuleApi.md#delete_backend_switching_rule) | **DELETE** /services/haproxy/configuration/frontends/{parent_name}/backend_switching_rules/{index} | Delete a Backend Switching Rule
[**get_backend_switching_rule**](BackendSwitchingRuleApi.md#get_backend_switching_rule) | **GET** /services/haproxy/configuration/frontends/{parent_name}/backend_switching_rules/{index} | Return one Backend Switching Rule
[**get_backend_switching_rules**](BackendSwitchingRuleApi.md#get_backend_switching_rules) | **GET** /services/haproxy/configuration/frontends/{parent_name}/backend_switching_rules | Return an array of all Backend Switching Rules
[**replace_backend_switching_rule**](BackendSwitchingRuleApi.md#replace_backend_switching_rule) | **PUT** /services/haproxy/configuration/frontends/{parent_name}/backend_switching_rules/{index} | Replace a Backend Switching Rule
[**replace_backend_switching_rules**](BackendSwitchingRuleApi.md#replace_backend_switching_rules) | **PUT** /services/haproxy/configuration/frontends/{parent_name}/backend_switching_rules | Replace an Backend Switching Rule list


# **create_backend_switching_rule**
> BackendSwitchingRule create_backend_switching_rule(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)

Add a new Backend Switching Rule

Adds a new Backend Switching Rule of the specified type in the specified frontend.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.backend_switching_rule import BackendSwitchingRule
from haproxy_dataplane_v3.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /v3
# See configuration.py for a list of all supported configuration parameters.
configuration = haproxy_dataplane_v3.Configuration(
    host = "/v3"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure HTTP basic authorization: basic_auth
configuration = haproxy_dataplane_v3.Configuration(
    username = os.environ["USERNAME"],
    password = os.environ["PASSWORD"]
)

# Enter a context with an instance of the API client
async with haproxy_dataplane_v3.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haproxy_dataplane_v3.BackendSwitchingRuleApi(api_client)
    index = 56 # int | Switching Rule Index
    parent_name = 'parent_name_example' # str | Parent name
    data = haproxy_dataplane_v3.BackendSwitchingRule() # BackendSwitchingRule | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Add a new Backend Switching Rule
        api_response = await api_instance.create_backend_switching_rule(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)
        print("The response of BackendSwitchingRuleApi->create_backend_switching_rule:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BackendSwitchingRuleApi->create_backend_switching_rule: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| Switching Rule Index | 
 **parent_name** | **str**| Parent name | 
 **data** | [**BackendSwitchingRule**](BackendSwitchingRule.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**BackendSwitchingRule**](BackendSwitchingRule.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Backend Switching Rule created |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_backend_switching_rule**
> delete_backend_switching_rule(index, parent_name, transaction_id=transaction_id, version=version, force_reload=force_reload)

Delete a Backend Switching Rule

Deletes a Backend Switching Rule configuration by it's index from the specified frontend.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /v3
# See configuration.py for a list of all supported configuration parameters.
configuration = haproxy_dataplane_v3.Configuration(
    host = "/v3"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure HTTP basic authorization: basic_auth
configuration = haproxy_dataplane_v3.Configuration(
    username = os.environ["USERNAME"],
    password = os.environ["PASSWORD"]
)

# Enter a context with an instance of the API client
async with haproxy_dataplane_v3.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haproxy_dataplane_v3.BackendSwitchingRuleApi(api_client)
    index = 56 # int | Switching Rule Index
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Delete a Backend Switching Rule
        await api_instance.delete_backend_switching_rule(index, parent_name, transaction_id=transaction_id, version=version, force_reload=force_reload)
    except Exception as e:
        print("Exception when calling BackendSwitchingRuleApi->delete_backend_switching_rule: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| Switching Rule Index | 
 **parent_name** | **str**| Parent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

void (empty response body)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**204** | Backend Switching Rule deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_backend_switching_rule**
> BackendSwitchingRule get_backend_switching_rule(index, parent_name, transaction_id=transaction_id)

Return one Backend Switching Rule

Returns one Backend Switching Rule configuration by it's index in the specified frontend.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.backend_switching_rule import BackendSwitchingRule
from haproxy_dataplane_v3.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /v3
# See configuration.py for a list of all supported configuration parameters.
configuration = haproxy_dataplane_v3.Configuration(
    host = "/v3"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure HTTP basic authorization: basic_auth
configuration = haproxy_dataplane_v3.Configuration(
    username = os.environ["USERNAME"],
    password = os.environ["PASSWORD"]
)

# Enter a context with an instance of the API client
async with haproxy_dataplane_v3.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haproxy_dataplane_v3.BackendSwitchingRuleApi(api_client)
    index = 56 # int | Switching Rule Index
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return one Backend Switching Rule
        api_response = await api_instance.get_backend_switching_rule(index, parent_name, transaction_id=transaction_id)
        print("The response of BackendSwitchingRuleApi->get_backend_switching_rule:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BackendSwitchingRuleApi->get_backend_switching_rule: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| Switching Rule Index | 
 **parent_name** | **str**| Parent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**BackendSwitchingRule**](BackendSwitchingRule.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful operation |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_backend_switching_rules**
> List[BackendSwitchingRule] get_backend_switching_rules(parent_name, transaction_id=transaction_id)

Return an array of all Backend Switching Rules

Returns all Backend Switching Rules that are configured in specified frontend.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.backend_switching_rule import BackendSwitchingRule
from haproxy_dataplane_v3.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /v3
# See configuration.py for a list of all supported configuration parameters.
configuration = haproxy_dataplane_v3.Configuration(
    host = "/v3"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure HTTP basic authorization: basic_auth
configuration = haproxy_dataplane_v3.Configuration(
    username = os.environ["USERNAME"],
    password = os.environ["PASSWORD"]
)

# Enter a context with an instance of the API client
async with haproxy_dataplane_v3.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haproxy_dataplane_v3.BackendSwitchingRuleApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return an array of all Backend Switching Rules
        api_response = await api_instance.get_backend_switching_rules(parent_name, transaction_id=transaction_id)
        print("The response of BackendSwitchingRuleApi->get_backend_switching_rules:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BackendSwitchingRuleApi->get_backend_switching_rules: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**List[BackendSwitchingRule]**](BackendSwitchingRule.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful operation |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_backend_switching_rule**
> BackendSwitchingRule replace_backend_switching_rule(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)

Replace a Backend Switching Rule

Replaces a Backend Switching Rule configuration by it's index in the specified frontend.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.backend_switching_rule import BackendSwitchingRule
from haproxy_dataplane_v3.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /v3
# See configuration.py for a list of all supported configuration parameters.
configuration = haproxy_dataplane_v3.Configuration(
    host = "/v3"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure HTTP basic authorization: basic_auth
configuration = haproxy_dataplane_v3.Configuration(
    username = os.environ["USERNAME"],
    password = os.environ["PASSWORD"]
)

# Enter a context with an instance of the API client
async with haproxy_dataplane_v3.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haproxy_dataplane_v3.BackendSwitchingRuleApi(api_client)
    index = 56 # int | Switching Rule Index
    parent_name = 'parent_name_example' # str | Parent name
    data = haproxy_dataplane_v3.BackendSwitchingRule() # BackendSwitchingRule | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Replace a Backend Switching Rule
        api_response = await api_instance.replace_backend_switching_rule(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)
        print("The response of BackendSwitchingRuleApi->replace_backend_switching_rule:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BackendSwitchingRuleApi->replace_backend_switching_rule: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| Switching Rule Index | 
 **parent_name** | **str**| Parent name | 
 **data** | [**BackendSwitchingRule**](BackendSwitchingRule.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**BackendSwitchingRule**](BackendSwitchingRule.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Backend Switching Rule replaced |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_backend_switching_rules**
> List[BackendSwitchingRule] replace_backend_switching_rules(parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)

Replace an Backend Switching Rule list

Replaces a whole list of Backend Switching Rules with the list given in parameter

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.backend_switching_rule import BackendSwitchingRule
from haproxy_dataplane_v3.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /v3
# See configuration.py for a list of all supported configuration parameters.
configuration = haproxy_dataplane_v3.Configuration(
    host = "/v3"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure HTTP basic authorization: basic_auth
configuration = haproxy_dataplane_v3.Configuration(
    username = os.environ["USERNAME"],
    password = os.environ["PASSWORD"]
)

# Enter a context with an instance of the API client
async with haproxy_dataplane_v3.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = haproxy_dataplane_v3.BackendSwitchingRuleApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    data = [haproxy_dataplane_v3.BackendSwitchingRule()] # List[BackendSwitchingRule] | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Replace an Backend Switching Rule list
        api_response = await api_instance.replace_backend_switching_rules(parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)
        print("The response of BackendSwitchingRuleApi->replace_backend_switching_rules:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BackendSwitchingRuleApi->replace_backend_switching_rules: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **data** | [**List[BackendSwitchingRule]**](BackendSwitchingRule.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**List[BackendSwitchingRule]**](BackendSwitchingRule.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | All Backend Switching Rule lines replaced |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

