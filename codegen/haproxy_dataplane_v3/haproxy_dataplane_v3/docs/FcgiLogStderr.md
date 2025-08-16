# FcgiLogStderr

Enables logging of STDERR messages that the FastCGI application reports. It is an optional setting. By default, HAProxy Enterprise ignores STDERR messages.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | [optional] 
**facility** | **str** |  | [optional] 
**format** | **str** |  | [optional] 
**var_global** | **bool** |  | [optional] 
**len** | **int** |  | [optional] 
**level** | **str** |  | [optional] 
**minlevel** | **str** |  | [optional] 
**sample** | [**Sample**](Sample.md) |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.fcgi_log_stderr import FcgiLogStderr

# TODO update the JSON string below
json = "{}"
# create an instance of FcgiLogStderr from a JSON string
fcgi_log_stderr_instance = FcgiLogStderr.from_json(json)
# print the JSON string representation of the object
print(FcgiLogStderr.to_json())

# convert the object into a dict
fcgi_log_stderr_dict = fcgi_log_stderr_instance.to_dict()
# create an instance of FcgiLogStderr from a dict
fcgi_log_stderr_from_dict = FcgiLogStderr.from_dict(fcgi_log_stderr_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


