# LogProfile

Defines a logging profile for one or more steps.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**log_tag** | **str** | Override syslog log tag set by other \&quot;log-tag\&quot; directives. | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** | Name of the logging profile. | 
**steps** | [**List[LogProfileStep]**](LogProfileStep.md) | List of steps where to override the logging. | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.log_profile import LogProfile

# TODO update the JSON string below
json = "{}"
# create an instance of LogProfile from a JSON string
log_profile_instance = LogProfile.from_json(json)
# print the JSON string representation of the object
print(LogProfile.to_json())

# convert the object into a dict
log_profile_dict = log_profile_instance.to_dict()
# create an instance of LogProfile from a dict
log_profile_from_dict = LogProfile.from_dict(log_profile_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


