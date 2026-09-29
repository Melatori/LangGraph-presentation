from pathlib import Path

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from backend_state import BackendState
from tools import TOOLS


MODEL = "anthropic:claude-sonnet-5"
INSTRUCTIONS_FILE = Path(__file__).resolve().parents[2] / ".claude" / "agents" / "java-spring-developer.md"
CONVENTIONS_FILE = Path(__file__).resolve().parents[1] / "conventions.md"
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
DEVELOPER_ROLE_FILE = PROMPTS_DIR / "developer.md"


def load_instructions(file: Path) -> str:
    text = file.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


def build_system_prompt(role_file: Path) -> str:
    # Order matters: general best practices -> project conventions (take precedence) -> agent role.
    return "\n\n".join(load_instructions(file) for file in [INSTRUCTIONS_FILE, CONVENTIONS_FILE, role_file])


llm = init_chat_model(MODEL, max_tokens=16000)


agent = create_agent(
    model=llm,
    tools=TOOLS,
    system_prompt=build_system_prompt(DEVELOPER_ROLE_FILE),
    state_schema=BackendState,
    name="backend"
)
