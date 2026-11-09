from langchain_ollama import ChatOllama

import json
from pathlib import Path

from schemas import JobPost

llm = ChatOllama(
    model="qwen3.5:9b", num_ctx=16384, temperature=0, reasoning=False
)  # no randomness, no hidden "thinking" tokens

SAMPLES = Path(__file__).parent / "samples"


def extract(schema, instruction: str, text: str):

    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    return llm.with_structured_output(schema).invoke(
        f"{instruction}\n Follow this JSON schema and its field descriptions:\n{schema_json}\n\n{text}"
    )


if __name__ == "__main__":
    for path in sorted(SAMPLES.glob("*.txt")):
        print(f"\n########## {path.name} ##########")
        print(
            extract(
                schema=JobPost,
                instruction="Extract the job information from this job post.",
                text=f"Job post:\n{path.read_text(encoding='utf-8')}",
            ).model_dump_json(indent=2)
        )
