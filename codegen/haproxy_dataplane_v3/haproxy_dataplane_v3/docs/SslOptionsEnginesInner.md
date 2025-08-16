# SslOptionsEnginesInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**algorithms** | **str** |  | [optional] 
**name** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.ssl_options_engines_inner import SslOptionsEnginesInner

# TODO update the JSON string below
json = "{}"
# create an instance of SslOptionsEnginesInner from a JSON string
ssl_options_engines_inner_instance = SslOptionsEnginesInner.from_json(json)
# print the JSON string representation of the object
print(SslOptionsEnginesInner.to_json())

# convert the object into a dict
ssl_options_engines_inner_dict = ssl_options_engines_inner_instance.to_dict()
# create an instance of SslOptionsEnginesInner from a dict
ssl_options_engines_inner_from_dict = SslOptionsEnginesInner.from_dict(ssl_options_engines_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


