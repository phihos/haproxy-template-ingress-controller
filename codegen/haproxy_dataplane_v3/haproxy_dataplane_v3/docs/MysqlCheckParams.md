# MysqlCheckParams


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**client_version** | **str** |  | [optional] 
**username** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.mysql_check_params import MysqlCheckParams

# TODO update the JSON string below
json = "{}"
# create an instance of MysqlCheckParams from a JSON string
mysql_check_params_instance = MysqlCheckParams.from_json(json)
# print the JSON string representation of the object
print(MysqlCheckParams.to_json())

# convert the object into a dict
mysql_check_params_dict = mysql_check_params_instance.to_dict()
# create an instance of MysqlCheckParams from a dict
mysql_check_params_from_dict = MysqlCheckParams.from_dict(mysql_check_params_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


