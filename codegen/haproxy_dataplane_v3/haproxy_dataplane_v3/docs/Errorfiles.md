# Errorfiles


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**codes** | **List[int]** |  | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.errorfiles import Errorfiles

# TODO update the JSON string below
json = "{}"
# create an instance of Errorfiles from a JSON string
errorfiles_instance = Errorfiles.from_json(json)
# print the JSON string representation of the object
print(Errorfiles.to_json())

# convert the object into a dict
errorfiles_dict = errorfiles_instance.to_dict()
# create an instance of Errorfiles from a dict
errorfiles_from_dict = Errorfiles.from_dict(errorfiles_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


