# Program

HAProxy program configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**command** | **str** | The command to be run, with flags and options. | 
**group** | **str** | The group to run the command as, if different than the HAProxy group. | [optional] 
**metadata** | **object** |  | [optional] 
**name** | **str** |  | 
**start_on_reload** | **str** | HAProxy stops and recreates child programs at reload. | [optional] 
**user** | **str** | The user to run the command as, if different than the HAProxy user. | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.program import Program

# TODO update the JSON string below
json = "{}"
# create an instance of Program from a JSON string
program_instance = Program.from_json(json)
# print the JSON string representation of the object
print(Program.to_json())

# convert the object into a dict
program_dict = program_instance.to_dict()
# create an instance of Program from a dict
program_from_dict = Program.from_dict(program_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


