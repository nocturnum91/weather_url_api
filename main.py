import calendar
import datetime
import time
import sys

import requests.exceptions

from requests.adapters import HTTPAdapter, Retry
import cgi

# 파라미터 순서: STN YEAR MONTH AUTHKEY

year = sys.argv[2]
month = sys.argv[3]

# http://203.247.66.126:8090/url/rdr_site_file.php?data=raw&tm=202210010015&stn=BRI&autyKey=
# http://203.247.66.126:8090/url/rdr_site_file.php?tm=201809011030&data=raw&stn=BRI&authKey= 없는 파일
url = 'http://203.247.66.126:8090/url/rdr_site_file.php'
params = {'data': 'raw', 'stn': sys.argv[1], 'authKey': sys.argv[4]}


# 입력받은 년-월의 시작일 반환 : YYYYMM010000
def get_date_of_first_month():
    first_date_str = year + month + '010000'
    # first_date_str = year + month + '011025'
    first_date_obj = datetime.datetime.strptime(first_date_str, '%Y%m%d%H%M')
    return first_date_obj


# 입력받은 년-월의 마지막일 반환 : YYYYMMDD2355 10분 단위 다운로드로 변경하려면 55를 50으로 변경
def get_date_of_last_month():
    last_date = calendar.monthrange(int(year), int(month))[1]
    last_date_str = year + month + str(last_date) + "2355"
    last_date_obj = datetime.datetime.strptime(last_date_str, '%Y%m%d%H%M')
    return last_date_obj


def retry_req(api_url):
    with requests.Session() as s:
        # 재시도 횟수
        retries = 5
        backoff_factor = 0.3
        status_forcelist = (500, 502, 504)

        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist)

        adapter = HTTPAdapter(max_retries=retry)
        s.mount('http://', adapter)
        s.mount('https://', adapter)

        res = s.get(api_url, params=params, timeout=10)
        # print(res.headers)

        return res


def download(api_url, file_name=None):
    response = retry_req(api_url)
    if not file_name:
        # 파일이 없는 경우
        if not response.headers.get('Content-Disposition'):
            print(response.content)
            return
        else:
            header = response.headers['Content-Disposition']
            value, param = cgi.parse_header(header)
            # 파일명을 Response Header의 Content-Disposition에서 가져옴
            file_name = str(param['filename'])
            print("fileName: " + file_name)
    with open(file_name, "wb") as file:
        # 파일 다운로드
        file.write(response.content)


start_tm = get_date_of_first_month()
end_tm = get_date_of_last_month()
while start_tm <= end_tm:
    # 10분 단위 다운로드로 변경하려면 minutes을 10으로 변경
    start_tm = start_tm + datetime.timedelta(minutes=5)
    # print(start_tm.strftime('%Y%m%d%H%M'))
    params['tm'] = start_tm.strftime('%Y%m%d%H%M')
    # print(params)
    download(url)
    time.sleep(0.01)
