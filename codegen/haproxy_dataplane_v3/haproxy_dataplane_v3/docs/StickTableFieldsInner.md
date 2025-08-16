# StickTableFieldsInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_field** | **str** |  | [optional] 
**period** | **int** |  | [optional] 
**type** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.stick_table_fields_inner import StickTableFieldsInner

# TODO update the JSON string below
json = "{}"
# create an instance of StickTableFieldsInner from a JSON string
stick_table_fields_inner_instance = StickTableFieldsInner.from_json(json)
# print the JSON string representation of the object
print(StickTableFieldsInner.to_json())

# convert the object into a dict
stick_table_fields_inner_dict = stick_table_fields_inner_instance.to_dict()
# create an instance of StickTableFieldsInner from a dict
stick_table_fields_inner_from_dict = StickTableFieldsInner.from_dict(stick_table_fields_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


