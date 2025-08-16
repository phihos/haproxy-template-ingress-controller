# FcgiSetParam

Sets a FastCGI parameter to pass to this application. Its value, defined by <format> can take a formatted string, the same as the log directive. Optionally, you can follow it with an ACL-based condition, in which case the FastCGI application evaluates it only if the condition is true.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**format** | **str** |  | [optional] 
**name** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.fcgi_set_param import FcgiSetParam

# TODO update the JSON string below
json = "{}"
# create an instance of FcgiSetParam from a JSON string
fcgi_set_param_instance = FcgiSetParam.from_json(json)
# print the JSON string representation of the object
print(FcgiSetParam.to_json())

# convert the object into a dict
fcgi_set_param_dict = fcgi_set_param_instance.to_dict()
# create an instance of FcgiSetParam from a dict
fcgi_set_param_from_dict = FcgiSetParam.from_dict(fcgi_set_param_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


