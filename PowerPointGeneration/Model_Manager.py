from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
import os
import time
from threading import Thread
from queue import Queue
from dotenv import load_dotenv

load_dotenv()

class ModelManager:
    def __init__(self, primary_config, secondary_config):
        self.primary_config = primary_config
        self.secondary_config = secondary_config
        self.primary_model = self._initialize_model(primary_config)
        self.secondary_model = self._initialize_model(secondary_config)

    def _initialize_model(self, config):
        try:
            if config["provider"] == "OpenAI":
                if not os.getenv("OPENAI_API_KEY"):
                    raise ValueError("OpenAI API key not found")
                return ChatOpenAI(
                    model=config["model_name"],
                    temperature=config["temperature"],
                )
            elif config["provider"] == "Claude":
                if not os.getenv("ANTHROPIC_API_KEY"):
                    raise ValueError("Claude API key not found")
                return ChatAnthropic(
                    model=config["model_name"],
                    temperature=config["temperature"]
                )
        except Exception as e:
            print(f"Error initializing {config['provider']}: {e}")
            return None

    @staticmethod
    def get_model(config):
        provider = config.get("provider")
        model_name = config.get("model_name")
        temperature = config.get("temperature", 0.7)

        if provider == "OpenAI":
            return ChatOpenAI(model=model_name, temperature=temperature)
        elif provider == "Claude":
            return ChatAnthropic(model=model_name, temperature=temperature)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _run_model(self, chain, input_queue):
        try:
            result = chain.invoke(input_queue.get())
            input_queue.put(('success', result))
        except Exception as e:
            input_queue.put(('error', str(e)))

    def generate(self, prompt_template, chain_input):
        if self.primary_model:
            input_queue = Queue()
            input_queue.put(chain_input)
            chain = prompt_template | self.primary_model | StrOutputParser()
            thread = Thread(target=self._run_model, args=(chain, input_queue))
            thread.start()
            thread.join(timeout=15)

            if thread.is_alive():
                print("Primary model timed out. Switching to secondary...")
            else:
                status, result = input_queue.get()
                if status == 'success':
                    return result
                print(f"Primary model error: {result}. Switching to secondary...")

        if self.secondary_model:
            try:
                chain = prompt_template | self.secondary_model | StrOutputParser()
                result = chain.invoke(chain_input)
                return result
            except Exception as e:
                print(f"Secondary model failed: {str(e)}")

        return 'Error: All models failed to generate a response.'

