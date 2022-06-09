# coding: utf-8
"""
Author: 張修成
Github: https://github.com/juzowa
Date: 2022.06.09
"""

from time import sleep
from os.path import exists
import pandas as pd
import os
import requests
from influxdb import InfluxDBClient
import datetime


def updatedb(stringdata,tablename):
    #db connect
    dbclient = InfluxDBClient('54.180.25.155',8086,'','','stock_data')
    #measurement為TABLE名稱 / topic為欄位名稱 / value為存入的值
    web_crawler_data = [
	    		{
	    			"measurement" : tablename,
		    		"tags" : {
			    		"topic":"stock2330_data"
			    	},
			    	"fields":{
			    		"value": stringdata
			    	}
			    }
		    ]

    #將測試資料存入爬蟲TABLE
    dbclient.write_points(web_crawler_data)
    return ("db write Sucess")


#api connect


mykey = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyMi0wNS0yMiAxNjo0MToxMyIsInVzZXJfaWQiOiJqdXpvd2EiLCJpcCI6IjExOC4xNjMuOC42MCJ9.xoeKaojxUrO9QHu7MT9Mf5X6J8DifP2IQwiQFRoFSiQ"

url = "https://api.web.finmindtrade.com/v2/user_info"
parload = {
    "token": mykey,
}
resp = requests.get(url, params=parload)
#print(resp.json())
print(resp.json()["user_count"])  # 使用次數
print(type(resp.json()["user_count"]))
print(resp.json()["api_request_limit"])  # api 使用上限
url = "https://api.finmindtrade.com/api/v4/taiwan_stock_tick_snapshot"
parameter = {
    "data_id": "2330",
    "token": mykey,
}





flag = 0
preday = 0



#check database have data
client = InfluxDBClient('54.180.25.155',8086,'','','stock_data')
#撈取爬蟲TABLE的資料
web_crawler_data = client.query('select * from web_crawler_data')
if len(list(web_crawler_data.get_points()))==0:#database no data
    print("file empty")
else:#database have data and get last line date 
    last_line = list(web_crawler_data.get_points())[-1]['value']
    print("file last line:",last_line)
    preday=pd.to_datetime(last_line.split()[-4]+" "+last_line.split()[-3], format='%Y-%m-%d %H:%M:%S.%f')
    print(type(preday))
    print("initialday:",preday)
    flag=1

i=0
while True:
    try:
        resp = requests.get(url, params=parameter,timeout=5)
        data = resp.json()      
        data = pd.DataFrame(data["data"])
        if data.empty:#no data return call spark
            curr_time = str(curr_time).split(' ')
            print("no data")
            curr_time = str(curr_time).split(' ')
            print(curr_time)
            os.system(f'python3 scripts/spark_predict.py --date {curr_time[0]} --time {curr_time[1]} --his_num {10}')
        else:
            if flag == 0:
                dateformat=pd.to_datetime(data["date"], format='%Y-%m-%d %H:%M:%S.%f')
                print(dateformat)
                dfAsString = pd.DataFrame.to_string(data,header=False, index=False)
                print("web_crawler_data update:")
                print(updatedb(dfAsString,"web_crawler_data"))
                print("prediction_data update:")
                print(updatedb(dfAsString,"prediction_data"))
                preday = dateformat
                flag=1
            #check datetime is same or not to wrtie back database
            else:
                dateformat=pd.to_datetime(data["date"], format='%Y-%m-%d %H:%M:%S.%f')
                print("predatatime:",preday)
                print("nowdatatime:",dateformat)
                print(list(preday < dateformat)[0])
                if(list(preday < dateformat)[0]):
                    dfAsString = pd.DataFrame.to_string(data,header=False, index=False)
                    print("web_crawler_data update:")
                    print(updatedb(dfAsString,"web_crawler_data"))
                    print("prediction_data update:")
                    print(updatedb(dfAsString,"prediction_data"))
                    preday = dateformat
                else:#over 5 second data duplicate call spark
                    print("Before 5 second:",preday)
                    preday = preday + datetime.timedelta(seconds=5)
                    print("over 5 second data still duplicate")
                    print("after 5 second:",preday)
                    pre_time = str(preday).split(' ')
                    os.system(f'python3 scripts/spark_predict.py --date {pre_time[0]} --time {pre_time[1]}.0 --his_num {10}')             
            print("--------------end--------------")
            i=i+1
            sleep(5)
    except requests.exceptions.Timeout:#call api error call spark
        print("timeouterror")
        curr_time = str(curr_time).split(' ')
        print(curr_time)
        os.system(f'python3 scripts/spark_predict.py --date {curr_time[0]} --time {curr_time[1]} --his_num {10}')
    except requests.exceptions.RequestException as e:#call api error call spark
        print("requesterror")
        curr_time = str(curr_time).split(' ')
        print(curr_time)
        os.system(f'python3 scripts/spark_predict.py --date {curr_time[0]} --time {curr_time[1]} --his_num {10}')

