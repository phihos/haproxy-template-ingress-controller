# DgramBind

HAProxy log forward dgram bind configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | [optional] 
**interface** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | [optional] 
**namespace** | **str** |  | [optional] 
**port** | **int** |  | [optional] 
**port_range_end** | **int** |  | [optional] 
**transparent** | **bool** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.dgram_bind import DgramBind

# TODO update the JSON string below
json = "{}"
# create an instance of DgramBind from a JSON string
dgram_bind_instance = DgramBind.from_json(json)
# print the JSON string representation of the object
print(DgramBind.to_json())

# convert the object into a dict
dgram_bind_dict = dgram_bind_instance.to_dict()
# create an instance of DgramBind from a dict
dgram_bind_from_dict = DgramBind.from_dict(dgram_bind_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


