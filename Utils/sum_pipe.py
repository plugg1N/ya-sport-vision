from summa.summarizer import summarize
from llama_cpp import Llama


def init_model() -> Llama:
    llm = Llama(
          model_path="/home/ubuntu/ya-sport-vision/sum/quant_gemma/gemma-2-9b-it-Q5_K_M.gguf",
          n_gpu_layers=-1, # Uncomment to use GPU acceleration
          # seed=1337, # Uncomment to set a specific seed
          n_ctx=8192,
          verbose=False
    )
    return llm


def gen_extra_sum(text_for_sum: str) -> str:
    list_of_parts_for_sum = text_for_sum.split("\n\n")
    list_of_parts_for_sum = list(filter(lambda x: len(x.split(":")[-1]), list_of_parts_for_sum))
    short_text =  "{}\n{}\n{}".format("\n".join(list_of_parts_for_sum[:3]),summarize("\n".join(list_of_parts_for_sum[3:-3]), ratio=0.1),"\n".join(list_of_parts_for_sum[-3:]))
    while "\n\n" in short_text:
        short_text = short_text.replace("\n\n", "\n")
    return short_text


def get_instruct(text: str):
  # print(text)
  instruct = f"""
  <start_of_turn>user Ты профессиональный спортивный журналист. Очень сильно сократи следующий текст, оставь лишь ключевые моменты текста. текст для сокращения: {text}. Сократи текст до двадцати слов<end_of_turn>
  <start_of_turn>model Без проблем, вот ваш сокращённый текст:"""
  return instruct


def generat_ans(instruct: str, llm: Llama):
  output = llm(instruct, # Prompt
        max_tokens=8192, # Generate up to 32 tokens, set to None to generate up to the end of the context window
        stop=["<end_of_turn>", "\n\n\n"], # Stop generating just before the model would generate a new question
        echo=False, # Echo the prompt back in the output
        stream=True,
        temperature=0.6
  ) # Generate a completion, can also call create_completion
  # print("Output: {output['choices']}")
  return output


def gen_abs_sum(instruct: str, llm: Llama) -> str:
    gener = generat_ans(instruct, llm)
    ans = ""
    for part in gener:
        if part['choices'][0]["text"] in ["\n\n", "", "\n", "**", "> "]:
            continue
        ans+=part['choices'][0]["text"]
    while "  " in ans:
        ans = ans.replace("  ", " ")
    return ans.strip()



def create_summary(text: str, llm: Llama) -> str:
    short_text = gen_extra_sum(text)
    texts = short_text.split("\n")
    index = 0
    temp = texts[index].split(":")[-1]
    back_t = ""
    res = []
    while index < len(texts):
        if len(temp) < 4096:
            index += 1
            if index ==  len(texts):
                break
            temp += "{}".format(texts[index].split(":")[-1])
        else:
            # res.append(temp)
            res.append(gen_abs_sum(get_instruct(temp), llm))
            index += 1
            temp = texts[index]
        # print(temp)
        if temp == back_t:
            break
        else:
            back_t = temp
    if temp != "":
        # res.append(temp)
        res.append(gen_abs_sum(get_instruct(temp), llm))
    sum_text = " ".join([line for line in res])
    sum_text = sum_text.replace("\n","")
    while "  " in sum_text:
        sum_text = sum_text.replace("  "," ")
    inst = f"""
    <start_of_turn>user
    Ты профффесиональный редактор теста. Перепиши текст, сохранив его суть, при этом убери все ошибки и повторы. текст для сокращения: {sum_text}.<end_of_turn>
    <start_of_turn>model
    Без проблем, вот ваш сокращённый текст: """
    ans = gen_abs_sum(inst, llm)
    return ans


def gen_answer(prompt: str,llm: Llama):
    inst = f"""
    <start_of_turn>user
    Ты профффесиональный спортивный комментатор. Отвечай на вопросы пользователя максимально ёмко и просто, будто обьясняешь ребёнку. Вопрос пользователя: {prompt}.<end_of_turn>
    <start_of_turn>model
    Без проблем, """
    ans = gen_abs_sum(inst, llm)
    return ans


def gen_conspect(prompt: str, llm: Llama):
    inst = f"""
    <start_of_turn>user
    Ты специалист в области математики и информатики. Законспектируй отрывок лекции, используя markdown разметку, отображая основные тезисы, а все математические выражения запиши, используя LaTeX. Отрывок лекции: {prompt}.<end_of_turn>
    <start_of_turn>model
    Конечно, вот ваш конспект с использованием markdown и LaTeX разметок: """
    ans = gen_abs_sum(inst, llm)
    return ans
