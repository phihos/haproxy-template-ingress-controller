# GlobalBaseHardenRejectPrivilegedPorts


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**quic** | **str** |  | [optional] 
**tcp** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.global_base_harden_reject_privileged_ports import GlobalBaseHardenRejectPrivilegedPorts

# TODO update the JSON string below
json = "{}"
# create an instance of GlobalBaseHardenRejectPrivilegedPorts from a JSON string
global_base_harden_reject_privileged_ports_instance = GlobalBaseHardenRejectPrivilegedPorts.from_json(json)
# print the JSON string representation of the object
print(GlobalBaseHardenRejectPrivilegedPorts.to_json())

# convert the object into a dict
global_base_harden_reject_privileged_ports_dict = global_base_harden_reject_privileged_ports_instance.to_dict()
# create an instance of GlobalBaseHardenRejectPrivilegedPorts from a dict
global_base_harden_reject_privileged_ports_from_dict = GlobalBaseHardenRejectPrivilegedPorts.from_dict(global_base_harden_reject_privileged_ports_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


