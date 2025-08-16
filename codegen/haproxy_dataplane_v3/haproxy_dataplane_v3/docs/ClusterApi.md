# haproxy_dataplane_v3.ClusterApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**delete_cluster**](ClusterApi.md#delete_cluster) | **DELETE** /cluster | Delete cluster settings
[**edit_cluster**](ClusterApi.md#edit_cluster) | **PUT** /cluster | Edit cluster settings
[**get_cluster**](ClusterApi.md#get_cluster) | **GET** /cluster | Return cluster data
[**initiate_certificate_refresh**](ClusterApi.md#initiate_certificate_refresh) | **POST** /cluster/certificate | Initiates a certificate refresh
[**post_cluster**](ClusterApi.md#post_cluster) | **POST** /cluster | Post cluster settings


# **delete_cluster**
> delete_cluster(configuration=configuration, version=version)

Delete cluster settings

Delete cluster settings and move the node back to single mode

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
    api_instance = haproxy_dataplane_v3.ClusterApi(api_client)
    configuration = 'configuration_example' # str | In case of moving to single mode do we keep or clean configuration (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Delete cluster settings
        await api_instance.delete_cluster(configuration=configuration, version=version)
    except Exception as e:
        print("Exception when calling ClusterApi->delete_cluster: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **configuration** | **str**| In case of moving to single mode do we keep or clean configuration | [optional] 
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
**204** | Cluster settings deleted and node moved to single mode |  -  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_cluster**
> ClusterSettings edit_cluster(data, version=version)

Edit cluster settings

Edit cluster settings

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.cluster_settings import ClusterSettings
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
    api_instance = haproxy_dataplane_v3.ClusterApi(api_client)
    data = haproxy_dataplane_v3.ClusterSettings() # ClusterSettings | 
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Edit cluster settings
        api_response = await api_instance.edit_cluster(data, version=version)
        print("The response of ClusterApi->edit_cluster:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ClusterApi->edit_cluster: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **data** | [**ClusterSettings**](ClusterSettings.md)|  | 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

[**ClusterSettings**](ClusterSettings.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Cluster settings changed |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_cluster**
> ClusterSettings get_cluster()

Return cluster data

Returns cluster data

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.cluster_settings import ClusterSettings
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
    api_instance = haproxy_dataplane_v3.ClusterApi(api_client)

    try:
        # Return cluster data
        api_response = await api_instance.get_cluster()
        print("The response of ClusterApi->get_cluster:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ClusterApi->get_cluster: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**ClusterSettings**](ClusterSettings.md)

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

# **initiate_certificate_refresh**
> initiate_certificate_refresh()

Initiates a certificate refresh

Initiates a certificate refresh

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
    api_instance = haproxy_dataplane_v3.ClusterApi(api_client)

    try:
        # Initiates a certificate refresh
        await api_instance.initiate_certificate_refresh()
    except Exception as e:
        print("Exception when calling ClusterApi->initiate_certificate_refresh: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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
**200** | refresh activated |  -  |
**403** | refresh not possible |  -  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_cluster**
> ClusterSettings post_cluster(data, configuration=configuration, advertised_address=advertised_address, advertised_port=advertised_port, version=version)

Post cluster settings

Post cluster settings

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.cluster_settings import ClusterSettings
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
    api_instance = haproxy_dataplane_v3.ClusterApi(api_client)
    data = haproxy_dataplane_v3.ClusterSettings() # ClusterSettings | 
    configuration = 'configuration_example' # str | In case of moving to single mode do we keep or clean configuration (optional)
    advertised_address = 'advertised_address_example' # str | Force the advertised address when joining a cluster (optional)
    advertised_port = 56 # int | Force the advertised port when joining a cluster (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Post cluster settings
        api_response = await api_instance.post_cluster(data, configuration=configuration, advertised_address=advertised_address, advertised_port=advertised_port, version=version)
        print("The response of ClusterApi->post_cluster:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ClusterApi->post_cluster: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **data** | [**ClusterSettings**](ClusterSettings.md)|  | 
 **configuration** | **str**| In case of moving to single mode do we keep or clean configuration | [optional] 
 **advertised_address** | **str**| Force the advertised address when joining a cluster | [optional] 
 **advertised_port** | **int**| Force the advertised port when joining a cluster | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

[**ClusterSettings**](ClusterSettings.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Cluster settings changed |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

