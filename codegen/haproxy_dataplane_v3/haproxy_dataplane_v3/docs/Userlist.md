# Userlist

Userlist with all it's children resources

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**groups** | **object** |  | [optional] 
**users** | **object** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.userlist import Userlist

# TODO update the JSON string below
json = "{}"
# create an instance of Userlist from a JSON string
userlist_instance = Userlist.from_json(json)
# print the JSON string representation of the object
print(Userlist.to_json())

# convert the object into a dict
userlist_dict = userlist_instance.to_dict()
# create an instance of Userlist from a dict
userlist_from_dict = Userlist.from_dict(userlist_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


