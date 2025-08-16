# WurflOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cache_size** | **int** |  | [optional] 
**data_file** | **str** |  | [optional] 
**information_list** | **str** |  | [optional] 
**information_list_separator** | **str** |  | [optional] 
**patch_file** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.wurfl_options import WurflOptions

# TODO update the JSON string below
json = "{}"
# create an instance of WurflOptions from a JSON string
wurfl_options_instance = WurflOptions.from_json(json)
# print the JSON string representation of the object
print(WurflOptions.to_json())

# convert the object into a dict
wurfl_options_dict = wurfl_options_instance.to_dict()
# create an instance of WurflOptions from a dict
wurfl_options_from_dict = WurflOptions.from_dict(wurfl_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


