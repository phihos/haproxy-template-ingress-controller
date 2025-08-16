# haproxy_dataplane_v3.DiscoveryApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_api_endpoints**](DiscoveryApi.md#get_api_endpoints) | **GET** / | Return list of root endpoints
[**get_configuration_endpoints**](DiscoveryApi.md#get_configuration_endpoints) | **GET** /services/haproxy/configuration | Return list of HAProxy advanced configuration endpoints
[**get_haproxy_endpoints**](DiscoveryApi.md#get_haproxy_endpoints) | **GET** /services/haproxy | Return list of HAProxy related endpoints
[**get_runtime_endpoints**](DiscoveryApi.md#get_runtime_endpoints) | **GET** /services/haproxy/runtime | Return list of HAProxy advanced runtime endpoints
[**get_services_endpoints**](DiscoveryApi.md#get_services_endpoints) | **GET** /services | Return list of service endpoints
[**get_spoe_endpoints**](DiscoveryApi.md#get_spoe_endpoints) | **GET** /services/haproxy/spoe | Return list of HAProxy SPOE endpoints
[**get_stats_endpoints**](DiscoveryApi.md#get_stats_endpoints) | **GET** /services/haproxy/stats | Return list of HAProxy stats endpoints
[**get_storage_endpoints**](DiscoveryApi.md#get_storage_endpoints) | **GET** /services/haproxy/storage | Return list of HAProxy storage endpoints


# **get_api_endpoints**
> List[Endpoint] get_api_endpoints()

Return list of root endpoints

Returns a list of root endpoints.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.endpoint import Endpoint
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
    api_instance = haproxy_dataplane_v3.DiscoveryApi(api_client)

    try:
        # Return list of root endpoints
        api_response = await api_instance.get_api_endpoints()
        print("The response of DiscoveryApi->get_api_endpoints:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DiscoveryApi->get_api_endpoints: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Endpoint]**](Endpoint.md)

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

# **get_configuration_endpoints**
> List[Endpoint] get_configuration_endpoints()

Return list of HAProxy advanced configuration endpoints

Returns a list of endpoints to be used for advanced configuration of HAProxy objects.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.endpoint import Endpoint
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
    api_instance = haproxy_dataplane_v3.DiscoveryApi(api_client)

    try:
        # Return list of HAProxy advanced configuration endpoints
        api_response = await api_instance.get_configuration_endpoints()
        print("The response of DiscoveryApi->get_configuration_endpoints:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DiscoveryApi->get_configuration_endpoints: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Endpoint]**](Endpoint.md)

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

# **get_haproxy_endpoints**
> List[Endpoint] get_haproxy_endpoints()

Return list of HAProxy related endpoints

Returns a list of HAProxy related endpoints.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.endpoint import Endpoint
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
    api_instance = haproxy_dataplane_v3.DiscoveryApi(api_client)

    try:
        # Return list of HAProxy related endpoints
        api_response = await api_instance.get_haproxy_endpoints()
        print("The response of DiscoveryApi->get_haproxy_endpoints:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DiscoveryApi->get_haproxy_endpoints: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Endpoint]**](Endpoint.md)

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

# **get_runtime_endpoints**
> List[Endpoint] get_runtime_endpoints()

Return list of HAProxy advanced runtime endpoints

Returns a list of endpoints to be used for advanced runtime settings of HAProxy objects.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.endpoint import Endpoint
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
    api_instance = haproxy_dataplane_v3.DiscoveryApi(api_client)

    try:
        # Return list of HAProxy advanced runtime endpoints
        api_response = await api_instance.get_runtime_endpoints()
        print("The response of DiscoveryApi->get_runtime_endpoints:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DiscoveryApi->get_runtime_endpoints: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Endpoint]**](Endpoint.md)

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

# **get_services_endpoints**
> List[Endpoint] get_services_endpoints()

Return list of service endpoints

Returns a list of API managed services endpoints.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.endpoint import Endpoint
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
    api_instance = haproxy_dataplane_v3.DiscoveryApi(api_client)

    try:
        # Return list of service endpoints
        api_response = await api_instance.get_services_endpoints()
        print("The response of DiscoveryApi->get_services_endpoints:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DiscoveryApi->get_services_endpoints: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Endpoint]**](Endpoint.md)

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

# **get_spoe_endpoints**
> List[Endpoint] get_spoe_endpoints()

Return list of HAProxy SPOE endpoints

Returns a list of endpoints to be used for SPOE settings of HAProxy.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.endpoint import Endpoint
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
    api_instance = haproxy_dataplane_v3.DiscoveryApi(api_client)

    try:
        # Return list of HAProxy SPOE endpoints
        api_response = await api_instance.get_spoe_endpoints()
        print("The response of DiscoveryApi->get_spoe_endpoints:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DiscoveryApi->get_spoe_endpoints: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Endpoint]**](Endpoint.md)

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

# **get_stats_endpoints**
> List[Endpoint] get_stats_endpoints()

Return list of HAProxy stats endpoints

Returns a list of HAProxy stats endpoints.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.endpoint import Endpoint
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
    api_instance = haproxy_dataplane_v3.DiscoveryApi(api_client)

    try:
        # Return list of HAProxy stats endpoints
        api_response = await api_instance.get_stats_endpoints()
        print("The response of DiscoveryApi->get_stats_endpoints:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DiscoveryApi->get_stats_endpoints: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Endpoint]**](Endpoint.md)

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

# **get_storage_endpoints**
> List[Endpoint] get_storage_endpoints()

Return list of HAProxy storage endpoints

Returns a list of endpoints that use HAProxy storage for persistency, e.g. maps, ssl certificates...

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.endpoint import Endpoint
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
    api_instance = haproxy_dataplane_v3.DiscoveryApi(api_client)

    try:
        # Return list of HAProxy storage endpoints
        api_response = await api_instance.get_storage_endpoints()
        print("The response of DiscoveryApi->get_storage_endpoints:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DiscoveryApi->get_storage_endpoints: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Endpoint]**](Endpoint.md)

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

