# haproxy_dataplane_v3.SSLRuntimeApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_ca_entry**](SSLRuntimeApi.md#add_ca_entry) | **POST** /services/haproxy/runtime/ssl_ca_files/{name}/entries | Add a certificate to a CA file
[**add_crt_list_entry**](SSLRuntimeApi.md#add_crt_list_entry) | **POST** /services/haproxy/runtime/ssl_crt_lists/entries | Add an entry into a crt-list
[**create_ca_file**](SSLRuntimeApi.md#create_ca_file) | **POST** /services/haproxy/runtime/ssl_ca_files | Creates a new SSL CA file
[**create_cert**](SSLRuntimeApi.md#create_cert) | **POST** /services/haproxy/runtime/ssl_certs | Create a new SSL certificate file
[**create_crl**](SSLRuntimeApi.md#create_crl) | **POST** /services/haproxy/runtime/ssl_crl_files | Create a new CRL file
[**delete_ca_file**](SSLRuntimeApi.md#delete_ca_file) | **DELETE** /services/haproxy/runtime/ssl_ca_files/{name} | Deletes a CA file
[**delete_cert**](SSLRuntimeApi.md#delete_cert) | **DELETE** /services/haproxy/runtime/ssl_certs/{name} | Delete a certificate
[**delete_crl**](SSLRuntimeApi.md#delete_crl) | **DELETE** /services/haproxy/runtime/ssl_crl_files/{name} | Delete a CRL file
[**delete_crt_list_entry**](SSLRuntimeApi.md#delete_crt_list_entry) | **DELETE** /services/haproxy/runtime/ssl_crt_lists/entries | Delete an entry from a crt-list
[**get_all_ca_files**](SSLRuntimeApi.md#get_all_ca_files) | **GET** /services/haproxy/runtime/ssl_ca_files | Return an array of all SSL CA files
[**get_all_certs**](SSLRuntimeApi.md#get_all_certs) | **GET** /services/haproxy/runtime/ssl_certs | Return a list of SSL certificate files
[**get_all_crl**](SSLRuntimeApi.md#get_all_crl) | **GET** /services/haproxy/runtime/ssl_crl_files | Return an array of all the CRL files
[**get_all_crt_list_entries**](SSLRuntimeApi.md#get_all_crt_list_entries) | **GET** /services/haproxy/runtime/ssl_crt_lists/entries | Get all the entries inside a crt-list
[**get_all_crt_lists**](SSLRuntimeApi.md#get_all_crt_lists) | **GET** /services/haproxy/runtime/ssl_crt_lists | Get the list of all crt-list files
[**get_ca_entry**](SSLRuntimeApi.md#get_ca_entry) | **GET** /services/haproxy/runtime/ssl_ca_files/{name}/entries/{index} | Return an SSL CA file cert entry
[**get_ca_file**](SSLRuntimeApi.md#get_ca_file) | **GET** /services/haproxy/runtime/ssl_ca_files/{name} | Return an SSL CA file
[**get_cert**](SSLRuntimeApi.md#get_cert) | **GET** /services/haproxy/runtime/ssl_certs/{name} | Return one structured certificate
[**get_crl**](SSLRuntimeApi.md#get_crl) | **GET** /services/haproxy/runtime/ssl_crl_files/{name} | Get the contents of a CRL file
[**replace_cert**](SSLRuntimeApi.md#replace_cert) | **PUT** /services/haproxy/runtime/ssl_certs/{name} | Replace the contents of a certificate
[**replace_crl**](SSLRuntimeApi.md#replace_crl) | **PUT** /services/haproxy/runtime/ssl_crl_files/{name} | Replace the contents of a CRL file
[**set_ca_file**](SSLRuntimeApi.md#set_ca_file) | **PUT** /services/haproxy/runtime/ssl_ca_files/{name} | Update the contents of a CA file


# **add_ca_entry**
> SslCertificate add_ca_entry(name, file_upload)

Add a certificate to a CA file

Adds an entry to an existing CA file using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL CA file name
    file_upload = None # bytearray | Payload of the cert entry

    try:
        # Add a certificate to a CA file
        api_response = await api_instance.add_ca_entry(name, file_upload)
        print("The response of SSLRuntimeApi->add_ca_entry:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->add_ca_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL CA file name | 
 **file_upload** | **bytearray**| Payload of the cert entry | 

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
**201** | Successful operation |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **add_crt_list_entry**
> add_crt_list_entry(name, data)

Add an entry into a crt-list

Appends an entry to the given crt-list using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL crt-list filename
    data = haproxy_dataplane_v3.SslCrtListEntry() # SslCrtListEntry | 

    try:
        # Add an entry into a crt-list
        await api_instance.add_crt_list_entry(name, data)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->add_crt_list_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL crt-list filename | 
 **data** | [**SslCrtListEntry**](SslCrtListEntry.md)|  | 

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
**201** | Successful operation |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_ca_file**
> create_ca_file(file_upload)

Creates a new SSL CA file

Creates a new SSL CA file using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    file_upload = None # bytearray | CA certificate file

    try:
        # Creates a new SSL CA file
        await api_instance.create_ca_file(file_upload)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->create_ca_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file_upload** | **bytearray**| CA certificate file | 

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
**201** | SSL CA file created |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_cert**
> create_cert(file_upload)

Create a new SSL certificate file

Creates a new SSL certificate file using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    file_upload = None # bytearray | Certificate file

    try:
        # Create a new SSL certificate file
        await api_instance.create_cert(file_upload)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->create_cert: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file_upload** | **bytearray**| Certificate file | 

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
**201** | Certificate created |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_crl**
> create_crl(file_upload)

Create a new CRL file

Creates a new CRL file with its contents using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    file_upload = None # bytearray | CRL file

    try:
        # Create a new CRL file
        await api_instance.create_crl(file_upload)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->create_crl: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **file_upload** | **bytearray**| CRL file | 

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
**201** | CRL file created |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**409** | The specified resource already exists |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_ca_file**
> delete_ca_file(name)

Deletes a CA file

Deletes a CA file

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL CA file name

    try:
        # Deletes a CA file
        await api_instance.delete_ca_file(name)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->delete_ca_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL CA file name | 

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
**204** | SSL CA deleted |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_cert**
> delete_cert(name)

Delete a certificate

Deletes a certificate using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL certificate name

    try:
        # Delete a certificate
        await api_instance.delete_cert(name)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->delete_cert: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL certificate name | 

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
**204** | File deleted |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_crl**
> delete_crl(name)

Delete a CRL file

Deletes a CRL file using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | CRL file name

    try:
        # Delete a CRL file
        await api_instance.delete_crl(name)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->delete_crl: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| CRL file name | 

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
**204** | File deleted |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_crt_list_entry**
> delete_crt_list_entry(name, cert_file, line_number=line_number)

Delete an entry from a crt-list

Deletes a single entry from the given crt-list using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL crt list name
    cert_file = 'cert_file_example' # str | SSL cert entry name
    line_number = 56 # int | The line number where the entry is located, in case several entries share the same certificate. (optional)

    try:
        # Delete an entry from a crt-list
        await api_instance.delete_crt_list_entry(name, cert_file, line_number=line_number)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->delete_crt_list_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL crt list name | 
 **cert_file** | **str**| SSL cert entry name | 
 **line_number** | **int**| The line number where the entry is located, in case several entries share the same certificate. | [optional] 

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

# **get_all_ca_files**
> List[SslCaFile] get_all_ca_files()

Return an array of all SSL CA files

Returns all SSL CA files using the runtime socket.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_ca_file import SslCaFile
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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)

    try:
        # Return an array of all SSL CA files
        api_response = await api_instance.get_all_ca_files()
        print("The response of SSLRuntimeApi->get_all_ca_files:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->get_all_ca_files: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[SslCaFile]**](SslCaFile.md)

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

# **get_all_certs**
> List[SslCertificate] get_all_certs()

Return a list of SSL certificate files

Returns certificate files descriptions from runtime.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)

    try:
        # Return a list of SSL certificate files
        api_response = await api_instance.get_all_certs()
        print("The response of SSLRuntimeApi->get_all_certs:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->get_all_certs: %s\n" % e)
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
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_crl**
> List[SslCrl] get_all_crl()

Return an array of all the CRL files

Returns all the certificate revocation list files using the runtime socket.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_crl import SslCrl
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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)

    try:
        # Return an array of all the CRL files
        api_response = await api_instance.get_all_crl()
        print("The response of SSLRuntimeApi->get_all_crl:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->get_all_crl: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[SslCrl]**](SslCrl.md)

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

# **get_all_crt_list_entries**
> List[SslCrtListEntry] get_all_crt_list_entries(name)

Get all the entries inside a crt-list

Returns an array of entries present inside the given crt-list file. Their index can be used to delete them.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL crt-list filename

    try:
        # Get all the entries inside a crt-list
        api_response = await api_instance.get_all_crt_list_entries(name)
        print("The response of SSLRuntimeApi->get_all_crt_list_entries:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->get_all_crt_list_entries: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL crt-list filename | 

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
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_crt_lists**
> List[SslCrtList] get_all_crt_lists()

Get the list of all crt-list files

Returns an array of crt-list file descriptions from runtime.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_crt_list import SslCrtList
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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)

    try:
        # Get the list of all crt-list files
        api_response = await api_instance.get_all_crt_lists()
        print("The response of SSLRuntimeApi->get_all_crt_lists:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->get_all_crt_lists: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[SslCrtList]**](SslCrtList.md)

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

# **get_ca_entry**
> SslCertificate get_ca_entry(name, index)

Return an SSL CA file cert entry

Returns an SSL CA file cert entry.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL CA file name
    index = 56 # int | SSL CA file index

    try:
        # Return an SSL CA file cert entry
        api_response = await api_instance.get_ca_entry(name, index)
        print("The response of SSLRuntimeApi->get_ca_entry:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->get_ca_entry: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL CA file name | 
 **index** | **int**| SSL CA file index | 

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

# **get_ca_file**
> SslCaFile get_ca_file(name)

Return an SSL CA file

Returns an SSL CA file by name using the runtime socket.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_ca_file import SslCaFile
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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL CA file name

    try:
        # Return an SSL CA file
        api_response = await api_instance.get_ca_file(name)
        print("The response of SSLRuntimeApi->get_ca_file:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->get_ca_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL CA file name | 

### Return type

[**SslCaFile**](SslCaFile.md)

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

# **get_cert**
> SslCertificate get_cert(name)

Return one structured certificate

Returns one structured certificate using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL certificate name

    try:
        # Return one structured certificate
        api_response = await api_instance.get_cert(name)
        print("The response of SSLRuntimeApi->get_cert:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->get_cert: %s\n" % e)
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
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_crl**
> List[SslCrlEntry] get_crl(name, index=index)

Get the contents of a CRL file

Returns one or all entries in a CRL file using the runtime socket.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.ssl_crl_entry import SslCrlEntry
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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | CRL file name
    index = 56 # int | Entry index to return. Starts at 1. If not provided, all entries are returned. (optional)

    try:
        # Get the contents of a CRL file
        api_response = await api_instance.get_crl(name, index=index)
        print("The response of SSLRuntimeApi->get_crl:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->get_crl: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| CRL file name | 
 **index** | **int**| Entry index to return. Starts at 1. If not provided, all entries are returned. | [optional] 

### Return type

[**List[SslCrlEntry]**](SslCrlEntry.md)

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

# **replace_cert**
> replace_cert(name, file_upload)

Replace the contents of a certificate

Sets a certificate payload using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL certificate name
    file_upload = None # bytearray | 

    try:
        # Replace the contents of a certificate
        await api_instance.replace_cert(name, file_upload)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->replace_cert: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL certificate name | 
 **file_upload** | **bytearray**|  | 

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
**200** | File updated |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replace_crl**
> replace_crl(name, file_upload)

Replace the contents of a CRL file

Replaces the contents of a CRL file using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | CRL file name
    file_upload = None # bytearray | CRL file contents

    try:
        # Replace the contents of a CRL file
        await api_instance.replace_crl(name, file_upload)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->replace_crl: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| CRL file name | 
 **file_upload** | **bytearray**| CRL file contents | 

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
**200** | File modified |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **set_ca_file**
> set_ca_file(name, file_upload)

Update the contents of a CA file

Replace the contents of a CA file using the runtime socket.

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
    api_instance = haproxy_dataplane_v3.SSLRuntimeApi(api_client)
    name = 'name_example' # str | SSL CA file name
    file_upload = None # bytearray | 

    try:
        # Update the contents of a CA file
        await api_instance.set_ca_file(name, file_upload)
    except Exception as e:
        print("Exception when calling SSLRuntimeApi->set_ca_file: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**| SSL CA file name | 
 **file_upload** | **bytearray**|  | 

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
**200** | SSL CA payload added |  -  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

