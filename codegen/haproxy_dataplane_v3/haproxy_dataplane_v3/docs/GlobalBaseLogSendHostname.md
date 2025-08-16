# GlobalBaseLogSendHostname


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **str** |  | 
**param** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.global_base_log_send_hostname import GlobalBaseLogSendHostname

# TODO update the JSON string below
json = "{}"
# create an instance of GlobalBaseLogSendHostname from a JSON string
global_base_log_send_hostname_instance = GlobalBaseLogSendHostname.from_json(json)
# print the JSON string representation of the object
print(GlobalBaseLogSendHostname.to_json())

# convert the object into a dict
global_base_log_send_hostname_dict = global_base_log_send_hostname_instance.to_dict()
# create an instance of GlobalBaseLogSendHostname from a dict
global_base_log_send_hostname_from_dict = GlobalBaseLogSendHostname.from_dict(global_base_log_send_hostname_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


