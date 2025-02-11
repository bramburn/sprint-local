# diff_match_patch.py

from typing import List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class Snake:
    start_x: int
    start_y: int
    end_x: int
    end_y: int


@dataclass
class Box:
    left: int
    top: int
    right: int
    bottom: int


class DiffMatchPatch:
    def __init__(self):
        pass

    def myers_diff(
        self, a: List[str], b: List[str]
    ) -> List[Tuple[str, Optional[str], Optional[str]]]:
        """
        Computes the diff between two lists of strings using the linear space Myers' diff algorithm.

        Returns a list of tuples representing the diff operations:
        ('=', line)   # No change
        ('-', line)   # Deletion
        ('+', line)   # Insertion
        """

        def find_middle_snake(box: Box, a: List[str], b: List[str]) -> Optional[Snake]:
            """
            Finds the middle snake within the given box.
            """
            N = box.right - box.left
            M = box.bottom - box.top
            delta = N - M
            max_d = (N + M + 1) // 2
            size = 2 * max_d + 1
            vf = [0] * size
            vb = [0] * size
            vf_offset = max_d
            vb_offset = max_d
            vf[vf_offset + 1] = box.left
            vb[vb_offset + 1] = box.right

            for d in range(max_d + 1):
                # Forward search
                for k in range(-d, d + 1, 2):
                    index = k + vf_offset
                    if k == -d or (k != d and vf[index - 1] < vf[index + 1]):
                        x = vf[index + 1]
                    else:
                        x = vf[index - 1] + 1
                    y = x - k
                    # Follow diagonal (snake)
                    while (
                        x < box.right
                        and y < box.bottom
                        and a[box.left + x] == b[box.top + y]
                    ):
                        x += 1
                        y += 1
                    vf[index] = x
                    # Check for overlap
                    c = k - delta
                    if 0 <= c < size:
                        overlap_val = vb[c + vb_offset]
                        if overlap_val >= x:
                            return Snake(
                                start_x=x,
                                start_y=y - c,
                                end_x=vb[c + vb_offset],
                                end_y=y,
                            )

                # Reverse search
                for k in range(-d, d + 1, 2):
                    c = k - delta
                    index = c + vb_offset
                    if k == -d or (k != d and vb[index - 1] > vb[index + 1]):
                        y = vb[index + 1]
                    else:
                        y = vb[index - 1] + 1
                    x = y + c
                    # Follow diagonal (snake)
                    while (
                        x > box.left
                        and y > box.top
                        and a[box.left + x - 1] == b[box.top + y - 1]
                    ):
                        x -= 1
                        y -= 1
                    vb[index] = y
                    # Check for overlap
                    fk = x - (y - c)
                    if 0 <= fk < size:
                        overlap_val = vf[fk + vf_offset]
                        if overlap_val >= x:
                            return Snake(
                                start_x=vf[fk + vf_offset],
                                start_y=y - c,
                                end_x=x,
                                end_y=y,
                            )

            return None

        def process_box(box: Box, a: List[str], b: List[str]) -> List[Snake]:
            """
            Recursively processes the given box to find all snakes.
            """
            # Base case: If the box is invalid, return an empty list
            if box.left >= box.right or box.top >= box.bottom:
                return []

            snake = find_middle_snake(box, a, b)
            if not snake:
                return []

            # Define sub-boxes
            left_box = Box(box.left, box.top, snake.start_x, snake.start_y)
            right_box = Box(snake.end_x, snake.end_y, box.right, box.bottom)

            # Recursively process sub-boxes
            return process_box(left_box, a, b) + [snake] + process_box(right_box, a, b)

        # Initialize the initial box covering the entire sequences
        initial_box = Box(0, 0, len(a), len(b))
        snakes = process_box(initial_box, a, b)

        # Reconstruct the diff from snakes
        diffs = []
        x, y = 0, 0
        for snake in snakes:
            # Handle deletions and insertions
            while x < snake.start_x and y < snake.start_y:
                if a[x] == b[y]:
                    diffs.append(("=", a[x], a[x]))
                else:
                    diffs.append(("-", a[x], None))
                    diffs.append(("+", None, b[y]))
                x += 1
                y += 1
            while x < snake.start_x:
                diffs.append(("-", a[x], None))
                x += 1
            while y < snake.start_y:
                diffs.append(("+", None, b[y]))
                y += 1
            # Handle equal (snake)
            for i in range(snake.start_x, snake.end_x):
                diffs.append(("=", a[i], a[i]))
                x += 1
                y += 1
        # Handle any remaining operations
        while x < len(a):
            diffs.append(("-", a[x], None))
            x += 1
        while y < len(b):
            diffs.append(("+", None, b[y]))
            y += 1

        return diffs
