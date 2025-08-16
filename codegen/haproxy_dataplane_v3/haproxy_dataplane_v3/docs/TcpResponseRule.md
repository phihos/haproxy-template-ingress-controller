# TcpResponseRule

HAProxy TCP Response Rule configuration (corresponds to tcp-response)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**action** | **str** |  | [optional] 
**bandwidth_limit_limit** | **str** |  | [optional] 
**bandwidth_limit_name** | **str** |  | [optional] 
**bandwidth_limit_period** | **str** |  | [optional] 
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**expr** | **str** |  | [optional] 
**log_level** | **str** |  | [optional] 
**lua_action** | **str** |  | [optional] 
**lua_params** | **str** |  | [optional] 
**mark_value** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**nice_value** | **int** |  | [optional] 
**rst_ttl** | **int** |  | [optional] 
**sc_expr** | **str** |  | [optional] 
**sc_id** | **int** |  | [optional] 
**sc_idx** | **int** |  | [optional] 
**sc_int** | **int** |  | [optional] 
**spoe_engine** | **str** |  | [optional] 
**spoe_group** | **str** |  | [optional] 
**timeout** | **int** |  | [optional] 
**tos_value** | **str** |  | [optional] 
**type** | **str** |  | 
**var_format** | **str** |  | [optional] 
**var_name** | **str** |  | [optional] 
**var_scope** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tcp_response_rule import TcpResponseRule

# TODO update the JSON string below
json = "{}"
# create an instance of TcpResponseRule from a JSON string
tcp_response_rule_instance = TcpResponseRule.from_json(json)
# print the JSON string representation of the object
print(TcpResponseRule.to_json())

# convert the object into a dict
tcp_response_rule_dict = tcp_response_rule_instance.to_dict()
# create an instance of TcpResponseRule from a dict
tcp_response_rule_from_dict = TcpResponseRule.from_dict(tcp_response_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


