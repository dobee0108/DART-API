import requests
import zipfile
import io
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI()

# OpenDart 인증키
API_KEY = "4480e3a5ef0edadd14eb6bcdd50b81b3ac1f52eb"

# 전역 변수로 corp_code map 캐싱
corp_map = {}

def load_corp_codes():
    global corp_map
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception("OpenDart API 요청 실패")

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    xml_data = zf.read(zf.namelist()[0])
    root = ET.fromstring(xml_data.decode("utf-8"))

    corp_map.clear()
    for elem in root.findall("list"):
        name = elem.find("corp_name").text.strip()
        code = elem.find("corp_code").text.strip()
        corp_map[name] = code

@app.on_event("startup")
def startup_event():
    load_corp_codes()

@app.get("/corpcode")
def get_corp_code(company_name: str = Query(..., description="회사명 (예: 삼성전자)")):
    code = corp_map.get(company_name.strip())
    if code:
        return {"company_name": company_name, "corp_code": code}
    else:
        return JSONResponse(status_code=404, content={"error": "기업명을 찾을 수 없습니다."})

@app.get("/financials")
def get_financials(
    corp_code: str = Query(..., description="corp_code 값"),
    year: str = Query(..., description="사업연도"),
    report_code: str = Query(..., description="보고서 코드 (11014 등)")
):
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": report_code
    }
    response = requests.get(url, params=params)
    return response.json()
