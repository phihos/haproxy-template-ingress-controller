# Nameserver

Nameserver used in Runtime DNS configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **str** |  | 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**port** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.nameserver import Nameserver

# TODO update the JSON string below
json = "{}"
# create an instance of Nameserver from a JSON string
nameserver_instance = Nameserver.from_json(json)
# print the JSON string representation of the object
print(Nameserver.to_json())

# convert the object into a dict
nameserver_dict = nameserver_instance.to_dict()
# create an instance of Nameserver from a dict
nameserver_from_dict = Nameserver.from_dict(nameserver_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


