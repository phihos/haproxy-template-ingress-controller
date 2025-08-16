# Errorfile


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **int** |  | [optional] 
**file** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.errorfile import Errorfile

# TODO update the JSON string below
json = "{}"
# create an instance of Errorfile from a JSON string
errorfile_instance = Errorfile.from_json(json)
# print the JSON string representation of the object
print(Errorfile.to_json())

# convert the object into a dict
errorfile_dict = errorfile_instance.to_dict()
# create an instance of Errorfile from a dict
errorfile_from_dict = Errorfile.from_dict(errorfile_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


