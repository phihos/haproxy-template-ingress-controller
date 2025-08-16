# SiteService


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**http_connection_mode** | **str** |  | [optional] 
**listeners** | [**List[Bind]**](Bind.md) |  | [optional] 
**maxconn** | **int** |  | [optional] 
**mode** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.site_service import SiteService

# TODO update the JSON string below
json = "{}"
# create an instance of SiteService from a JSON string
site_service_instance = SiteService.from_json(json)
# print the JSON string representation of the object
print(SiteService.to_json())

# convert the object into a dict
site_service_dict = site_service_instance.to_dict()
# create an instance of SiteService from a dict
site_service_from_dict = SiteService.from_dict(site_service_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


