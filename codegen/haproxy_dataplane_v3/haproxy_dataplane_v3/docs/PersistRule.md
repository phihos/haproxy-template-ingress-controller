# PersistRule


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**rdp_cookie_name** | **str** |  | [optional] 
**type** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.persist_rule import PersistRule

# TODO update the JSON string below
json = "{}"
# create an instance of PersistRule from a JSON string
persist_rule_instance = PersistRule.from_json(json)
# print the JSON string representation of the object
print(PersistRule.to_json())

# convert the object into a dict
persist_rule_dict = persist_rule_instance.to_dict()
# create an instance of PersistRule from a dict
persist_rule_from_dict = PersistRule.from_dict(persist_rule_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


