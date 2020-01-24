#! /usr/bin/env python3

import argparse
import requests
import time
import csv
import os
import json
import botocore
import boto3
import random



def getToken(seldon):
    post_data = {"grant_type": "client_credentials"}
    requestOauth = requests.post(seldon+'/oauth/token', auth=('oauth-key', 'oauth-secret'), data=post_data, json={'grant_type=client_credentials'})
    # print(requestOauth.content)
    data = requestOauth.json();
    access_token = data['access_token']
    return access_token


def fetchS3data(bucket,filename,accesskey, secretkey, s3endpoint):
    client = boto3.client('s3',
                           endpoint_url=s3endpoint,
                           aws_access_key_id=accesskey,
                           aws_secret_access_key=secretkey,
#                           region_name=DEFAULT_REGION,
                           verify=False)
    csv_obj = client.get_object(Bucket=bucket, Key=filename)
    class_one = []
    class_zero=[]
    body = csv_obj['Body']
    csv_string = body.read().decode('utf-8').splitlines()
    for each in csv_string[1:]:
        if each[-1] == "0":
            class_zero.append(each)
        else:
            class_one.append(each)

    return [class_zero,class_one]


def invokeModel(msg, access_token, seldon):

# "Time","V1","V2","V3","V4","V5","V6","V7","V8","V9","V10","V11","V12","V13","V14","V15","V16","V17","V18","V19","V20","V21","V22","V23","V24","V25","V26","V27","V28","Amount","Class" - Fields we get on the consumer
# ['V3','V4','V10','V11','V12','V14','V17','Amount'] - Fields to be sent to the model

    payload = ""+msg[3]+","+msg[4]+","+msg[10]+","+msg[11]+","+msg[12]+","+msg[14]+","+msg[17]+","+msg[29]
    headers = {'Content-type': 'application/json', 'Authorization': 'Bearer {}'.format(access_token)}
    #Read the test dataframe and stream each row

    # Send the post request for the prediction
    requestPrediction = requests.post(seldon+'/api/v0.1/predictions', headers=headers, json={"strData": payload })
    predictionData = requestPrediction.json();
    datafield = predictionData['data']
    predictionArray = datafield['ndarray']
    print(predictionArray[0])


def sendMessage(payload, access_token, seldon):
    msg = payload.decode('utf-8')
    msgAsList = msg[1:-1].split(",")
    print(msgAsList)
    modelResponse = invokeModel(msgAsList, access_token, seldon)
    print("modelResponse: ", modelResponse)


def main():


    seldon = os.environ['seldon']

    access_token = getToken(seldon)
    print(access_token)

    s3bucket = os.environ['s3bucket']
    accesskey = os.environ['ACCESS_KEY_ID']
    secretkey = os.environ['SECRET_ACCESS_KEY']
    s3endpoint = os.environ['s3endpoint']
    filename = os.environ['filename']

    print(s3bucket,filename, s3endpoint)
    print("AK:", accesskey)
    print("SK:",secretkey)
    messages = fetchS3data(s3bucket,filename,accesskey, secretkey, s3endpoint)

    class_zero = messages[0]
    class_one = messages[1]

    one_pointer=0
    zero_pointer=0
    print(len(class_zero))
    print(len(class_one))

    while True:
        prob = random.randint(1,6)
        print("Send msg with prop:",prob)
        if prob == 5:
            if one_pointer < len(class_one):
                sendMessage(json.dumps(class_one[one_pointer]).encode('utf-8'), access_token, seldon)
                one_pointer = one_pointer + 1
            else:
                one_pointer = 0
                sendMessage(json.dumps(class_one[one_pointer]).encode('utf-8'), access_token, seldon)
        else:
            if zero_pointer < len(class_zero):
                sendMessage(json.dumps(class_zero[zero_pointer]).encode('utf-8'), access_token, seldon)
                zero_pointer = zero_pointer + 1
            else:
                one_pointer = 0
                sendMessage(json.dumps(class_zero[zero_pointer]).encode('utf-8'), access_token, seldon)

        time.sleep(random.randint(2,6))

    print("Done.")


if __name__ == '__main__':
    main()



