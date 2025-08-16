# HttpClientOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**resolvers_disabled** | **str** |  | [optional] 
**resolvers_id** | **str** |  | [optional] 
**resolvers_prefer** | **str** |  | [optional] 
**retries** | **int** |  | [optional] 
**ssl_ca_file** | **str** |  | [optional] 
**ssl_verify** | **str** |  | [optional] 
**timeout_connect** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.http_client_options import HttpClientOptions

# TODO update the JSON string below
json = "{}"
# create an instance of HttpClientOptions from a JSON string
http_client_options_instance = HttpClientOptions.from_json(json)
# print the JSON string representation of the object
print(HttpClientOptions.to_json())

# convert the object into a dict
http_client_options_dict = http_client_options_instance.to_dict()
# create an instance of HttpClientOptions from a dict
http_client_options_from_dict = HttpClientOptions.from_dict(http_client_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


