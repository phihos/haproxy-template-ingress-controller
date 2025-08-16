# ReplaceRuntimeMapEntryRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | Map value | 

## Example

```python
from haproxy_dataplane_v3.models.replace_runtime_map_entry_request import ReplaceRuntimeMapEntryRequest

# TODO update the JSON string below
json = "{}"
# create an instance of ReplaceRuntimeMapEntryRequest from a JSON string
replace_runtime_map_entry_request_instance = ReplaceRuntimeMapEntryRequest.from_json(json)
# print the JSON string representation of the object
print(ReplaceRuntimeMapEntryRequest.to_json())

# convert the object into a dict
replace_runtime_map_entry_request_dict = replace_runtime_map_entry_request_instance.to_dict()
# create an instance of ReplaceRuntimeMapEntryRequest from a dict
replace_runtime_map_entry_request_from_dict = ReplaceRuntimeMapEntryRequest.from_dict(replace_runtime_map_entry_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


