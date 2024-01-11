"""获取当前时间的工具."""
from datetime import datetime
import cn2an
from pydantic import BaseModel, Field

class GetTime(BaseModel):
    query: str = Field()

def get_time(no_use: str) -> str:
    '''
        Agent--获取当前时间的工具.

        入参： str 随意输入即可

        返回: str
    '''
    print("===>get_time")
    time_now = datetime.now()
    time_now_str = time_now.strftime('%H时%M分%S秒')
    date_now_str = time_now.strftime('%Y年%m月%d日')
    weekday = str(time_now.weekday() + 1)
    weekday_cn = cn2an.an2cn(weekday)
    if weekday_cn == "七":
        weekday_cn = "日"
    return "今天的日期是:" + date_now_str + ",当前时间为:" + time_now_str + ",今天是星期" + weekday_cn

if __name__ == '__main__':
    print(get_time(''))
    # 今天的日期是:2024年01月09日,当前时间为:18时09分59秒,今天是星期二