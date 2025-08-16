# AwsFilters


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**key** | **str** | Key to use as filter, using the format specified at https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options | 
**value** | **str** | Value of the filter to use | 

## Example

```python
from haproxy_dataplane_v3.models.aws_filters import AwsFilters

# TODO update the JSON string below
json = "{}"
# create an instance of AwsFilters from a JSON string
aws_filters_instance = AwsFilters.from_json(json)
# print the JSON string representation of the object
print(AwsFilters.to_json())

# convert the object into a dict
aws_filters_dict = aws_filters_instance.to_dict()
# create an instance of AwsFilters from a dict
aws_filters_from_dict = AwsFilters.from_dict(aws_filters_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


