import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def debug_enabled() -> bool:
    value = os.getenv("BUD_E_DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def ensure_mem0_dir():
    mem0_dir = os.getenv("MEM0_DIR")
    if not mem0_dir:
        mem0_dir = os.path.join(os.getcwd(), ".mem0")
        os.environ["MEM0_DIR"] = mem0_dir
    os.makedirs(mem0_dir, exist_ok=True)
    return mem0_dir


@dataclass
class DynamicMemoryItem:
    memory: str
    score: float | None = None
    source: str = "dynamic"


class DynamicMemoryAdapter:
    provider_name = "none"

    def search(self, query: str, user_id: str, limit: int = 3) -> list[DynamicMemoryItem]:
        return []

    def capture_turn(self, user_id: str, user_message: str, assistant_message: str) -> None:
        return None


class NullDynamicMemoryAdapter(DynamicMemoryAdapter):
    provider_name = "none"


class Mem0DynamicMemoryAdapter(DynamicMemoryAdapter):
    provider_name = "mem0"

    def __init__(self):
        ensure_mem0_dir()
        mode = os.getenv("BUD_E_MEM0_MODE", "platform").strip().lower()
        self.mode = mode

        if mode == "platform":
            from mem0 import MemoryClient

            api_key = os.getenv("MEM0_API_KEY")
            org_id = os.getenv("MEM0_ORG_ID")
            project_id = os.getenv("MEM0_PROJECT_ID")
            self.memory = MemoryClient(api_key=api_key, org_id=org_id, project_id=project_id)
        else:
            from mem0 import Memory

            config = {"version": "v1.1"}
            if hasattr(Memory, "from_config"):
                self.memory = Memory.from_config(config)
            else:
                self.memory = Memory(config=config)

    def search(self, query: str, user_id: str, limit: int = 3) -> list[DynamicMemoryItem]:
        if self.mode == "platform":
            results = self.memory.search(query=query, version="v2", filters={"AND": [{"user_id": user_id}]})
        else:
            results = self.memory.search(query=query, user_id=user_id, limit=limit)

        entries = []
        raw_results = results.get("results", []) if isinstance(results, dict) else results
        for item in raw_results[:limit]:
            entries.append(
                DynamicMemoryItem(
                    memory=item.get("memory", "").strip(),
                    score=item.get("score"),
                    source="mem0",
                )
            )
        return [entry for entry in entries if entry.memory]

    def capture_turn(self, user_id: str, user_message: str, assistant_message: str) -> None:
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message},
        ]
        self.memory.add(messages, user_id=user_id)


def get_dynamic_memory_adapter() -> DynamicMemoryAdapter:
    provider = os.getenv("BUD_E_DYNAMIC_MEMORY_PROVIDER", "none").strip().lower()

    if provider == "mem0":
        try:
            return Mem0DynamicMemoryAdapter()
        except Exception as exc:
            if debug_enabled():
                print(f"Dynamic memory fallback to none: {exc}")
            return NullDynamicMemoryAdapter()

    return NullDynamicMemoryAdapter()


def format_dynamic_memories_for_prompt(memories: list[DynamicMemoryItem]) -> str:
    if not memories:
        return ""

    lines = ["\nRelevant dynamic memories:"]
    for memory in memories:
        lines.append(f"- {memory.memory}")
    lines.append("- Use these memories only when they help answer the current request.")
    lines.append("- Treat child profile memory as the source of truth for stable identity and parent settings.\n")
    return "\n".join(lines)
