"""Generate the words of propositions that match NatATL Recall regex patterns, with
`*` and `.`."""


class RegexWitnessGenerator:
    """Generates the words of propositions that match a regex with `*` (repetition)
    and `.` (sequencing): `a and b.q*` gives `a and b . q . q` and longer words."""

    def __init__(self, pattern: str, length: int):
        """`pattern` is a regex such as `"a and b.q*"`; `length` is the word length."""
        self.original_pattern = pattern
        self.length = length
        self.groups = self._split_groups_by_star(pattern)
        self.generated = set()
        self._generate_combinations()

    def _split_groups_by_star(self, pattern: str) -> list:
        """Split `pattern` at `*` and `.` into groups, each `*` kept in its group."""
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
        """Extend the partial word `current` from group `pos` on, by backtracking."""
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
        """The next witness word, or None when all have been generated."""
        while self.combinations:
            word = self.combinations.pop(0)
            if word not in self.generated:
                self.generated.add(word)
                return word
        return None


def store_word(word: str) -> list[str]:
    """Split a witness word on ` . `.

    `"a and b . q . q"` gives `["a and b", "q", "q"]`.
    """
    substrings = word.split(" . ")
    result = []
    for substring in substrings:
        result.append(substring.strip())
    return result
