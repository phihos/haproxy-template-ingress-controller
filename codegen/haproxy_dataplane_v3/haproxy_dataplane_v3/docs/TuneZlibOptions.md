# TuneZlibOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**memlevel** | **int** |  | [optional] 
**windowsize** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tune_zlib_options import TuneZlibOptions

# TODO update the JSON string below
json = "{}"
# create an instance of TuneZlibOptions from a JSON string
tune_zlib_options_instance = TuneZlibOptions.from_json(json)
# print the JSON string representation of the object
print(TuneZlibOptions.to_json())

# convert the object into a dict
tune_zlib_options_dict = tune_zlib_options_instance.to_dict()
# create an instance of TuneZlibOptions from a dict
tune_zlib_options_from_dict = TuneZlibOptions.from_dict(tune_zlib_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


