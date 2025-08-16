# haproxy_dataplane_v3.StatsApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_stats**](StatsApi.md#get_stats) | **GET** /services/haproxy/stats/native | Gets stats


# **get_stats**
> NativeStats get_stats(type=type, name=name, parent=parent)

Gets stats

Getting stats from the HAProxy.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.native_stats import NativeStats
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
    api_instance = haproxy_dataplane_v3.StatsApi(api_client)
    type = 'type_example' # str | Object type to get stats for (one of frontend, backend, server) (optional)
    name = 'name_example' # str | Object name to get stats for (optional)
    parent = 'parent_example' # str | Object parent name to get stats for, in case the object is a server (optional)

    try:
        # Gets stats
        api_response = await api_instance.get_stats(type=type, name=name, parent=parent)
        print("The response of StatsApi->get_stats:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StatsApi->get_stats: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **type** | **str**| Object type to get stats for (one of frontend, backend, server) | [optional] 
 **name** | **str**| Object name to get stats for | [optional] 
 **parent** | **str**| Object parent name to get stats for, in case the object is a server | [optional] 

### Return type

[**NativeStats**](NativeStats.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**500** | Internal Server Error |  -  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

