# Forwardfor


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enabled** | **str** |  | 
**var_except** | **str** |  | [optional] 
**header** | **str** |  | [optional] 
**ifnone** | **bool** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.forwardfor import Forwardfor

# TODO update the JSON string below
json = "{}"
# create an instance of Forwardfor from a JSON string
forwardfor_instance = Forwardfor.from_json(json)
# print the JSON string representation of the object
print(Forwardfor.to_json())

# convert the object into a dict
forwardfor_dict = forwardfor_instance.to_dict()
# create an instance of Forwardfor from a dict
forwardfor_from_dict = Forwardfor.from_dict(forwardfor_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


