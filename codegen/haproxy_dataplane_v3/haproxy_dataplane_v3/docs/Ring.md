# Ring

Ring with all it's children resources

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**description** | **str** |  | [optional] 
**format** | **str** |  | [optional] 
**maxlen** | **int** |  | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**size** | **int** |  | [optional] 
**timeout_connect** | **int** |  | [optional] 
**timeout_server** | **int** |  | [optional] 
**servers** | **object** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ring import Ring

# TODO update the JSON string below
json = "{}"
# create an instance of Ring from a JSON string
ring_instance = Ring.from_json(json)
# print the JSON string representation of the object
print(Ring.to_json())

# convert the object into a dict
ring_dict = ring_instance.to_dict()
# create an instance of Ring from a dict
ring_from_dict = Ring.from_dict(ring_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


