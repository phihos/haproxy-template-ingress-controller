# SslOcspResponseResponses


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cert_status** | **str** |  | [optional] 
**certificate_id** | [**SslCertificateIdCertificateId**](SslCertificateIdCertificateId.md) |  | [optional] 
**next_update** | **date** |  | [optional] 
**revocation_reason** | **str** |  | [optional] 
**this_update** | **date** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.ssl_ocsp_response_responses import SslOcspResponseResponses

# TODO update the JSON string below
json = "{}"
# create an instance of SslOcspResponseResponses from a JSON string
ssl_ocsp_response_responses_instance = SslOcspResponseResponses.from_json(json)
# print the JSON string representation of the object
print(SslOcspResponseResponses.to_json())

# convert the object into a dict
ssl_ocsp_response_responses_dict = ssl_ocsp_response_responses_instance.to_dict()
# create an instance of SslOcspResponseResponses from a dict
ssl_ocsp_response_responses_from_dict = SslOcspResponseResponses.from_dict(ssl_ocsp_response_responses_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


