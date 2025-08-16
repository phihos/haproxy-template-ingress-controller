# Source


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | 
**address_second** | **str** |  | [optional] 
**hdr** | **str** |  | [optional] 
**interface** | **str** |  | [optional] 
**occ** | **str** |  | [optional] 
**port** | **int** |  | [optional] 
**port_second** | **int** |  | [optional] 
**usesrc** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.source import Source

# TODO update the JSON string below
json = "{}"
# create an instance of Source from a JSON string
source_instance = Source.from_json(json)
# print the JSON string representation of the object
print(Source.to_json())

# convert the object into a dict
source_dict = source_instance.to_dict()
# create an instance of Source from a dict
source_from_dict = Source.from_dict(source_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


