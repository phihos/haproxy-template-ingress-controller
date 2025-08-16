# SpoeGroup

SPOE group section configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**messages** | **str** |  | [optional] 
**name** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.spoe_group import SpoeGroup

# TODO update the JSON string below
json = "{}"
# create an instance of SpoeGroup from a JSON string
spoe_group_instance = SpoeGroup.from_json(json)
# print the JSON string representation of the object
print(SpoeGroup.to_json())

# convert the object into a dict
spoe_group_dict = spoe_group_instance.to_dict()
# create an instance of SpoeGroup from a dict
spoe_group_from_dict = SpoeGroup.from_dict(spoe_group_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


