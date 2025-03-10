import argparse
import json
import os
import re
from pathlib import Path
from tqdm import tqdm
import argparse
import json
import os
from pathlib import Path
from tqdm import tqdm
import sys
sys.path.append('E:/A25cun/coder')
import os
import sys
from human_eval.evaluation import evaluate_functional_correctness
from deepcoder.agent import MultiAgent

data_abs_dir = "E:\A25cun\coder\deepcoder\evaluation\mbpp_data"
deepcoder = MultiAgent()

def read_test_examples(data_path: str):
    def format_test_example(q, tests, code: str=None):
        prompt = ">>> Problem:\n{}\n>>> Test Cases:\n{}\n".format(q.strip(), "\n".join(tests))
        if code:
            code = code.replace("\r", "").replace("\t", "    ")
            prompt += "\n>>> Code:\n```python\n{}\n```".format(code)
        return prompt

    examples = [json.loads(x) for x in open(data_path)]
    print("Read all {} examples from {} over!".format(len(examples), data_path))

    # test_cases
    examples_str = []
    for i in range(1, 4):
        ex = examples[i]
        q, test, code = ex['text'], ex['test_list'], ex['code']
        ex_prompt = format_test_example(q, test, code)
        example_prompt = '- Example {}:\n{}'.format(i, ex_prompt)
        examples_str += [example_prompt]

    for i in range(10, 510):
        ex = examples[i]
        q, test, code = ex['text'], ex['test_list'], ex['code']
        
        prompt = format_test_example(q, test, code=None)

        prompt_with_shots = '''
Please refer the given examples and generate a python function for my problem.
Examples are listed as follows:
{}

Here is my problem:
{}
'''.strip().format('\n\n'.join(examples_str), prompt)
        yield {
            'task_id': ex['task_id'],
            'prompt': prompt_with_shots
        }

def convert_for_evaluation(example):
    gpt_completion = example['gpt_completion']
    generation = gpt_completion
    try:
        code_block: str = re.findall(f'```python\n(.*?)```', gpt_completion, re.DOTALL | re.IGNORECASE)[0]
        generation = code_block
    except Exception as ex:
        print("Failed to extract codeblock:\n{}".format(gpt_completion))

    example['generation'] = generation
    return example

def generate_one(example):
    prompt = example['prompt']
    example['gpt_completion'] = deepcoder.get_answer(prompt)
    # example['gpt_completion']= "```python\nprint(\"hello\")\n```"
    import time 
    time.sleep(1)
    return convert_for_evaluation(example)


def generate_main(args):
    saved_path = args.output_path
    temp_dir = args.temp_dir
    os.makedirs(temp_dir, exist_ok=True)
    problem_file = os.path.join(data_abs_dir, f"mbpp.jsonl")

    examples = list(read_test_examples(problem_file))
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
                last_task_id = int(generated_examples[-1]['task_id']) 
                print("last_task_id : ",last_task_id)
    except FileNotFoundError:  
        # File does not exist, we can start fresh  
        pass  

    # Process examples and generate output  
    for i, ex in enumerate(tqdm(examples, desc='Generating')):  
        task_id = int(ex['task_id'])   
        
        if last_task_id and task_id <= last_task_id:  
            continue  
        
        try:  
            # Call the generation function  
            gen_example = generate_one(ex)  
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
    with open(saved_path, 'a', encoding='utf-8') as fw:  
        for ex in generated_examples:  
            fw.write(json.dumps(ex) + '\n')  
        print("Final save: saved {} processed examples into {} over!".format(len(generated_examples), saved_path))  

    print("Generate all over!!!")  
    return saved_path,temp_dir,problem_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str, help="output path of your generation", default='E:\\A25cun\\coder\\deepcoder\\evaluation\\output\\python_mbpp.jsonl')  
    parser.add_argument('--temp_dir', type=str, help="temp dir for evaluation", default="tmp")
    args = parser.parse_args()
    generate_main(args)
    pass