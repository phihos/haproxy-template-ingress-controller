# EnvironmentOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**presetenv** | [**List[EnvironmentOptionsPresetenvInner]**](EnvironmentOptionsPresetenvInner.md) |  | [optional] 
**resetenv** | **str** |  | [optional] 
**setenv** | [**List[EnvironmentOptionsSetenvInner]**](EnvironmentOptionsSetenvInner.md) |  | [optional] 
**unsetenv** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.environment_options import EnvironmentOptions

# TODO update the JSON string below
json = "{}"
# create an instance of EnvironmentOptions from a JSON string
environment_options_instance = EnvironmentOptions.from_json(json)
# print the JSON string representation of the object
print(EnvironmentOptions.to_json())

# convert the object into a dict
environment_options_dict = environment_options_instance.to_dict()
# create an instance of EnvironmentOptions from a dict
environment_options_from_dict = EnvironmentOptions.from_dict(environment_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


