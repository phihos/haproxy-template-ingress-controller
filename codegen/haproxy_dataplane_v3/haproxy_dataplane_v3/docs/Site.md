# Site

Site configuration. Sites are considered as one service and all farms connected to that service. Farms are connected to service using use-backend and default_backend directives. Sites let you configure simple HAProxy configurations, for more advanced options use /haproxy/configuration endpoints. 

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**farms** | [**List[SiteFarmsInner]**](SiteFarmsInner.md) |  | [optional] 
**name** | **str** |  | 
**service** | [**SiteService**](SiteService.md) |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.site import Site

# TODO update the JSON string below
json = "{}"
# create an instance of Site from a JSON string
site_instance = Site.from_json(json)
# print the JSON string representation of the object
print(Site.to_json())

# convert the object into a dict
site_dict = site_instance.to_dict()
# create an instance of Site from a dict
site_from_dict = Site.from_dict(site_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


