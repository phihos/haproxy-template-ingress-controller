# StickRule

Define a pattern used to create an entry in a stickiness table or matching condition or associate a user to a server.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**pattern** | **str** |  | 
**table** | **str** |  | [optional] 
**type** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.stick_rule import StickRule

# TODO update the JSON string below
json = "{}"
# create an instance of StickRule from a JSON string
stick_rule_instance = StickRule.from_json(json)
# print the JSON string representation of the object
print(StickRule.to_json())

# convert the object into a dict
stick_rule_dict = stick_rule_instance.to_dict()
# create an instance of StickRule from a dict
stick_rule_from_dict = StickRule.from_dict(stick_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


