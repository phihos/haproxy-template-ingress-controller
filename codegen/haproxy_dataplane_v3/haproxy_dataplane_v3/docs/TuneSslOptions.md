# TuneSslOptions


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cachesize** | **int** |  | [optional] 
**capture_buffer_size** | **int** |  | [optional] 
**ctx_cache_size** | **int** |  | [optional] 
**default_dh_param** | **int** |  | [optional] 
**force_private_cache** | **bool** |  | [optional] 
**keylog** | **str** |  | [optional] 
**lifetime** | **int** |  | [optional] 
**maxrecord** | **int** |  | [optional] 
**ocsp_update_max_delay** | **int** |  | [optional] 
**ocsp_update_min_delay** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.tune_ssl_options import TuneSslOptions

# TODO update the JSON string below
json = "{}"
# create an instance of TuneSslOptions from a JSON string
tune_ssl_options_instance = TuneSslOptions.from_json(json)
# print the JSON string representation of the object
print(TuneSslOptions.to_json())

# convert the object into a dict
tune_ssl_options_dict = tune_ssl_options_instance.to_dict()
# create an instance of TuneSslOptions from a dict
tune_ssl_options_from_dict = TuneSslOptions.from_dict(tune_ssl_options_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


