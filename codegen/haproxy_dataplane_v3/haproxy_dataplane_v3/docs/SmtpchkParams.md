# SmtpchkParams


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**domain** | **str** |  | [optional] 
**hello** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.smtpchk_params import SmtpchkParams

# TODO update the JSON string below
json = "{}"
# create an instance of SmtpchkParams from a JSON string
smtpchk_params_instance = SmtpchkParams.from_json(json)
# print the JSON string representation of the object
print(SmtpchkParams.to_json())

# convert the object into a dict
smtpchk_params_dict = smtpchk_params_instance.to_dict()
# create an instance of SmtpchkParams from a dict
smtpchk_params_from_dict = SmtpchkParams.from_dict(smtpchk_params_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


