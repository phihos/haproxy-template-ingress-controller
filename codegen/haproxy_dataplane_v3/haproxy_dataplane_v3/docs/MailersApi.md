# haproxy_dataplane_v3.MailersApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_mailers_section**](MailersApi.md#create_mailers_section) | **POST** /services/haproxy/configuration/mailers_section | Add a new Mailers section
[**delete_mailers_section**](MailersApi.md#delete_mailers_section) | **DELETE** /services/haproxy/configuration/mailers_section/{name} | Delete a Mailers section
[**edit_mailers_section**](MailersApi.md#edit_mailers_section) | **PUT** /services/haproxy/configuration/mailers_section/{name} | Modify a Mailers section
[**get_mailers_section**](MailersApi.md#get_mailers_section) | **GET** /services/haproxy/configuration/mailers_section/{name} | Return a Mailers section
[**get_mailers_sections**](MailersApi.md#get_mailers_sections) | **GET** /services/haproxy/configuration/mailers_section | Return an array of mailers sections


# **create_mailers_section**
> MailersSection create_mailers_section(data, transaction_id=transaction_id, version=version, force_reload=force_reload, full_section=full_section)

Add a new Mailers section

Creates a new empty Mailers section

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.mailers_section import MailersSection
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
    api_instance = haproxy_dataplane_v3.MailersApi(api_client)
    data = haproxy_dataplane_v3.MailersSection() # MailersSection | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)
    full_section = False # bool | Indicates if the action affects the specified child resources as well (optional) (default to False)

    try:
        # Add a new Mailers section
        api_response = await api_instance.create_mailers_section(data, transaction_id=transaction_id, version=version, force_reload=force_reload, full_section=full_section)
        print("The response of MailersApi->create_mailers_section:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MailersApi->create_mailers_section: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **data** | [**MailersSection**](MailersSection.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]
 **full_section** | **bool**| Indicates if the action affects the specified child resources as well | [optional] [default to False]

### Return type

[**MailersSection**](MailersSection.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Mailers created |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_mailers_section**
> delete_mailers_section(name, transaction_id=transaction_id, version=version, force_reload=force_reload)

Delete a Mailers section

Deletes a mailers from the configuration by it's name.

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
    api_instance = haproxy_dataplane_v3.MailersApi(api_client)
    name = 'name_example' # str | Mailers name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Delete a Mailers section
        await api_instance.delete_mailers_section(name, transaction_id=transaction_id, version=version, force_reload=force_reload)
    except Exception as e:
        print("Exception when calling MailersApi->delete_mailers_section: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Mailers name | 
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
**204** | Mailers deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_mailers_section**
> MailersSection edit_mailers_section(name, data, transaction_id=transaction_id, version=version, force_reload=force_reload, full_section=full_section)

Modify a Mailers section

Modifies a mailers configuration by it's name.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.mailers_section import MailersSection
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
    api_instance = haproxy_dataplane_v3.MailersApi(api_client)
    name = 'name_example' # str | Mailers name
    data = haproxy_dataplane_v3.MailersSection() # MailersSection | 
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    version = 56 # int | Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it's own version. (optional)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)
    full_section = False # bool | Indicates if the action affects the specified child resources as well (optional) (default to False)

    try:
        # Modify a Mailers section
        api_response = await api_instance.edit_mailers_section(name, data, transaction_id=transaction_id, version=version, force_reload=force_reload, full_section=full_section)
        print("The response of MailersApi->edit_mailers_section:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MailersApi->edit_mailers_section: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Mailers name | 
 **data** | [**MailersSection**](MailersSection.md)|  | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **version** | **int**| Version used for checking configuration version. Cannot be used when transaction is specified, transaction has it&#39;s own version. | [optional] 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]
 **full_section** | **bool**| Indicates if the action affects the specified child resources as well | [optional] [default to False]

### Return type

[**MailersSection**](MailersSection.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Mailers configuration updated |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_mailers_section**
> MailersSection get_mailers_section(name, transaction_id=transaction_id, full_section=full_section)

Return a Mailers section

Returns one mailers configuration by it's name.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.mailers_section import MailersSection
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
    api_instance = haproxy_dataplane_v3.MailersApi(api_client)
    name = 'name_example' # str | Mailers name
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    full_section = False # bool | Indicates if the action affects the specified child resources as well (optional) (default to False)

    try:
        # Return a Mailers section
        api_response = await api_instance.get_mailers_section(name, transaction_id=transaction_id, full_section=full_section)
        print("The response of MailersApi->get_mailers_section:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MailersApi->get_mailers_section: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Mailers name | 
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **full_section** | **bool**| Indicates if the action affects the specified child resources as well | [optional] [default to False]

### Return type

[**MailersSection**](MailersSection.md)

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

# **get_mailers_sections**
> List[MailersSection] get_mailers_sections(transaction_id=transaction_id, full_section=full_section)

Return an array of mailers sections

Returns an array of all the configured mailers in HAProxy

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.mailers_section import MailersSection
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
    api_instance = haproxy_dataplane_v3.MailersApi(api_client)
    transaction_id = 'transaction_id_example' # str | ID of the transaction where we want to add the operation. Cannot be used when version is specified. (optional)
    full_section = False # bool | Indicates if the action affects the specified child resources as well (optional) (default to False)

    try:
        # Return an array of mailers sections
        api_response = await api_instance.get_mailers_sections(transaction_id=transaction_id, full_section=full_section)
        print("The response of MailersApi->get_mailers_sections:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling MailersApi->get_mailers_sections: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **transaction_id** | **str**| ID of the transaction where we want to add the operation. Cannot be used when version is specified. | [optional] 
 **full_section** | **bool**| Indicates if the action affects the specified child resources as well | [optional] [default to False]

### Return type

[**List[MailersSection]**](MailersSection.md)

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

