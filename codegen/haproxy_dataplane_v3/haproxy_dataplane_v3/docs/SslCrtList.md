# SslCrtList

SSL Crt List file

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**file** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_crt_list import SslCrtList

# TODO update the JSON string below
json = "{}"
# create an instance of SslCrtList from a JSON string
ssl_crt_list_instance = SslCrtList.from_json(json)
# print the JSON string representation of the object
print(SslCrtList.to_json())

# convert the object into a dict
ssl_crt_list_dict = ssl_crt_list_instance.to_dict()
# create an instance of SslCrtList from a dict
ssl_crt_list_from_dict = SslCrtList.from_dict(ssl_crt_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


