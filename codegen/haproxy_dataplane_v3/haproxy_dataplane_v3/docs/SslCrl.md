# SslCrl

A file containing one or more SSL/TLS CRLs

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**description** | **str** |  | [optional] 
**file** | **str** |  | [optional] 
**storage_name** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_crl import SslCrl

# TODO update the JSON string below
json = "{}"
# create an instance of SslCrl from a JSON string
ssl_crl_instance = SslCrl.from_json(json)
# print the JSON string representation of the object
print(SslCrl.to_json())

# convert the object into a dict
ssl_crl_dict = ssl_crl_instance.to_dict()
# create an instance of SslCrl from a dict
ssl_crl_from_dict = SslCrl.from_dict(ssl_crl_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


