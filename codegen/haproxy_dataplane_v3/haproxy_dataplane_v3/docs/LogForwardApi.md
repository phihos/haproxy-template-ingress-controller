# haproxy_dataplane_v3.LogForwardApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_log_forward**](LogForwardApi.md#create_log_forward) | **POST** /services/haproxy/configuration/log_forwards | Add a log forward
[**delete_log_forward**](LogForwardApi.md#delete_log_forward) | **DELETE** /services/haproxy/configuration/log_forwards/{name} | Delete a log forward
[**get_log_forward**](LogForwardApi.md#get_log_forward) | **GET** /services/haproxy/configuration/log_forwards/{name} | Return a log forward
[**get_log_forwards**](LogForwardApi.md#get_log_forwards) | **GET** /services/haproxy/configuration/log_forwards | Return an array of log forwards
[**replace_log_forward**](LogForwardApi.md#replace_log_forward) | **PUT** /services/haproxy/configuration/log_forwards/{name} | Replace a log forward


# **create_log_forward**
> LogForward create_log_forward(data, transaction_id=transaction_id, version=version, force_reload=force_reload, full_section=full_section)

Add a log forward

Adds a new log_forward to the configuration file.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.log_forward import LogForward
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
    api_instance = haproxy_dataplane_v3.LogForwardApi(api_client)
    data = haproxy_dataplane_v3.LogForward() # LogForward | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)
    full_section = False # bool | Indicates if the action affects the specified child resources as well (optional) (default to False)

    try:
        # Add a log forward
        api_response = await api_instance.create_log_forward(data, transaction_id=transaction_id, version=version, force_reload=force_reload, full_section=full_section)
        print("The response of LogForwardApi->create_log_forward:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LogForwardApi->create_log_forward: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **data** | [**LogForward**](LogForward.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]
 **full_section** | **bool**| Indicates if the action affects the specified child resources as well | [optional] [default to False]

### Return type

[**LogForward**](LogForward.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Log Forward created |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_log_forward**
> delete_log_forward(name, transaction_id=transaction_id, version=version, force_reload=force_reload)

Delete a log forward

Deletes a log forward from the configuration by it's name.

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
    api_instance = haproxy_dataplane_v3.LogForwardApi(api_client)
    name = 'name_example' # str | Log Forward name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Delete a log forward
        await api_instance.delete_log_forward(name, transaction_id=transaction_id, version=version, force_reload=force_reload)
    except Exception as e:
        print("Exception when calling LogForwardApi->delete_log_forward: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Log Forward name | 
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
**204** | Log Forward deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_log_forward**
> LogForward get_log_forward(name, transaction_id=transaction_id, full_section=full_section)

Return a log forward

Returns one log forward configuration by it's name.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.log_forward import LogForward
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
    api_instance = haproxy_dataplane_v3.LogForwardApi(api_client)
    name = 'name_example' # str | Log Forward name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    full_section = False # bool | Indicates if the action affects the specified child resources as well (optional) (default to False)

    try:
        # Return a log forward
        api_response = await api_instance.get_log_forward(name, transaction_id=transaction_id, full_section=full_section)
        print("The response of LogForwardApi->get_log_forward:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LogForwardApi->get_log_forward: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Log Forward name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **full_section** | **bool**| Indicates if the action affects the specified child resources as well | [optional] [default to False]

### Return type

[**LogForward**](LogForward.md)

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

# **get_log_forwards**
> List[LogForward] get_log_forwards(transaction_id=transaction_id, full_section=full_section)

Return an array of log forwards

Returns an array of all configured log forwards.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.log_forward import LogForward
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
    api_instance = haproxy_dataplane_v3.LogForwardApi(api_client)
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    full_section = False # bool | Indicates if the action affects the specified child resources as well (optional) (default to False)

    try:
        # Return an array of log forwards
        api_response = await api_instance.get_log_forwards(transaction_id=transaction_id, full_section=full_section)
        print("The response of LogForwardApi->get_log_forwards:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LogForwardApi->get_log_forwards: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **full_section** | **bool**| Indicates if the action affects the specified child resources as well | [optional] [default to False]

### Return type

[**List[LogForward]**](LogForward.md)

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

# **replace_log_forward**
> LogForward replace_log_forward(name, data, transaction_id=transaction_id, version=version, force_reload=force_reload, full_section=full_section)

Replace a log forward

Replaces a log forward configuration by it's name.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.log_forward import LogForward
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
    api_instance = haproxy_dataplane_v3.LogForwardApi(api_client)
    name = 'name_example' # str | Log Forward name
    data = haproxy_dataplane_v3.LogForward() # LogForward | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)
    full_section = False # bool | Indicates if the action affects the specified child resources as well (optional) (default to False)

    try:
        # Replace a log forward
        api_response = await api_instance.replace_log_forward(name, data, transaction_id=transaction_id, version=version, force_reload=force_reload, full_section=full_section)
        print("The response of LogForwardApi->replace_log_forward:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LogForwardApi->replace_log_forward: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Log Forward name | 
 **data** | [**LogForward**](LogForward.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]
 **full_section** | **bool**| Indicates if the action affects the specified child resources as well | [optional] [default to False]

### Return type

[**LogForward**](LogForward.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Log Forward replaced |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

