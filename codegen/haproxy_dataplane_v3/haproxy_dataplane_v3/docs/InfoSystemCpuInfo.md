# InfoSystemCpuInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**model** | **str** |  | [optional] 
**num_cpus** | **int** | Number of logical CPUs | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.info_system_cpu_info import InfoSystemCpuInfo

# TODO update the JSON string below
json = "{}"
# create an instance of InfoSystemCpuInfo from a JSON string
info_system_cpu_info_instance = InfoSystemCpuInfo.from_json(json)
# print the JSON string representation of the object
print(InfoSystemCpuInfo.to_json())

# convert the object into a dict
info_system_cpu_info_dict = info_system_cpu_info_instance.to_dict()
# create an instance of InfoSystemCpuInfo from a dict
info_system_cpu_info_from_dict = InfoSystemCpuInfo.from_dict(info_system_cpu_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


