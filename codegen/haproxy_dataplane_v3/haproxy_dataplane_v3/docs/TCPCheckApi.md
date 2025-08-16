# haproxy_dataplane_v3.TCPCheckApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_tcp_check_backend**](TCPCheckApi.md#create_tcp_check_backend) | **POST** /services/haproxy/configuration/backends/{parent_name}/tcp_checks/{index} | Add a new TCP check
[**create_tcp_check_defaults**](TCPCheckApi.md#create_tcp_check_defaults) | **POST** /services/haproxy/configuration/defaults/{parent_name}/tcp_checks/{index} | Add a new TCP check
[**delete_tcp_check_backend**](TCPCheckApi.md#delete_tcp_check_backend) | **DELETE** /services/haproxy/configuration/backends/{parent_name}/tcp_checks/{index} | Delete a TCP check
[**delete_tcp_check_defaults**](TCPCheckApi.md#delete_tcp_check_defaults) | **DELETE** /services/haproxy/configuration/defaults/{parent_name}/tcp_checks/{index} | Delete a TCP check
[**get_all_tcp_check_backend**](TCPCheckApi.md#get_all_tcp_check_backend) | **GET** /services/haproxy/configuration/backends/{parent_name}/tcp_checks | Return an array of TCP checks
[**get_all_tcp_check_defaults**](TCPCheckApi.md#get_all_tcp_check_defaults) | **GET** /services/haproxy/configuration/defaults/{parent_name}/tcp_checks | Return an array of TCP checks
[**get_tcp_check_backend**](TCPCheckApi.md#get_tcp_check_backend) | **GET** /services/haproxy/configuration/backends/{parent_name}/tcp_checks/{index} | Return one TCP check
[**get_tcp_check_defaults**](TCPCheckApi.md#get_tcp_check_defaults) | **GET** /services/haproxy/configuration/defaults/{parent_name}/tcp_checks/{index} | Return one TCP check
[**replace_all_tcp_check_backend**](TCPCheckApi.md#replace_all_tcp_check_backend) | **PUT** /services/haproxy/configuration/backends/{parent_name}/tcp_checks | Replace an TCP Check list
[**replace_all_tcp_check_defaults**](TCPCheckApi.md#replace_all_tcp_check_defaults) | **PUT** /services/haproxy/configuration/defaults/{parent_name}/tcp_checks | Replace an TCP Check list
[**replace_tcp_check_backend**](TCPCheckApi.md#replace_tcp_check_backend) | **PUT** /services/haproxy/configuration/backends/{parent_name}/tcp_checks/{index} | Replace a TCP check
[**replace_tcp_check_defaults**](TCPCheckApi.md#replace_tcp_check_defaults) | **PUT** /services/haproxy/configuration/defaults/{parent_name}/tcp_checks/{index} | Replace a TCP check


# **create_tcp_check_backend**
> TcpCheck create_tcp_check_backend(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)

Add a new TCP check

Adds a new TCP check of the specified type in the specified parent.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    index = 56 # int | TCP check Index
    parent_name = 'parent_name_example' # str | Parent name
    data = haproxy_dataplane_v3.TcpCheck() # TcpCheck | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Add a new TCP check
        api_response = await api_instance.create_tcp_check_backend(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)
        print("The response of TCPCheckApi->create_tcp_check_backend:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->create_tcp_check_backend: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| TCP check Index | 
 **parent_name** | **str**| Parent name | 
 **data** | [**TcpCheck**](TcpCheck.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**TcpCheck**](TcpCheck.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | TCP check created |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_tcp_check_defaults**
> TcpCheck create_tcp_check_defaults(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)

Add a new TCP check

Adds a new TCP check of the specified type in the specified parent.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    index = 56 # int | TCP check Index
    parent_name = 'parent_name_example' # str | Parent name
    data = haproxy_dataplane_v3.TcpCheck() # TcpCheck | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Add a new TCP check
        api_response = await api_instance.create_tcp_check_defaults(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)
        print("The response of TCPCheckApi->create_tcp_check_defaults:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->create_tcp_check_defaults: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| TCP check Index | 
 **parent_name** | **str**| Parent name | 
 **data** | [**TcpCheck**](TcpCheck.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**TcpCheck**](TcpCheck.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | TCP check created |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_tcp_check_backend**
> delete_tcp_check_backend(index, parent_name, transaction_id=transaction_id, version=version, force_reload=force_reload)

Delete a TCP check

Deletes a TCP check configuration by it's index from the specified parent.

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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    index = 56 # int | TCP check Index
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Delete a TCP check
        await api_instance.delete_tcp_check_backend(index, parent_name, transaction_id=transaction_id, version=version, force_reload=force_reload)
    except Exception as e:
        print("Exception when calling TCPCheckApi->delete_tcp_check_backend: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| TCP check Index | 
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
**204** | TCP check deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_tcp_check_defaults**
> delete_tcp_check_defaults(index, parent_name, transaction_id=transaction_id, version=version, force_reload=force_reload)

Delete a TCP check

Deletes a TCP check configuration by it's index from the specified parent.

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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    index = 56 # int | TCP check Index
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Delete a TCP check
        await api_instance.delete_tcp_check_defaults(index, parent_name, transaction_id=transaction_id, version=version, force_reload=force_reload)
    except Exception as e:
        print("Exception when calling TCPCheckApi->delete_tcp_check_defaults: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| TCP check Index | 
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
**204** | TCP check deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_tcp_check_backend**
> List[TcpCheck] get_all_tcp_check_backend(parent_name, transaction_id=transaction_id)

Return an array of TCP checks

Returns all TCP checks that are configured in specified parent.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return an array of TCP checks
        api_response = await api_instance.get_all_tcp_check_backend(parent_name, transaction_id=transaction_id)
        print("The response of TCPCheckApi->get_all_tcp_check_backend:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->get_all_tcp_check_backend: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**List[TcpCheck]**](TcpCheck.md)

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

# **get_all_tcp_check_defaults**
> List[TcpCheck] get_all_tcp_check_defaults(parent_name, transaction_id=transaction_id)

Return an array of TCP checks

Returns all TCP checks that are configured in specified parent.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return an array of TCP checks
        api_response = await api_instance.get_all_tcp_check_defaults(parent_name, transaction_id=transaction_id)
        print("The response of TCPCheckApi->get_all_tcp_check_defaults:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->get_all_tcp_check_defaults: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**List[TcpCheck]**](TcpCheck.md)

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

# **get_tcp_check_backend**
> TcpCheck get_tcp_check_backend(index, parent_name, transaction_id=transaction_id)

Return one TCP check

Returns one TCP check configuration by it's index in the specified parent.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    index = 56 # int | TCP Check Index
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return one TCP check
        api_response = await api_instance.get_tcp_check_backend(index, parent_name, transaction_id=transaction_id)
        print("The response of TCPCheckApi->get_tcp_check_backend:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->get_tcp_check_backend: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| TCP Check Index | 
 **parent_name** | **str**| Parent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**TcpCheck**](TcpCheck.md)

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

# **get_tcp_check_defaults**
> TcpCheck get_tcp_check_defaults(index, parent_name, transaction_id=transaction_id)

Return one TCP check

Returns one TCP check configuration by it's index in the specified parent.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    index = 56 # int | TCP Check Index
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return one TCP check
        api_response = await api_instance.get_tcp_check_defaults(index, parent_name, transaction_id=transaction_id)
        print("The response of TCPCheckApi->get_tcp_check_defaults:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->get_tcp_check_defaults: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| TCP Check Index | 
 **parent_name** | **str**| Parent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**TcpCheck**](TcpCheck.md)

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

# **replace_all_tcp_check_backend**
> List[TcpCheck] replace_all_tcp_check_backend(parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)

Replace an TCP Check list

Replaces a whole list of TCP Checks with the list given in parameter

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    data = [haproxy_dataplane_v3.TcpCheck()] # List[TcpCheck] | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Replace an TCP Check list
        api_response = await api_instance.replace_all_tcp_check_backend(parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)
        print("The response of TCPCheckApi->replace_all_tcp_check_backend:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->replace_all_tcp_check_backend: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **data** | [**List[TcpCheck]**](TcpCheck.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**List[TcpCheck]**](TcpCheck.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | All TCP Check lines replaced |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_all_tcp_check_defaults**
> List[TcpCheck] replace_all_tcp_check_defaults(parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)

Replace an TCP Check list

Replaces a whole list of TCP Checks with the list given in parameter

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    data = [haproxy_dataplane_v3.TcpCheck()] # List[TcpCheck] | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Replace an TCP Check list
        api_response = await api_instance.replace_all_tcp_check_defaults(parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)
        print("The response of TCPCheckApi->replace_all_tcp_check_defaults:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->replace_all_tcp_check_defaults: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **data** | [**List[TcpCheck]**](TcpCheck.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**List[TcpCheck]**](TcpCheck.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | All TCP Check lines replaced |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_tcp_check_backend**
> TcpCheck replace_tcp_check_backend(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)

Replace a TCP check

Replaces a TCP Check configuration by it's index in the specified parent.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    index = 56 # int | TCP Check Index
    parent_name = 'parent_name_example' # str | Parent name
    data = haproxy_dataplane_v3.TcpCheck() # TcpCheck | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Replace a TCP check
        api_response = await api_instance.replace_tcp_check_backend(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)
        print("The response of TCPCheckApi->replace_tcp_check_backend:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->replace_tcp_check_backend: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| TCP Check Index | 
 **parent_name** | **str**| Parent name | 
 **data** | [**TcpCheck**](TcpCheck.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**TcpCheck**](TcpCheck.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | TCP check replaced |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_tcp_check_defaults**
> TcpCheck replace_tcp_check_defaults(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)

Replace a TCP check

Replaces a TCP Check configuration by it's index in the specified parent.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.tcp_check import TcpCheck
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
    api_instance = haproxy_dataplane_v3.TCPCheckApi(api_client)
    index = 56 # int | TCP Check Index
    parent_name = 'parent_name_example' # str | Parent name
    data = haproxy_dataplane_v3.TcpCheck() # TcpCheck | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Replace a TCP check
        api_response = await api_instance.replace_tcp_check_defaults(index, parent_name, data, transaction_id=transaction_id, version=version, force_reload=force_reload)
        print("The response of TCPCheckApi->replace_tcp_check_defaults:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TCPCheckApi->replace_tcp_check_defaults: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **index** | **int**| TCP Check Index | 
 **parent_name** | **str**| Parent name | 
 **data** | [**TcpCheck**](TcpCheck.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**TcpCheck**](TcpCheck.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | TCP check replaced |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

