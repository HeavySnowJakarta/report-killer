"""Command-line interface for Report Killer."""

import click
import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from .config import Config
from .agent import ReportAgent

console = Console()


@click.group()
def cli():
    """Report Killer - AI-powered document completion tool."""
    pass


@cli.command()
def configure():
    """Configure the Report Killer settings."""
    console.print(Panel.fit("🔧 [bold]Report Killer Configuration[/bold]"))
    
    config = Config.load()
    
    # API Configuration
    console.print("\n[cyan]API Configuration[/cyan]")
    api_url = Prompt.ask("API URL", default=config.api_url)
    api_key = Prompt.ask("API Key", default=config.api_key or "", password=True)
    model = Prompt.ask("Model", default=config.model)
    
    # Proxy Configuration
    console.print("\n[cyan]Proxy Configuration (optional)[/cyan]")
    use_proxy = Confirm.ask("Do you want to configure a proxy?", default=bool(config.http_proxy))
    
    http_proxy = None
    https_proxy = None
    if use_proxy:
        http_proxy = Prompt.ask("HTTP Proxy", default=config.http_proxy or "")
        https_proxy = Prompt.ask("HTTPS Proxy", default=config.https_proxy or "")
    
    # Custom Prompt
    console.print("\n[cyan]Custom Prompt (optional)[/cyan]")
    custom_prompt = Prompt.ask(
        "Additional instructions for the AI",
        default=config.custom_prompt or ""
    )
    
    # Documents Directory
    console.print("\n[cyan]Documents Directory[/cyan]")
    documents_dir = Prompt.ask("Documents directory", default=config.documents_dir)
    
    # Save configuration
    config.api_url = api_url
    config.api_key = api_key
    config.model = model
    config.http_proxy = http_proxy
    config.https_proxy = https_proxy
    config.custom_prompt = custom_prompt
    config.documents_dir = documents_dir
    
    config.save()
    
    console.print("\n[green]✓ Configuration saved successfully![/green]")


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path (default: overwrites input)')
@click.option('--api-key', help='API key (overrides config)')
@click.option('--model', help='Model name (overrides config)')
@click.option('--prompt', help='Additional prompt (overrides config)')
def process(input_file, output, api_key, model, prompt):
    """Process a Word document and fill in the answers."""
    console.print(Panel.fit("📝 [bold]Report Killer - Document Processor[/bold]"))
    
    # Load configuration
    config = Config.load()
    
    # Override with command-line arguments
    if api_key:
        config.api_key = api_key
    if model:
        config.model = model
    if prompt:
        config.custom_prompt = prompt
    
    # Validate configuration
    if not config.api_key:
        console.print("[red]Error: API key not configured![/red]")
        console.print("Run 'report-killer configure' to set up your API key.")
        return
    
    # Create agent
    agent = ReportAgent(config)
    
    # Process document
    output_path = output or input_file
    success = agent.process_document(input_file, output_path)
    
    if success:
        console.print(f"\n[green]✓ Document processed successfully![/green]")
        console.print(f"[cyan]Output saved to:[/cyan] {output_path}")
    else:
        console.print(f"\n[red]✗ Failed to process document[/red]")
        exit(1)


@cli.command()
def test():
    """Test the Report Killer with the test document."""
    console.print(Panel.fit("🧪 [bold]Report Killer - Test Mode[/bold]"))
    
    # Check if test file exists
    test_file = Path("tests/test_ai_doc.docx")
    if not test_file.exists():
        console.print(f"[red]Error: Test file not found at {test_file}[/red]")
        return
    
    # Load configuration
    config = Config.load()
    
    if not config.api_key:
        console.print("[red]Error: API key not configured![/red]")
        console.print("Run 'report-killer configure' to set up your API key.")
        return
    
    # Create documents directory
    docs_dir = Path(config.documents_dir)
    docs_dir.mkdir(exist_ok=True)
    
    # Copy test file to documents directory
    import shutil
    output_file = docs_dir / "test_ai_doc_output.docx"
    shutil.copy(test_file, output_file)
    
    console.print(f"[cyan]Testing with:[/cyan] {test_file}")
    console.print(f"[cyan]Output will be saved to:[/cyan] {output_file}")
    
    # Create agent
    agent = ReportAgent(config)
    
    # Process document
    success = agent.process_document(str(output_file))
    
    if success:
        console.print(f"\n[green]✓ Test completed successfully![/green]")
        console.print(f"[cyan]Check the output at:[/cyan] {output_file}")
    else:
        console.print(f"\n[red]✗ Test failed[/red]")
        exit(1)


@cli.command()
def info():
    """Show current configuration and status."""
    console.print(Panel.fit("ℹ️  [bold]Report Killer - Information[/bold]"))
    
    config = Config.load()
    
    console.print("\n[cyan]Configuration:[/cyan]")
    console.print(f"  API URL: {config.api_url}")
    console.print(f"  API Key: {'*' * 20 if config.api_key else '[red]Not configured[/red]'}")
    console.print(f"  Model: {config.model}")
    console.print(f"  HTTP Proxy: {config.http_proxy or '[dim]Not set[/dim]'}")
    console.print(f"  HTTPS Proxy: {config.https_proxy or '[dim]Not set[/dim]'}")
    console.print(f"  Custom Prompt: {config.custom_prompt or '[dim]Not set[/dim]'}")
    console.print(f"  Documents Dir: {config.documents_dir}")
    
    # Check environment
    agent = ReportAgent(config)
    checks = agent.check_environment()
    
    console.print("\n[cyan]Environment Check:[/cyan]")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        color = "green" if passed else "red"
        console.print(f"  [{color}]{status}[/{color}] {check}")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
