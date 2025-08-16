# LogForward

LogForward with all it's children resources

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
**binds** | **object** |  | [optional] 
**dgram_binds** | **object** |  | [optional] 
**log_target_list** | [**List[LogTarget]**](LogTarget.md) | HAProxy log target array (corresponds to log directives) | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.log_forward import LogForward

# TODO update the JSON string below
json = "{}"
# create an instance of LogForward from a JSON string
log_forward_instance = LogForward.from_json(json)
# print the JSON string representation of the object
print(LogForward.to_json())

# convert the object into a dict
log_forward_dict = log_forward_instance.to_dict()
# create an instance of LogForward from a dict
log_forward_from_dict = LogForward.from_dict(log_forward_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


