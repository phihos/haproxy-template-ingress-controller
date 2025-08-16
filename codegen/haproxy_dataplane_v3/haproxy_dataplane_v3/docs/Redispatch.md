# Redispatch


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **str** |  | 
**interval** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.redispatch import Redispatch

# TODO update the JSON string below
json = "{}"
# create an instance of Redispatch from a JSON string
redispatch_instance = Redispatch.from_json(json)
# print the JSON string representation of the object
print(Redispatch.to_json())

# convert the object into a dict
redispatch_dict = redispatch_instance.to_dict()
# create an instance of Redispatch from a dict
redispatch_from_dict = Redispatch.from_dict(redispatch_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


