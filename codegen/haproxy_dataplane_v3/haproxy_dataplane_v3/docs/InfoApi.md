# InfoApi


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**build_date** | **datetime** | HAProxy Dataplane API build date | [optional] 
**version** | **str** | HAProxy Dataplane API version string | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.info_api import InfoApi

# TODO update the JSON string below
json = "{}"
# create an instance of InfoApi from a JSON string
info_api_instance = InfoApi.from_json(json)
# print the JSON string representation of the object
print(InfoApi.to_json())

# convert the object into a dict
info_api_dict = info_api_instance.to_dict()
# create an instance of InfoApi from a dict
info_api_from_dict = InfoApi.from_dict(info_api_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


