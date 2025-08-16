# EnvironmentOptionsPresetenvInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**value** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.environment_options_presetenv_inner import EnvironmentOptionsPresetenvInner

# TODO update the JSON string below
json = "{}"
# create an instance of EnvironmentOptionsPresetenvInner from a JSON string
environment_options_presetenv_inner_instance = EnvironmentOptionsPresetenvInner.from_json(json)
# print the JSON string representation of the object
print(EnvironmentOptionsPresetenvInner.to_json())

# convert the object into a dict
environment_options_presetenv_inner_dict = environment_options_presetenv_inner_instance.to_dict()
# create an instance of EnvironmentOptionsPresetenvInner from a dict
environment_options_presetenv_inner_from_dict = EnvironmentOptionsPresetenvInner.from_dict(environment_options_presetenv_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


