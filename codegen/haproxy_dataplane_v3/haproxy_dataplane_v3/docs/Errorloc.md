# Errorloc


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** |  | 
**metadata** | **object** |  | [optional] 
**url** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.errorloc import Errorloc

# TODO update the JSON string below
json = "{}"
# create an instance of Errorloc from a JSON string
errorloc_instance = Errorloc.from_json(json)
# print the JSON string representation of the object
print(Errorloc.to_json())

# convert the object into a dict
errorloc_dict = errorloc_instance.to_dict()
# create an instance of Errorloc from a dict
errorloc_from_dict = Errorloc.from_dict(errorloc_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


