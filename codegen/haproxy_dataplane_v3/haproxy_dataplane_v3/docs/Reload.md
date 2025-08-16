# Reload

HAProxy reload

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | [optional] 
**reload_timestamp** | **int** |  | [optional] 
**response** | **str** |  | [optional] 
**status** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.reload import Reload

# TODO update the JSON string below
json = "{}"
# create an instance of Reload from a JSON string
reload_instance = Reload.from_json(json)
# print the JSON string representation of the object
print(Reload.to_json())

# convert the object into a dict
reload_dict = reload_instance.to_dict()
# create an instance of Reload from a dict
reload_from_dict = Reload.from_dict(reload_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


