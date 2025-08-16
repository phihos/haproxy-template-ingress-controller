# haproxy_dataplane_v3.InformationApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_haproxy_process_info**](InformationApi.md#get_haproxy_process_info) | **GET** /services/haproxy/runtime/info | Return HAProxy process information
[**get_info**](InformationApi.md#get_info) | **GET** /info | Return API, hardware and OS information


# **get_haproxy_process_info**
> ProcessInfo get_haproxy_process_info()

Return HAProxy process information

Return HAProxy process information

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.process_info import ProcessInfo
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
    api_instance = haproxy_dataplane_v3.InformationApi(api_client)

    try:
        # Return HAProxy process information
        api_response = await api_instance.get_haproxy_process_info()
        print("The response of InformationApi->get_haproxy_process_info:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling InformationApi->get_haproxy_process_info: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**ProcessInfo**](ProcessInfo.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_info**
> Info get_info()

Return API, hardware and OS information

Return API, hardware and OS information

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.info import Info
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
    api_instance = haproxy_dataplane_v3.InformationApi(api_client)

    try:
        # Return API, hardware and OS information
        api_response = await api_instance.get_info()
        print("The response of InformationApi->get_info:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling InformationApi->get_info: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**Info**](Info.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

