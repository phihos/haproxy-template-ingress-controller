# HttpAfterResponseRule

HAProxy HTTP after response rule configuration (corresponds to http-after-response directives)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**acl_file** | **str** |  | [optional] 
**acl_keyfmt** | **str** |  | [optional] 
**capture_id** | **int** |  | [optional] 
**capture_len** | **int** |  | [optional] 
**capture_sample** | **str** |  | [optional] 
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**hdr_format** | **str** |  | [optional] 
**hdr_match** | **str** |  | [optional] 
**hdr_method** | **str** |  | [optional] 
**hdr_name** | **str** |  | [optional] 
**log_level** | **str** |  | [optional] 
**map_file** | **str** |  | [optional] 
**map_keyfmt** | **str** |  | [optional] 
**map_valuefmt** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**sc_expr** | **str** |  | [optional] 
**sc_id** | **int** |  | [optional] 
**sc_idx** | **int** |  | [optional] 
**sc_int** | **int** |  | [optional] 
**status** | **int** |  | [optional] 
**status_reason** | **str** |  | [optional] 
**strict_mode** | **str** |  | [optional] 
**type** | **str** |  | 
**var_expr** | **str** |  | [optional] 
**var_format** | **str** |  | [optional] 
**var_name** | **str** |  | [optional] 
**var_scope** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.http_after_response_rule import HttpAfterResponseRule

# TODO update the JSON string below
json = "{}"
# create an instance of HttpAfterResponseRule from a JSON string
http_after_response_rule_instance = HttpAfterResponseRule.from_json(json)
# print the JSON string representation of the object
print(HttpAfterResponseRule.to_json())

# convert the object into a dict
http_after_response_rule_dict = http_after_response_rule_instance.to_dict()
# create an instance of HttpAfterResponseRule from a dict
http_after_response_rule_from_dict = HttpAfterResponseRule.from_dict(http_after_response_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


