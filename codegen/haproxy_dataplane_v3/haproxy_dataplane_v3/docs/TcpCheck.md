# TcpCheck


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**action** | **str** |  | 
**addr** | **str** |  | [optional] 
**alpn** | **str** |  | [optional] 
**check_comment** | **str** |  | [optional] 
**data** | **str** |  | [optional] 
**default** | **bool** |  | [optional] 
**error_status** | **str** |  | [optional] 
**exclamation_mark** | **bool** |  | [optional] 
**fmt** | **str** |  | [optional] 
**hex_fmt** | **str** |  | [optional] 
**hex_string** | **str** |  | [optional] 
**linger** | **bool** |  | [optional] 
**match** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**min_recv** | **int** |  | [optional] 
**ok_status** | **str** |  | [optional] 
**on_error** | **str** |  | [optional] 
**on_success** | **str** |  | [optional] 
**pattern** | **str** |  | [optional] 
**port** | **int** |  | [optional] 
**port_string** | **str** |  | [optional] 
**proto** | **str** |  | [optional] 
**send_proxy** | **bool** |  | [optional] 
**sni** | **str** |  | [optional] 
**ssl** | **bool** |  | [optional] 
**status_code** | **str** |  | [optional] 
**tout_status** | **str** |  | [optional] 
**var_expr** | **str** |  | [optional] 
**var_fmt** | **str** |  | [optional] 
**var_name** | **str** |  | [optional] 
**var_scope** | **str** |  | [optional] 
**via_socks4** | **bool** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tcp_check import TcpCheck

# TODO update the JSON string below
json = "{}"
# create an instance of TcpCheck from a JSON string
tcp_check_instance = TcpCheck.from_json(json)
# print the JSON string representation of the object
print(TcpCheck.to_json())

# convert the object into a dict
tcp_check_dict = tcp_check_instance.to_dict()
# create an instance of TcpCheck from a dict
tcp_check_from_dict = TcpCheck.from_dict(tcp_check_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


