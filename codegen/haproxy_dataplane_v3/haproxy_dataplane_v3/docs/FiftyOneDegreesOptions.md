# FiftyOneDegreesOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cache_size** | **int** |  | [optional] 
**data_file** | **str** |  | [optional] 
**property_name_list** | **str** |  | [optional] 
**property_separator** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.fifty_one_degrees_options import FiftyOneDegreesOptions

# TODO update the JSON string below
json = "{}"
# create an instance of FiftyOneDegreesOptions from a JSON string
fifty_one_degrees_options_instance = FiftyOneDegreesOptions.from_json(json)
# print the JSON string representation of the object
print(FiftyOneDegreesOptions.to_json())

# convert the object into a dict
fifty_one_degrees_options_dict = fifty_one_degrees_options_instance.to_dict()
# create an instance of FiftyOneDegreesOptions from a dict
fifty_one_degrees_options_from_dict = FiftyOneDegreesOptions.from_dict(fifty_one_degrees_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


