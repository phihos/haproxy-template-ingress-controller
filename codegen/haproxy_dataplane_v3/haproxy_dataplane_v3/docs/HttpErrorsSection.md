# HttpErrorsSection

A globally declared group of HTTP errors

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**error_files** | [**List[Errorfile]**](Errorfile.md) |  | 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 

## Example

```python
from haproxy_dataplane_v3.models.http_errors_section import HttpErrorsSection

# TODO update the JSON string below
json = "{}"
# create an instance of HttpErrorsSection from a JSON string
http_errors_section_instance = HttpErrorsSection.from_json(json)
# print the JSON string representation of the object
print(HttpErrorsSection.to_json())

# convert the object into a dict
http_errors_section_dict = http_errors_section_instance.to_dict()
# create an instance of HttpErrorsSection from a dict
http_errors_section_from_dict = HttpErrorsSection.from_dict(http_errors_section_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


