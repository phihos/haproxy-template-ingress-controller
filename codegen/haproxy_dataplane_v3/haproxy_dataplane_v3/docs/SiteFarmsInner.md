# SiteFarmsInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**balance** | [**Balance**](Balance.md) |  | [optional] 
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**forwardfor** | [**Forwardfor**](Forwardfor.md) |  | [optional] 
**mode** | **str** |  | [optional] 
**name** | **str** |  | 
**servers** | [**List[Server]**](Server.md) |  | [optional] 
**use_as** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.site_farms_inner import SiteFarmsInner

# TODO update the JSON string below
json = "{}"
# create an instance of SiteFarmsInner from a JSON string
site_farms_inner_instance = SiteFarmsInner.from_json(json)
# print the JSON string representation of the object
print(SiteFarmsInner.to_json())

# convert the object into a dict
site_farms_inner_dict = site_farms_inner_instance.to_dict()
# create an instance of SiteFarmsInner from a dict
site_farms_inner_from_dict = SiteFarmsInner.from_dict(site_farms_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


