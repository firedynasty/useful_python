#!/usr/bin/env python3
"""
Mental Subtraction Practice
Based on Arthur Benjamin's "Secrets of Mental Math"

Supports:
- 3-digit minus 3-digit
- 4-digit minus 3-digit

Key technique: Work left to right, not right to left
"""

import random
import time
import re


def extract_answer(user_input):
    """
    Extract the final answer from user input.

    User can write notes and put final answer in quotes at the end.
    Example: '9210 - 500 8710+ 4 ; "8714"' → extracts 8714

    If no quotes found, tries to parse the entire input as a number.
    """
    # Look for quoted answer (supports both " and ')
    match = re.search(r'["\'](-?\d+)["\']', user_input)
    if match:
        return int(match.group(1))

    # Fallback: try to parse the whole input as a number
    cleaned = user_input.strip()
    if cleaned.lstrip('-').isdigit():
        return int(cleaned)

    raise ValueError("No valid answer found")


def generate_problem(mode):
    """Generate a subtraction problem based on the selected mode."""
    if mode == 1:  # 3-digit minus 3-digit
        num1 = random.randint(100, 999)
        num2 = random.randint(100, 999)
    elif mode == 2:  # 4-digit minus 3-digit
        num1 = random.randint(1000, 9999)
        num2 = random.randint(100, 999)
    else:
        raise ValueError("Invalid mode")

    # Ensure num1 >= num2 (no negative results)
    if num1 < num2:
        num1, num2 = num2, num1
        # If we swapped and mode was 2, num1 might now be 3-digit
        # Regenerate to maintain 4-digit minus 3-digit
        if mode == 2 and num1 < 1000:
            num1 = random.randint(1000, 9999)

    return num1, num2


def show_benjamin_technique(num1, num2):
    """
    Show Arthur Benjamin's left-to-right subtraction technique.

    The key insight: subtract left to right, adjusting as you go.
    Example: 567 - 284
    - 500 - 200 = 300 (keep running total: 300)
    - 60 - 80 = -20 (adjust: 300 - 20 = 280)
    - 7 - 4 = 3 (final: 280 + 3 = 283)
    """
    print("\n--- Arthur Benjamin's Left-to-Right Technique ---")
    print(f"Problem: {num1} - {num2}")

    str1 = str(num1)
    str2 = str(num2).zfill(len(str1))  # Pad with zeros to match length

    running_total = 0
    place_values = [10 ** (len(str1) - 1 - i) for i in range(len(str1))]

    print("\nStep by step:")
    for i, (d1, d2, place) in enumerate(zip(str1, str2, place_values)):
        digit1 = int(d1)
        digit2 = int(d2)
        diff = (digit1 - digit2) * place
        running_total += diff

        place_name = {1000: "thousands", 100: "hundreds", 10: "tens", 1: "ones"}.get(place, f"{place}s")

        print(f"  {place_name}: {digit1} - {digit2} = {digit1 - digit2} → {diff:+d}")
        print(f"    Running total: {running_total}")

    print(f"\nFinal answer: {running_total}")
    return running_total


def complement_technique(num1, num2):
    """
    Show the complement technique for subtraction.

    Example: 1000 - 643
    - Find complement of 643 to 1000: 357 (each digit's complement to 9, last to 10)
    """
    print("\n--- Complement Technique (for round numbers) ---")
    print(f"Problem: {num1} - {num2}")

    # Check if num1 is a round number (power of 10)
    str1 = str(num1)
    if str1[0] == '1' and all(c == '0' for c in str1[1:]):
        print(f"\n{num1} is a round number! Use complement method:")
        print(f"Find the complement of {num2} to {num1}")

        str2 = str(num2)
        complement_digits = []

        for i, digit in enumerate(str2):
            d = int(digit)
            if i == len(str2) - 1:  # Last digit
                comp = 10 - d if d != 0 else 0
            else:
                comp = 9 - d
            complement_digits.append(str(comp))
            print(f"  Digit {digit}: complement is {comp}")

        result = int(''.join(complement_digits))
        print(f"\nComplement: {result}")
    else:
        print("(This technique works best when subtracting from round numbers like 100, 1000, etc.)")
        result = num1 - num2
        print(f"Answer: {result}")

    return result


def practice_session(mode, num_problems=10):
    """Run a practice session."""
    mode_names = {
        1: "3-digit minus 3-digit",
        2: "4-digit minus 3-digit"
    }

    print(f"\n{'='*50}")
    print(f"Practice Mode: {mode_names[mode]}")
    print(f"Number of problems: {num_problems}")
    print("Write your working, put final answer in quotes: \"8714\"")
    print("Or just type the number directly")
    print("Type 'q' to quit, 'h' for hint/technique")
    print(f"{'='*50}\n")

    correct = 0
    total = 0
    total_time = 0

    for i in range(num_problems):
        num1, num2 = generate_problem(mode)
        answer = num1 - num2

        print(f"\nProblem {i + 1}/{num_problems}:")
        print(f"  {num1}")
        print(f"- {num2}")
        print("-" * (len(str(num1)) + 2))

        start_time = time.time()
        user_input = input("Your answer: ").strip()
        elapsed = time.time() - start_time

        if user_input.lower() == 'q':
            print("\nQuitting practice session...")
            break
        elif user_input.lower() == 'h':
            show_benjamin_technique(num1, num2)
            # Give another chance after hint
            user_input = input("\nTry again: ").strip()
            if user_input.lower() == 'q':
                break
            elapsed = time.time() - start_time

        try:
            user_answer = extract_answer(user_input)
            total += 1
            total_time += elapsed

            if user_answer == answer:
                correct += 1
                print(f"✓ Correct! ({elapsed:.1f}s)")
            else:
                print(f"✗ Incorrect. The answer is {answer}")
                show_benjamin_technique(num1, num2)
        except ValueError:
            print(f"Invalid input. The answer was {answer}")
            total += 1

    # Show results
    if total > 0:
        print(f"\n{'='*50}")
        print("SESSION RESULTS")
        print(f"{'='*50}")
        print(f"Score: {correct}/{total} ({100*correct/total:.1f}%)")
        print(f"Average time: {total_time/total:.1f} seconds per problem")
        print(f"{'='*50}")


def main():
    """Main menu."""
    print("""
╔══════════════════════════════════════════════════════╗
║       MENTAL SUBTRACTION PRACTICE                    ║
║   Based on Arthur Benjamin's "Secrets of Mental Math"║
╚══════════════════════════════════════════════════════╝
    """)

    while True:
        print("\nSelect mode:")
        print("  1. 3-digit minus 3-digit  (e.g., 567 - 284)")
        print("  2. 4-digit minus 3-digit  (e.g., 4523 - 876)")
        print("  3. Learn the technique (demonstration)")
        print("  4. Quit")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == '1':
            try:
                n = int(input("How many problems? [10]: ").strip() or "10")
            except ValueError:
                n = 10
            practice_session(1, n)
        elif choice == '2':
            try:
                n = int(input("How many problems? [10]: ").strip() or "10")
            except ValueError:
                n = 10
            practice_session(2, n)
        elif choice == '3':
            print("\n--- DEMONSTRATION ---")
            # 3-digit example
            show_benjamin_technique(567, 284)
            print()
            # 4-digit example
            show_benjamin_technique(4523, 876)
            print()
            # Complement example
            complement_technique(1000, 643)
        elif choice == '4':
            print("\nGoodbye! Keep practicing!")
            break
        else:
            print("Invalid choice. Please enter 1-4.")


if __name__ == "__main__":
    main()
