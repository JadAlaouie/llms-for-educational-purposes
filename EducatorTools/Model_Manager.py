from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
import os
import time
from threading import Thread
from queue import Queue
from dotenv import load_dotenv

load_dotenv()

PRICING = {
    "gpt-4o-mini": {"input": 0.150 / 1000000, "output": 0.600 / 1000000},
    "claude-3-haiku-20240307": {"input": 0.25 / 1000000, "output": 1.25 / 1000000},
    "claude-3-5-sonnet-20241022": {"input": 3 / 1000000, "output": 1.25 / 1000000} 
}

class ModelManager:
    def __init__(self, primary_config, secondary_config):
        self.primary_config = primary_config
        self.secondary_config = secondary_config
        
        self.primary_model = self._initialize_model(primary_config)
        self.secondary_model = self._initialize_model(secondary_config)

    def _initialize_model(self, config):
        try:
            if config["provider"] == "OpenAI":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OpenAI API key not found")
                return ChatOpenAI(
                    model=config["model_name"],
                    temperature=config["temperature"],
                )
            elif config["provider"] == "Claude":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("Claude API key not found")
                return ChatAnthropic(
                    model=config["model_name"],
                    temperature=config["temperature"]
                )
            else:
                raise ValueError(f"Unsupported provider: {config['provider']}")
        except Exception as e:
            print(f"Error initializing {config['provider']}: {e}")
            return None

    def _run_model(self, chain, input_queue, is_primary=True):
        model_type = "Primary" if is_primary else "Secondary"
        try:
            chain_input = input_queue.get()
            model_response = chain.invoke(chain_input)
            content = StrOutputParser().invoke(model_response)

            input_tokens = model_response.usage_metadata.get("input_tokens", 0)
            output_tokens = model_response.usage_metadata.get("output_tokens", 0)

            model_name = self.primary_config["model_name"] if is_primary else self.secondary_config["model_name"]
            input_cost = input_tokens * PRICING[model_name]["input"]
            output_cost = output_tokens * PRICING[model_name]["output"]
            total_cost = input_cost + output_cost

            print(f"{model_type} Model Tokens → Input: {input_tokens}, Output: {output_tokens}")

            input_queue.put(('success', content, total_cost, input_tokens, output_tokens))

        except Exception as e:
            print(f"{model_type} model failed: {e}")
            input_queue.put(('error', str(e), 0, 0, 0))

    def generate(self, prompt_template, chain_input):
        if self.primary_model:
            input_queue = Queue()
            input_queue.put(chain_input)
            chain = prompt_template | self.primary_model

            thread = Thread(target=self._run_model, args=(chain, input_queue, True))
            thread.start()
            thread.join(timeout=40)

            if thread.is_alive():
                print("Primary model timeout. Switching to secondary model...")
                return self._try_secondary_model(prompt_template, chain_input)

            status, result, total_cost, input_tokens, output_tokens = input_queue.get()
            if status == 'success':
                return result, total_cost

            print("Primary model error:", result)

        return self._try_secondary_model(prompt_template, chain_input)

    def _try_secondary_model(self, prompt_template, chain_input):
        """Runs the secondary model in case the primary one fails"""
        if self.secondary_model:
            try:
                input_queue = Queue()
                input_queue.put(chain_input)
                chain = prompt_template | self.secondary_model

                thread = Thread(target=self._run_model, args=(chain, input_queue, False))
                thread.start()
                thread.join(timeout=15)

                if thread.is_alive():
                    print("Secondary model timed out. No response available.")
                    return "Error: Secondary model timed out.", 0

                status, result, total_cost, input_tokens, output_tokens = input_queue.get()

                if status == 'success':
                    return result, total_cost

                print(f"Secondary model error: {result}")

            except Exception as e:
                print(f"Secondary model failed: {str(e)}")

        print("Error: All models failed to generate a response.")
        return "Error: All models failed to generate a response.", 0