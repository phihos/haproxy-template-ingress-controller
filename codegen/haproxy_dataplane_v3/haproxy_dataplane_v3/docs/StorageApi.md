# haproxy_dataplane_v3.StorageApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_storage_general_file**](StorageApi.md#create_storage_general_file) | **POST** /services/haproxy/storage/general | Creates a managed storage general use file with contents
[**create_storage_map_file**](StorageApi.md#create_storage_map_file) | **POST** /services/haproxy/storage/maps | Creates a managed storage map file with its entries
[**create_storage_ssl_certificate**](StorageApi.md#create_storage_ssl_certificate) | **POST** /services/haproxy/storage/ssl_certificates | Create SSL certificate
[**create_storage_ssl_crt_list_entry**](StorageApi.md#create_storage_ssl_crt_list_entry) | **POST** /services/haproxy/storage/ssl_crt_lists/{name}/entries | Creates a new entry in a CrtList
[**create_storage_ssl_crt_list_file**](StorageApi.md#create_storage_ssl_crt_list_file) | **POST** /services/haproxy/storage/ssl_crt_lists | Create a certificate list
[**delete_storage_general_file**](StorageApi.md#delete_storage_general_file) | **DELETE** /services/haproxy/storage/general/{name} | Deletes a managed general use file from disk
[**delete_storage_map**](StorageApi.md#delete_storage_map) | **DELETE** /services/haproxy/storage/maps/{name} | Deletes a managed map file from disk
[**delete_storage_ssl_certificate**](StorageApi.md#delete_storage_ssl_certificate) | **DELETE** /services/haproxy/storage/ssl_certificates/{name} | Delete SSL certificate from disk
[**delete_storage_ssl_crt_list_entry**](StorageApi.md#delete_storage_ssl_crt_list_entry) | **DELETE** /services/haproxy/storage/ssl_crt_lists/{name}/entries | Deletes an entry from CrtList file
[**delete_storage_ssl_crt_list_file**](StorageApi.md#delete_storage_ssl_crt_list_file) | **DELETE** /services/haproxy/storage/ssl_crt_lists/{name} | Delete a certificate list from disk
[**get_all_storage_general_files**](StorageApi.md#get_all_storage_general_files) | **GET** /services/haproxy/storage/general | Return a list of all managed general use files
[**get_all_storage_map_files**](StorageApi.md#get_all_storage_map_files) | **GET** /services/haproxy/storage/maps | Return a list of all managed map files
[**get_all_storage_ssl_certificates**](StorageApi.md#get_all_storage_ssl_certificates) | **GET** /services/haproxy/storage/ssl_certificates | Return all available SSL certificates on disk
[**get_all_storage_ssl_crt_list_files**](StorageApi.md#get_all_storage_ssl_crt_list_files) | **GET** /services/haproxy/storage/ssl_crt_lists | Return all available certificate lists on disk
[**get_one_storage_general_file**](StorageApi.md#get_one_storage_general_file) | **GET** /services/haproxy/storage/general/{name} | Return the contents of one managed general use file from disk
[**get_one_storage_map**](StorageApi.md#get_one_storage_map) | **GET** /services/haproxy/storage/maps/{name} | Return the contents of one managed map file from disk
[**get_one_storage_ssl_certificate**](StorageApi.md#get_one_storage_ssl_certificate) | **GET** /services/haproxy/storage/ssl_certificates/{name} | Return one SSL certificate from disk
[**get_one_storage_ssl_crt_list_file**](StorageApi.md#get_one_storage_ssl_crt_list_file) | **GET** /services/haproxy/storage/ssl_crt_lists/{name} | Return one certificate list from disk
[**get_storage_ssl_crt_list_entries**](StorageApi.md#get_storage_ssl_crt_list_entries) | **GET** /services/haproxy/storage/ssl_crt_lists/{name}/entries | Returns all the entries in a CrtList
[**replace_storage_general_file**](StorageApi.md#replace_storage_general_file) | **PUT** /services/haproxy/storage/general/{name} | Replace contents of a managed general use file on disk
[**replace_storage_map_file**](StorageApi.md#replace_storage_map_file) | **PUT** /services/haproxy/storage/maps/{name} | Replace contents of a managed map file on disk
[**replace_storage_ssl_certificate**](StorageApi.md#replace_storage_ssl_certificate) | **PUT** /services/haproxy/storage/ssl_certificates/{name} | Replace SSL certificates on disk
[**replace_storage_ssl_crt_list_file**](StorageApi.md#replace_storage_ssl_crt_list_file) | **PUT** /services/haproxy/storage/ssl_crt_lists/{name} | Replace a certificate lists on disk


# **create_storage_general_file**
> GeneralFile create_storage_general_file(file_upload=file_upload)

Creates a managed storage general use file with contents

Creates a managed storage general use file with contents.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.general_file import GeneralFile
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    file_upload = None # bytearray | General use file content (optional)

    try:
        # Creates a managed storage general use file with contents
        api_response = await api_instance.create_storage_general_file(file_upload=file_upload)
        print("The response of StorageApi->create_storage_general_file:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->create_storage_general_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file_upload** | **bytearray**| General use file content | [optional] 

### Return type

[**GeneralFile**](GeneralFile.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | General use file created with its contents |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_storage_map_file**
> Dict create_storage_map_file(file_upload=file_upload)

Creates a managed storage map file with its entries

Creates a managed storage map file with its entries.

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    file_upload = None # bytearray | The map file contents (optional)

    try:
        # Creates a managed storage map file with its entries
        api_response = await api_instance.create_storage_map_file(file_upload=file_upload)
        print("The response of StorageApi->create_storage_map_file:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->create_storage_map_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file_upload** | **bytearray**| The map file contents | [optional] 

### Return type

**Dict**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Map file created with its entries |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_storage_ssl_certificate**
> SslCertificate create_storage_ssl_certificate(skip_reload=skip_reload, force_reload=force_reload, file_upload=file_upload)

Create SSL certificate

Creates SSL certificate.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_certificate import SslCertificate
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    skip_reload = False # bool | If set, no reload will be initiated after update (optional) (default to False)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)
    file_upload = None # bytearray | The SSL certificate to upload (optional)

    try:
        # Create SSL certificate
        api_response = await api_instance.create_storage_ssl_certificate(skip_reload=skip_reload, force_reload=force_reload, file_upload=file_upload)
        print("The response of StorageApi->create_storage_ssl_certificate:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->create_storage_ssl_certificate: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **skip_reload** | **bool**| If set, no reload will be initiated after update | [optional] [default to False]
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]
 **file_upload** | **bytearray**| The SSL certificate to upload | [optional] 

### Return type

[**SslCertificate**](SslCertificate.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | SSL certificate created |  -  |
**202** | SSL certificate created requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_storage_ssl_crt_list_entry**
> SslCrtListEntry create_storage_ssl_crt_list_entry(name, data, force_reload=force_reload)

Creates a new entry in a CrtList

Creates a new entry in a certificate list.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_crt_list_entry import SslCrtListEntry
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | SSL crt-list file
    data = haproxy_dataplane_v3.SslCrtListEntry() # SslCrtListEntry | SSL crt-list entry
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Creates a new entry in a CrtList
        api_response = await api_instance.create_storage_ssl_crt_list_entry(name, data, force_reload=force_reload)
        print("The response of StorageApi->create_storage_ssl_crt_list_entry:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->create_storage_ssl_crt_list_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL crt-list file | 
 **data** | [**SslCrtListEntry**](SslCrtListEntry.md)| SSL crt-list entry | 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**SslCrtListEntry**](SslCrtListEntry.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | New entry added |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_storage_ssl_crt_list_file**
> SslCrtListFile create_storage_ssl_crt_list_file(force_reload=force_reload, file_upload=file_upload)

Create a certificate list

Creates a certificate list.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_crt_list_file import SslCrtListFile
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)
    file_upload = None # bytearray | The certificate list to upload (optional)

    try:
        # Create a certificate list
        api_response = await api_instance.create_storage_ssl_crt_list_file(force_reload=force_reload, file_upload=file_upload)
        print("The response of StorageApi->create_storage_ssl_crt_list_file:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->create_storage_ssl_crt_list_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]
 **file_upload** | **bytearray**| The certificate list to upload | [optional] 

### Return type

[**SslCrtListFile**](SslCrtListFile.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Certificate list created |  -  |
**202** | Certificate list created requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_storage_general_file**
> delete_storage_general_file(name)

Deletes a managed general use file from disk

Deletes a managed general use file from disk.

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | General use file storage_name

    try:
        # Deletes a managed general use file from disk
        await api_instance.delete_storage_general_file(name)
    except Exception as e:
        print("Exception when calling StorageApi->delete_storage_general_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| General use file storage_name | 

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
**204** | General use file deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_storage_map**
> delete_storage_map(name)

Deletes a managed map file from disk

Deletes a managed map file from disk.

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | Map file storage_name

    try:
        # Deletes a managed map file from disk
        await api_instance.delete_storage_map(name)
    except Exception as e:
        print("Exception when calling StorageApi->delete_storage_map: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Map file storage_name | 

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
**204** | Map file deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_storage_ssl_certificate**
> delete_storage_ssl_certificate(name, skip_reload=skip_reload, force_reload=force_reload)

Delete SSL certificate from disk

Deletes SSL certificate from disk.

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | SSL certificate name
    skip_reload = False # bool | If set, no reload will be initiated after update (optional) (default to False)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Delete SSL certificate from disk
        await api_instance.delete_storage_ssl_certificate(name, skip_reload=skip_reload, force_reload=force_reload)
    except Exception as e:
        print("Exception when calling StorageApi->delete_storage_ssl_certificate: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL certificate name | 
 **skip_reload** | **bool**| If set, no reload will be initiated after update | [optional] [default to False]
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
**202** | SSL certificate deleted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**204** | SSL certificate deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_storage_ssl_crt_list_entry**
> delete_storage_ssl_crt_list_entry(name, certificate, line_number, force_reload=force_reload)

Deletes an entry from CrtList file

Deletes an entry from a certificate list.

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | SSL crt list name
    certificate = 'certificate_example' # str | SSL certificate filename
    line_number = 56 # int | The line number in the crt-list
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Deletes an entry from CrtList file
        await api_instance.delete_storage_ssl_crt_list_entry(name, certificate, line_number, force_reload=force_reload)
    except Exception as e:
        print("Exception when calling StorageApi->delete_storage_ssl_crt_list_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL crt list name | 
 **certificate** | **str**| SSL certificate filename | 
 **line_number** | **int**| The line number in the crt-list | 
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
**204** | Successful operation |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_storage_ssl_crt_list_file**
> delete_storage_ssl_crt_list_file(name, skip_reload=skip_reload, force_reload=force_reload)

Delete a certificate list from disk

Deletes a certificate list from disk.

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | Certificate list name
    skip_reload = False # bool | If set, no reload will be initiated after update (optional) (default to False)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Delete a certificate list from disk
        await api_instance.delete_storage_ssl_crt_list_file(name, skip_reload=skip_reload, force_reload=force_reload)
    except Exception as e:
        print("Exception when calling StorageApi->delete_storage_ssl_crt_list_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Certificate list name | 
 **skip_reload** | **bool**| If set, no reload will be initiated after update | [optional] [default to False]
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
**202** | Certificate list deleted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**204** | Certificate list deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_storage_general_files**
> List[GeneralFile] get_all_storage_general_files()

Return a list of all managed general use files

Returns a list of all managed general use files

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.general_file import GeneralFile
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)

    try:
        # Return a list of all managed general use files
        api_response = await api_instance.get_all_storage_general_files()
        print("The response of StorageApi->get_all_storage_general_files:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_all_storage_general_files: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[GeneralFile]**](GeneralFile.md)

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

# **get_all_storage_map_files**
> List[Dict] get_all_storage_map_files()

Return a list of all managed map files

Returns a list of all managed map files

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)

    try:
        # Return a list of all managed map files
        api_response = await api_instance.get_all_storage_map_files()
        print("The response of StorageApi->get_all_storage_map_files:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_all_storage_map_files: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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

# **get_all_storage_ssl_certificates**
> List[SslCertificate] get_all_storage_ssl_certificates()

Return all available SSL certificates on disk

Returns all available SSL certificates on disk.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_certificate import SslCertificate
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)

    try:
        # Return all available SSL certificates on disk
        api_response = await api_instance.get_all_storage_ssl_certificates()
        print("The response of StorageApi->get_all_storage_ssl_certificates:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_all_storage_ssl_certificates: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[SslCertificate]**](SslCertificate.md)

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

# **get_all_storage_ssl_crt_list_files**
> List[SslCrtListFile] get_all_storage_ssl_crt_list_files()

Return all available certificate lists on disk

Returns all available certificate lists on disk.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_crt_list_file import SslCrtListFile
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)

    try:
        # Return all available certificate lists on disk
        api_response = await api_instance.get_all_storage_ssl_crt_list_files()
        print("The response of StorageApi->get_all_storage_ssl_crt_list_files:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_all_storage_ssl_crt_list_files: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[SslCrtListFile]**](SslCrtListFile.md)

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

# **get_one_storage_general_file**
> bytearray get_one_storage_general_file(name)

Return the contents of one managed general use file from disk

Returns the contents of one managed general use file from disk

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | General use file storage_name

    try:
        # Return the contents of one managed general use file from disk
        api_response = await api_instance.get_one_storage_general_file(name)
        print("The response of StorageApi->get_one_storage_general_file:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_one_storage_general_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| General use file storage_name | 

### Return type

**bytearray**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/octet-stream

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful operation |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_one_storage_map**
> bytearray get_one_storage_map(name)

Return the contents of one managed map file from disk

Returns the contents of one managed map file from disk

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | Map file storage_name

    try:
        # Return the contents of one managed map file from disk
        api_response = await api_instance.get_one_storage_map(name)
        print("The response of StorageApi->get_one_storage_map:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_one_storage_map: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Map file storage_name | 

### Return type

**bytearray**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/octet-stream

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful operation |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_one_storage_ssl_certificate**
> SslCertificate get_one_storage_ssl_certificate(name)

Return one SSL certificate from disk

Returns one SSL certificate from disk.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_certificate import SslCertificate
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | SSL certificate name

    try:
        # Return one SSL certificate from disk
        api_response = await api_instance.get_one_storage_ssl_certificate(name)
        print("The response of StorageApi->get_one_storage_ssl_certificate:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_one_storage_ssl_certificate: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL certificate name | 

### Return type

[**SslCertificate**](SslCertificate.md)

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

# **get_one_storage_ssl_crt_list_file**
> bytearray get_one_storage_ssl_crt_list_file(name)

Return one certificate list from disk

Returns one certificate list from disk.

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | Certificate list name

    try:
        # Return one certificate list from disk
        api_response = await api_instance.get_one_storage_ssl_crt_list_file(name)
        print("The response of StorageApi->get_one_storage_ssl_crt_list_file:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_one_storage_ssl_crt_list_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Certificate list name | 

### Return type

**bytearray**

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/octet-stream

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful operation |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_storage_ssl_crt_list_entries**
> List[SslCrtListEntry] get_storage_ssl_crt_list_entries(name)

Returns all the entries in a CrtList

Returns all the entries in a certificate list.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_crt_list_entry import SslCrtListEntry
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | SSL crt-list file

    try:
        # Returns all the entries in a CrtList
        api_response = await api_instance.get_storage_ssl_crt_list_entries(name)
        print("The response of StorageApi->get_storage_ssl_crt_list_entries:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->get_storage_ssl_crt_list_entries: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL crt-list file | 

### Return type

[**List[SslCrtListEntry]**](SslCrtListEntry.md)

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

# **replace_storage_general_file**
> replace_storage_general_file(name, skip_reload=skip_reload, force_reload=force_reload, file_upload=file_upload)

Replace contents of a managed general use file on disk

Replaces the contents of a managed general use file on disk

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | General use file storage_name
    skip_reload = False # bool | If set, no reload will be initiated after update (optional) (default to False)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)
    file_upload = None # bytearray | General use file content (optional)

    try:
        # Replace contents of a managed general use file on disk
        await api_instance.replace_storage_general_file(name, skip_reload=skip_reload, force_reload=force_reload, file_upload=file_upload)
    except Exception as e:
        print("Exception when calling StorageApi->replace_storage_general_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| General use file storage_name | 
 **skip_reload** | **bool**| If set, no reload will be initiated after update | [optional] [default to False]
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]
 **file_upload** | **bytearray**| General use file content | [optional] 

### Return type

void (empty response body)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**204** | General use file replaced |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_storage_map_file**
> replace_storage_map_file(name, data, skip_reload=skip_reload, force_reload=force_reload)

Replace contents of a managed map file on disk

Replaces the contents of a managed map file on disk

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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | Map file storage_name
    data = 'data_example' # str | 
    skip_reload = False # bool | If set, no reload will be initiated after update (optional) (default to False)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Replace contents of a managed map file on disk
        await api_instance.replace_storage_map_file(name, data, skip_reload=skip_reload, force_reload=force_reload)
    except Exception as e:
        print("Exception when calling StorageApi->replace_storage_map_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Map file storage_name | 
 **data** | **str**|  | 
 **skip_reload** | **bool**| If set, no reload will be initiated after update | [optional] [default to False]
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

void (empty response body)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: text/plain
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**204** | Map file replaced |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_storage_ssl_certificate**
> SslCertificate replace_storage_ssl_certificate(name, data, skip_reload=skip_reload, force_reload=force_reload)

Replace SSL certificates on disk

Replaces SSL certificate on disk.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_certificate import SslCertificate
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | SSL certificate name
    data = 'data_example' # str | 
    skip_reload = False # bool | If set, no reload will be initiated after update (optional) (default to False)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Replace SSL certificates on disk
        api_response = await api_instance.replace_storage_ssl_certificate(name, data, skip_reload=skip_reload, force_reload=force_reload)
        print("The response of StorageApi->replace_storage_ssl_certificate:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->replace_storage_ssl_certificate: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL certificate name | 
 **data** | **str**|  | 
 **skip_reload** | **bool**| If set, no reload will be initiated after update | [optional] [default to False]
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**SslCertificate**](SslCertificate.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: text/plain
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | SSL certificate replaced |  -  |
**202** | SSL certificate replaced and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_storage_ssl_crt_list_file**
> SslCrtListFile replace_storage_ssl_crt_list_file(name, data, skip_reload=skip_reload, force_reload=force_reload)

Replace a certificate lists on disk

Replaces a certificate list on disk.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_crt_list_file import SslCrtListFile
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
    api_instance = haproxy_dataplane_v3.StorageApi(api_client)
    name = 'name_example' # str | Certificate list name
    data = 'data_example' # str | 
    skip_reload = False # bool | If set, no reload will be initiated after update (optional) (default to False)
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Replace a certificate lists on disk
        api_response = await api_instance.replace_storage_ssl_crt_list_file(name, data, skip_reload=skip_reload, force_reload=force_reload)
        print("The response of StorageApi->replace_storage_ssl_crt_list_file:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StorageApi->replace_storage_ssl_crt_list_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| Certificate list name | 
 **data** | **str**|  | 
 **skip_reload** | **bool**| If set, no reload will be initiated after update | [optional] [default to False]
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**SslCrtListFile**](SslCrtListFile.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: text/plain
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Certificate list replaced |  -  |
**202** | Certificate list replaced and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

