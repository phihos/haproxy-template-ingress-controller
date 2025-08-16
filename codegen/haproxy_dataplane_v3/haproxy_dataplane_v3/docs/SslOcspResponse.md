# SslOcspResponse

SSL OCSP Response

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**base64_response** | **str** |  | [optional] 
**ocsp_response_status** | **str** |  | [optional] 
**produced_at** | **date** |  | [optional] 
**responder_id** | **List[str]** |  | [optional] 
**response_type** | **str** |  | [optional] 
**responses** | [**SslOcspResponseResponses**](SslOcspResponseResponses.md) |  | [optional] 
**version** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_ocsp_response import SslOcspResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SslOcspResponse from a JSON string
ssl_ocsp_response_instance = SslOcspResponse.from_json(json)
# print the JSON string representation of the object
print(SslOcspResponse.to_json())

# convert the object into a dict
ssl_ocsp_response_dict = ssl_ocsp_response_instance.to_dict()
# create an instance of SslOcspResponse from a dict
ssl_ocsp_response_from_dict = SslOcspResponse.from_dict(ssl_ocsp_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


