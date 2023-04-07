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
                "aws configure set aws_access_key_id '******' && aws configure set aws_secret_access_key '************' && aws configure set aws_session_token 'IQoJb3JpZ2luX2VjEE0aCXVzLXdlc3QtMiJGMEQCIHj9hvovtV5NE/Rbl96+L77DTkhtKGitqTjv5XtMPUozAiBBjkpEQvOVavV9YZ9A/3CpuCSYfU3c5YCfKdv5kuJC3yqNAwg2EAEaDDA2NDA0NzYwMTU5MCIMsfnDv6Ecj5+R6/h8KuoCYP/vyxiAaJDFywv3POpiG3pK8wD3WbJSc6JYjA4L9JFFrBnPBGp1i5xc3NPhG8azxEZe9nDtBO1Cb/bLXWaKdyT3JVqihBRJbATicUkfpDKsLcK8Cx+t3fkm3wQ1GMwFbyOCSVyPRLItNfIPgdm4WsaajvsKudPjo04Wg3TF2pcVgVIAHRShjGh1r7DWuMD0NzP99WCEunAQD+WDQy/DUAkECttNUxr/vyAcDzW8XCYCj0B0JiHc2RIIUQAffmOVBeQ9Uv1TcVUObN0K4Mhj1jWLvSBbj4CAIVvQ2k94S9xNoNpmWlKOn4hn65qzwBapf/50r/tkKA2JvwGbcveIrC4FX59Rl1WNjN0WVPrOTTnN+gPkixoSriWkPtdTw2tFiWQtuQRI9TCSgHwK5OGKFYQvNquwm5EZrwkLajgOgrFlCbzErq73fQcgVYmMqwpmVdA7RXkuKXkaw73YBroTTuRIBIJRCd194hIw5dq8oQY6pwGc2nhi4vyrTsxSPWHocpUJrZSYXgRLKq11EMc+F7/MJK3pFBl6rfpq+Fn1kEgkctcu4hu8y1WXuOrE3bV4r9VE4LyE6JFB8B/Topx79Z443a+m+hhz0MAYjsp5orvtGai0kn9IjTKalrhfqx32mSJPJqAEzaPDMrmyYyxU6DM4AaJi2b23UfraQRvQbwNAm4HXqB2/Bik3OPFPd5SZrDzZ2z/trFYTCA==' && aws configure set region 'us-west-2' && aws configure set output 'json'",
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
