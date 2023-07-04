import boto3, json

region = "ap-southeast-1"
kendra_index_id = "dc1992a2-dbd4-4684-90e8-059cfc1551d7"
endpoint_name = "jumpstart-dft-hf-llm-falcon-7b-bf16"

import langchain
from langchain.chains import ConversationalRetrievalChain
from langchain import SagemakerEndpoint
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.prompts import PromptTemplate
import json
from kendra_retriever import AmazonKendraRetriever

langchain.debug = False

class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


MAX_HISTORY_LENGTH = 5


def build_chain():
    class ContentHandler(LLMContentHandler):
        content_type = "application/json"
        accepts = "application/json"

        def transform_input(self, prompt: str, model_kwargs: dict) -> bytes:
            input_str = json.dumps({"inputs": prompt, "parameters": model_kwargs})
            return input_str.encode("utf-8")

        def transform_output(self, output: bytes) -> str:
            response_json = json.loads(output.read().decode("utf-8"))
            return response_json[0]["generated_text"]

    content_handler = ContentHandler()

    llm = SagemakerEndpoint(
            endpoint_name=endpoint_name,
            region_name="us-east-1",
            model_kwargs={"max_new_tokens": 300, "return_full_text": True},
            content_handler=content_handler,
    )

    retriever = AmazonKendraRetriever(index_id=kendra_index_id, region_name=region)

    prompt_template = """The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it  does not know.
          {context}
          Instruction: Based on the above documents, provide a detailed answer for, '{question}'. If not present in the document, answer "don't know"
        Solution:"""

    PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
    )

    condense_qa_template = """
            Given the following conversation and a follow up question, rephrase the follow up question 
            to be a standalone question.
            Chat History:
            {chat_history}
            Follow Up Input: {question}
            Standalone question:"""
    standalone_question_prompt = PromptTemplate.from_template(condense_qa_template)

    qa = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            condense_question_prompt=standalone_question_prompt,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": PROMPT},
        )

    return qa


def run_chain(chain, prompt: str, history=[]):
    return chain({"question": prompt, "chat_history": history})


def build_response(body: dict, status_code=200):
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }

def lambda_function(event, context):
    _question = json.loads(event["body"])["question"]
    qa = build_chain()
        
    result = run_chain(qa, _question, [])

    sources = []
    if "source_documents" in result:
        for d in result["source_documents"]:
            sources.append(d.metadata["source"])
    
    return build_response({"answer":result["answer"], "sources": sources})