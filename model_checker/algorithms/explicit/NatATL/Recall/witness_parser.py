"""
Witness parser for NatATL Recall regex patterns.

This module generates witness words (sequences of atomic propositions) that
match regex patterns used in recall strategies. It handles patterns with
Kleene star (*) and concatenation (.) operators.
"""


class RegexWitnessGenerator:
    """
    Generator for witness words matching regex patterns.

    Generates all possible sequences of atomic propositions that match a given
    regex pattern. Supports Kleene star (*) for repetition and concatenation (.)
    for sequencing.

    Example:
        Pattern "a and b.q*" with length 3 generates words like:
        - "a and b . q . q"
        - "a and b . q . q . q"
    """

    def __init__(self, pattern: str, length: int):
        """
        Initialize witness generator.

        Args:
            pattern: Regex pattern string (e.g., "a and b.q*")
            length: Desired length of generated witness words
        """
        self.original_pattern = pattern
        self.length = length
        self.groups = self._split_groups_by_star(pattern)
        self.generated = set()
        self._generate_combinations()

    def _split_groups_by_star(self, pattern: str) -> list:
        """
        Split pattern into groups separated by '*' or '.' operators.

        Args:
            pattern: Regex pattern string

        Returns:
            List of pattern groups, with '*' preserved in group strings
        """
        groups = []
        buffer = []
        for char in pattern:
            if char == "*" or char == ".":
                if char == "*":
                    if buffer:
                        groups.append("".join(buffer) + "*")
                        buffer = []
                else:
                    if buffer:
                        groups.append("".join(buffer))
                        buffer = []
            else:
                buffer.append(char)
        if buffer:
            groups.append("".join(buffer))
        return groups

    def _generate_combinations(self) -> None:
        """Generate all possible witness word combinations matching the pattern."""
        self.combinations = []
        self._backtrack([], 0)

    def _backtrack(self, current: list, pos: int) -> None:
        """
        Backtracking algorithm to generate witness words.

        Args:
            current: Current partial word being built
            pos: Current position in groups list
        """
        if pos >= len(self.groups):
            if len(current) == self.length:
                self.combinations.append(" . ".join(current))
            return

        group = self.groups[pos]
        if group.endswith("*"):
            base = group[:-1]
            remaining_length = self.length - len(current)
            for i in range(remaining_length + 1):
                self._backtrack(current + [base] * i, pos + 1)
        else:
            if len(current) < self.length:
                self._backtrack(current + [group], pos + 1)

    def next_word(self) -> str | None:
        """
        Get the next generated witness word.

        Returns:
            Next witness word string, or None if all words have been generated
        """
        while self.combinations:
            word = self.combinations.pop(0)
            if word not in self.generated:
                self.generated.add(word)
                return word
        return None


def store_word(word: str) -> list[str]:
    """
    Parse a witness word string into a list of proposition strings.

    Splits a witness word (e.g., "a and b . q . q") into individual
    proposition components, removing whitespace.

    Args:
        word: Witness word string with " . " separators

    Returns:
        List of proposition strings

    Example:
        store_word("a and b . q . q") -> ["a and b", "q", "q"]
    """
    substrings = word.split(" . ")
    result = []
    for substring in substrings:
        result.append(substring.strip())
    return result
