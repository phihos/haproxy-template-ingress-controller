# haproxy_dataplane_v3.ConfigurationApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_configuration_version**](ConfigurationApi.md#get_configuration_version) | **GET** /services/haproxy/configuration/version | Return a configuration version
[**get_ha_proxy_configuration**](ConfigurationApi.md#get_ha_proxy_configuration) | **GET** /services/haproxy/configuration/raw | Return HAProxy configuration
[**post_ha_proxy_configuration**](ConfigurationApi.md#post_ha_proxy_configuration) | **POST** /services/haproxy/configuration/raw | Push new haproxy configuration


# **get_configuration_version**
> int get_configuration_version(transaction_id=transaction_id)

Return a configuration version

Returns configuration version.

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
    api_instance = haproxy_dataplane_v3.ConfigurationApi(api_client)
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)

    try:
        # Return a configuration version
        api_response = await api_instance.get_configuration_version(transaction_id=transaction_id)
        print("The response of ConfigurationApi->get_configuration_version:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ConfigurationApi->get_configuration_version: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
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
**200** | Configuration version |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_ha_proxy_configuration**
> str get_ha_proxy_configuration(transaction_id=transaction_id, version=version)

Return HAProxy configuration

Returns HAProxy configuration file in plain text

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
    api_instance = haproxy_dataplane_v3.ConfigurationApi(api_client)
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)

    try:
        # Return HAProxy configuration
        api_response = await api_instance.get_ha_proxy_configuration(transaction_id=transaction_id, version=version)
        print("The response of ConfigurationApi->get_ha_proxy_configuration:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ConfigurationApi->get_ha_proxy_configuration: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 

### Return type

**str**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Operation successful |  * Cluster-Version - Cluster configuration version <br>  * Configuration-Version - Configuration file version <br>  * Configuration-Checksum - Configuration file md5 checksum <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_ha_proxy_configuration**
> str post_ha_proxy_configuration(data, skip_version=skip_version, skip_reload=skip_reload, only_validate=only_validate, x_runtime_actions=x_runtime_actions, version=version, force_reload=force_reload)

Push new haproxy configuration

Push a new haproxy configuration file in plain text

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
    api_instance = haproxy_dataplane_v3.ConfigurationApi(api_client)
    data = 'data_example' # str | 
    skip_version = False # bool | If set, no version check will be done and the pushed config will be enforced (optional) (default to False)
    skip_reload = False # bool | If set, no reload will be initiated and runtime actions from X-Runtime-Actions will be applied (optional) (default to False)
    only_validate = False # bool | If set, only validates configuration, without applying it (optional) (default to False)
    x_runtime_actions = 'x_runtime_actions_example' # str | List of Runtime API commands with parameters separated by ';' (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Push new haproxy configuration
        api_response = await api_instance.post_ha_proxy_configuration(data, skip_version=skip_version, skip_reload=skip_reload, only_validate=only_validate, x_runtime_actions=x_runtime_actions, version=version, force_reload=force_reload)
        print("The response of ConfigurationApi->post_ha_proxy_configuration:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ConfigurationApi->post_ha_proxy_configuration: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **data** | **str**|  | 
 **skip_version** | **bool**| If set, no version check will be done and the pushed config will be enforced | [optional] [default to False]
 **skip_reload** | **bool**| If set, no reload will be initiated and runtime actions from X-Runtime-Actions will be applied | [optional] [default to False]
 **only_validate** | **bool**| If set, only validates configuration, without applying it | [optional] [default to False]
 **x_runtime_actions** | **str**| List of Runtime API commands with parameters separated by &#39;;&#39; | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

**str**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: text/plain
 - **Accept**: text/plain

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | New HAProxy configuration pushed |  * Cluster-Version - Cluster configuration version <br>  * Configuration-Version - Configuration file version <br>  * Configuration-Checksum - Configuration file md5 checksum <br>  |
**202** | Configuration change accepted and reload requested |  * Cluster-Version - Cluster configuration version <br>  * Configuration-Version - Configuration file version <br>  * Configuration-Checksum - Configuration file md5 checksum <br>  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

