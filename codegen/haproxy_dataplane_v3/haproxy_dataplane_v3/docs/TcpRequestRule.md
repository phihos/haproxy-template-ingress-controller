# TcpRequestRule

HAProxy TCP Request Rule configuration (corresponds to tcp-request)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**action** | **str** |  | [optional] 
**bandwidth_limit_limit** | **str** |  | [optional] 
**bandwidth_limit_name** | **str** |  | [optional] 
**bandwidth_limit_period** | **str** |  | [optional] 
**capture_len** | **int** |  | [optional] 
**capture_sample** | **str** |  | [optional] 
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**expr** | **str** |  | [optional] 
**gpt_value** | **str** |  | [optional] 
**log_level** | **str** |  | [optional] 
**lua_action** | **str** |  | [optional] 
**lua_params** | **str** |  | [optional] 
**mark_value** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**nice_value** | **int** |  | [optional] 
**resolve_protocol** | **str** |  | [optional] 
**resolve_resolvers** | **str** |  | [optional] 
**resolve_var** | **str** |  | [optional] 
**rst_ttl** | **int** |  | [optional] 
**sc_idx** | **str** |  | [optional] 
**sc_inc_id** | **str** |  | [optional] 
**sc_int** | **int** |  | [optional] 
**server_name** | **str** |  | [optional] 
**service_name** | **str** |  | [optional] 
**spoe_engine_name** | **str** |  | [optional] 
**spoe_group_name** | **str** |  | [optional] 
**switch_mode_proto** | **str** |  | [optional] 
**timeout** | **int** |  | [optional] 
**tos_value** | **str** |  | [optional] 
**track_key** | **str** |  | [optional] 
**track_stick_counter** | **int** |  | [optional] 
**track_table** | **str** |  | [optional] 
**type** | **str** |  | 
**var_format** | **str** |  | [optional] 
**var_name** | **str** |  | [optional] 
**var_scope** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tcp_request_rule import TcpRequestRule

# TODO update the JSON string below
json = "{}"
# create an instance of TcpRequestRule from a JSON string
tcp_request_rule_instance = TcpRequestRule.from_json(json)
# print the JSON string representation of the object
print(TcpRequestRule.to_json())

# convert the object into a dict
tcp_request_rule_dict = tcp_request_rule_instance.to_dict()
# create an instance of TcpRequestRule from a dict
tcp_request_rule_from_dict = TcpRequestRule.from_dict(tcp_request_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


