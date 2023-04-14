import time
import json
import boto3

def lambda_handler(event, context):
    ec2 = boto3.client("ec2")
    ssm = boto3.client("ssm")

    filters = [{'Name':'tag:Name', 'Values':['bastion-server-5g-dp-dev']}]
    describeInstances = ec2.describe_instances(Filters=filters)
    
    for reservation in describeInstances["Reservations"]:
        for instance in reservation["Instances"]:
            if instance["State"]["Name"] == "running":
                instanceId = instance["InstanceId"]

    response = ssm.send_command(
        InstanceIds=[instanceId],
        DocumentName="AWS-RunShellScript",
        Parameters={
            "commands": [
                "cd ~",
                "aws configure set aws_access_key_id '******' && aws configure set aws_secret_access_key '************' && aws configure set aws_session_token '*****************************' && aws configure set region 'us-west-2' && aws configure set output 'json'",
                "aws sts get-caller-identity",
                "aws eks update-kubeconfig --region us-east-1 --name dp-es",
                "aws s3 cp --recursive s3://cnf-scripts-deployment/ .",  
                "sudo chmod +x cnf_testsuite.sh",  
                "./cnf_testsuite.sh"
            ]
        }
    )

    command_id = response["Command"]["CommandId"]
    print(f"Command ID: {command_id}")
    
    time.sleep(30)  # Wait for 30 seconds before checking the command status

    # Check if the command is still running
    status = ssm.get_command_invocation(
        CommandId=command_id,
        InstanceId=instanceId
    )["Status"]
    while status == "InProgress":
        print("Command still running...")
        time.sleep(30)
        status = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instanceId
        )["Status"]

    # Check if the command completed successfully
    if status != "Success":
        print(f"Command failed with status: {status}")
        output = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instanceId
        )["StandardErrorContent"]
    else:
        output = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instanceId
        )["StandardOutputContent"]

    print(f"Command output: {output}")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Command executed successfully",
            "output": output
        })
    }
