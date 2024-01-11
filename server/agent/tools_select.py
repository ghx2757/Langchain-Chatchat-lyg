from langchain.tools import Tool
from server.agent.tools import *


## 请注意，如果你是为了使用AgentLM，在这里，你应该使用英文版本。

tools = [
    # Tool.from_function(
    #     func=get_time,
    #     name="get_time",
    #     description="Useful for when you need to answer questions about Date or Time.",
    #     args_schema=GetTime,
    # ),
    # Tool.from_function(
    #     func=get_weather,
    #     name="get_weather",
    #     description="Useful for when you need to answer questions about weather information. Input should be a string of city and country split by ',', both must be in English, the country should be a ISO 3166-1 alpha-2 code, for example 'London,GB'.",
    #     args_schema=GetWeather,
    # ),
    # Tool.from_function(
    #     func=webglm,
    #     name="webglm",
    #     description="Useful for when you are unable to obtain the latest news about the question, use this tool for online search.",
    # ),
    

    Tool.from_function(
        func=calculate,
        name="calculate",
        description="Useful for when you need to answer questions about simple calculations",
        args_schema=CalculatorInput,
    ),
    Tool.from_function(
        func=arxiv,
        name="arxiv",
        description="A wrapper around Arxiv.org for searching and retrieving scientific articles in various fields.",
        args_schema=ArxivInput,
    ),
    Tool.from_function(
        func=weathercheck,
        name="weather_check",
        description="",
        args_schema=WhetherSchema,
    ),
    Tool.from_function(
        func=shell,
        name="shell",
        description="Use Shell to execute Linux commands",
        args_schema=ShellInput,
    ),
    Tool.from_function(
        func=search_knowledgebase_complex,
        name="search_knowledgebase_complex",
        description="Use Use this tool to search local knowledgebase and get information",
        args_schema=KnowledgeSearchInput,
    ),
    Tool.from_function(
        func=search_internet,
        name="search_internet",
        description="Use this tool to use bing search engine to search the internet",
        args_schema=SearchInternetInput,
    ),
    Tool.from_function(
        func=wolfram,
        name="Wolfram",
        description="Useful for when you need to calculate difficult formulas",
        args_schema=WolframInput,
    ),
    Tool.from_function(
        func=search_youtube,
        name="search_youtube",
        description="use this tools to search youtube videos",
        args_schema=YoutubeInput,
    ),
]

tool_names = [tool.name for tool in tools]



    