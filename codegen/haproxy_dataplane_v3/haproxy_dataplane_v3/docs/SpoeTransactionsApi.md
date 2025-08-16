# haproxy_dataplane_v3.SpoeTransactionsApi

All URIs are relative to */v3*

Method | HTTP request | Description
------------- | ------------- | -------------
[**commit_spoe_transaction**](SpoeTransactionsApi.md#commit_spoe_transaction) | **PUT** /services/haproxy/spoe/spoe_files/{parent_name}/transactions/{id} | Commit transaction
[**delete_spoe_transaction**](SpoeTransactionsApi.md#delete_spoe_transaction) | **DELETE** /services/haproxy/spoe/spoe_files/{parent_name}/transactions/{id} | Delete a transaction
[**get_all_spoe_transaction**](SpoeTransactionsApi.md#get_all_spoe_transaction) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/transactions | Return list of SPOE configuration transactions.
[**get_spoe_transaction**](SpoeTransactionsApi.md#get_spoe_transaction) | **GET** /services/haproxy/spoe/spoe_files/{parent_name}/transactions/{id} | Return one SPOE configuration transactions
[**start_spoe_transaction**](SpoeTransactionsApi.md#start_spoe_transaction) | **POST** /services/haproxy/spoe/spoe_files/{parent_name}/transactions | Start a new transaction


# **commit_spoe_transaction**
> SpoeTransaction commit_spoe_transaction(parent_name, id, force_reload=force_reload)

Commit transaction

Commit transaction, execute all operations in transaction and return msg

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_transaction import SpoeTransaction
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
    api_instance = haproxy_dataplane_v3.SpoeTransactionsApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    id = 'id_example' # str | Transaction id
    force_reload = False # bool | If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. (optional) (default to False)

    try:
        # Commit transaction
        api_response = await api_instance.commit_spoe_transaction(parent_name, id, force_reload=force_reload)
        print("The response of SpoeTransactionsApi->commit_spoe_transaction:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeTransactionsApi->commit_spoe_transaction: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **id** | **str**| Transaction id | 
 **force_reload** | **bool**| If set, do a force reload, do not wait for the configured reload-delay. Cannot be used when transaction is specified, as changes in transaction are not applied directly to configuration. | [optional] [default to False]

### Return type

[**SpoeTransaction**](SpoeTransaction.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Transaction successfully committed |  -  |
**202** | Configuration change accepted and reload requested |  * Reload-ID - ID of the requested reload <br>  |
**400** | Bad request |  * Configuration-Version - Configuration file version <br>  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_spoe_transaction**
> delete_spoe_transaction(parent_name, id)

Delete a transaction

Deletes a transaction.

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
    api_instance = haproxy_dataplane_v3.SpoeTransactionsApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    id = 'id_example' # str | Transaction id

    try:
        # Delete a transaction
        await api_instance.delete_spoe_transaction(parent_name, id)
    except Exception as e:
        print("Exception when calling SpoeTransactionsApi->delete_spoe_transaction: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **id** | **str**| Transaction id | 

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
**204** | Transaction deleted |  -  |
**404** | The specified resource was not found |  * Configuration-Version - Configuration file version <br>  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_spoe_transaction**
> List[SpoeTransaction] get_all_spoe_transaction(parent_name, status=status)

Return list of SPOE configuration transactions.

Returns a list of SPOE configuration transactions. Transactions can be filtered by their status.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_transaction import SpoeTransaction
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
    api_instance = haproxy_dataplane_v3.SpoeTransactionsApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    status = 'status_example' # str | Filter by transaction status (optional)

    try:
        # Return list of SPOE configuration transactions.
        api_response = await api_instance.get_all_spoe_transaction(parent_name, status=status)
        print("The response of SpoeTransactionsApi->get_all_spoe_transaction:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeTransactionsApi->get_all_spoe_transaction: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **status** | **str**| Filter by transaction status | [optional] 

### Return type

[**List[SpoeTransaction]**](SpoeTransaction.md)

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

# **get_spoe_transaction**
> SpoeTransaction get_spoe_transaction(parent_name, id)

Return one SPOE configuration transactions

Returns one SPOE configuration transactions.

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_transaction import SpoeTransaction
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
    api_instance = haproxy_dataplane_v3.SpoeTransactionsApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    id = 'id_example' # str | Transaction id

    try:
        # Return one SPOE configuration transactions
        api_response = await api_instance.get_spoe_transaction(parent_name, id)
        print("The response of SpoeTransactionsApi->get_spoe_transaction:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeTransactionsApi->get_spoe_transaction: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **id** | **str**| Transaction id | 

### Return type

[**SpoeTransaction**](SpoeTransaction.md)

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

# **start_spoe_transaction**
> SpoeTransaction start_spoe_transaction(parent_name, version)

Start a new transaction

Starts a new transaction and returns it's id

### Example

* Basic Authentication (basic_auth):

```python
import haproxy_dataplane_v3
from haproxy_dataplane_v3.models.spoe_transaction import SpoeTransaction
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
    api_instance = haproxy_dataplane_v3.SpoeTransactionsApi(api_client)
    parent_name = 'parent_name_example' # str | Parent name
    version = 56 # int | Configuration version on which to work on

    try:
        # Start a new transaction
        api_response = await api_instance.start_spoe_transaction(parent_name, version)
        print("The response of SpoeTransactionsApi->start_spoe_transaction:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SpoeTransactionsApi->start_spoe_transaction: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parent_name** | **str**| Parent name | 
 **version** | **int**| Configuration version on which to work on | 

### Return type

[**SpoeTransaction**](SpoeTransaction.md)

### Authorization

[basic_auth](../README.md#basic_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Transaction started |  -  |
**429** | Too many open transactions |  -  |
**0** | General Error |  * Configuration-Version - Configuration file version <br>  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

