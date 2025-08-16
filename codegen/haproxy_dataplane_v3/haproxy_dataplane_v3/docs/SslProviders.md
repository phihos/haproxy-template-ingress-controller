# SslProviders

SSL Providers

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**providers** | **List[str]** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_providers import SslProviders

# TODO update the JSON string below
json = "{}"
# create an instance of SslProviders from a JSON string
ssl_providers_instance = SslProviders.from_json(json)
# print the JSON string representation of the object
print(SslProviders.to_json())

# convert the object into a dict
ssl_providers_dict = ssl_providers_instance.to_dict()
# create an instance of SslProviders from a dict
ssl_providers_from_dict = SslProviders.from_dict(ssl_providers_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


