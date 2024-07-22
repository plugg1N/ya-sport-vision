import asyncio
import json

from summa.summarizer import summarize
from llama_cpp import Llama

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


def init_model() -> Llama:
    llm = Llama(
          model_path="/home/ubuntu/ya-sport-vision/sum/quant_gemma/gemma-2-9b-it-Q5_K_M.gguf",
          n_gpu_layers=-1, # Uncomment to use GPU acceleration
          # seed=1337, # Uncomment to set a specific seed
          n_ctx=8192,
          verbose=False
    )
    return llm


def gen_extra_sum(text_for_sum: str, ratio_length=0.4) -> str:
    list_of_parts_for_sum = text_for_sum.split("\n")
    # list_of_parts_for_sum = list(filter(lambda x: len(x.split(":")[-1]), list_of_parts_for_sum))
    short_text =  "{}\n{}\n{}".format("\n".join(list_of_parts_for_sum[:3]),summarize("\n".join(list_of_parts_for_sum[3:-3]), ratio=ratio_length),"\n".join(list_of_parts_for_sum[-3:]))
    while "\n\n" in short_text:
        short_text = short_text.replace("\n\n", "\n")
    return short_text


def get_instruct(text: str):
  # print(text)
  instruct = f"""
  <start_of_turn>user Ты профессиональный спортивный журналист. Твоя задача рассказать только об основных моментах части игры, ориентируясь на текст, но не путай термины и не додумывай события. Не используй слова: ['овертайм', 'матч завершился'] если их нет в тексте. текстовая расшифровка игры: {text}. Максимум ты можешь использовать сто слов. <end_of_turn>
  <start_of_turn>model Без проблем, вот ваша текстовая выжимка:"""
  return instruct


async def get_part_instruct(text: str, key: str, answer_topic: str, producer, consumer_sum):
    # data = {"answer_topic": answer_topic, "command": "get_llm_summary", "id": key}
    # print(data)
    # await producer.send_and_wait("redis_get", data)
    prev_sum = ""
    # async for msg in consumer_sum:
            # print(
            # "{}:{:d}:{:d}: key={} value={} timestamp_ms={}".format(
                # msg.topic, msg.partition, msg.offset, msg.key, msg.value,
                    # msg.timestamp))
            # data = msg.value
            # print(data)
            # if key == data["id"]:
                # prev_sum = data["ans"]
                # break
    if prev_sum != "":
        instruct = f"""
        <start_of_turn>user Ты профессиональный спортивный журналист. Сократи следующий текст, оставь лишь ключевые моменты текста. текст для сокращения: {text}. Сократи текст до ста слов. Для понимания контекста матча используй предыдущий пересказ: {prev_sum}<end_of_turn>
        <start_of_turn>model Без проблем, вот ваш сокращённый текст:"""
    else:
        instruct = f"""
        <start_of_turn>user Ты профессиональный спортивный журналист. Сократи следующий текст, оставь лишь ключевые моменты текста. текст для сокращения: {text}. Сократи текст до ста слов. <end_of_turn>
        <start_of_turn>model Без проблем, вот ваш сокращённый текст:"""
    return instruct


def generat_ans(instruct: str):
  output = llm(instruct, # Prompt
        max_tokens=8192, # Generate up to 32 tokens, set to None to generate up to the end of the context window
               stop=["<end_of_turn>", "\n\n\n", "***", "Изменения:"], # Stop generating just before the model would generate a new question
        echo=False, # Echo the prompt back in the output
        stream=True,
        temperature=0.6
  ) # Generate a completion, can also call create_completion
  # print("Output: {output['choices']}")
  return output


def gen_llm_answer(instruct: str) -> str:
    gener = generat_ans(instruct)
    ans = ""
    for part in gener:
        if part['choices'][0]["text"] in ["\n\n", "", "\n", "**", "> ", '\"']:
            continue
        ans+=part['choices'][0]["text"]
    while "  " in ans:
        ans = ans.replace("  ", " ")
    return ans.strip()



def create_summary(text: str) -> str:
    short_text = gen_extra_sum(text)
    # print(short_text)
    texts = short_text.split("\n")
    index = 0
    temp = texts[index].split(":")[-1]
    back_t = ""
    res = []
    while index < len(texts)-1:
        if len(temp) < 5000:
            index += 1
            if index ==  len(texts):
                break
            temp += "{}".format(texts[index].split(":")[-1])
        else:
            # res.append(temp)
            res.append(gen_llm_answer(get_instruct(temp)))
            index += 1
            temp = texts[index]
        # print(temp)
        if temp == back_t:
            break
        else:
            back_t = temp
    if temp != "":
        # res.append(temp)
        res.append(gen_llm_answer(get_instruct(temp)))
    sum_text = " ".join([line for line in res])
    sum_text = sum_text.replace("\n","")
    while "  " in sum_text:
        sum_text = sum_text.replace("  "," ")
    inst = f"""
    <start_of_turn>user
    Ты професиональный редактор теста. Перепиши текст, сохранив его суть, при этом убери все ошибки и повторы. текст для сокращения: {sum_text}.<end_of_turn>
    <start_of_turn>model
    Без проблем, вот ваш сокращённый текст: """
    ans = gen_llm_answer(inst)
    return ans


async def create_part_summary(text: str, key, producer) -> str:
    short_text = gen_extra_sum(text, ratio_length=0.4)
    print(short_text)
    texts = short_text.split("\n")
    index = 0
    temp = texts[index]
    back_t = ""
    res = []
    answer_topic = "sum_part"
    consumer_sum = AIOKafkaConsumer(
        answer_topic,
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda x: json.loads(x.decode("utf-8")))
    await consumer_sum.start()
    try:
        while index < len(texts)-1:
            if len(temp) < 4096:
                index += 1
                if index ==  len(texts):
                    break
                temp += "{}".format(texts[index].split(":")[-1])
            else:
                # res.append(temp)
                res.append(gen_llm_answer(await get_part_instruct(temp, key, answer_topic, producer, consumer_sum)))
                index += 1
                temp = texts[index]
            # print(temp)
            if temp == back_t:
                break
            else:
                back_t = temp
        if temp != "":
            # res.append(temp)
            res.append(gen_llm_answer(await get_part_instruct(temp, key, answer_topic, producer, consumer_sum)))
        sum_text = " ".join([line for line in res])
        sum_text = sum_text.replace("\n","")
        while "  " in sum_text:
            sum_text = sum_text.replace("  "," ")
        # inst = f"""
        # <start_of_turn>user
        # Ты професиональный редактор теста. Перепиши текст, сохранив его суть, при этом убери все ошибки и повторы. текст для сокращения: {sum_text}.<end_of_turn>
        # <start_of_turn>model
        # Без проблем, вот ваш сокращённый текст: """
        # ans = gen_llm_answer(inst)
        # data = {"command": "put_llm_summary", "id": key, "text": sum_text}
        # await producer.send_and_wait("redis_get", data)
        return sum_text
    finally:
        await consumer_sum.stop()


async def gen_answer(prompt: str, key: str, producer):
    answer_topic = "redis_history"
    inst = f"""
    <start_of_turn>user
    Ты професиональный спортивный комментатор. Отвечай на вопросы пользователя максимально ёмко и просто, будто обьясняешь ребёнку. Вопрос пользователя: {prompt}. <end_of_turn>
    <start_of_turn>model
    Без проблем, """
    consumer_redis = AIOKafkaConsumer(
        answer_topic,
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda x: json.loads(x.decode("utf-8")))
    chat = ""
    await consumer_redis.start()
    data = {"id": key, "command": "get_llm_history", "answer_topic": answer_topic}
    consumer_rag = AIOKafkaConsumer(
        "give_rag",
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda x: json.loads(x.decode("utf-8")))
    await consumer_rag.start()
    await producer.send_and_wait("redis_get", data)
    try:
        # print(answer_topic == data["answer_topic"])
        # print(chat,"cons")
        async for msg in consumer_redis:
            # print(
            # "{}:{:d}:{:d}: key={} value={} timestamp_ms={}".format(
                # msg.topic, msg.partition, msg.offset, msg.key, msg.value,
                    # msg.timestamp))
            data = msg.value
            # print(data)
            if key == data["id"]:
                if data["ans"] is not None:
                    chat = data["ans"]
                break
        else:
            print("no message")
        temp = inst.split("<end_of_turn>")
        print(temp)
        rag_dop_inf = ""
        await producer.send_and_wait("get_rag", {"command":"question", "id": key, "query": prompt})
        async for msg in consumer_rag:
            data = msg.value
            print(data)
            if key == data["id"]:
                if data["ans"] is not None:
                    rag_dop_inf = data["ans"]
                break
        chat = f"{chat}\n{temp[0]}"
        if rag_dop_inf != "":
            chat += f"Дополнительная информация для ответа: {rag_dop_inf}"
        chat += f"<end_of_turn>{temp[1]}"
        ans = await asyncio.get_running_loop().run_in_executor(None, gen_llm_answer, chat)
        ### TODO валидация
        await producer.send_and_wait("redis_get", {"id": key, "prompt": inst, "ans": ans, "command": "put_llm_history"})
        return ans
    except Exception as e:
        print(e)
    finally:
        await consumer_redis.stop()
        await consumer_rag.stop()


async def gen_conspect(prompt: str):
    inst = f"""
    <start_of_turn>user
    Ты специалист в области математики и информатики. Законспектируй отрывок лекции, используя markdown разметку, отображая основные тезисы, а все математические выражения запиши, используя LaTeX. Отрывок лекции: {prompt}.<end_of_turn>
    <start_of_turn>model
    Конечно, вот ваш конспект с использованием markdown и LaTeX разметок: """
    ans = asyncio.get_running_loop().run_in_executor(None, gen_llm_answer, inst)
    return ans


async def get_command():
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092",
                            value_serializer=lambda x: json.dumps(x).encode("utf-8"))

    consumer = AIOKafkaConsumer(
        "llm_question",
        bootstrap_servers='localhost:9092',
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    await producer.start()
    await consumer.start()
    try:
        async for message in consumer:
            # print(message.value, "cons")
            data = message.value
            answer_topic = data["answer_topic"]
            if data["command"] == "question":
                ans = await gen_answer(data["prompt"], data["id"], producer)
                # print(ans)
                await producer.send_and_wait(answer_topic, {"ans": ans, "id": data["id"]})
            elif data["command"] == "part_summary":
                ans = await create_part_summary(data["for_summary_text"], data["id"], producer)
                # print(ans)
                await producer.send_and_wait(answer_topic, {"ans": ans, "id": data["id"]})
            elif data["command"] == "summary":
                ans = await asyncio.get_running_loop().run_in_executor(None, create_summary, data["for_summary_text"])
                # print(ans)
                await producer.send_and_wait(answer_topic, {"ans": ans, "id": data["id"]})
            else:
                await producer.send_and_wait(answer_topic, {"error": "Unknown command"})
    finally:
        await producer.stop()
        await consumer.stop()


if __name__ == "__main__":
    llm = init_model()
    asyncio.run(get_command())
