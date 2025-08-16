# SslCrtListFile

A file referencing one or more certificates with their configuration.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**description** | **str** |  | [optional] 
**file** | **str** |  | [optional] 
**size** | **int** | File size in bytes. | [optional] 
**storage_name** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_crt_list_file import SslCrtListFile

# TODO update the JSON string below
json = "{}"
# create an instance of SslCrtListFile from a JSON string
ssl_crt_list_file_instance = SslCrtListFile.from_json(json)
# print the JSON string representation of the object
print(SslCrtListFile.to_json())

# convert the object into a dict
ssl_crt_list_file_dict = ssl_crt_list_file_instance.to_dict()
# create an instance of SslCrtListFile from a dict
ssl_crt_list_file_from_dict = SslCrtListFile.from_dict(ssl_crt_list_file_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


