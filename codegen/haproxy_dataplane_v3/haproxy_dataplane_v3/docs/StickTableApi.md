# haproxy_dataplane_v3.StickTableApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_stick_table**](StickTableApi.md#get_stick_table) | **GET** /services/haproxy/runtime/stick_tables/{name} | Return Stick Table
[**get_stick_table_entries**](StickTableApi.md#get_stick_table_entries) | **GET** /services/haproxy/runtime/stick_tables/{parent_name}/entries | Return Stick Table Entries
[**get_stick_tables**](StickTableApi.md#get_stick_tables) | **GET** /services/haproxy/runtime/stick_tables | Return Stick Tables
[**set_stick_table_entries**](StickTableApi.md#set_stick_table_entries) | **POST** /services/haproxy/runtime/stick_tables/{parent_name}/entries | Set Entry to Stick Table


# **get_stick_table**
> StickTable get_stick_table(name)

Return Stick Table

Returns one stick table from runtime.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.stick_table import StickTable
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
    api_instance = haproxy_dataplane_v3.StickTableApi(api_client)
    name = 'name_example' # str | Stick table name

    try:
        # Return Stick Table
        api_response = await api_instance.get_stick_table(name)
        print("The response of StickTableApi->get_stick_table:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StickTableApi->get_stick_table: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Stick table name | 

### Return type

[**StickTable**](StickTable.md)

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

# **get_stick_table_entries**
> List[StickTableEntry] get_stick_table_entries(parent_name, filter=filter, key=key, count=count, offset=offset)

Return Stick Table Entries

Returns an array of all entries in a given stick tables.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.stick_table_entry import StickTableEntry
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
    api_instance = haproxy_dataplane_v3.StickTableApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    filter = 'filter_example' # str | A list of filters in format data.<type> <operator> <value> separated by comma (optional)
    key = 'key_example' # str | Key which we want the entries for (optional)
    count = 56 # int | Max number of entries to be returned for pagination (optional)
    offset = 56 # int | Offset which indicates how many items we skip in pagination (optional)

    try:
        # Return Stick Table Entries
        api_response = await api_instance.get_stick_table_entries(parent_name, filter=filter, key=key, count=count, offset=offset)
        print("The response of StickTableApi->get_stick_table_entries:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StickTableApi->get_stick_table_entries: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **filter** | **str**| A list of filters in format data.&lt;type&gt; &lt;operator&gt; &lt;value&gt; separated by comma | [optional] 
 **key** | **str**| Key which we want the entries for | [optional] 
 **count** | **int**| Max number of entries to be returned for pagination | [optional] 
 **offset** | **int**| Offset which indicates how many items we skip in pagination | [optional] 

### Return type

[**List[StickTableEntry]**](StickTableEntry.md)

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

# **get_stick_tables**
> List[StickTable] get_stick_tables()

Return Stick Tables

Returns an array of all stick tables.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.stick_table import StickTable
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
    api_instance = haproxy_dataplane_v3.StickTableApi(api_client)

    try:
        # Return Stick Tables
        api_response = await api_instance.get_stick_tables()
        print("The response of StickTableApi->get_stick_tables:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StickTableApi->get_stick_tables: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[StickTable]**](StickTable.md)

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

# **set_stick_table_entries**
> set_stick_table_entries(parent_name, stick_table_entry=stick_table_entry)

Set Entry to Stick Table

Create or update a stick-table entry in the table.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.set_stick_table_entries_request import SetStickTableEntriesRequest
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
    api_instance = haproxy_dataplane_v3.StickTableApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    stick_table_entry = haproxy_dataplane_v3.SetStickTableEntriesRequest() # SetStickTableEntriesRequest | Stick table entry (optional)

    try:
        # Set Entry to Stick Table
        await api_instance.set_stick_table_entries(parent_name, stick_table_entry=stick_table_entry)
    except Exception as e:
        print("Exception when calling StickTableApi->set_stick_table_entries: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **stick_table_entry** | [**SetStickTableEntriesRequest**](SetStickTableEntriesRequest.md)| Stick table entry | [optional] 

### Return type

void (empty response body)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Successful operation |  -  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

