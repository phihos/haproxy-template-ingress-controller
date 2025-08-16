# PgsqlCheckParams


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**username** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.pgsql_check_params import PgsqlCheckParams

# TODO update the JSON string below
json = "{}"
# create an instance of PgsqlCheckParams from a JSON string
pgsql_check_params_instance = PgsqlCheckParams.from_json(json)
# print the JSON string representation of the object
print(PgsqlCheckParams.to_json())

# convert the object into a dict
pgsql_check_params_dict = pgsql_check_params_instance.to_dict()
# create an instance of PgsqlCheckParams from a dict
pgsql_check_params_from_dict = PgsqlCheckParams.from_dict(pgsql_check_params_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


