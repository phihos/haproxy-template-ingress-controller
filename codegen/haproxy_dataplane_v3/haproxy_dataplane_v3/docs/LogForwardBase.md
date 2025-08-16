# LogForwardBase

HAProxy log forward configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**assume_rfc6587_ntf** | **bool** |  | [optional] 
**backlog** | **int** |  | [optional] 
**dont_parse_log** | **bool** |  | [optional] 
**maxconn** | **int** |  | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**timeout_client** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.log_forward_base import LogForwardBase

# TODO update the JSON string below
json = "{}"
# create an instance of LogForwardBase from a JSON string
log_forward_base_instance = LogForwardBase.from_json(json)
# print the JSON string representation of the object
print(LogForwardBase.to_json())

# convert the object into a dict
log_forward_base_dict = log_forward_base_instance.to_dict()
# create an instance of LogForwardBase from a dict
log_forward_base_from_dict = LogForwardBase.from_dict(log_forward_base_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


