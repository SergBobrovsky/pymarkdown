"""
Module to provide a tokenization of a markdown-encoded string.
"""


class TokenizedMarkdown:
    """
    Class to provide a tokenization of a markdown-encoded string.
    """

    def __init__(self):
        """
        Initializes a new instance of the TokenizedMarkdown class.
        """
        self.ws_char = " \t"
        self.tokenized_document = None
        self.stack = ["document"]

    def transform(self, your_text_string):
        """
        Transform a markdown-encoded string into an array of tokens.
        """

        self.tokenized_document = []
        next_token = your_text_string.split("\n", 1)
        print("---")
        while next_token:
            print("next-line>>" + str(next_token))
            print("stack>>" + str(self.stack))
            print("current_block>>" + self.stack[-1])
            print("---")

            next_line = next_token[0]
            new_tokens = []
            if not next_line or not next_line.strip():
                new_tokens = self.handle_blank_line(next_line, from_main_transform=True)
            else:
                new_tokens = self.parse_line_for_container_blocks(next_line)

            print("---")
            print("before>>" + str(self.tokenized_document))
            self.tokenized_document.extend(new_tokens)
            print("after>>" + str(self.tokenized_document))
            print("---")
            if len(next_token) == 2:
                next_token = next_token[1].split("\n", 1)
            else:
                next_token = None

        print("cleanup")
        return self.close_open_blocks(
            self.tokenized_document, include_container_blocks=True
        )

    def close_open_blocks(
        self,
        destination_array=None,
        only_these_blocks=None,
        include_container_blocks=False,
    ):
        """
        Close any open blocks that are currently on the stack.
        """

        new_tokens = []
        if destination_array:
            new_tokens = destination_array

        while self.stack[-1] != "document":
            print("cob>>" + str(self.stack))
            if only_these_blocks and self.stack[-1] not in only_these_blocks:
                print("cob>>not in only")
                break
            if not include_container_blocks and self.stack[-1] == "block-quote":
                print("cob>>not block quotes")
                break

            top_element = self.stack[-1]
            extra_elements = []
            if top_element == "icode-block":
                while self.tokenized_document[-1].startswith("[BLANK"):
                    last_element = self.tokenized_document[-1]
                    extra_elements.append(last_element)
                    del self.tokenized_document[-1]

            if top_element.startswith("fcode-block"):
                new_tokens.append("[end-fcode-block:]")
            else:
                new_tokens.append("[end-" + top_element + "]")
            new_tokens.extend(extra_elements)
            del self.stack[-1]
        return new_tokens

    def handle_blank_line(self, input_line, from_main_transform):
        """
        Handle the processing of a blank line.
        """

        if from_main_transform:
            close_only_these_blocks = None
            do_include_container_blocks = True
        else:
            close_only_these_blocks = ["para"]
            do_include_container_blocks = False
        print("from_main_transform>>" + str(from_main_transform))
        print("close_only_these_blocks>>" + str(close_only_these_blocks))
        print("do_include_container_blocks>>" + str(do_include_container_blocks))

        non_whitespace_index, extracted_whitespace = self.extract_whitespace(
            input_line, 0
        )

        new_tokens = None
        if self.stack[-1] == "icode-block":
            stack_bq_count = self.count_of_block_quotes_on_stack()
            if stack_bq_count:
                print("hbl>>indented code block within block quote")
            else:
                print("hbl>>indented code block")
                new_tokens = []
        elif self.stack[-1].startswith("fcode-block:"):
            stack_bq_count = self.count_of_block_quotes_on_stack()

            if stack_bq_count:
                print("hbl>>fenced code block within block quote")
            else:
                print("hbl>>fenced code block")
                new_tokens = []

        if new_tokens is None:
            new_tokens = self.close_open_blocks(
                only_these_blocks=close_only_these_blocks,
                include_container_blocks=do_include_container_blocks,
            )

        print("new_tokens>>" + str(new_tokens))
        assert non_whitespace_index == len(input_line)
        new_tokens.append("[BLANK:" + extracted_whitespace + "]")
        return new_tokens

    def parse_indented_code_block(
        self, line_to_parse, start_index, extracted_whitespace
    ):
        """
        Handle the parsing of an indented code block
        """

        new_tokens = []

        if (
            self.determine_whitespace_length(extracted_whitespace) >= 4
            and self.stack[-1] != "para"
        ):
            if self.stack[-1] != "icode-block":
                self.stack.append("icode-block")
                new_tokens.append("[icode-block:" + extracted_whitespace + "]")
                extracted_whitespace = ""
            new_tokens.append(
                "[text:"
                + line_to_parse[start_index:]
                + ":"
                + extracted_whitespace
                + "]"
            )
        return new_tokens

    def parse_fenced_code_block(self, line_to_parse, start_index, extracted_whitespace):
        """
        Handle the parsing of a fenced code block
        """

        new_tokens = []

        if (
            self.determine_whitespace_length(extracted_whitespace) <= 3
            and start_index < len(line_to_parse)
            and (line_to_parse[start_index] == "~" or line_to_parse[start_index] == "`")
        ):
            collected_count, new_index = self.collect_while_character(
                line_to_parse, start_index, line_to_parse[start_index]
            )
            (
                non_whitespace_index,
                extracted_whitespace_before_info_string,
            ) = self.extract_whitespace(line_to_parse, new_index)

            non_whitespace_index_character = None
            if non_whitespace_index < len(line_to_parse):
                non_whitespace_index_character = line_to_parse[non_whitespace_index]

            if collected_count >= 3 and non_whitespace_index_character != "`":

                preface = "fcode-block:"
                if self.stack[-1].startswith(preface):
                    if (
                        self.stack[-1][len(preface)] == line_to_parse[start_index]
                        and collected_count >= int(self.stack[-1][len(preface) + 2 :])
                        and non_whitespace_index >= len(line_to_parse)
                    ):
                        new_tokens.append(
                            "[end-fcode-block:" + extracted_whitespace + "]"
                        )
                        del self.stack[-1]
                else:

                    if (
                        line_to_parse[start_index] == "~"
                        or "`" not in line_to_parse[non_whitespace_index:]
                    ):
                        (
                            after_extracted_text_index,
                            extracted_text,
                        ) = self.extract_until_whitespace(
                            line_to_parse, non_whitespace_index
                        )
                        text_after_extracted_text = line_to_parse[
                            after_extracted_text_index:
                        ]

                        new_tokens = self.close_open_blocks(only_these_blocks=["para"])

                        self.stack.append(
                            "fcode-block:"
                            + line_to_parse[start_index]
                            + ":"
                            + str(collected_count)
                        )
                        new_tokens.append(
                            "[fcode-block:"
                            + line_to_parse[start_index]
                            + ":"
                            + str(collected_count)
                            + ":"
                            + extracted_text
                            + ":"
                            + text_after_extracted_text
                            + ":"
                            + extracted_whitespace
                            + ":"
                            + extracted_whitespace_before_info_string
                            + "]"
                        )
        return new_tokens

    def parse_thematic_break(
        self, line_to_parse, start_index, extracted_whitespace, this_bq_count,
    ):
        """
        Handle the parsing of a thematic break.
        """

        new_tokens = []
        stack_bq_count = self.count_of_block_quotes_on_stack()

        if (
            self.determine_whitespace_length(extracted_whitespace) <= 3
            and start_index < len(line_to_parse)
            and (
                line_to_parse[start_index] == "*"
                or line_to_parse[start_index] == "-"
                or line_to_parse[start_index] == "_"
            )
        ):
            start_char = line_to_parse[start_index]
            index = start_index

            char_count = 0
            while index < len(line_to_parse):
                if line_to_parse[index] in self.ws_char:
                    index = index + 1
                elif line_to_parse[index] == start_char:
                    index = index + 1
                    char_count = char_count + 1
                else:
                    break

            if char_count >= 3 and index == len(line_to_parse):

                if self.stack[-1] == "para":
                    new_tokens.append("[end-" + self.stack[-1] + "]")
                    del self.stack[-1]
                if this_bq_count == 0 and stack_bq_count > 0:
                    new_tokens = self.close_open_blocks(
                        destination_array=new_tokens,
                        only_these_blocks="block-quote",
                        include_container_blocks=True,
                    )
                new_tokens.append(
                    "[tbreak:"
                    + start_char
                    + ":"
                    + extracted_whitespace
                    + ":"
                    + line_to_parse[start_index:index]
                    + "]"
                )
        return new_tokens

    def parse_atx_headings(self, line_to_parse, start_index, extracted_whitespace):
        """
        Handle the parsing of an atx heading.
        """

        new_tokens = []
        if (
            self.determine_whitespace_length(extracted_whitespace) <= 3
            and start_index < len(line_to_parse)
            and (line_to_parse[start_index] == "#")
        ):
            hash_count, new_index = self.collect_while_character(
                line_to_parse, start_index, "#"
            )
            (
                non_whitespace_index,
                extracted_whitespace_at_start,
            ) = self.extract_whitespace(line_to_parse, new_index)

            if hash_count <= 6 and (
                extracted_whitespace_at_start
                or non_whitespace_index == len(line_to_parse)
            ):

                new_tokens = self.close_open_blocks(new_tokens)
                remaining_line = line_to_parse[non_whitespace_index:]
                (
                    end_index,
                    extracted_whitespace_at_end,
                ) = self.extract_whitespace_from_end(remaining_line)
                while end_index > 0 and remaining_line[end_index - 1] == "#":
                    end_index = end_index - 1
                extracted_whitespace_before_end = ""
                if end_index > 0:
                    if remaining_line[end_index - 1] in self.ws_char:
                        remaining_line = remaining_line[:end_index]
                        (
                            end_index,
                            extracted_whitespace_before_end,
                        ) = self.extract_whitespace_from_end(remaining_line)
                        remaining_line = remaining_line[:end_index]
                    else:
                        extracted_whitespace_at_end = ""
                else:
                    remaining_line = ""

                new_tokens.append(
                    "[atx:"
                    + str(hash_count)
                    + ":"
                    + remaining_line
                    + ":"
                    + extracted_whitespace
                    + ":"
                    + extracted_whitespace_at_start
                    + ":"
                    + extracted_whitespace_at_end
                    + ":"
                    + extracted_whitespace_before_end
                    + "]"
                )
        return new_tokens

    def parse_setext_headings(self, line_to_parse, start_index, extracted_whitespace):
        """
        Handle the parsing of an setext heading.
        """

        new_tokens = []
        if (
            self.determine_whitespace_length(extracted_whitespace) <= 3
            and start_index < len(line_to_parse)
            and (line_to_parse[start_index] == "=" or line_to_parse[start_index] == "-")
            and self.stack[-1] == "para"
        ):

            _, collected_to_index = self.collect_while_character(
                line_to_parse, start_index, line_to_parse[start_index]
            )
            (
                after_whitespace_index,
                extra_whitespace_after_setext,
            ) = self.extract_whitespace(line_to_parse, collected_to_index)
            if after_whitespace_index == len(line_to_parse):
                new_tokens.append(
                    "[end-setext:"
                    + extracted_whitespace
                    + ":"
                    + extra_whitespace_after_setext
                    + "]"
                )
                token_index = len(self.tokenized_document) - 1
                while not self.tokenized_document[token_index].startswith("[para:"):
                    token_index = token_index - 1
                replacement_token = (
                    "[setext:"
                    + line_to_parse[start_index]
                    + ":"
                    + self.tokenized_document[token_index][len("[para:") :]
                )
                self.tokenized_document[token_index] = replacement_token
                del self.stack[-1]
        return new_tokens

    def parse_paragraph(
        self, line_to_parse, start_index, extracted_whitespace, this_bq_count,
    ):
        """
        Handle the parsing of a paragraph.
        """

        new_tokens = []

        stack_bq_count = self.count_of_block_quotes_on_stack()
        print(
            "parse_paragraph>stack_bq_count>"
            + str(stack_bq_count)
            + ">this_bq_count>"
            + str(this_bq_count)
            + "<"
        )
        if stack_bq_count != 0 and this_bq_count == 0:
            new_tokens = self.close_open_blocks(
                only_these_blocks="block-quote", include_container_blocks=True
            )

        if self.stack[-1] != "para":
            self.stack.append("para")
            new_tokens.append("[para:" + extracted_whitespace + "]")
            extracted_whitespace = ""
        new_tokens.append(
            "[text:" + line_to_parse[start_index:] + ":" + extracted_whitespace + "]"
        )
        return new_tokens

    def count_of_block_quotes_on_stack(self):
        """
        Helper method to count the number of block quotes currently on the stack.
        """

        stack_bq_count = 0
        for next_item_on_stack in self.stack:
            if next_item_on_stack == "block-quote":
                stack_bq_count = stack_bq_count + 1

        return stack_bq_count

    @classmethod
    def count_block_quote_starts(cls, line_to_parse, start_index):
        """
        Having detected a block quote character (">") on a line, continue to consume
        and count while the block quote pattern is there.
        """

        this_bq_count = 1
        start_index = start_index + 1

        while True:
            if start_index < len(line_to_parse) and line_to_parse[start_index] == " ":
                start_index = start_index + 1
            if start_index == len(line_to_parse) or line_to_parse[start_index] != ">":
                break
            this_bq_count = this_bq_count + 1
            start_index = start_index + 1
        return this_bq_count, start_index

    def check_for_lazy_handling(self, this_bq_count, stack_bq_count, line_to_parse, start_index, extracted_whitespace):
        """
        Check if there is any processing to be handled during the handling of
        lazy continuation lines in block quotes.
        """

        container_level_tokens = []
        if this_bq_count == 0 and stack_bq_count > 0:
            print("haven't processed")
            print(
                "this_bq_count>"
                + str(this_bq_count)
                + ">>stack_bq_count>>"
                + str(stack_bq_count)
                + "<<"
            )
            if (
                self.stack[-1].startswith("fcode-block:")
                or self.stack[-1] == "icode-block"
            ):
                assert not container_level_tokens
                container_level_tokens = self.close_open_blocks(
                    only_these_blocks=["block-quote", self.stack[-1]],
                    include_container_blocks=True,
                )

        if stack_bq_count > 0:
            if (
                self.determine_whitespace_length(extracted_whitespace) <= 3
                and start_index < len(line_to_parse)
                and (
                    line_to_parse[start_index] == "="
                    or line_to_parse[start_index] == "-"
                )
                and self.stack[-1] == "para"
            ):
                print("set_atx")
                assert not container_level_tokens
                container_level_tokens = self.close_open_blocks(
                    only_these_blocks=["para", "block-quote"],
                    include_container_blocks=True,
                )
            else:
                print("no set atx!!!!!!!!!!!!")

        return container_level_tokens

    def ensure_stack_at_level(self, this_bq_count, stack_bq_count, extracted_whitespace):

        container_level_tokens = []
        if this_bq_count > stack_bq_count:
            container_level_tokens = self.close_open_blocks(
                only_these_blocks=["para"]
            )
            while this_bq_count > stack_bq_count:
                self.stack.append("block-quote")
                stack_bq_count = stack_bq_count + 1
                container_level_tokens.append(
                    "[block-quote:" + extracted_whitespace + "]"
                )
        return container_level_tokens, stack_bq_count

    def handle_block_quote_section(self, line_to_parse, start_index, this_bq_count, stack_bq_count, extracted_whitespace):
        leaf_tokens = []
        container_level_tokens = []

        this_bq_count, start_index = self.count_block_quote_starts(
            line_to_parse, start_index
        )

        if not self.stack[-1].startswith("fcode-block:"):
            container_level_tokens, stack_bq_count = self.ensure_stack_at_level(this_bq_count, stack_bq_count, extracted_whitespace)

            line_to_parse = line_to_parse[start_index:]

            if not line_to_parse.strip():
                leaf_tokens = self.handle_blank_line(
                    line_to_parse, from_main_transform=False
                )
        return line_to_parse, start_index, leaf_tokens, container_level_tokens, stack_bq_count, this_bq_count

    def parse_line_for_container_blocks(self, line_to_parse):
        """
        Parse the line, taking care to handle any container blocks before deciding
        whether or not to pass the (remaining parts of the) line to the leaf block
        processor.
        """

        print("Line:" + line_to_parse + ":")
        container_level_tokens = []
        leaf_tokens = []
        start_index, extracted_whitespace = self.extract_whitespace(line_to_parse, 0)

        stack_bq_count = self.count_of_block_quotes_on_stack()

        this_bq_count = 0
        if self.determine_whitespace_length(extracted_whitespace) <= 3 \
            and line_to_parse[start_index] == ">":

            assert not container_level_tokens
            assert not leaf_tokens
            line_to_parse, start_index, leaf_tokens, container_level_tokens, stack_bq_count, this_bq_count = self.handle_block_quote_section(line_to_parse, start_index, this_bq_count, stack_bq_count, extracted_whitespace)

        if not leaf_tokens:
            lazy_tokens = self.check_for_lazy_handling(this_bq_count, stack_bq_count, line_to_parse, start_index, extracted_whitespace)
            container_level_tokens.extend(lazy_tokens)

        if leaf_tokens:
            print("adding tokesn>>" + str(leaf_tokens))
        else:
            print("parsing leaf>>")
            leaf_tokens = self.parse_line_for_leaf_blocks(
                line_to_parse, 0, this_bq_count
            )
            print("parsed leaf>>" + str(leaf_tokens))

        container_level_tokens.extend(leaf_tokens)
        return container_level_tokens

    def parse_line_for_leaf_blocks(self, line_to_parse, start_index, this_bq_count):
        """
        Parse the contents of a line for a leaf block.
        """

        print("Leaf Line:" + line_to_parse + ":")
        new_tokens = []
        pre_tokens = []
        start_index, extracted_whitespace = self.extract_whitespace(
            line_to_parse, start_index
        )

        if (
            self.stack[-1] == "icode-block"
            and self.determine_whitespace_length(extracted_whitespace) <= 3
        ):
            pre_tokens.append("[end-" + self.stack[-1] + "]")
            del self.stack[-1]
            while self.tokenized_document[-1].startswith("[BLANK"):
                last_element = self.tokenized_document[-1]
                pre_tokens.append(last_element)
                del self.tokenized_document[-1]

        new_tokens = self.parse_fenced_code_block(
            line_to_parse, start_index, extracted_whitespace
        )
        if self.stack[-1].startswith("fcode-block:"):
            if not new_tokens:
                new_tokens.append(
                    "[text:"
                    + line_to_parse[start_index:]
                    + ":"
                    + extracted_whitespace
                    + "]"
                )
        else:
            if not new_tokens:
                new_tokens = self.parse_atx_headings(
                    line_to_parse, start_index, extracted_whitespace
                )
            if not new_tokens:
                new_tokens = self.parse_indented_code_block(
                    line_to_parse, start_index, extracted_whitespace
                )
            if not new_tokens:
                new_tokens = self.parse_setext_headings(
                    line_to_parse, start_index, extracted_whitespace
                )
            if not new_tokens:
                new_tokens = self.parse_thematic_break(
                    line_to_parse, start_index, extracted_whitespace, this_bq_count,
                )
            if not new_tokens:
                new_tokens = self.parse_paragraph(
                    line_to_parse, start_index, extracted_whitespace, this_bq_count,
                )

        pre_tokens.extend(new_tokens)
        return pre_tokens

    @classmethod
    def collect_while_character(cls, line_to_parse, start_index, match_character):
        """
        Collect a sequence of the same character from a given starting point in a string.
        """

        index = start_index
        while index < len(line_to_parse) and line_to_parse[index] == match_character:
            index = index + 1
        return index - start_index, index

    def extract_whitespace(self, source_string, start_index):
        """
        From the start_index, continue extracting whitespace while we have it.
        """

        index = start_index
        while index < len(source_string) and source_string[index] in self.ws_char:
            index = index + 1

        return index, source_string[start_index:index]

    def extract_until_whitespace(self, source_string, start_index):
        """
        From the start_index, continue extracting until we hit whitespace.
        """

        index = start_index
        while index < len(source_string) and source_string[index] not in self.ws_char:
            index = index + 1

        return index, source_string[start_index:index]

    def extract_whitespace_from_end(self, source_string):
        """
        From the start_index, continue extracting whitespace while we have it.
        """
        if not source_string:
            return 0, ""

        index = len(source_string) - 1
        while index >= 0 and source_string[index] in self.ws_char:
            index = index - 1

        return index + 1, source_string[index + 1 :]

    @classmethod
    def determine_whitespace_length(cls, extracted_whitespace):
        """
        Given a string of whitespace characters, determine the length.
        """

        whitespace_length = 0
        for next_character in extracted_whitespace:
            if next_character == " ":
                whitespace_length = whitespace_length + 1
            else:
                whitespace_length = whitespace_length + 4
        return whitespace_length
