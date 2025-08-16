# MapEntry

One Map Entry

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | [optional] [readonly] 
**key** | **str** |  | [optional] 
**value** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.map_entry import MapEntry

# TODO update the JSON string below
json = "{}"
# create an instance of MapEntry from a JSON string
map_entry_instance = MapEntry.from_json(json)
# print the JSON string representation of the object
print(MapEntry.to_json())

# convert the object into a dict
map_entry_dict = map_entry_instance.to_dict()
# create an instance of MapEntry from a dict
map_entry_from_dict = MapEntry.from_dict(map_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


