# Originalto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **str** |  | 
**var_except** | **str** |  | [optional] 
**header** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.originalto import Originalto

# TODO update the JSON string below
json = "{}"
# create an instance of Originalto from a JSON string
originalto_instance = Originalto.from_json(json)
# print the JSON string representation of the object
print(Originalto.to_json())

# convert the object into a dict
originalto_dict = originalto_instance.to_dict()
# create an instance of Originalto from a dict
originalto_from_dict = Originalto.from_dict(originalto_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


