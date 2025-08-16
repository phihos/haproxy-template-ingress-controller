# InfoSystemMemInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**dataplaneapi_memory** | **int** |  | [optional] 
**free_memory** | **int** |  | [optional] 
**total_memory** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.info_system_mem_info import InfoSystemMemInfo

# TODO update the JSON string below
json = "{}"
# create an instance of InfoSystemMemInfo from a JSON string
info_system_mem_info_instance = InfoSystemMemInfo.from_json(json)
# print the JSON string representation of the object
print(InfoSystemMemInfo.to_json())

# convert the object into a dict
info_system_mem_info_dict = info_system_mem_info_instance.to_dict()
# create an instance of InfoSystemMemInfo from a dict
info_system_mem_info_from_dict = InfoSystemMemInfo.from_dict(info_system_mem_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


