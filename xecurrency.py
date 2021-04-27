import requests
from requests import ConnectionError
from requests.utils import unquote
import logging
import json
from pprint import pprint
import re
import os
from typing import Union,NoReturn,Optional,AnyStr
from base64 import b64decode, b64encode

logging.basicConfig(level=logging.ERROR)

#https://www.xe.com/api/stats.php?fromCurrency=USD&toCurrency=EUR
# content = requests.get('https://api.exchangeratesapi.io/history?start_at=2000-01-01&end_at=2001-09-01&base=USD')
# pprint(json.loads(content.content))
# https://www.xe.com/themes/xe/js/react/currency-data_en-json.0c37f4b6ae5322ea8c64.min.js
# https://www.xe.com/api/page_resources/converter.php?fromCurrency=USD&toCurrency=EUR



class XEconversion:


    def __init__(self) -> NoReturn:

        self.s = requests.session()
        self.s.headers.update({
            'user-agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.53'
            })


    def __enter__(self):
        return self

    def __exit__(self,*args) -> NoReturn:
        self.s.close()

    def saveCodes(self) -> dict:

        data = self.s.get('https://www.xe.com/themes/xe/js/react/currency-data_en-json.0c37f4b6ae5322ea8c64.min.js')
        code: dict = {}
        content: str = data.text
        data: str = re.compile(
                r"(?<=JSON.parse).*'\)").search(content).group(0).replace("('","").rstrip("')"
                )
        json_data: dict = json.loads(data.encode('utf-8').decode('unicode_escape'))

        for details in json_data:
            code[details] = json_data[details]['name']

        return code

    def writeFile(self, filepath: str) -> NoReturn:

        _retrivedJson = self.saveCodes()

        if not os.path.exists(filepath):
            with open(filepath,'w') as json_f:
                json_f.write(json.dumps(_retrivedJson))
        else:
            file = open(filepath,'r+')
            _fileJson = file.read()
            if _fileJson != _retrivedJson:
               with open(filepath,'w') as json_f:
                    json_f.write(json.dumps(_retrivedJson))
            file.close()

    def getCodes(self) -> dict:

        with open('currencyCodes.json','r') as codeF:
            _codes = codeF.read().encode('raw_unicode_escape').decode()
            return json.loads(_codes)

    def getRate(self,fromC: str,toC: str) -> Union[None,float]:

        try:
            curentCurrency = self.s.get(
                f'https://www.xe.com/api/page_resources/converter.php?fromCurrency={fromC.upper()}&toCurrency={toC.upper()}'
                )
            val = curentCurrency.json()
            getRate = val["payload"]["rates"]["rate"]
            # print(type(self.decodeRateData(getRate)))
            rateValue = self.decodeRateData(getRate)
            # print(type(getRate))


            return float(rateValue)
        except ConnectionError:
            logging.error("Connection error while making the request")
            return None




    def decode64(self, data: str) -> list:
        # 'add padding (=) if given data has no padding and performs base64 decoding'

        if len(data) % 4 != 0:
            data = data.ljust(len(data) + 4 - len(data) % 4, '=')

        b_decoded: str = b64decode(data)

        # convert a bytes object into a list of integers using list(b)
        return list(b_decoded)


    def decodeRateData(self,data: str) -> str:
        strip4: str = data[len(data) - 4:]
        codepos: int = sum(map(lambda e: ord(e), strip4))
        codepos = (len(data) - 10) % codepos
        codepos = (len(data) - 14) if (codepos > len(data) - 14) else codepos

        key: str = data[codepos:codepos+10]
        data = data[:codepos] + data[codepos+10:]

        decodedData: list = self.decode64(unquote(data))

        result: str = ''
        i: int
        j: int
        for j, i in enumerate(range(0, len(decodedData), 10)):
            # accesing bytes object( b'....' ) by index returns the ord() value of that byte
            char1: int = decodedData[i]
            keychar: str = key[len(key) + (j % len(key)) - 1 if (j % len(key)) - 1 < 0 else (j % len(key)) - 1]
            char1 = chr(char1 - ord(keychar[0]))

            # result += char1 + decodedData[i+1:i+10].decode('utf-8')
            result += char1 + ''.join(map(lambda e: chr(e), decodedData[i+1:i+10]))

        return result

    def get_thirty_day_rate(self,
                            fromCurrency: str,
                            toCurrency: str,
                            rateType: Optional[str] = None) -> Union[None,str]:

        try:
            rateContent = self.s.get(f'https://www.xe.com/api/stats.php?fromCurrency={fromCurrency.upper()}&toCurrency={toCurrency.upper()}')
            json_data = rateContent.json()
            if rateType == None:
                return float(json_data["payload"]["Last_30_Days"]["average"])
            elif rateType.lower() == "high":
                return float(json_data["payload"]["Last_30_Days"]["high"])
            elif rateType.lower() == "low":
                return float(json_data["payload"]["Last_30_Days"]["low"])
            else:
                raise Exception("The ratetype must be either None or high or low")

        except Exception as e:
            print(e)
            return None


    def get_ninety_day_rate(self,
                            fromCurrency:str,
                            toCurrency:str,
                            rateType: Optional[str]=None) -> Union[str,None]:
        rateContent = self.s.get(f'https://www.xe.com/api/stats.php?fromCurrency={fromCurrency.upper()}&toCurrency={toCurrency.upper()}')
        json_data = rateContent.json()
        if rateType == None:
            return json_data["payload"]["Last_90_Days"]["average"]
        elif rateType.lower() == "high":
            return json_data["payload"]["Last_90_Days"]["high"]
        elif rateType.lower() == "low":
            return json_data["payload"]["Last_90_Days"]["low"]
        else:
            raise Exception("The ratetype must be either None or high or low")














if __name__ =="__main__":
    obj = XEconversion()

    # obj.writeFile('currencyCodes.json')
    # pprint(obj.getCodes())
    pprint(obj.getRate('usd','inr'))
    print(obj.getCodes())
    print(type(obj.getCodes()))
    # pprint(obj.get_thirty_day_rate('usd','inr',rateType='high'))
    # print(XEconversion.decodeBase64('gy4xOTc2NjgzOYk1SUOAwzZ0wRMDc5'))
