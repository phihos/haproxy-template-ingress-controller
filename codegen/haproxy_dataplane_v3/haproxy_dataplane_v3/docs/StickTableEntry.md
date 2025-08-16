# StickTableEntry

One entry in stick table

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bytes_in_cnt** | **int** |  | [optional] 
**bytes_in_rate** | **int** |  | [optional] 
**bytes_out_cnt** | **int** |  | [optional] 
**bytes_out_rate** | **int** |  | [optional] 
**conn_cnt** | **int** |  | [optional] 
**conn_cur** | **int** |  | [optional] 
**conn_rate** | **int** |  | [optional] 
**exp** | **int** |  | [optional] 
**glitch_cnt** | **int** |  | [optional] 
**glitch_rate** | **int** |  | [optional] 
**gpc0** | **int** |  | [optional] 
**gpc0_rate** | **int** |  | [optional] 
**gpc1** | **int** |  | [optional] 
**gpc1_rate** | **int** |  | [optional] 
**gpt0** | **int** |  | [optional] 
**http_err_cnt** | **int** |  | [optional] 
**http_err_rate** | **int** |  | [optional] 
**http_req_cnt** | **int** |  | [optional] 
**http_req_rate** | **int** |  | [optional] 
**id** | **str** |  | [optional] 
**key** | **str** |  | [optional] 
**server_id** | **int** |  | [optional] 
**sess_cnt** | **int** |  | [optional] 
**sess_rate** | **int** |  | [optional] 
**use** | **bool** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.stick_table_entry import StickTableEntry

# TODO update the JSON string below
json = "{}"
# create an instance of StickTableEntry from a JSON string
stick_table_entry_instance = StickTableEntry.from_json(json)
# print the JSON string representation of the object
print(StickTableEntry.to_json())

# convert the object into a dict
stick_table_entry_dict = stick_table_entry_instance.to_dict()
# create an instance of StickTableEntry from a dict
stick_table_entry_from_dict = StickTableEntry.from_dict(stick_table_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


