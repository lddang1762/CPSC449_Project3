import boto3

def clearTable(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:9000")

    table = dynamodb.Table("Polls")
    if table:
        table.delete()

def initPolls(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:9000")

    table = dynamodb.create_table(
        TableName='Polls',
        KeySchema=[
            {
                'AttributeName': 'pollId',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'startDate',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'pollId',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'startDate',
                'AttributeType': 'N'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        },
    )

    return table


if __name__ == '__main__':
    clearTable()
    pollTable = initPolls()
    print("Table status:", pollTable.table_status)
