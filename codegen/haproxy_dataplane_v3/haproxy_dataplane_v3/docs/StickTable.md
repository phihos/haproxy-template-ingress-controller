# StickTable

Stick Table Information

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fields** | [**List[StickTableFieldsInner]**](StickTableFieldsInner.md) |  | [optional] 
**name** | **str** |  | [optional] 
**size** | **int** |  | [optional] 
**type** | **str** |  | [optional] 
**used** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.stick_table import StickTable

# TODO update the JSON string below
json = "{}"
# create an instance of StickTable from a JSON string
stick_table_instance = StickTable.from_json(json)
# print the JSON string representation of the object
print(StickTable.to_json())

# convert the object into a dict
stick_table_dict = stick_table_instance.to_dict()
# create an instance of StickTable from a dict
stick_table_from_dict = StickTable.from_dict(stick_table_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


