# haproxy_dataplane_v3.MapsApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_map_entry**](MapsApi.md#add_map_entry) | **POST** /services/haproxy/runtime/maps/{parent_name}/entries | Adds an entry into the map file
[**add_payload_runtime_map**](MapsApi.md#add_payload_runtime_map) | **PUT** /services/haproxy/runtime/maps/{name} | Add a new map payload
[**clear_runtime_map**](MapsApi.md#clear_runtime_map) | **DELETE** /services/haproxy/runtime/maps/{name} | Remove all map entries from the map file
[**delete_runtime_map_entry**](MapsApi.md#delete_runtime_map_entry) | **DELETE** /services/haproxy/runtime/maps/{parent_name}/entries/{id} | Deletes all the map entries from the map by its id
[**get_all_runtime_map_files**](MapsApi.md#get_all_runtime_map_files) | **GET** /services/haproxy/runtime/maps | Return runtime map files
[**get_one_runtime_map**](MapsApi.md#get_one_runtime_map) | **GET** /services/haproxy/runtime/maps/{name} | Return one runtime map file
[**get_runtime_map_entry**](MapsApi.md#get_runtime_map_entry) | **GET** /services/haproxy/runtime/maps/{parent_name}/entries/{id} | Return one map runtime setting
[**replace_runtime_map_entry**](MapsApi.md#replace_runtime_map_entry) | **PUT** /services/haproxy/runtime/maps/{parent_name}/entries/{id} | Replace the value corresponding to each id in a map
[**show_runtime_map**](MapsApi.md#show_runtime_map) | **GET** /services/haproxy/runtime/maps/{parent_name}/entries | Return one map runtime entries


# **add_map_entry**
> MapEntry add_map_entry(parent_name, data, force_sync=force_sync)

Adds an entry into the map file

Adds an entry into the map file.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.map_entry import MapEntry
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
    api_instance = haproxy_dataplane_v3.MapsApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    data = haproxy_dataplane_v3.MapEntry() # MapEntry | 
    force_sync = False # bool | If true, immediately syncs changes to disk (optional) (default to False)

    try:
        # Adds an entry into the map file
        api_response = await api_instance.add_map_entry(parent_name, data, force_sync=force_sync)
        print("The response of MapsApi->add_map_entry:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MapsApi->add_map_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **data** | [**MapEntry**](MapEntry.md)|  | 
 **force_sync** | **bool**| If true, immediately syncs changes to disk | [optional] [default to False]

### Return type

[**MapEntry**](MapEntry.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Map entry created |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **add_payload_runtime_map**
> List[MapEntry] add_payload_runtime_map(name, data, force_sync=force_sync)

Add a new map payload

Adds a new map payload.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.map_entry import MapEntry
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
    api_instance = haproxy_dataplane_v3.MapsApi(api_client)
    name = 'name_example' # str | Map file name
    data = [haproxy_dataplane_v3.MapEntry()] # List[MapEntry] | 
    force_sync = False # bool | If true, immediately syncs changes to disk (optional) (default to False)

    try:
        # Add a new map payload
        api_response = await api_instance.add_payload_runtime_map(name, data, force_sync=force_sync)
        print("The response of MapsApi->add_payload_runtime_map:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MapsApi->add_payload_runtime_map: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Map file name | 
 **data** | [**List[MapEntry]**](MapEntry.md)|  | 
 **force_sync** | **bool**| If true, immediately syncs changes to disk | [optional] [default to False]

### Return type

[**List[MapEntry]**](MapEntry.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Map payload added |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **clear_runtime_map**
> clear_runtime_map(name, force_delete=force_delete, force_sync=force_sync)

Remove all map entries from the map file

Remove all map entries from the map file.

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
    api_instance = haproxy_dataplane_v3.MapsApi(api_client)
    name = 'name_example' # str | Map file name
    force_delete = True # bool | If true, deletes file from disk (optional)
    force_sync = False # bool | If true, immediately syncs changes to disk (optional) (default to False)

    try:
        # Remove all map entries from the map file
        await api_instance.clear_runtime_map(name, force_delete=force_delete, force_sync=force_sync)
    except Exception as e:
        print("Exception when calling MapsApi->clear_runtime_map: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Map file name | 
 **force_delete** | **bool**| If true, deletes file from disk | [optional] 
 **force_sync** | **bool**| If true, immediately syncs changes to disk | [optional] [default to False]

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
**204** | All map entries deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_runtime_map_entry**
> delete_runtime_map_entry(id, parent_name, force_sync=force_sync)

Deletes all the map entries from the map by its id

Delete all the map entries from the map by its id.

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
    api_instance = haproxy_dataplane_v3.MapsApi(api_client)
    id = 'id_example' # str | Map id
    parent_name = 'parent_name_example' # str | Parent name
    force_sync = False # bool | If true, immediately syncs changes to disk (optional) (default to False)

    try:
        # Deletes all the map entries from the map by its id
        await api_instance.delete_runtime_map_entry(id, parent_name, force_sync=force_sync)
    except Exception as e:
        print("Exception when calling MapsApi->delete_runtime_map_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Map id | 
 **parent_name** | **str**| Parent name | 
 **force_sync** | **bool**| If true, immediately syncs changes to disk | [optional] [default to False]

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
**204** | Map key/value deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_runtime_map_files**
> List[Dict] get_all_runtime_map_files(include_unmanaged=include_unmanaged)

Return runtime map files

Returns runtime map files.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.dict import Dict
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
    api_instance = haproxy_dataplane_v3.MapsApi(api_client)
    include_unmanaged = False # bool | If true, also show unmanaged map files loaded in haproxy (optional) (default to False)

    try:
        # Return runtime map files
        api_response = await api_instance.get_all_runtime_map_files(include_unmanaged=include_unmanaged)
        print("The response of MapsApi->get_all_runtime_map_files:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MapsApi->get_all_runtime_map_files: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **include_unmanaged** | **bool**| If true, also show unmanaged map files loaded in haproxy | [optional] [default to False]

### Return type

**List[Dict]**

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

# **get_one_runtime_map**
> Dict get_one_runtime_map(name)

Return one runtime map file

Returns one runtime map file.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.dict import Dict
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
    api_instance = haproxy_dataplane_v3.MapsApi(api_client)
    name = 'name_example' # str | Map file name

    try:
        # Return one runtime map file
        api_response = await api_instance.get_one_runtime_map(name)
        print("The response of MapsApi->get_one_runtime_map:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MapsApi->get_one_runtime_map: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Map file name | 

### Return type

**Dict**

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

# **get_runtime_map_entry**
> MapEntry get_runtime_map_entry(id, parent_name)

Return one map runtime setting

Returns one map runtime setting by it's id.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.map_entry import MapEntry
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
    api_instance = haproxy_dataplane_v3.MapsApi(api_client)
    id = 'id_example' # str | Map id
    parent_name = 'parent_name_example' # str | Parent name

    try:
        # Return one map runtime setting
        api_response = await api_instance.get_runtime_map_entry(id, parent_name)
        print("The response of MapsApi->get_runtime_map_entry:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MapsApi->get_runtime_map_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Map id | 
 **parent_name** | **str**| Parent name | 

### Return type

[**MapEntry**](MapEntry.md)

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

# **replace_runtime_map_entry**
> MapEntry replace_runtime_map_entry(id, parent_name, data, force_sync=force_sync)

Replace the value corresponding to each id in a map

Replaces the value corresponding to each id in a map.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.map_entry import MapEntry
from haproxy_dataplane_v3.models.replace_runtime_map_entry_request import ReplaceRuntimeMapEntryRequest
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
    api_instance = haproxy_dataplane_v3.MapsApi(api_client)
    id = 'id_example' # str | Map id
    parent_name = 'parent_name_example' # str | Parent name
    data = haproxy_dataplane_v3.ReplaceRuntimeMapEntryRequest() # ReplaceRuntimeMapEntryRequest | 
    force_sync = False # bool | If true, immediately syncs changes to disk (optional) (default to False)

    try:
        # Replace the value corresponding to each id in a map
        api_response = await api_instance.replace_runtime_map_entry(id, parent_name, data, force_sync=force_sync)
        print("The response of MapsApi->replace_runtime_map_entry:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MapsApi->replace_runtime_map_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Map id | 
 **parent_name** | **str**| Parent name | 
 **data** | [**ReplaceRuntimeMapEntryRequest**](ReplaceRuntimeMapEntryRequest.md)|  | 
 **force_sync** | **bool**| If true, immediately syncs changes to disk | [optional] [default to False]

### Return type

[**MapEntry**](MapEntry.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Map value replaced |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **show_runtime_map**
> List[MapEntry] show_runtime_map(parent_name)

Return one map runtime entries

Returns an array of all entries in a given runtime map file.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.map_entry import MapEntry
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
    api_instance = haproxy_dataplane_v3.MapsApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name

    try:
        # Return one map runtime entries
        api_response = await api_instance.show_runtime_map(parent_name)
        print("The response of MapsApi->show_runtime_map:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MapsApi->show_runtime_map: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 

### Return type

[**List[MapEntry]**](MapEntry.md)

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

