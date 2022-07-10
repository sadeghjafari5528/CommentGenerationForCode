# -*- coding: utf-8 -*-
"""CodeTrans: CommentGenerationForCode_TransformerFineTuned.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1krt-x0LmdkuoTeHDzZkjLwLN2Vk_rNmF

### Install the necessary libraries
"""

!pip install datasets transformers[sentencepiece]

"""### Load the necessary libraries"""

from datasets import load_dataset, load_metric
from transformers import AutoTokenizer
from transformers import AutoModelForSeq2SeqLM, DataCollatorForSeq2Seq, Seq2SeqTrainingArguments, Seq2SeqTrainer, SummarizationPipeline
from transformers import AutoTokenizer, AutoModelWithLMHead, Text2TextGenerationPipeline
import numpy as np
import json

"""### Load the model and its tokenizer libraries"""

model_checkpoint = "SEBIS/code_trans_t5_small_code_comment_generation_java_transfer_learning_finetune"
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
model = AutoModelForSeq2SeqLM.from_pretrained(model_checkpoint)

"""### Load the evaluation metric"""

bleu_metric = load_metric("bleu")

"""### Load dataset"""

with open("data.json") as f:
  data = json.load(f)

codes = []
comments = []
for sample in data:
  codes.append(sample["method_text"])
  comments.append(sample["comment_text"])

"""### Tokenize the dataset"""

max_input_length = 512
max_target_length = 512
source_input = "code"
target_output = "comment"

def preprocess_function(examples):
    inputs = examples[source_input]
    targets = examples[target_output]
    model_inputs = tokenizer(inputs, max_length=max_input_length, truncation=True)

    # Setup the tokenizer for targets
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(targets, max_length=max_target_length, truncation=True)

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

def get_tokenized_datasets(codes, comments, train, val, test):
  no_data = len(codes)

  train_data = []
  for i in range(0, int(no_data*train)):
    train_data.append(preprocess_function({"code":codes[i], "comment":comments[i]}))
  #train_data = preprocess_function(train_data)

  val_data = []
  for i in range(int(no_data*train), int(no_data*(train + val))):
    val_data.append(preprocess_function({"code":codes[i], "comment":comments[i]}))
  #val_data = preprocess_function(val_data)

  test_data = []
  for i in range(int(no_data*(train + val)), int(no_data*(train + val + test))):
    test_data.append(preprocess_function({"code":codes[i], "comment":comments[i]}))
  #test_data = preprocess_function(test_data)
  return {"train":train_data, "validation":val_data, "test":test_data}

tokenized_datasets = get_tokenized_datasets(codes, comments, 0.8, 0.1, 0.1)

"""### Define the training arguments"""

batch_size = 8
model_name = model_checkpoint.split("/")[-1]
args = Seq2SeqTrainingArguments(
    f"{model_name}-finetuned-{source_input}-to-{target_output}",
    evaluation_strategy = "epoch",
    learning_rate=1e-4,
    warmup_ratio=0.1,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=10,
    predict_with_generate=True,
    fp16=False,
    fp16_opt_level="02",
    push_to_hub=False,
    gradient_accumulation_steps=32,
    seed=42,
    load_best_model_at_end=True,
    metric_for_best_model="eval_bleu",
    greater_is_better=True,
    save_strategy="epoch"
)

"""### Create the data collator for the inputs/outputs batching"""

data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

"""### Create the evaluation metric function"""

def postprocess_text(preds, labels):
    preds = [pred.strip().split() for pred in preds]
    labels = [[label.strip().split()] for label in labels]

    return preds, labels

def compute_metrics(eval_preds):
    preds, labels = eval_preds
    if isinstance(preds, tuple):
        preds = preds[0]
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)

    # Replace -100 in the labels as we can't decode them.
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    # Some simple post-processing
    decoded_preds, decoded_labels = postprocess_text(decoded_preds, decoded_labels)

    result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
    result = {"bleu": result["bleu"]*100}

    prediction_lens = [np.count_nonzero(pred != tokenizer.pad_token_id) for pred in preds]
    result["gen_len"] = np.mean(prediction_lens)
    result = {k: round(v, 4) for k, v in result.items()}
    return result

"""### Create the trainer based on the above declarations and functions"""

trainer = Seq2SeqTrainer(
    model,
    args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    data_collator=data_collator,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

"""### Start training"""

trainer.train()

"""### Create inference pipeline"""

original_pipeline = SummarizationPipeline(
    model=model,
    tokenizer=tokenizer,
    device=0
)

pipeline = SummarizationPipeline(
    model=trainer.model,
    tokenizer=tokenizer,
    device=0
)

"""### Make prediction for a single example on the test tdataset"""

!pip install javalang
import javalang

def tokenize_java_code(code):
    tokenList = []
    tokens = list(javalang.tokenizer.tokenize(code))
    for token in tokens:
        tokenList.append(token.value)
    
    return ' '.join(tokenList)

code = codes[5010]

tokenized_code = tokenize_java_code(code)
print("Output after tokenization: " + tokenized_code)

print(comments[5010])

print(original_pipeline([tokenized_code])) # original model

print(pipeline([tokenized_code])) # fine tuned model