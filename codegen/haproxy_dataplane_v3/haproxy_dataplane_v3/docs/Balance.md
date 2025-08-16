# Balance


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**algorithm** | **str** |  | 
**hash_expression** | **str** |  | [optional] 
**hdr_name** | **str** |  | [optional] 
**hdr_use_domain_only** | **bool** |  | [optional] 
**random_draws** | **int** |  | [optional] 
**rdp_cookie_name** | **str** |  | [optional] 
**uri_depth** | **int** |  | [optional] 
**uri_len** | **int** |  | [optional] 
**uri_path_only** | **bool** |  | [optional] 
**uri_whole** | **bool** |  | [optional] 
**url_param** | **str** |  | [optional] 
**url_param_check_post** | **int** |  | [optional] 
**url_param_max_wait** | **int** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.balance import Balance

# TODO update the JSON string below
json = "{}"
# create an instance of Balance from a JSON string
balance_instance = Balance.from_json(json)
# print the JSON string representation of the object
print(Balance.to_json())

# convert the object into a dict
balance_dict = balance_instance.to_dict()
# create an instance of Balance from a dict
balance_from_dict = Balance.from_dict(balance_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


