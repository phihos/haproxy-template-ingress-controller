# InfoSystem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cpu_info** | [**InfoSystemCpuInfo**](InfoSystemCpuInfo.md) |  | [optional] 
**hostname** | **str** | Hostname where the HAProxy is running | [optional] 
**mem_info** | [**InfoSystemMemInfo**](InfoSystemMemInfo.md) |  | [optional] 
**os_string** | **str** | OS string | [optional] 
**time** | **int** | Current time in milliseconds since Epoch. | [optional] 
**uptime** | **int** | System uptime | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.info_system import InfoSystem

# TODO update the JSON string below
json = "{}"
# create an instance of InfoSystem from a JSON string
info_system_instance = InfoSystem.from_json(json)
# print the JSON string representation of the object
print(InfoSystem.to_json())

# convert the object into a dict
info_system_dict = info_system_instance.to_dict()
# create an instance of InfoSystem from a dict
info_system_from_dict = InfoSystem.from_dict(info_system_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


