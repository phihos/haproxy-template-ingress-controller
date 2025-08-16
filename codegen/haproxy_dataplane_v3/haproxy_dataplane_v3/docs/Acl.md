# Acl

The use of Access Control Lists (ACL) provides a flexible solution to perform content switching and generally to take decisions based on content extracted from the request, the response or any environmental status. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**acl_name** | **str** |  | 
**criterion** | **str** |  | 
**metadata** | **object** |  | [optional] 
**value** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.acl import Acl

# TODO update the JSON string below
json = "{}"
# create an instance of Acl from a JSON string
acl_instance = Acl.from_json(json)
# print the JSON string representation of the object
print(Acl.to_json())

# convert the object into a dict
acl_dict = acl_instance.to_dict()
# create an instance of Acl from a dict
acl_from_dict = Acl.from_dict(acl_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


