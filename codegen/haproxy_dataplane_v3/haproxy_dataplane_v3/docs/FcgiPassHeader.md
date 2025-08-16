# FcgiPassHeader

Specifies the name of a request header to pass to the FastCGI application. Optionally, you can follow it with an ACL-based condition, in which case the FastCGI application evaluates it only if the condition is true. Most request headers are already available to the FastCGI application with the prefix \"HTTP\". Thus, you only need this directive to pass headers that are purposefully omitted. Currently, the headers \"Authorization\", \"Proxy-Authorization\", and hop-by-hop headers are omitted. Note that the headers \"Content-type\" and \"Content-length\" never pass to the FastCGI application because they are already converted into parameters.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cond** | **str** |  | [optional] 
**cond_test** | **str** |  | [optional] 
**name** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.fcgi_pass_header import FcgiPassHeader

# TODO update the JSON string below
json = "{}"
# create an instance of FcgiPassHeader from a JSON string
fcgi_pass_header_instance = FcgiPassHeader.from_json(json)
# print the JSON string representation of the object
print(FcgiPassHeader.to_json())

# convert the object into a dict
fcgi_pass_header_dict = fcgi_pass_header_instance.to_dict()
# create an instance of FcgiPassHeader from a dict
fcgi_pass_header_from_dict = FcgiPassHeader.from_dict(fcgi_pass_header_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


