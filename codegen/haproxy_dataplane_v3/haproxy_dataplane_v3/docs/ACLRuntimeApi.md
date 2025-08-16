# haproxy_dataplane_v3.ACLRuntimeApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_payload_runtime_acl**](ACLRuntimeApi.md#add_payload_runtime_acl) | **PUT** /services/haproxy/runtime/acls/{parent_name}/entries | Add a new ACL payload
[**services_haproxy_runtime_acls_get**](ACLRuntimeApi.md#services_haproxy_runtime_acls_get) | **GET** /services/haproxy/runtime/acls | Return an array of all ACL files
[**services_haproxy_runtime_acls_id_get**](ACLRuntimeApi.md#services_haproxy_runtime_acls_id_get) | **GET** /services/haproxy/runtime/acls/{id} | Return an ACL file
[**services_haproxy_runtime_acls_parent_name_entries_get**](ACLRuntimeApi.md#services_haproxy_runtime_acls_parent_name_entries_get) | **GET** /services/haproxy/runtime/acls/{parent_name}/entries | Return an ACL entries
[**services_haproxy_runtime_acls_parent_name_entries_id_delete**](ACLRuntimeApi.md#services_haproxy_runtime_acls_parent_name_entries_id_delete) | **DELETE** /services/haproxy/runtime/acls/{parent_name}/entries/{id} | Delete an ACL entry
[**services_haproxy_runtime_acls_parent_name_entries_id_get**](ACLRuntimeApi.md#services_haproxy_runtime_acls_parent_name_entries_id_get) | **GET** /services/haproxy/runtime/acls/{parent_name}/entries/{id} | Return an ACL entry
[**services_haproxy_runtime_acls_parent_name_entries_post**](ACLRuntimeApi.md#services_haproxy_runtime_acls_parent_name_entries_post) | **POST** /services/haproxy/runtime/acls/{parent_name}/entries | Add entry to an ACL file


# **add_payload_runtime_acl**
> List[AclFileEntry] add_payload_runtime_acl(parent_name, data)

Add a new ACL payload

Adds a new ACL payload.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.acl_file_entry import AclFileEntry
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
    api_instance = haproxy_dataplane_v3.ACLRuntimeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    data = [haproxy_dataplane_v3.AclFileEntry()] # List[AclFileEntry] | 

    try:
        # Add a new ACL payload
        api_response = await api_instance.add_payload_runtime_acl(parent_name, data)
        print("The response of ACLRuntimeApi->add_payload_runtime_acl:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ACLRuntimeApi->add_payload_runtime_acl: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **data** | [**List[AclFileEntry]**](AclFileEntry.md)|  | 

### Return type

[**List[AclFileEntry]**](AclFileEntry.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | ACL payload added |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **services_haproxy_runtime_acls_get**
> List[AclFile] services_haproxy_runtime_acls_get()

Return an array of all ACL files

Returns all ACL files using the runtime socket.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.acl_file import AclFile
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
    api_instance = haproxy_dataplane_v3.ACLRuntimeApi(api_client)

    try:
        # Return an array of all ACL files
        api_response = await api_instance.services_haproxy_runtime_acls_get()
        print("The response of ACLRuntimeApi->services_haproxy_runtime_acls_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ACLRuntimeApi->services_haproxy_runtime_acls_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[AclFile]**](AclFile.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful operation |  -  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **services_haproxy_runtime_acls_id_get**
> AclFile services_haproxy_runtime_acls_id_get(id)

Return an ACL file

Returns an ACL file by id using the runtime socket.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.acl_file import AclFile
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
    api_instance = haproxy_dataplane_v3.ACLRuntimeApi(api_client)
    id = 'id_example' # str | ACL file entry ID

    try:
        # Return an ACL file
        api_response = await api_instance.services_haproxy_runtime_acls_id_get(id)
        print("The response of ACLRuntimeApi->services_haproxy_runtime_acls_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ACLRuntimeApi->services_haproxy_runtime_acls_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| ACL file entry ID | 

### Return type

[**AclFile**](AclFile.md)

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

# **services_haproxy_runtime_acls_parent_name_entries_get**
> List[AclFileEntry] services_haproxy_runtime_acls_parent_name_entries_get(parent_name)

Return an ACL entries

Returns an ACL runtime setting using the runtime socket.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.acl_file_entry import AclFileEntry
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
    api_instance = haproxy_dataplane_v3.ACLRuntimeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name

    try:
        # Return an ACL entries
        api_response = await api_instance.services_haproxy_runtime_acls_parent_name_entries_get(parent_name)
        print("The response of ACLRuntimeApi->services_haproxy_runtime_acls_parent_name_entries_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ACLRuntimeApi->services_haproxy_runtime_acls_parent_name_entries_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 

### Return type

[**List[AclFileEntry]**](AclFileEntry.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful operation |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **services_haproxy_runtime_acls_parent_name_entries_id_delete**
> services_haproxy_runtime_acls_parent_name_entries_id_delete(parent_name, id)

Delete an ACL entry

Deletes the entry from the ACL by its value using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.ACLRuntimeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    id = 'id_example' # str | File entry ID

    try:
        # Delete an ACL entry
        await api_instance.services_haproxy_runtime_acls_parent_name_entries_id_delete(parent_name, id)
    except Exception as e:
        print("Exception when calling ACLRuntimeApi->services_haproxy_runtime_acls_parent_name_entries_id_delete: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **id** | **str**| File entry ID | 

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
**204** | Successful operation |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **services_haproxy_runtime_acls_parent_name_entries_id_get**
> AclFileEntry services_haproxy_runtime_acls_parent_name_entries_id_get(parent_name, id)

Return an ACL entry

Returns the ACL entry by its ID using the runtime socket.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.acl_file_entry import AclFileEntry
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
    api_instance = haproxy_dataplane_v3.ACLRuntimeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    id = 'id_example' # str | File entry ID

    try:
        # Return an ACL entry
        api_response = await api_instance.services_haproxy_runtime_acls_parent_name_entries_id_get(parent_name, id)
        print("The response of ACLRuntimeApi->services_haproxy_runtime_acls_parent_name_entries_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ACLRuntimeApi->services_haproxy_runtime_acls_parent_name_entries_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **id** | **str**| File entry ID | 

### Return type

[**AclFileEntry**](AclFileEntry.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful operation |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **services_haproxy_runtime_acls_parent_name_entries_post**
> AclFileEntry services_haproxy_runtime_acls_parent_name_entries_post(parent_name, data)

Add entry to an ACL file

Adds an entry into the ACL file using the runtime socket.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.acl_file_entry import AclFileEntry
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
    api_instance = haproxy_dataplane_v3.ACLRuntimeApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    data = haproxy_dataplane_v3.AclFileEntry() # AclFileEntry | 

    try:
        # Add entry to an ACL file
        api_response = await api_instance.services_haproxy_runtime_acls_parent_name_entries_post(parent_name, data)
        print("The response of ACLRuntimeApi->services_haproxy_runtime_acls_parent_name_entries_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ACLRuntimeApi->services_haproxy_runtime_acls_parent_name_entries_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **data** | [**AclFileEntry**](AclFileEntry.md)|  | 

### Return type

[**AclFileEntry**](AclFileEntry.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | ACL entry created |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

