# AwsRegion

AWS region configuration

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**access_key_id** | **str** | AWS Access Key ID. | [optional] 
**allowlist** | [**List[AwsFilters]**](AwsFilters.md) | Specify the AWS filters used to filter the EC2 instances to add | [optional] 
**denylist** | [**List[AwsFilters]**](AwsFilters.md) | Specify the AWS filters used to filter the EC2 instances to ignore | [optional] 
**description** | **str** |  | [optional] 
**enabled** | **bool** |  | 
**id** | **str** | Auto generated ID. | [optional] [readonly] 
**ipv4_address** | **str** | Select which IPv4 address the Service Discovery has to use for the backend server entry | 
**name** | **str** |  | 
**region** | **str** |  | 
**retry_timeout** | **int** | Duration in seconds in-between data pulling requests to the AWS region | 
**secret_access_key** | **str** | AWS Secret Access Key. | [optional] 
**server_slots_base** | **int** |  | [optional] 
**server_slots_growth_increment** | **int** |  | [optional] 
**server_slots_growth_type** | **str** |  | [optional] [default to 'exponential']

## Example

```python
from haproxy_dataplane_v3.models.aws_region import AwsRegion

# TODO update the JSON string below
json = "{}"
# create an instance of AwsRegion from a JSON string
aws_region_instance = AwsRegion.from_json(json)
# print the JSON string representation of the object
print(AwsRegion.to_json())

# convert the object into a dict
aws_region_dict = aws_region_instance.to_dict()
# create an instance of AwsRegion from a dict
aws_region_from_dict = AwsRegion.from_dict(aws_region_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


