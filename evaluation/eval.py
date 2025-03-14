import argparse
import json
import os
# import torch
from pathlib import Path
from tqdm import tqdm
import sys
sys.path.append('E:/A25cun/coder')
import os
from openai import OpenAI
from swarm import Swarm, Agent
from deepcoder.utils import pretty_print_messages,process_and_print_streaming_response,extract_generation_code, languge_settings
import sys
from human_eval.evaluation import evaluate_functional_correctness
from deepcoder.agent import MultiAgent

data_abs_dir = "E:\A25cun\coder\deepcoder\evaluation\data"


def build_deepseekcoder_instruction(languge: str, question: str):
    return '''
Please continue to complete the function. You are not allowed to modify the given code and do the completion only. Please return all completed function in a codeblock. Here is the given code to do completion:
```{}
{}
```
'''.strip().format(languge.lower(), question.strip())

deepcoder = MultiAgent()

from deepcoder.utils import extract_generation_code
def generate_one(example, lang):
    prompt = build_deepseekcoder_instruction(languge_settings[lang]['full_name'], example['prompt'])
    
    example['output'] = deepcoder.get_answer(prompt)
    # example['output'] = "```python\nprint(\"hello\")\n```"
    # import time 
    # time.sleep(1)
    return extract_generation_code(example, lang_code=lang)

def generate_main(args):
    lang = args.language
    saved_path = args.output_path
    temp_dir = args.temp_dir
    os.makedirs(temp_dir, exist_ok=True)
    problem_file = os.path.join(data_abs_dir, f"humaneval-{lang}.jsonl")

    examples = [json.loads(x) for x in open(problem_file) if x.strip()]
    print("Read {} examples for evaluation over.".format(len(examples)))

    # Initialize a list to hold generated examples  
    generated_examples = []  
    last_task_id = None

    # Load existing saved examples if any, to avoid overwriting  
    try:  
        with open(saved_path, 'r', encoding='utf-8') as fw:  
            for line in fw:  
                generated_examples.append(json.loads(line))  
            if generated_examples:
                last_task_id = int(generated_examples[-1]['task_id'].split('/')[1]) 
                print("last_task_id : ",last_task_id)
    except FileNotFoundError:  
        # File does not exist, we can start fresh  
        pass  

    # Process examples and generate output  
    for i, ex in enumerate(tqdm(examples, desc='Generating')):  
        task_id = int(ex['task_id'].split('/')[1])  # Extract numerical part from 'Python/0'  
        
        if last_task_id and task_id <= last_task_id:  
            continue  
        
        try:  
            # Call the generation function  
            gen_example = generate_one(ex, args.language)  
            generated_examples.append(gen_example)  

            # Save every 5 processed examples  
            if (i + 1) % 2 == 0:  
                with open(saved_path, 'a', encoding='utf-8') as fw:  # Append mode  
                    for example in generated_examples[-2:]:  
                        fw.write(json.dumps(example) + '\n')  
                    print("Saved {} processed examples into {}".format(2, saved_path))  

        except Exception as e:  
            print(f"Error processing example {ex['task_id']}: {e}")  
            # Handle the error as appropriate (logging, etc.)  

    # Final save after all examples processed  
    with open(saved_path, 'w', encoding='utf-8') as fw:  
        for ex in generated_examples:  
            fw.write(json.dumps(ex) + '\n')  
        print("Final save: saved {} processed examples into {} over!".format(len(generated_examples), saved_path))  

    print("Generate all over!!!")  

    return saved_path,temp_dir,problem_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str, help="output path of your generation",default="output/python.jsonl")
    parser.add_argument('--language', type=str, help="langauge",default="python")
    parser.add_argument('--temp_dir', type=str, help="temp dir for evaluation", default="tmp")
    args = parser.parse_args()
    input_file,tmp,problem_file =generate_main(args)
    print("input_file : ",input_file)
    print("tmp : ",tmp)
    print("problem_file : ",problem_file)
    result = evaluate_functional_correctness(
        input_file=input_file,
        tmp_dir=tmp,
        n_workers=8,
        timeout=3.0,
        problem_file=problem_file,
        language="python"
    )
    print(result)