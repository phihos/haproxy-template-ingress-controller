# SslCrtListEntry

SSL Crt List Entry

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**file** | **str** |  | [optional] 
**line_number** | **int** |  | [optional] 
**sni_filter** | **List[str]** |  | [optional] 
**ssl_bind_config** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_crt_list_entry import SslCrtListEntry

# TODO update the JSON string below
json = "{}"
# create an instance of SslCrtListEntry from a JSON string
ssl_crt_list_entry_instance = SslCrtListEntry.from_json(json)
# print the JSON string representation of the object
print(SslCrtListEntry.to_json())

# convert the object into a dict
ssl_crt_list_entry_dict = ssl_crt_list_entry_instance.to_dict()
# create an instance of SslCrtListEntry from a dict
ssl_crt_list_entry_from_dict = SslCrtListEntry.from_dict(ssl_crt_list_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


