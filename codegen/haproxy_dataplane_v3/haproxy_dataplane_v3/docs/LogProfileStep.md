# LogProfileStep

Defines what to log for a given step.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**drop** | **str** | If enabled, no log shall be emitted for the given step. | [optional] 
**format** | **str** | Override \&quot;log-format\&quot; or \&quot;error-log-format\&quot; strings depending on the step. | [optional] 
**metadata** | **object** |  | [optional] 
**sd** | **str** | Override the \&quot;log-format-sd\&quot; string. | [optional] 
**step** | **str** | Logging step name. | 

## Example

```python
from haproxy_dataplane_v3.models.log_profile_step import LogProfileStep

# TODO update the JSON string below
json = "{}"
# create an instance of LogProfileStep from a JSON string
log_profile_step_instance = LogProfileStep.from_json(json)
# print the JSON string representation of the object
print(LogProfileStep.to_json())

# convert the object into a dict
log_profile_step_dict = log_profile_step_instance.to_dict()
# create an instance of LogProfileStep from a dict
log_profile_step_from_dict = LogProfileStep.from_dict(log_profile_step_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


