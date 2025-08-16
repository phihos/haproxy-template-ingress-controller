# DeviceAtlasOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**json_file** | **str** |  | [optional] 
**log_level** | **str** |  | [optional] 
**properties_cookie** | **str** |  | [optional] 
**separator** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.device_atlas_options import DeviceAtlasOptions

# TODO update the JSON string below
json = "{}"
# create an instance of DeviceAtlasOptions from a JSON string
device_atlas_options_instance = DeviceAtlasOptions.from_json(json)
# print the JSON string representation of the object
print(DeviceAtlasOptions.to_json())

# convert the object into a dict
device_atlas_options_dict = device_atlas_options_instance.to_dict()
# create an instance of DeviceAtlasOptions from a dict
device_atlas_options_from_dict = DeviceAtlasOptions.from_dict(device_atlas_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


