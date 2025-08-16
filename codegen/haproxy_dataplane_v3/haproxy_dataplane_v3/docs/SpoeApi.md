# haproxy_dataplane_v3.SpoeApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_spoe**](SpoeApi.md#create_spoe) | **POST** /services/haproxy/spoe/spoe_files | Creates SPOE file with its entries
[**create_spoe_agent**](SpoeApi.md#create_spoe_agent) | **POST** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/agents | Add a new spoe agent to scope
[**create_spoe_group**](SpoeApi.md#create_spoe_group) | **POST** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/groups | Add a new SPOE groups
[**create_spoe_message**](SpoeApi.md#create_spoe_message) | **POST** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/messages | Add a new spoe message to scope
[**create_spoe_scope**](SpoeApi.md#create_spoe_scope) | **POST** /services/haproxy/spoe/spoe_files/{parent_name}/scopes | Add a new spoe scope
[**delete_spoe_agent**](SpoeApi.md#delete_spoe_agent) | **DELETE** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/agents/{name} | Delete a SPOE agent
[**delete_spoe_file**](SpoeApi.md#delete_spoe_file) | **DELETE** /services/haproxy/spoe/spoe_files/{name} | Delete SPOE file
[**delete_spoe_group**](SpoeApi.md#delete_spoe_group) | **DELETE** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/groups/{name} | Delete a SPOE groups
[**delete_spoe_message**](SpoeApi.md#delete_spoe_message) | **DELETE** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/messages/{name} | Delete a spoe message
[**delete_spoe_scope**](SpoeApi.md#delete_spoe_scope) | **DELETE** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{name} | Delete a SPOE scope
[**get_all_spoe_agent**](SpoeApi.md#get_all_spoe_agent) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/agents | Return an array of spoe agents in one scope
[**get_all_spoe_files**](SpoeApi.md#get_all_spoe_files) | **GET** /services/haproxy/spoe/spoe_files | Return all available SPOE files
[**get_all_spoe_group**](SpoeApi.md#get_all_spoe_group) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/groups | Return an array of SPOE groups
[**get_all_spoe_message**](SpoeApi.md#get_all_spoe_message) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/messages | Return an array of spoe messages in one scope
[**get_all_spoe_scope**](SpoeApi.md#get_all_spoe_scope) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/scopes | Return an array of spoe scopes
[**get_one_spoe_file**](SpoeApi.md#get_one_spoe_file) | **GET** /services/haproxy/spoe/spoe_files/{name} | Return one SPOE file
[**get_spoe_agent**](SpoeApi.md#get_spoe_agent) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/agents/{name} | Return a spoe agent
[**get_spoe_configuration_version**](SpoeApi.md#get_spoe_configuration_version) | **GET** /services/haproxy/spoe/{parent_name}/version | Return a SPOE configuration version
[**get_spoe_group**](SpoeApi.md#get_spoe_group) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/groups/{name} | Return a SPOE groups
[**get_spoe_message**](SpoeApi.md#get_spoe_message) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/messages/{name} | Return a spoe message
[**get_spoe_scope**](SpoeApi.md#get_spoe_scope) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{name} | Return one SPOE scope
[**replace_spoe_agent**](SpoeApi.md#replace_spoe_agent) | **PUT** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/agents/{name} | Replace a SPOE agent
[**replace_spoe_group**](SpoeApi.md#replace_spoe_group) | **PUT** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/groups/{name} | Replace a SPOE groups
[**replace_spoe_message**](SpoeApi.md#replace_spoe_message) | **PUT** /services/haproxy/spoe/spoe_files/{parent_name}/scopes/{scope_name}/messages/{name} | Replace a spoe message


# **create_spoe**
> str create_spoe(file_upload=file_upload)

Creates SPOE file with its entries

Creates SPOE file with its entries.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    file_upload = None # bytearray | The spoe file to upload (optional)

    try:
        # Creates SPOE file with its entries
        api_response = await api_instance.create_spoe(file_upload=file_upload)
        print("The response of SpoeApi->create_spoe:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->create_spoe: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file_upload** | **bytearray**| The spoe file to upload | [optional] 

### Return type

**str**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | SPOE file created with its entries |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_spoe_agent**
> SpoeAgent create_spoe_agent(parent_name, scope_name, data, transaction_id=transaction_id, version=version)

Add a new spoe agent to scope

Adds a new spoe agent to the spoe scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_agent import SpoeAgent
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    data = haproxy_dataplane_v3.SpoeAgent() # SpoeAgent | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Add a new spoe agent to scope
        api_response = await api_instance.create_spoe_agent(parent_name, scope_name, data, transaction_id=transaction_id, version=version)
        print("The response of SpoeApi->create_spoe_agent:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->create_spoe_agent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **data** | [**SpoeAgent**](SpoeAgent.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

[**SpoeAgent**](SpoeAgent.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Spoe agent created |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_spoe_group**
> SpoeGroup create_spoe_group(parent_name, scope_name, data, transaction_id=transaction_id, version=version)

Add a new SPOE groups

Adds a new SPOE groups to the SPOE scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_group import SpoeGroup
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    data = haproxy_dataplane_v3.SpoeGroup() # SpoeGroup | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Add a new SPOE groups
        api_response = await api_instance.create_spoe_group(parent_name, scope_name, data, transaction_id=transaction_id, version=version)
        print("The response of SpoeApi->create_spoe_group:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->create_spoe_group: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **data** | [**SpoeGroup**](SpoeGroup.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

[**SpoeGroup**](SpoeGroup.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Spoe groups created |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_spoe_message**
> SpoeMessage create_spoe_message(parent_name, scope_name, data, transaction_id=transaction_id, version=version)

Add a new spoe message to scope

Adds a new spoe message to the spoe scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_message import SpoeMessage
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    data = haproxy_dataplane_v3.SpoeMessage() # SpoeMessage | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Add a new spoe message to scope
        api_response = await api_instance.create_spoe_message(parent_name, scope_name, data, transaction_id=transaction_id, version=version)
        print("The response of SpoeApi->create_spoe_message:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->create_spoe_message: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **data** | [**SpoeMessage**](SpoeMessage.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

[**SpoeMessage**](SpoeMessage.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Spoe message created |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_spoe_scope**
> str create_spoe_scope(parent_name, data, transaction_id=transaction_id, version=version)

Add a new spoe scope

Adds a new spoe scope.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    data = 'data_example' # str | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Add a new spoe scope
        api_response = await api_instance.create_spoe_scope(parent_name, data, transaction_id=transaction_id, version=version)
        print("The response of SpoeApi->create_spoe_scope:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->create_spoe_scope: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **data** | **str**|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

**str**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Spoe scope created |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_spoe_agent**
> delete_spoe_agent(parent_name, scope_name, name, transaction_id=transaction_id, version=version)

Delete a SPOE agent

Deletes a SPOE agent from the configuration in one SPOE scope.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    name = 'name_example' # str | Spoe agent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Delete a SPOE agent
        await api_instance.delete_spoe_agent(parent_name, scope_name, name, transaction_id=transaction_id, version=version)
    except Exception as e:
        print("Exception when calling SpoeApi->delete_spoe_agent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **name** | **str**| Spoe agent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

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
**204** | Spoe agent deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_spoe_file**
> delete_spoe_file(name)

Delete SPOE file

Deletes SPOE file.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    name = 'name_example' # str | SPOE file name

    try:
        # Delete SPOE file
        await api_instance.delete_spoe_file(name)
    except Exception as e:
        print("Exception when calling SpoeApi->delete_spoe_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SPOE file name | 

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
**204** | SPOE file deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_spoe_group**
> delete_spoe_group(parent_name, scope_name, name, transaction_id=transaction_id, version=version)

Delete a SPOE groups

Deletes a SPOE groups from the one SPOE scope.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    name = 'name_example' # str | Spoe group name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Delete a SPOE groups
        await api_instance.delete_spoe_group(parent_name, scope_name, name, transaction_id=transaction_id, version=version)
    except Exception as e:
        print("Exception when calling SpoeApi->delete_spoe_group: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **name** | **str**| Spoe group name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

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
**204** | Spoe group deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_spoe_message**
> delete_spoe_message(parent_name, scope_name, name, transaction_id=transaction_id, version=version)

Delete a spoe message

Deletes a spoe message from the SPOE scope.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    name = 'name_example' # str | Spoe message name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Delete a spoe message
        await api_instance.delete_spoe_message(parent_name, scope_name, name, transaction_id=transaction_id, version=version)
    except Exception as e:
        print("Exception when calling SpoeApi->delete_spoe_message: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **name** | **str**| Spoe message name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

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
**204** | Spoe message deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_spoe_scope**
> delete_spoe_scope(parent_name, name, transaction_id=transaction_id, version=version)

Delete a SPOE scope

Deletes a SPOE scope from the configuration file.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    name = 'name_example' # str | Spoe scope name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Delete a SPOE scope
        await api_instance.delete_spoe_scope(parent_name, name, transaction_id=transaction_id, version=version)
    except Exception as e:
        print("Exception when calling SpoeApi->delete_spoe_scope: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **name** | **str**| Spoe scope name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

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
**204** | Spoe scope deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_spoe_agent**
> List[SpoeAgent] get_all_spoe_agent(parent_name, scope_name, transaction_id=transaction_id)

Return an array of spoe agents in one scope

Returns an array of all configured spoe agents in one scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_agent import SpoeAgent
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return an array of spoe agents in one scope
        api_response = await api_instance.get_all_spoe_agent(parent_name, scope_name, transaction_id=transaction_id)
        print("The response of SpoeApi->get_all_spoe_agent:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_all_spoe_agent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**List[SpoeAgent]**](SpoeAgent.md)

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

# **get_all_spoe_files**
> List[str] get_all_spoe_files()

Return all available SPOE files

Returns all available SPOE files.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)

    try:
        # Return all available SPOE files
        api_response = await api_instance.get_all_spoe_files()
        print("The response of SpoeApi->get_all_spoe_files:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_all_spoe_files: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

**List[str]**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful operation |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_spoe_group**
> List[SpoeGroup] get_all_spoe_group(parent_name, scope_name, transaction_id=transaction_id)

Return an array of SPOE groups

Returns an array of all configured SPOE groups in one SPOE scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_group import SpoeGroup
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return an array of SPOE groups
        api_response = await api_instance.get_all_spoe_group(parent_name, scope_name, transaction_id=transaction_id)
        print("The response of SpoeApi->get_all_spoe_group:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_all_spoe_group: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**List[SpoeGroup]**](SpoeGroup.md)

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

# **get_all_spoe_message**
> List[SpoeMessage] get_all_spoe_message(parent_name, scope_name, transaction_id=transaction_id)

Return an array of spoe messages in one scope

Returns an array of all configured spoe messages in one scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_message import SpoeMessage
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return an array of spoe messages in one scope
        api_response = await api_instance.get_all_spoe_message(parent_name, scope_name, transaction_id=transaction_id)
        print("The response of SpoeApi->get_all_spoe_message:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_all_spoe_message: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**List[SpoeMessage]**](SpoeMessage.md)

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

# **get_all_spoe_scope**
> List[str] get_all_spoe_scope(parent_name, transaction_id=transaction_id)

Return an array of spoe scopes

Returns an array of all configured spoe scopes.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return an array of spoe scopes
        api_response = await api_instance.get_all_spoe_scope(parent_name, transaction_id=transaction_id)
        print("The response of SpoeApi->get_all_spoe_scope:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_all_spoe_scope: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

**List[str]**

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

# **get_one_spoe_file**
> GetOneSpoeFile200Response get_one_spoe_file(name)

Return one SPOE file

Returns one SPOE file.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.get_one_spoe_file200_response import GetOneSpoeFile200Response
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    name = 'name_example' # str | SPOE file name

    try:
        # Return one SPOE file
        api_response = await api_instance.get_one_spoe_file(name)
        print("The response of SpoeApi->get_one_spoe_file:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_one_spoe_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SPOE file name | 

### Return type

[**GetOneSpoeFile200Response**](GetOneSpoeFile200Response.md)

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

# **get_spoe_agent**
> SpoeAgent get_spoe_agent(parent_name, scope_name, name, transaction_id=transaction_id)

Return a spoe agent

Returns one spoe agent configuration in one SPOE scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_agent import SpoeAgent
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    name = 'name_example' # str | Spoe agent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return a spoe agent
        api_response = await api_instance.get_spoe_agent(parent_name, scope_name, name, transaction_id=transaction_id)
        print("The response of SpoeApi->get_spoe_agent:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_spoe_agent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **name** | **str**| Spoe agent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**SpoeAgent**](SpoeAgent.md)

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

# **get_spoe_configuration_version**
> int get_spoe_configuration_version(parent_name, transaction_id=transaction_id)

Return a SPOE configuration version

Returns SPOE configuration version.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return a SPOE configuration version
        api_response = await api_instance.get_spoe_configuration_version(parent_name, transaction_id=transaction_id)
        print("The response of SpoeApi->get_spoe_configuration_version:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_spoe_configuration_version: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

**int**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | SPOE configuration version |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_spoe_group**
> SpoeGroup get_spoe_group(parent_name, scope_name, name, transaction_id=transaction_id)

Return a SPOE groups

Returns one SPOE groups configuration in one SPOE scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_group import SpoeGroup
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    name = 'name_example' # str | Spoe group name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return a SPOE groups
        api_response = await api_instance.get_spoe_group(parent_name, scope_name, name, transaction_id=transaction_id)
        print("The response of SpoeApi->get_spoe_group:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_spoe_group: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **name** | **str**| Spoe group name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**SpoeGroup**](SpoeGroup.md)

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

# **get_spoe_message**
> SpoeMessage get_spoe_message(parent_name, scope_name, name, transaction_id=transaction_id)

Return a spoe message

Returns one spoe message configuration in SPOE scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_message import SpoeMessage
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    name = 'name_example' # str | Spoe message name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return a spoe message
        api_response = await api_instance.get_spoe_message(parent_name, scope_name, name, transaction_id=transaction_id)
        print("The response of SpoeApi->get_spoe_message:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_spoe_message: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **name** | **str**| Spoe message name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

[**SpoeMessage**](SpoeMessage.md)

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

# **get_spoe_scope**
> str get_spoe_scope(parent_name, name, transaction_id=transaction_id)

Return one SPOE scope

Returns one SPOE scope in one SPOE file.

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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    name = 'name_example' # str | Spoe scope
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return one SPOE scope
        api_response = await api_instance.get_spoe_scope(parent_name, name, transaction_id=transaction_id)
        print("The response of SpoeApi->get_spoe_scope:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->get_spoe_scope: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **name** | **str**| Spoe scope | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 

### Return type

**str**

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

# **replace_spoe_agent**
> SpoeAgent replace_spoe_agent(parent_name, scope_name, name, data, transaction_id=transaction_id, version=version)

Replace a SPOE agent

Replaces a SPOE agent configuration in one SPOE scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_agent import SpoeAgent
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    name = 'name_example' # str | Spoe agent name
    data = haproxy_dataplane_v3.SpoeAgent() # SpoeAgent | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Replace a SPOE agent
        api_response = await api_instance.replace_spoe_agent(parent_name, scope_name, name, data, transaction_id=transaction_id, version=version)
        print("The response of SpoeApi->replace_spoe_agent:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->replace_spoe_agent: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **name** | **str**| Spoe agent name | 
 **data** | [**SpoeAgent**](SpoeAgent.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

[**SpoeAgent**](SpoeAgent.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Spoe agent replaced |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_spoe_group**
> SpoeGroup replace_spoe_group(parent_name, scope_name, name, data, transaction_id=transaction_id, version=version)

Replace a SPOE groups

Replaces a SPOE groups configuration in one SPOE scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_group import SpoeGroup
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    name = 'name_example' # str | Spoe group name
    data = haproxy_dataplane_v3.SpoeGroup() # SpoeGroup | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Replace a SPOE groups
        api_response = await api_instance.replace_spoe_group(parent_name, scope_name, name, data, transaction_id=transaction_id, version=version)
        print("The response of SpoeApi->replace_spoe_group:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->replace_spoe_group: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **name** | **str**| Spoe group name | 
 **data** | [**SpoeGroup**](SpoeGroup.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

[**SpoeGroup**](SpoeGroup.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Spoe groups replaced |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_spoe_message**
> SpoeMessage replace_spoe_message(parent_name, scope_name, name, data, transaction_id=transaction_id, version=version)

Replace a spoe message

Replaces a spoe message configuration in one SPOE scope.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_message import SpoeMessage
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
    api_instance = haproxy_dataplane_v3.SpoeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    scope_name = 'scope_name_example' # str | Spoe scope name
    name = 'name_example' # str | Spoe message name
    data = haproxy_dataplane_v3.SpoeMessage() # SpoeMessage | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Replace a spoe message
        api_response = await api_instance.replace_spoe_message(parent_name, scope_name, name, data, transaction_id=transaction_id, version=version)
        print("The response of SpoeApi->replace_spoe_message:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeApi->replace_spoe_message: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **scope_name** | **str**| Spoe scope name | 
 **name** | **str**| Spoe message name | 
 **data** | [**SpoeMessage**](SpoeMessage.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

[**SpoeMessage**](SpoeMessage.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Spoe message replaced |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

