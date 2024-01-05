from fastapi import Body, Request
from sse_starlette.sse import EventSourceResponse
from fastapi.concurrency import run_in_threadpool
from configs import (LLM_MODELS, 
                     VECTOR_SEARCH_TOP_K, 
                     SCORE_THRESHOLD, 
                     TEMPERATURE,
                     USE_RERANKER,
                     RERANKER_MODEL,
                     RERANKER_MAX_LENGTH,
                     MODEL_PATH)
from server.utils import wrap_done, get_ChatOpenAI
from server.utils import BaseResponse, get_prompt_template
from langchain.chains import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from typing import AsyncIterable, List, Optional, Dict
import asyncio
from langchain.prompts.chat import ChatPromptTemplate
from server.chat.utils import History
from server.knowledge_base.kb_service.base import KBServiceFactory
import json
from urllib.parse import urlencode
from server.knowledge_base.kb_doc_api import search_docs
from Goods.goods import good_list


from server.reranker.reranker import LangchainReranker
from server.utils import embedding_device
async def knowledge_base_chat(query: str = Body(..., description="用户输入", examples=["你好"]),
                              knowledge_base_name: str = Body(..., description="知识库名称", examples=["samples"]),
                              top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
                              score_threshold: float = Body(
                                  SCORE_THRESHOLD,
                                  description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右",
                                  ge=0,
                                  le=2
                              ),
                              history: List[History] = Body(
                                  [],
                                  description="历史对话",
                                  examples=[[
                                      {"role": "user",
                                       "content": "我们来玩成语接龙，我先来，生龙活虎"},
                                      {"role": "assistant",
                                       "content": "虎头虎脑"}]]
                              ),
                              stream: bool = Body(False, description="流式输出"),
                              model_name: str = Body(LLM_MODELS[0], description="LLM 模型名称。"),
                              temperature: float = Body(TEMPERATURE, description="LLM 采样温度", ge=0.0, le=1.0),
                              max_tokens: Optional[int] = Body(
                                  None,
                                  description="限制LLM生成Token数量，默认None代表模型最大值"
                              ),
                              prompt_name: str = Body(
                                  "default",
                                  description="使用的prompt模板名称(在configs/prompt_config.py中配置)"
                              ),
                              request: Request = None,                              
                              kb_index: Dict = None,
                              ):
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    history = [History.from_data(h) for h in history]

    async def knowledge_base_chat_iterator(
            query: str,
            top_k: int,
            history: Optional[List[History]],
            model_name: str = model_name,
            prompt_name: str = prompt_name,
    ) -> AsyncIterable[str]:
        nonlocal max_tokens
        callback = AsyncIteratorCallbackHandler()
        if isinstance(max_tokens, int) and max_tokens <= 0:
            max_tokens = None

        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback],
        )
        ## 从对应的知识库中寻找query相关的内容
        docs = search_docs(query, knowledge_base_name, top_k, score_threshold, kb_index)
        docs = await run_in_threadpool(search_docs,
                                       query=query,
                                       knowledge_base_name=knowledge_base_name,
                                       top_k=top_k,
                                       score_threshold=score_threshold)

        # 加入reranker
        if USE_RERANKER:
            reranker_model_path = MODEL_PATH["reranker"].get(RERANKER_MODEL,"BAAI/bge-reranker-large")
            print("-----------------model path------------------")
            print(reranker_model_path)
            reranker_model = LangchainReranker(top_n=top_k,
                                            device=embedding_device(),
                                            max_length=RERANKER_MAX_LENGTH,
                                            model_name_or_path=reranker_model_path
                                            )
            print(docs)
            docs = reranker_model.compress_documents(documents=docs,
                                                     query=query)
            print("---------after rerank------------------")
            print(docs)
        context = "\n".join([doc.page_content for doc in docs])

        if len(docs) == 0:  # 如果没有找到相关文档，使用对应empty模板
            prompt_template = get_prompt_template("knowledge_base_chat", prompt_name + "empty")
            print(f"\033[32m\n当前prompt模板prompt_template为：{prompt_name}empty\n{prompt_template}\033[0m")
        else:            

        if len(docs) == 0:  # 如果没有找到相关文档，使用empty模板
            prompt_template = get_prompt_template("knowledge_base_chat", "empty")
        else:
            prompt_template = get_prompt_template("knowledge_base_chat", prompt_name)
            print(f"\033[32m\n当前prompt模板prompt_template为：{prompt_name}\n{prompt_template}\033[0m")

        goods = good_list[kb_index["brand_name"]][kb_index["category_name"]][kb_index["product_name"]][kb_index["produce_date"]]["context"]


        # prompt_name = kb_index["brand_name"] + '+' + kb_index["category_name"] + '+' + kb_index["product_name"] + '+' + kb_index["produce_date"]
        # print(f"\033[32m\nprompt_name：{prompt_name}\033[0m")
        # prompt_template = get_prompt_template("knowledge_base_chat", prompt_name)        
        # print(f"\033[32m\nprompt_template：\n{prompt_template}\033[0m")

        input_msg = History(role="user", content=prompt_template).to_msg_template(False)
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_template() for i in history] + [input_msg])
        chain = LLMChain(prompt=chat_prompt, llm=model)

        # Begin a task that runs in the background.
        task = asyncio.create_task(wrap_done(
            chain.acall({"goods":goods ,"context": context, "question": query}),
            callback.done),
        )


        source_documents = []
        for inum, doc in enumerate(docs):
            filename = doc.metadata.get("source")
            parameters = urlencode({"knowledge_base_name": knowledge_base_name, "file_name": filename})
            base_url = request.base_url
            url = f"{base_url}knowledge_base/download_doc?" + parameters
            text = f"""出处 [{inum + 1}] [{filename}]({url}) \n\n{doc.page_content}\n\n"""
            source_documents.append(text)

        if len(source_documents) == 0:  # 没有找到相关文档
            source_documents.append(f"<span style='color:red'>未找到相关文档,该回答为大模型自身能力解答！</span>")

        if stream:
            async for token in callback.aiter():
                # Use server-sent-events to stream the response
                yield json.dumps({"answer": token}, ensure_ascii=False)
            yield json.dumps({"docs": source_documents}, ensure_ascii=False)
        else:
            answer = ""
            async for token in callback.aiter():
                answer += token
            yield json.dumps({"answer": answer,
                            "docs": source_documents},
                            ensure_ascii=False)

        await task

        # 匹配不到不走大模型.
        # if len(docs) != 0:
        #     task = asyncio.create_task(wrap_done(
        #         chain.acall({"goods":goods ,"context": context, "question": query}),
        #         callback.done),
        #     )
            
        #     source_documents = []
        #     for inum, doc in enumerate(docs):
        #         filename = doc.metadata.get("source")
        #         parameters = urlencode({"knowledge_base_name": knowledge_base_name, "file_name": filename})
        #         base_url = request.base_url
        #         url = f"{base_url}knowledge_base/download_doc?" + parameters
        #         text = f"""出处 [{inum + 1}] [{filename}]({url}) \n\n{doc.page_content}\n\n"""
        #         source_documents.append(text)

        #     if stream:
        #         async for token in callback.aiter():
        #             # Use server-sent-events to stream the response
        #             yield json.dumps({"answer": token}, ensure_ascii=False)
        #         yield json.dumps({"docs": source_documents}, ensure_ascii=False)
        #     else:
        #         answer = ""
        #         async for token in callback.aiter():
        #             answer += token
        #         yield json.dumps({"answer": answer,
        #                         "docs": source_documents},
        #                         ensure_ascii=False)
        #     await task
        # else:
        #     source_documents = []
        #     source_documents.append(f"<span style='color:red'>未找到相关文档,该回答为固定回答！</span>")
        #     answer = "不好意思呀~,你提出的问题暂时难住我了，你可以换一个有关该商品信息的问题，或者描述的详细一点===ღ( ´･ᴗ･` )"
        #     for str in answer:
        #         yield json.dumps({"answer": str} ,ensure_ascii=False)
        #     yield json.dumps({"docs": source_documents}, ensure_ascii=False)

    return StreamingResponse(knowledge_base_chat_iterator(query=query,
                                                          top_k=top_k,
                                                          history=history,
                                                          model_name=model_name,
                                                          prompt_name=prompt_name),
                             media_type="text/event-stream")
    return EventSourceResponse(knowledge_base_chat_iterator(query, top_k, history,model_name,prompt_name))

