# HttpchkParams


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**host** | **str** |  | [optional] 
**method** | **str** |  | [optional] 
**uri** | **str** |  | [optional] 
**version** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.httpchk_params import HttpchkParams

# TODO update the JSON string below
json = "{}"
# create an instance of HttpchkParams from a JSON string
httpchk_params_instance = HttpchkParams.from_json(json)
# print the JSON string representation of the object
print(HttpchkParams.to_json())

# convert the object into a dict
httpchk_params_dict = httpchk_params_instance.to_dict()
# create an instance of HttpchkParams from a dict
httpchk_params_from_dict = HttpchkParams.from_dict(httpchk_params_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


