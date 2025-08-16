# HttpCheck


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**addr** | **str** |  | [optional] 
**alpn** | **str** |  | [optional] 
**body** | **str** |  | [optional] 
**body_log_format** | **str** |  | [optional] 
**check_comment** | **str** |  | [optional] 
**default** | **bool** |  | [optional] 
**error_status** | **str** |  | [optional] 
**exclamation_mark** | **bool** |  | [optional] 
**headers** | [**List[ReturnHeader]**](ReturnHeader.md) |  | [optional] 
**linger** | **bool** |  | [optional] 
**match** | **str** |  | [optional] 
**metadata** | **object** |  | [optional] 
**method** | **str** |  | [optional] 
**min_recv** | **int** |  | [optional] 
**ok_status** | **str** |  | [optional] 
**on_error** | **str** |  | [optional] 
**on_success** | **str** |  | [optional] 
**pattern** | **str** |  | [optional] 
**port** | **int** |  | [optional] 
**port_string** | **str** |  | [optional] 
**proto** | **str** |  | [optional] 
**send_proxy** | **bool** |  | [optional] 
**sni** | **str** |  | [optional] 
**ssl** | **bool** |  | [optional] 
**status_code** | **str** |  | [optional] 
**tout_status** | **str** |  | [optional] 
**type** | **str** |  | 
**uri** | **str** |  | [optional] 
**uri_log_format** | **str** |  | [optional] 
**var_expr** | **str** |  | [optional] 
**var_format** | **str** |  | [optional] 
**var_name** | **str** |  | [optional] 
**var_scope** | **str** |  | [optional] 
**version** | **str** |  | [optional] 
**via_socks4** | **bool** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.http_check import HttpCheck

# TODO update the JSON string below
json = "{}"
# create an instance of HttpCheck from a JSON string
http_check_instance = HttpCheck.from_json(json)
# print the JSON string representation of the object
print(HttpCheck.to_json())

# convert the object into a dict
http_check_dict = http_check_instance.to_dict()
# create an instance of HttpCheck from a dict
http_check_from_dict = HttpCheck.from_dict(http_check_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


