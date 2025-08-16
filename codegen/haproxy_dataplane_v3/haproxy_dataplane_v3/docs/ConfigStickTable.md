# ConfigStickTable


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**expire** | **int** |  | [optional] 
**keylen** | **int** |  | [optional] 
**metadata** | **object** |  | [optional] 
**nopurge** | **bool** |  | [optional] 
**peers** | **str** |  | [optional] 
**recv_only** | **bool** |  | [optional] 
**size** | **int** |  | [optional] 
**srvkey** | **str** |  | [optional] 
**store** | **str** |  | [optional] 
**type** | **str** |  | [optional] 
**write_to** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.config_stick_table import ConfigStickTable

# TODO update the JSON string below
json = "{}"
# create an instance of ConfigStickTable from a JSON string
config_stick_table_instance = ConfigStickTable.from_json(json)
# print the JSON string representation of the object
print(ConfigStickTable.to_json())

# convert the object into a dict
config_stick_table_dict = config_stick_table_instance.to_dict()
# create an instance of ConfigStickTable from a dict
config_stick_table_from_dict = ConfigStickTable.from_dict(config_stick_table_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


