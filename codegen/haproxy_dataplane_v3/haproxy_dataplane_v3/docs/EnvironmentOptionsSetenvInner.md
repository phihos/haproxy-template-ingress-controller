# EnvironmentOptionsSetenvInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**value** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.environment_options_setenv_inner import EnvironmentOptionsSetenvInner

# TODO update the JSON string below
json = "{}"
# create an instance of EnvironmentOptionsSetenvInner from a JSON string
environment_options_setenv_inner_instance = EnvironmentOptionsSetenvInner.from_json(json)
# print the JSON string representation of the object
print(EnvironmentOptionsSetenvInner.to_json())

# convert the object into a dict
environment_options_setenv_inner_dict = environment_options_setenv_inner_instance.to_dict()
# create an instance of EnvironmentOptionsSetenvInner from a dict
environment_options_setenv_inner_from_dict = EnvironmentOptionsSetenvInner.from_dict(environment_options_setenv_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


