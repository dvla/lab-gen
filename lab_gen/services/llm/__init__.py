"""Configure LLMS."""

from langchain.globals import set_debug

from lab_gen.settings import settings


set_debug(settings.log_level.value == "DEBUG")
