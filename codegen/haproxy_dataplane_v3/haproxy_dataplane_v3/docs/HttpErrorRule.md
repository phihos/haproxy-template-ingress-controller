# HttpErrorRule

HAProxy HTTP error rule configuration (corresponds to http-error directives)

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | **object** |  | [optional] 
**return_content** | **str** |  | [optional] 
**return_content_format** | **str** |  | [optional] 
**return_content_type** | **str** |  | [optional] 
**return_hdrs** | [**List[ReturnHeader]**](ReturnHeader.md) |  | [optional] 
**status** | **int** |  | 
**type** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.http_error_rule import HttpErrorRule

# TODO update the JSON string below
json = "{}"
# create an instance of HttpErrorRule from a JSON string
http_error_rule_instance = HttpErrorRule.from_json(json)
# print the JSON string representation of the object
print(HttpErrorRule.to_json())

# convert the object into a dict
http_error_rule_dict = http_error_rule_instance.to_dict()
# create an instance of HttpErrorRule from a dict
http_error_rule_from_dict = HttpErrorRule.from_dict(http_error_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


