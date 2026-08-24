import asyncio
import contextlib
import io
import shlex

import click

speakable = frozenset(["help", "summarise", "quote", "examine", "bike"])


@click.group(name="narrator")
def commands():
    pass


@commands.command()
@click.pass_obj
def help(request):
    """show this message"""
    return request.handler.help(request.message)


@commands.command()
@click.option("-n", "count", type=int, default=50, help="how many messages to read")
@click.pass_obj
def summarise(request, count):
    """summarise the last n messages"""
    return request.handler.summarise(request.message, count)


@commands.command()
@click.pass_obj
def quote(request):
    """post a random message from this thread"""
    return request.handler.quote(request.message)


@commands.command()
@click.option("--summarise", "summarised", is_flag=True, help="summarise the matches instead")
@click.argument("query", nargs=-1, required=True)
@click.pass_obj
def find(request, summarised, query):
    """search this thread's history for a phrase"""
    return request.handler.find(request.message, " ".join(query), summarised)


@commands.command()
@click.argument("item", nargs=-1, required=True)
@click.pass_obj
def examine(request, item):
    """look up the OSRS examine text for an item"""
    return request.handler.examine(request.message, " ".join(item))


@commands.command()
@click.argument("name", nargs=-1, required=True)
@click.pass_obj
def bike(request, name):
    """look up a bike's specs"""
    return request.handler.bike(request.message, " ".join(name))


@commands.command()
@click.argument("prompt", nargs=-1, required=True)
@click.pass_obj
def gen(request, prompt):
    """generate an image"""
    return request.handler.gen(request.message, " ".join(prompt))


@commands.command()
@click.argument("prompt", nargs=-1, required=True)
@click.pass_obj
def genfill(request, prompt):
    """regenerate the masked part of the group photo"""
    return request.handler.genfill(request.message, " ".join(prompt))


@commands.command()
@click.option("--pitch", type=click.Choice(["high", "low"]), default=None, help="shift the voice pitch")
@click.argument("text", nargs=-1, required=True)
@click.pass_obj
def say(request, pitch, text):
    """reply with a voice clip"""
    return request.handler.say(request.message, " ".join(text), pitch)


@commands.command()
@click.argument("postcode", nargs=-1, required=True)
@click.pass_obj
def crime(request, postcode):
    """map link and crime plot for a postcode"""
    return request.handler.crime(request.message, " ".join(postcode))


@commands.command()
@click.pass_obj
def echoimages(request):
    """resend recent images in this thread"""
    return request.handler.echoimages(request.message)


@commands.command()
@click.pass_obj
def randomimage(request):
    """post a random image from this thread"""
    return request.handler.randomimage(request.message)


def name_in(text):
    words = text.split()
    return words[0].lower() if words else ""


def is_command(text):
    return name_in(text) in commands.commands


def tokenise(text):
    try:
        words = shlex.split(text)
    except ValueError:
        words = text.split()
    return [words[0].lower()] + words[1:] if words else []


async def run(request, text):
    printed = io.StringIO()
    try:
        with contextlib.redirect_stdout(printed):
            result = commands.main(args=tokenise(text), prog_name="", standalone_mode=False, obj=request)
    except click.ClickException as error:
        return error.format_message()
    if isinstance(result, int):
        return printed.getvalue().strip() or None
    return await result if asyncio.iscoroutine(result) else result


def help_text():
    return "\n\n".join(help_line_for(name, command) for name, command in sorted(commands.commands.items()))


def help_line_for(name, command):
    options = " ".join(option.opts[0] for option in command.params if isinstance(option, click.Option))
    arguments = " ".join(argument.name.upper() for argument in command.params
                         if isinstance(argument, click.Argument))
    usage = " ".join(part for part in [name, f"[{options}]" if options else "", arguments] if part)
    return f"{usage} - {command.short_help or command.help}"
