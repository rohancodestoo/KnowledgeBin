from notes.utils import generate_image_description, generate_image, generate_completion, generate_summary, generate_tags

def test_utils():
    print("Testing generate_image_description...")
    desc = generate_image_description("My Daily Journal")
    print(f"Description: {desc}")
    
    print("\nTesting generate_image...")
    url = generate_image(desc)
    print(f"Image URL: {url}")
    
    print("\nTesting generate_completion...")
    comp = generate_completion("The quick brown fox jumps over")
    print(f"Completion: {comp}")
    
    print("\nTesting generate_summary...")
    summary = generate_summary("Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation. Python is dynamically typed and garbage-collected. It supports multiple programming paradigms, including structured, object-oriented and functional programming.")
    print(f"Summary: {summary}")
    
    print("\nTesting generate_tags...")
    tags = generate_tags("Meeting notes for the Q3 marketing strategy. We need to focus on social media growth and SEO optimization.")
    print(f"Tags: {tags}")

if __name__ == "__main__":
    test_utils()
