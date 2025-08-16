# SslOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**acme_scheduler** | **str** |  | [optional] 
**ca_base** | **str** |  | [optional] 
**crt_base** | **str** |  | [optional] 
**default_bind_ciphers** | **str** |  | [optional] 
**default_bind_ciphersuites** | **str** |  | [optional] 
**default_bind_client_sigalgs** | **str** |  | [optional] 
**default_bind_curves** | **str** |  | [optional] 
**default_bind_options** | **str** |  | [optional] 
**default_bind_sigalgs** | **str** |  | [optional] 
**default_server_ciphers** | **str** |  | [optional] 
**default_server_ciphersuites** | **str** |  | [optional] 
**default_server_client_sigalgs** | **str** |  | [optional] 
**default_server_curves** | **str** |  | [optional] 
**default_server_options** | **str** |  | [optional] 
**default_server_sigalgs** | **str** |  | [optional] 
**dh_param_file** | **str** |  | [optional] 
**engines** | [**List[SslOptionsEnginesInner]**](SslOptionsEnginesInner.md) |  | [optional] 
**issuers_chain_path** | **str** |  | [optional] 
**load_extra_files** | **str** |  | [optional] 
**maxsslconn** | **int** |  | [optional] 
**maxsslrate** | **int** |  | [optional] 
**mode_async** | **str** |  | [optional] 
**propquery** | **str** |  | [optional] 
**provider** | **str** |  | [optional] 
**provider_path** | **str** |  | [optional] 
**security_level** | **int** |  | [optional] 
**server_verify** | **str** |  | [optional] 
**skip_self_issued_ca** | **bool** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_options import SslOptions

# TODO update the JSON string below
json = "{}"
# create an instance of SslOptions from a JSON string
ssl_options_instance = SslOptions.from_json(json)
# print the JSON string representation of the object
print(SslOptions.to_json())

# convert the object into a dict
ssl_options_dict = ssl_options_instance.to_dict()
# create an instance of SslOptions from a dict
ssl_options_from_dict = SslOptions.from_dict(ssl_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


