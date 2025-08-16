# MailersSection

MailersSection with all it's children resources

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**timeout** | **int** |  | [optional] 
**mailer_entries** | **object** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.mailers_section import MailersSection

# TODO update the JSON string below
json = "{}"
# create an instance of MailersSection from a JSON string
mailers_section_instance = MailersSection.from_json(json)
# print the JSON string representation of the object
print(MailersSection.to_json())

# convert the object into a dict
mailers_section_dict = mailers_section_instance.to_dict()
# create an instance of MailersSection from a dict
mailers_section_from_dict = MailersSection.from_dict(mailers_section_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


