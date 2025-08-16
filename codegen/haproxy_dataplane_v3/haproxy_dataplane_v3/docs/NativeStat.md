# NativeStat

Current stats for one object.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**backend_name** | **str** |  | [optional] 
**name** | **str** |  | [optional] 
**stats** | [**NativeStatStats**](NativeStatStats.md) |  | [optional] 
**type** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.native_stat import NativeStat

# TODO update the JSON string below
json = "{}"
# create an instance of NativeStat from a JSON string
native_stat_instance = NativeStat.from_json(json)
# print the JSON string representation of the object
print(NativeStat.to_json())

# convert the object into a dict
native_stat_dict = native_stat_instance.to_dict()
# create an instance of NativeStat from a dict
native_stat_from_dict = NativeStat.from_dict(native_stat_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


