# RingBase

HAProxy ring configuration

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

## Example

```python
from haproxy_dataplane_v3.models.ring_base import RingBase

# TODO update the JSON string below
json = "{}"
# create an instance of RingBase from a JSON string
ring_base_instance = RingBase.from_json(json)
# print the JSON string representation of the object
print(RingBase.to_json())

# convert the object into a dict
ring_base_dict = ring_base_instance.to_dict()
# create an instance of RingBase from a dict
ring_base_from_dict = RingBase.from_dict(ring_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


