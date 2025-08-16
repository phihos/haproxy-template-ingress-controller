# GlobalBaseCpuMapsInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cpu_set** | **str** |  | 
**process** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.global_base_cpu_maps_inner import GlobalBaseCpuMapsInner

# TODO update the JSON string below
json = "{}"
# create an instance of GlobalBaseCpuMapsInner from a JSON string
global_base_cpu_maps_inner_instance = GlobalBaseCpuMapsInner.from_json(json)
# print the JSON string representation of the object
print(GlobalBaseCpuMapsInner.to_json())

# convert the object into a dict
global_base_cpu_maps_inner_dict = global_base_cpu_maps_inner_instance.to_dict()
# create an instance of GlobalBaseCpuMapsInner from a dict
global_base_cpu_maps_inner_from_dict = GlobalBaseCpuMapsInner.from_dict(global_base_cpu_maps_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


