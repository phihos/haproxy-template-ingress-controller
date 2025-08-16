# SpoeTransaction

SPOE configuration transaction

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version** | **int** |  | [optional] 
**id** | **str** |  | [optional] 
**status** | **str** |  | [optional] 

## Example

```python
from haproxy_dataplane_v3.models.spoe_transaction import SpoeTransaction

# TODO update the JSON string below
json = "{}"
# create an instance of SpoeTransaction from a JSON string
spoe_transaction_instance = SpoeTransaction.from_json(json)
# print the JSON string representation of the object
print(SpoeTransaction.to_json())

# convert the object into a dict
spoe_transaction_dict = spoe_transaction_instance.to_dict()
# create an instance of SpoeTransaction from a dict
spoe_transaction_from_dict = SpoeTransaction.from_dict(spoe_transaction_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


