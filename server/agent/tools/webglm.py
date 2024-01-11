from server.agent.tools.webglm_linux_os.model import load_model, citation_correction
import argparse
from server.agent.tools.webglm_linux_os.arguments import add_model_config_args
from server.agent.tools.webglm_linux_os.model import language_translate



def webglm(question: str) -> str:
    arg = argparse.ArgumentParser()
    add_model_config_args(arg)
    args = arg.parse_args() 
    webglm = load_model(args)

    question = question.strip()
    question = language_translate.baidu_translate(question)
    final_results = {}
    for results in webglm.stream_query(question):
        final_results.update(results)
        if "references" in results:
            for ix, ref in enumerate(results["references"]):
                #print("Reference [%d](%s): %s"%(ix + 1, ref['url'], ref['text']))
                pass
        if "answer" in results:
            print("\n%s\n"%citation_correction(results["answer"], [ref['text'] for ref in final_results["references"]]))
            return citation_correction(results["answer"], [ref['text'] for ref in final_results["references"]])


if __name__ == '__main__':
    print(webglm("李铁假球"))
