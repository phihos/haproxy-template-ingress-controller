# NativeStats

HAProxy stats array

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error** | **str** |  | [optional] 
**runtime_api** | **str** |  | [optional] 
**stats** | [**List[NativeStat]**](NativeStat.md) |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.native_stats import NativeStats

# TODO update the JSON string below
json = "{}"
# create an instance of NativeStats from a JSON string
native_stats_instance = NativeStats.from_json(json)
# print the JSON string representation of the object
print(NativeStats.to_json())

# convert the object into a dict
native_stats_dict = native_stats_instance.to_dict()
# create an instance of NativeStats from a dict
native_stats_from_dict = NativeStats.from_dict(native_stats_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


