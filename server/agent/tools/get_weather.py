import requests
from pydantic import BaseModel, Field

class GetWeather(BaseModel):
    query: str = Field()
# OPENWEATHER_API_KEY = "2396a2ca7589f811fb038a2ffa1cc1b4" # wjm
OPENWEATHER_API_KEY = "526134873b19da21fac3d25509807d39" # ghx
lang = "zh_cn" # 语言

def get_weather(city_country: str) -> str:
    print("===>get_time")
    '''获取当前天气的工具.'''
    base_url = f'http://api.openweathermap.org/data/2.5/weather?'
    url = f"{base_url}q={city_country}&lang={lang}&appid={OPENWEATHER_API_KEY}"
    res = requests.get(url)
    weather = res.json()
    if weather["cod"] != 200:
        return "没有寻找到有关该城市的天气信息"
    else:
        description = weather["weather"][0]["description"] # 天气状况
        temp = weather["main"]["temp"] - 273.15 # 温度
        feels_like = int(weather["main"]["feels_like"] - 273.15) # 体感温度
        humidity = weather["main"]["humidity"] # 湿度
        wind_speed = weather["wind"]["speed"] # 风速度

        des = f"该地区当前天气为:{description},体感温度{feels_like}℃,空气湿度{humidity}%,风速{wind_speed}米/秒"
        return des

if __name__ == '__main__':
    print(get_weather('New York'))
