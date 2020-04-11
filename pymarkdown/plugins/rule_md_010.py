"""
Module to implement a plugin that looks for hard tabs in the files.
"""
from pymarkdown.plugin_manager import Plugin, PluginDetails


class RuleMd010(Plugin):
    """
    Class to implement a plugin that looks for hard tabs in the files.
    """

    def get_details(self):
        """
        Get the details for the plugin.
        """
        return PluginDetails(
            # whitespace, hard_tab
            plugin_name="no-hard-tabs",
            plugin_id="MD010",
            plugin_enabled_by_default=True,
            plugin_description="Hard tabs",
        )  # https://github.com/DavidAnson/markdownlint/blob/master/doc/Rules.md#md010---hard-tabs
        # Parameters: code_blocks (boolean; default true)

    def starting_new_file(self):
        """
        Event that the a new file to be scanned is starting.
        """

    def next_line(self, line):
        """
        Event that a new line is being processed.
        """

    def completed_file(self):
        """
        Event that the file being currently scanned is now completed.
        """
