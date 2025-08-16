# HttpResponseRule

HAProxy HTTP response rule configuration (corresponds to http-response directives)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**acl_file** | **str** |  | [optional] 
**acl_keyfmt** | **str** |  | [optional] 
**bandwidth_limit_limit** | **str** |  | [optional] 
**bandwidth_limit_name** | **str** |  | [optional] 
**bandwidth_limit_period** | **str** |  | [optional] 
**cache_name** | **str** |  | [optional] 
**capture_id** | **int** |  | [optional] 
**capture_sample** | **str** |  | [optional] 
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**deny_status** | **int** |  | [optional] 
**expr** | **str** |  | [optional] 
**hdr_format** | **str** |  | [optional] 
**hdr_match** | **str** |  | [optional] 
**hdr_method** | **str** |  | [optional] 
**hdr_name** | **str** |  | [optional] 
**log_level** | **str** |  | [optional] 
**lua_action** | **str** |  | [optional] 
**lua_params** | **str** |  | [optional] 
**map_file** | **str** |  | [optional] 
**map_keyfmt** | **str** |  | [optional] 
**map_valuefmt** | **str** |  | [optional] 
**mark_value** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**nice_value** | **int** |  | [optional] 
**redir_code** | **int** |  | [optional] 
**redir_option** | **str** |  | [optional] 
**redir_type** | **str** |  | [optional] 
**redir_value** | **str** |  | [optional] 
**return_content** | **str** |  | [optional] 
**return_content_format** | **str** |  | [optional] 
**return_content_type** | **str** |  | [optional] 
**return_hdrs** | [**List[ReturnHeader]**](ReturnHeader.md) |  | [optional] 
**return_status_code** | **int** |  | [optional] 
**rst_ttl** | **int** |  | [optional] 
**sc_expr** | **str** |  | [optional] 
**sc_id** | **int** |  | [optional] 
**sc_idx** | **int** |  | [optional] 
**sc_int** | **int** |  | [optional] 
**spoe_engine** | **str** |  | [optional] 
**spoe_group** | **str** |  | [optional] 
**status** | **int** |  | [optional] 
**status_reason** | **str** |  | [optional] 
**strict_mode** | **str** |  | [optional] 
**timeout** | **str** |  | [optional] 
**timeout_type** | **str** |  | [optional] 
**tos_value** | **str** |  | [optional] 
**track_sc_key** | **str** |  | [optional] 
**track_sc_stick_counter** | **int** |  | [optional] 
**track_sc_table** | **str** |  | [optional] 
**type** | **str** |  | 
**var_expr** | **str** |  | [optional] 
**var_format** | **str** |  | [optional] 
**var_name** | **str** |  | [optional] 
**var_scope** | **str** |  | [optional] 
**wait_at_least** | **int** |  | [optional] 
**wait_time** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.http_response_rule import HttpResponseRule

# TODO update the JSON string below
json = "{}"
# create an instance of HttpResponseRule from a JSON string
http_response_rule_instance = HttpResponseRule.from_json(json)
# print the JSON string representation of the object
print(HttpResponseRule.to_json())

# convert the object into a dict
http_response_rule_dict = http_response_rule_instance.to_dict()
# create an instance of HttpResponseRule from a dict
http_response_rule_from_dict = HttpResponseRule.from_dict(http_response_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


