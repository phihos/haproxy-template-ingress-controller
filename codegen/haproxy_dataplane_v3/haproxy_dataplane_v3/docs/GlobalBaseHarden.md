# GlobalBaseHarden


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**reject_privileged_ports** | [**GlobalBaseHardenRejectPrivilegedPorts**](GlobalBaseHardenRejectPrivilegedPorts.md) |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.global_base_harden import GlobalBaseHarden

# TODO update the JSON string below
json = "{}"
# create an instance of GlobalBaseHarden from a JSON string
global_base_harden_instance = GlobalBaseHarden.from_json(json)
# print the JSON string representation of the object
print(GlobalBaseHarden.to_json())

# convert the object into a dict
global_base_harden_dict = global_base_harden_instance.to_dict()
# create an instance of GlobalBaseHarden from a dict
global_base_harden_from_dict = GlobalBaseHarden.from_dict(global_base_harden_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


