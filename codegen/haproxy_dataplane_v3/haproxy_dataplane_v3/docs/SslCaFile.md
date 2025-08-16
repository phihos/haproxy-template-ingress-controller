# SslCaFile

A file containing one or more SSL/TLS certificates and keys

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**count** | **str** |  | [optional] 
**file** | **str** |  | [optional] 
**storage_name** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_ca_file import SslCaFile

# TODO update the JSON string below
json = "{}"
# create an instance of SslCaFile from a JSON string
ssl_ca_file_instance = SslCaFile.from_json(json)
# print the JSON string representation of the object
print(SslCaFile.to_json())

# convert the object into a dict
ssl_ca_file_dict = ssl_ca_file_instance.to_dict()
# create an instance of SslCaFile from a dict
ssl_ca_file_from_dict = SslCaFile.from_dict(ssl_ca_file_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


