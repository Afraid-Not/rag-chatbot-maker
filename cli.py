import asyncio
import sys

import typer
from rich.console import Console
from rich.panel import Panel

sys.stdin.reconfigure(encoding="utf-8", errors="replace")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.core.memory_bank import MemoryBank
from app.core.rag import ask

console = Console()
app = typer.Typer()


@app.command()
def chat(user_id: str = typer.Option("default", help="사용자 ID")):
    """다이어트 식품 RAG 챗봇과 대화합니다."""
    console.print(Panel("다이어트 식품 RAG 챗봇", style="bold green"))
    console.print("종료: quit | 메모리 저장: /remember <key> <value>\n")

    loop = asyncio.new_event_loop()

    while True:
        try:
            question = console.input("[bold cyan]You:[/] ")
        except (EOFError, KeyboardInterrupt):
            break

        if question.strip().lower() in ("quit", "exit", "q"):
            console.print("안녕히 가세요!", style="bold yellow")
            break

        if question.strip().startswith("/remember"):
            parts = question.strip().split(maxsplit=2)
            if len(parts) < 3:
                console.print("사용법: /remember <key> <value>", style="red")
                continue
            _, key, value = parts
            bank = MemoryBank(user_id)
            loop.run_until_complete(bank.save(key, value))
            console.print(f"저장됨: {key} = {value}", style="green")
            continue

        if question.strip().startswith("/memory"):
            bank = MemoryBank(user_id)
            memories = loop.run_until_complete(bank.get_all())
            if memories:
                for k, v in memories.items():
                    console.print(f"  {k}: {v}", style="dim")
            else:
                console.print("저장된 메모리가 없습니다.", style="dim")
            continue

        result = loop.run_until_complete(ask(question, user_id))
        console.print(f"\n[bold green]Bot:[/] {result['answer']}")
        console.print(f"\n[dim]출처:\n{result['sources']}[/dim]\n")

    loop.close()


def main():
    app()


if __name__ == "__main__":
    main()
