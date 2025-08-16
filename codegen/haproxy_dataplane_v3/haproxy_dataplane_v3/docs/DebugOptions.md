# DebugOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**anonkey** | **int** |  | [optional] 
**quiet** | **bool** |  | [optional] 
**stress_level** | **int** |  | [optional] 
**zero_warning** | **bool** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.debug_options import DebugOptions

# TODO update the JSON string below
json = "{}"
# create an instance of DebugOptions from a JSON string
debug_options_instance = DebugOptions.from_json(json)
# print the JSON string representation of the object
print(DebugOptions.to_json())

# convert the object into a dict
debug_options_dict = debug_options_instance.to_dict()
# create an instance of DebugOptions from a dict
debug_options_from_dict = DebugOptions.from_dict(debug_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


