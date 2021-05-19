from urllib.parse import unquote, quote
import xml.etree.ElementTree as et
import json
import requests
import pandas as pd
import sys
import time
import boto3
import os
import mysql.connector
import csv

svc_url = "http://openapi.data.go.kr/openapi/service/rest/Covid19/getCovid19SidoInfStateJson"

serviceKey = "zeZFtWeuBxxTVWDR7dapGZQt%2BwyEBQ6Ps1dyYioLpvkJYgPD%2Fhyk8ofKPDQbDqCTY6ghCfqseuOJ1DAWYtr%2FvQ%3D%3D"

str_format = svc_url + "?serviceKey={0}&pageNo={1}&numOfRows={2}&startCreateDt={3}&endCreateDt={4}"

columns = ["등록순서", "기준일시", "도시명", "도시명(영문)", "확진자 수", "전일대비 증감 수", "격리중 환자수", "격리 해제 수", "사망자 수", "10만명당 발생률",
           "해외유입 수", "지역발생 수", "등록일시분초", "수정일시분초"]


def get_covid19_data(startCreateDt, endCreateDt, pageNo=1, numOfRows=10):
    q_str = str_format.format(serviceKey, pageNo, numOfRows, startCreateDt, endCreateDt)
    res = requests.get(q_str)

    xtree = et.fromstring(res.text)
    xtree_header = xtree.find('header')
    xtree_body_items = xtree.find('body').find('items')

    rows = []
    for node in xtree_body_items:
        seq = node.find("seq").text
        createDt = node.find("createDt").text
        deathCnt = node.find("deathCnt").text
        defCnt = node.find("defCnt").text
        gubun = node.find("gubun").text
        gubunCn = node.find("gubunCn").text
        gubunEn = node.find("gubunEn").text
        incDec = node.find("incDec").text
        isolClearCnt = node.find("isolClearCnt").text
        isolIngCnt = node.find("isolIngCnt").text
        localOccCnt = node.find("localOccCnt").text
        overFlowCnt = node.find("overFlowCnt").text
        qurRate = node.find("qurRate").text
        stdDay = node.find("stdDay").text
        updateDt = node.find("updateDt").text

        rows.append({"등록순서": seq,
                     "기준일시": stdDay,
                     "도시명": gubun,
                     "도시명(영문)": gubunEn,
                     "확진자 수": defCnt,
                     "전일대비 증감 수": incDec,
                     "격리중 환자수": isolIngCnt,
                     "격리 해제 수": isolClearCnt,
                     "사망자 수": deathCnt,
                     "10만명당 발생률": qurRate,
                     "해외유입 수": overFlowCnt,
                     "지역발생 수": localOccCnt,
                     "등록일시분초": createDt,
                     "수정일시분초": updateDt})

    df = pd.DataFrame(rows, columns=columns[0:14])
    df.to_csv('covid_db.csv', index=False, header=False)

    return df


if __name__ == '__main__':

    arguments = sys.argv

    # ['covid19.py', 'pediod', '20210501', '20210501']

    if arguments[1] == 'period':
        startdt = arguments[2]
        enddt = arguments[3]
        df = get_covid19_data(startdt, enddt)

    elif arguments[1] == 'today':
        startdt = enddt = time.strftime('%Y%m%d', time.localtime(time.time()))
        df = get_covid19_data(startdt, enddt)

    print(df)

ENDPOINT="covid-aurora-cluster-instance-1.cb49bmr3kzgc.ap-northeast-2.rds.amazonaws.com"
PORT="3306"
USR="admin"
PASSWD="admin000"
REGION="ap-northeast-2"
DATABASE="covid_data_aurora"
os.environ['LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN'] = '1'
try:
    conn = mysql.connector.connect(host=ENDPOINT, user=USR, passwd=PASSWD, port=PORT, database=DATABASE)
    cur = conn.cursor()
    sql = 'insert into covid_data_aurora.covid_data_city (등록순서, 기준일시, 도시명, 도시영문, 확진자수, 전일대비증감수, 격리중환자수, 격리해제수, 사망자수, 10만명당발생률, 해외유입수, 지역발생수, 등록일시분초, 수정일시분초) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    f = open('covid_db.csv', 'r', encoding='utf-8')
    rd = csv.reader(f)

    for line in rd:
        cur.execute(sql, (line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8], line[9], line[10], line[11], line[12], line[13]))
    conn.commit()
    conn.close()
    f.close()
    # cur.execute('insert into covid_data values(df)')
    # query_results = cur.fetchall()
    # print(query_results)
except Exception as e:
    print("Database connection failed due to {}".format(e))
