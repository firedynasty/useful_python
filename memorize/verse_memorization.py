import difflib
import pyperclip

def main():
    print("Welcome to the Verse Memorization Trainer!")
    print("----------------------------------------")
    
    # Get the verse to memorize
    memorized_verse = input("Enter the verse you want to memorize: ")
    print("\nGreat! Now you can practice recalling this verse.")
    
    while True:
        print("\nOptions:")
        print("0: Change the memorized verse")
        print("1: Test your memory")
        print("2: Quit")
        
        choice = input("\nEnter your choice (0/1/2): ")
        
        if choice == "0":
            memorized_verse = input("Enter the new verse to memorize: ")
            print("Verse updated successfully!")
            
        elif choice == "1":
            print("\nNow try to recall the verse from memory...")
            attempt = input("Your attempt: ")
            
            # Compare the attempt with the original verse
            similarity = compare_verses(memorized_verse, attempt)
            percentage = similarity * 100
            
            print(f"\nAccuracy: {percentage:.1f}%")
            
            # Show differences
            if similarity < 1.0:
                print("\nHere's where your recall differs from the original:")
                show_differences(memorized_verse, attempt)
            else:
                print("\nPerfect recall! Great job!")
            
            # Copy to clipboard in the required format
            clipboard_text = f"""first input: {memorized_verse}, second input: {attempt}"""
            pyperclip.copy(clipboard_text)
            print("\nResults copied to clipboard!")
            
        elif choice == "2":
            print("Thank you for using the Verse Memorization Trainer. Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

def compare_verses(original, attempt):
    """Calculate similarity ratio between original verse and attempt"""
    matcher = difflib.SequenceMatcher(None, original, attempt)
    return matcher.ratio()

def show_differences(original, attempt):
    """Display the differences between original verse and attempt"""
    d = difflib.Differ()
    diff = list(d.compare(original.splitlines(), attempt.splitlines()))
    
    if not original.splitlines() or not attempt.splitlines():
        # Handle case where one of them doesn't have newlines
        diff = list(d.compare([original], [attempt]))
    
    for line in diff:
        if line.startswith('+ '):
            print(f"\033[92m{line}\033[0m")  # Green for additions
        elif line.startswith('- '):
            print(f"\033[91m{line}\033[0m")  # Red for deletions
        elif line.startswith('? '):
            continue  # Skip the markers
        else:
            print(line)  # Unchanged lines
            
if __name__ == "__main__":
    main()

    