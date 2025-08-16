# GeneralFile

General use file

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**description** | **str** |  | [optional] 
**file** | **str** |  | [optional] 
**id** | **str** |  | [optional] 
**size** | **int** | File size in bytes. | [optional] 
**storage_name** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.general_file import GeneralFile

# TODO update the JSON string below
json = "{}"
# create an instance of GeneralFile from a JSON string
general_file_instance = GeneralFile.from_json(json)
# print the JSON string representation of the object
print(GeneralFile.to_json())

# convert the object into a dict
general_file_dict = general_file_instance.to_dict()
# create an instance of GeneralFile from a dict
general_file_from_dict = GeneralFile.from_dict(general_file_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


